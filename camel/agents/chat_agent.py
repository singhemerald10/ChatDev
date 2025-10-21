# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from camel.agents import BaseAgent
from camel.configs import ChatGPTConfig
from camel.messages import ChatMessage, MessageType, SystemMessage
from camel.model_backend import ModelBackend, ModelFactory
from camel.typing import ModelType, RoleType
from camel.utils import (
    get_model_token_limit,
    num_tokens_from_messages,
    openai_api_key_required,
)
from chatdev.utils import log_visualize

try:
    from openai.types.chat import ChatCompletion
    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version


@dataclass(frozen=True)
class ChatAgentResponse:
    msgs: List[ChatMessage]
    terminated: bool
    info: Dict[str, Any]

    @property
    def msg(self):
        if self.terminated:
            raise RuntimeError(f"error in ChatAgentResponse, info:{self.info}")
        if len(self.msgs) > 1:
            raise RuntimeError("Property msg is only available for a single message")
        if len(self.msgs) == 0:
            if len(self.info) > 0:
                raise RuntimeError(f"Empty msgs in ChatAgentResponse, info:{self.info}")
            return None
        return self.msgs[0]


class ChatAgent(BaseAgent):
    """Class for managing conversations of CAMEL Chat Agents."""

    def __init__(
        self,
        system_message: SystemMessage,
        memory=None,
        model: Optional[ModelType] = None,
        model_config: Optional[Any] = None,
        message_window_size: Optional[int] = None,
    ) -> None:
        self.system_message: SystemMessage = system_message
        self.role_name: str = system_message.role_name
        self.role_type: RoleType = system_message.role_type
        self.model: ModelType = model if model is not None else ModelType.GPT_3_5_TURBO
        self.model_config: ChatGPTConfig = model_config or ChatGPTConfig()
        self.model_token_limit: int = get_model_token_limit(self.model)
        self.message_window_size: Optional[int] = message_window_size
        self.model_backend: ModelBackend = ModelFactory.create(
            self.model, self.model_config.__dict__
        )
        self.terminated: bool = False
        self.info: bool = False
        self.init_messages()

        if (
            memory is not None
            and self.role_name in ["Code Reviewer", "Programmer", "Software Test Engineer"]
        ):
            self.memory = memory
        else:
            self.memory = None

    def reset(self) -> List[MessageType]:
        self.terminated = False
        self.init_messages()
        return self.stored_messages

    def get_info(
        self,
        id: Optional[str],
        usage: Optional[Dict[str, int]],
        termination_reasons: List[str],
        num_tokens: int,
    ) -> Dict[str, Any]:
        return {
            "id": id,
            "usage": usage,
            "termination_reasons": termination_reasons,
            "num_tokens": num_tokens,
        }

    def init_messages(self) -> None:
        self.stored_messages: List[MessageType] = [self.system_message]

    def update_messages(self, message: ChatMessage) -> List[MessageType]:
        self.stored_messages.append(message)
        return self.stored_messages

    # camel/agents/chat_agent.py

    # ... inside the ChatAgent class ...

    def use_memory(self, input_message) -> Optional[str]:
        """
        Retrieves relevant memories from the HybridMemory instance.
        Accepts either a ChatMessage or a raw string.
        """
        if self.memory is None:
            return None

        # --- Handle both ChatMessage and str inputs safely ---
        if isinstance(input_message, str):
            query = input_message
        elif hasattr(input_message, "content"):
            query = input_message.content
        else:
            raise TypeError(f"Unexpected input type for use_memory: {type(input_message)}")

        # Retrieve top-k relevant entries
        retrieved_entries = self.memory.retrieve(query, k=5)

        if not retrieved_entries:
            log_visualize(self.role_name, "thinking back but found nothing useful")
            return None

        target_memory = [entry["text"] for entry in retrieved_entries]

        if self.role_name == "Programmer":
            target_memory_str = "".join(target_memory)
            log_visualize(
                self.role_name,
                f"thinking back and found related code:\n--------------------------\n{target_memory_str}",
            )
        else:
            target_memory_str = "; ".join(target_memory)
            log_visualize(
                self.role_name,
                f"thinking back and found related text:\n--------------------------\n{target_memory_str}",
            )

        return target_memory_str

    @retry(wait=wait_exponential(min=5, max=60), stop=stop_after_attempt(5))
    @openai_api_key_required
    def step(self, input_message: ChatMessage) -> ChatAgentResponse:
        """Performs a single step in the chat session by generating a response."""
        messages = self.update_messages(input_message)
        if self.message_window_size is not None and len(messages) > self.message_window_size:
            messages = [self.system_message] + messages[-self.message_window_size:]

        openai_messages = [m.to_openai_message() for m in messages]
        num_tokens = num_tokens_from_messages(openai_messages, self.model)

        output_messages: Optional[List[ChatMessage]]
        info: Dict[str, Any]

        if num_tokens < self.model_token_limit:
            response = self.model_backend.run(messages=openai_messages)

            # ----- NEW OPENAI API -----
            if openai_new_api:
                if not isinstance(response, ChatCompletion):
                    raise RuntimeError("OpenAI returned unexpected struct")

                output_messages = []
                for choice in response.choices:
                    message_dict = dict(choice.message)
                    # Strip out unsupported fields
                    for k in ["annotations", "refusal", "tool_calls", "function_call"]:
                        message_dict.pop(k, None)

                    chat_message = ChatMessage(
                        role_name=self.role_name,
                        role_type=self.role_type,
                        meta_dict=dict(),
                        **message_dict,
                    )
                    output_messages.append(chat_message)

                info = self.get_info(
                    response.id,
                    response.usage,
                    [str(choice.finish_reason) for choice in response.choices],
                    num_tokens,
                )

            # ----- OLD OPENAI API -----
            else:
                if not isinstance(response, dict):
                    raise RuntimeError("OpenAI returned unexpected struct")

                output_messages = []
                for choice in response["choices"]:
                    message_dict = dict(choice["message"])
                    for k in ["annotations", "refusal", "tool_calls", "function_call"]:
                        message_dict.pop(k, None)

                    chat_message = ChatMessage(
                        role_name=self.role_name,
                        role_type=self.role_type,
                        meta_dict=dict(),
                        **message_dict,
                    )
                    output_messages.append(chat_message)

                info = self.get_info(
                    response["id"],
                    response["usage"],
                    [str(choice["finish_reason"]) for choice in response["choices"]],
                    num_tokens,
                )

            # Detect <INFO> phase marker
            if (
                output_messages
                and output_messages[0].content.split("\n")[-1].startswith("<INFO>")
            ):
                self.info = True

        else:
            self.terminated = True
            output_messages = []
            info = self.get_info(
                None,
                None,
                ["max_tokens_exceeded_by_camel"],
                num_tokens,
            )

        return ChatAgentResponse(output_messages, self.terminated, info)

    def __repr__(self) -> str:
        return f"ChatAgent({self.role_name}, {self.role_type}, {self.model})"

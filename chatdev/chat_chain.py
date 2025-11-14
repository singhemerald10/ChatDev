import importlib
import json
import logging
import os
import shutil
import time
from datetime import datetime

from camel.agents import RolePlaying
from camel.configs import ChatGPTConfig
from camel.typing import TaskType, ModelType
from chatdev.chat_env import ChatEnv, ChatEnvConfig
from chatdev.statistics import get_info
from camel.web_spider import modal_trans
from chatdev.utils import log_visualize, now

from chatdev.role_validation import RoleValidator
from chatdev.cycle_detector import CycleDetector
from chatdev.hybrid_memory import HybridMemory
from chatdev.dta import DynamicTerminationAgent

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
memory_path = os.path.join(root_dir, "ecl", "memory", "chatdev_memory.json")


def check_bool(s):
    return str(s).lower() == "true"


class ChatChain:
    """
    ChatChain — Reliability-Enhanced Orchestration Class
    Integrates Role Validation, Cycle Detection, Hybrid Memory, and Dynamic Termination
    into the ChatDev software development workflow.
    """

    def __init__(self,
                 config_path: str,
                 config_phase_path: str,
                 config_role_path: str,
                 config_constraints_path: str,
                 task_prompt: str,
                 project_name: str,
                 org_name: str,
                 model_type: ModelType = ModelType.GPT_3_5_TURBO,
                 code_path: str = None):

        # --- Load Configurations ---
        self.config_path = config_path
        self.config_phase_path = config_phase_path
        self.config_role_path = config_role_path
        self.config_constraints_path = config_constraints_path
        self.task_prompt_raw = task_prompt
        self.project_name = project_name
        self.org_name = org_name
        self.model_type = model_type
        self.code_path = code_path

        with open(self.config_path, "r", encoding="utf8") as f:
            self.config = json.load(f)
        with open(self.config_phase_path, "r", encoding="utf8") as f:
            self.config_phase = json.load(f)
        with open(self.config_role_path, "r", encoding="utf8") as f:
            self.config_role = json.load(f)
        with open(self.config_constraints_path, "r", encoding="utf8") as f:
            self.config_constraints = json.load(f)

        # --- Chain Configuration ---
        self.chain = self.config["chain"]
        self.recruitments = self.config["recruitments"]
        self.web_spider = self.config.get("web_spider", False)

        self.chat_turn_limit_default = int(self.config.get("chat_turn_limit_default", 10))

        # --- Initialize Environment ---
        self.chat_env_config = ChatEnvConfig(
            clear_structure=check_bool(self.config["clear_structure"]),
            gui_design=check_bool(self.config["gui_design"]),
            git_management=check_bool(self.config["git_management"]),
            incremental_develop=check_bool(self.config["incremental_develop"]),
            background_prompt=self.config["background_prompt"],
            with_memory=check_bool(self.config["with_memory"])
        )
        self.chat_env = ChatEnv(self.chat_env_config)

        # --- Initialize Reliability Modules ---
        self.role_validator = RoleValidator(self.config_constraints)
        self.cycle_detector = CycleDetector(window=16, min_cycle_len=2, sim_threshold=0.85)
        self.hybrid_memory = HybridMemory(storage_path=memory_path)
        self.dta = DynamicTerminationAgent(
            max_steps=int(self.config.get("max_steps", 500)),
            idle_threshold_sec=int(self.config.get("idle_timeout_sec", 300)),
            cycle_limit=int(self.config.get("cycle_limit", 3))
        )

        # --- Initialize Logging ---
        self.start_time, self.log_filepath = self.get_logfilepath()

        # --- Initialize Role Prompts ---
        self.role_prompts = {role: "\n".join(self.config_role[role]) for role in self.config_role}

        # --- Initialize Phase Modules ---
        self.compose_phase_module = importlib.import_module("chatdev.composed_phase")
        self.phase_module = importlib.import_module("chatdev.phase")

        self.phases = {}
        for phase in self.config_phase:
            phase_cfg = self.config_phase[phase]
            phase_class = getattr(self.phase_module, phase)
            phase_instance = phase_class(
                assistant_role_name=phase_cfg["assistant_role_name"],
                user_role_name=phase_cfg["user_role_name"],
                phase_prompt="\n\n".join(phase_cfg["phase_prompt"]),
                role_prompts=self.role_prompts,
                phase_name=phase,
                model_type=self.model_type,
                log_filepath=self.log_filepath
            )
            self.phases[phase] = phase_instance

    # ======================================================================
    # ========================== CORE EXECUTION ============================
    # ======================================================================

    def make_recruitment(self):
        for employee in self.recruitments:
            self.chat_env.recruit(agent_name=employee)

    def execute_step(self, phase_item: dict):
        """
        Execute a phase with integrated reliability checks.
        Returns structured telemetry for reliability evaluation.
        """
        import time
        from datetime import datetime

        phase = phase_item["phase"]
        phase_type = phase_item["phaseType"]
        start_time = time.time()

        telemetry = {
            "phase": phase,
            "phase_type": phase_type,
            "timestamp": datetime.utcnow().isoformat(),
            "actions": [],
            "decisions": [],
            "terminated": False
        }

        # --- Run Phase ---
        try:
            if phase_type == "SimplePhase":
                limit = phase_item["max_turn_step"]
                reflect = check_bool(phase_item["need_reflect"])
                self.chat_env = self.phases[phase].execute(
                    self.chat_env,
                    self.chat_turn_limit_default if limit <= 0 else limit,
                    reflect
                )
            elif phase_type == "ComposedPhase":
                cycle_num = phase_item["cycleNum"]
                composition = phase_item["Composition"]
                phase_class = getattr(self.compose_phase_module, phase, None)
                if not phase_class:
                    raise RuntimeError(f"Composed phase '{phase}' not implemented.")
                composed = phase_class(
                    phase_name=phase,
                    cycle_num=cycle_num,
                    composition=composition,
                    config_phase=self.config_phase,
                    config_role=self.config_role,
                    model_type=self.model_type,
                    log_filepath=self.log_filepath
                )
                self.chat_env = composed.execute(self.chat_env)
            else:
                raise RuntimeError(f"Unsupported phaseType '{phase_type}'")

        except Exception as e:
            self.chat_env.log(f"[ERROR] Phase execution failed: {e}")
            telemetry["error"] = str(e)

        # --- Reliability Checks ---
        if hasattr(self.chat_env, "last_actions"):
            for role_name, action_text in self.chat_env.last_actions.items():
                if not action_text:
                    continue

                action_entry = {
                    "role": role_name,
                    "text": action_text,
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Role Validation
                ok, decision = self.role_validator.enforce(role_name, action_text)
                telemetry["decisions"].append({
                    "module": "RoleValidator",
                    "role": role_name,
                    "ok": ok,
                    "reason": decision["reason"]
                })
                if not ok:
                    self.chat_env.log(f"[RoleValidator] {role_name}: {decision['reason']}")
                    continue  # skip to next role

                # Memory Persistence
                self.hybrid_memory.write(
                    text=action_text,
                    meta={"role": role_name, "phase": phase, "phase_type": phase_type},
                    persist=True
                )

                # Cycle Detection
                self.cycle_detector.add_action(role_name, action_text)
                cycle_info = self.cycle_detector.detect_cycle(role_name)
                if cycle_info:
                    self.chat_env.log(
                        f"[CycleDetector] {role_name} loop: len={cycle_info['cycle_len']} conf={cycle_info.get('confidence', 1.0):.2f}"
                    )
                    telemetry["decisions"].append({
                        "module": "CycleDetector",
                        "role": role_name,
                        "cycle_info": cycle_info
                    })

                telemetry["actions"].append(action_entry)

        # --- Dynamic Termination Evaluation ---
        term_decision = self.dta.maybe_terminate(
            self.chat_env, {"cycle_detector": self.cycle_detector}
        )
        telemetry["decisions"].append({
            "module": "DTA",
            "decision": term_decision
        })

        if term_decision.get("terminate"):
            self.chat_env.log(f"[DTA] Termination triggered: {term_decision['reason']}")
            self.chat_env.terminated = True
            telemetry["terminated"] = True

        telemetry["elapsed_time"] = round(time.time() - start_time, 3)
        self.chat_env.telemetry_log = getattr(self.chat_env, "telemetry_log", [])
        self.chat_env.telemetry_log.append(telemetry)

        return {
            "phase": phase,
            "terminated": telemetry["terminated"],
            "telemetry": telemetry,
            "memory_size": len(self.hybrid_memory.long_term),
            "last_actions": getattr(self.chat_env, "last_actions", {})
        }

    # ======================================================================
    # ======================== SUPPORT METHODS =============================
    # ======================================================================

    def execute_chain(self):
        for phase_item in self.chain:
            res = self.execute_step(phase_item)
            if res.get("terminated"):
                break

    def get_logfilepath(self):
        start_time = now()
        root = os.path.dirname(os.path.dirname(__file__))
        directory = os.path.join(root, "WareHouse")
        os.makedirs(directory, exist_ok=True)
        log_filepath = os.path.join(
            directory, f"{self.project_name}_{self.org_name}_{start_time}.log"
        )
        return start_time, log_filepath

    def pre_processing(self):
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)
        directory = os.path.join(root, "WareHouse")

        if self.chat_env.config.clear_structure:
            for filename in os.listdir(directory):
                path = os.path.join(directory, filename)
                if os.path.isfile(path) and not filename.endswith((".py", ".log")):
                    os.remove(path)
                    print(f"{path} Removed.")

        software_path = os.path.join(
            directory, "_".join([self.project_name, self.org_name, self.start_time])
        )
        self.chat_env.set_directory(software_path)

        if self.chat_env.config.with_memory:
            self.chat_env.memory = self.hybrid_memory
            self.chat_env.init_memory()

        for cfg in [self.config_path, self.config_phase_path, self.config_role_path]:
            shutil.copy(cfg, software_path)

        if check_bool(self.config["incremental_develop"]):
            for root, dirs, files in os.walk(self.code_path):
                rel = os.path.relpath(root, self.code_path)
                target_dir = os.path.join(software_path, "base", rel)
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    shutil.copy2(os.path.join(root, file), os.path.join(target_dir, file))
            self.chat_env._load_from_hardware(os.path.join(software_path, "base"))

        with open(os.path.join(software_path, self.project_name + ".prompt"), "w") as f:
            f.write(self.task_prompt_raw)

        preprocess_msg = f"""
**[Preprocessing]**
**ChatDev Starts** ({self.start_time})

**Project**: {self.project_name}
**Org**: {self.org_name}
**Log**: {self.log_filepath}
"""
        log_visualize(preprocess_msg)

    def post_processing(self):
        self.chat_env.write_meta()
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)

        post_info = "**[Post Info]**\n\n"
        now_time = now()
        fmt = "%Y%m%d%H%M%S"
        duration = (
            datetime.strptime(now_time, fmt) - datetime.strptime(self.start_time, fmt)
        ).total_seconds()

        post_info += f"🕑 Duration: {duration:.2f}s\n\n"
        post_info += f"ChatDev Started: {self.start_time}\nChatDev Ended: {now_time}\n\n"

        directory = self.chat_env.env_dict["directory"]
        if self.chat_env.config.clear_structure:
            for filename in os.listdir(directory):
                path = os.path.join(directory, filename)
                if os.path.isdir(path) and path.endswith("__pycache__"):
                    shutil.rmtree(path, ignore_errors=True)
                    post_info += f"{path} Removed.\n"

        log_visualize(post_info)
        logging.shutdown()
        time.sleep(1)

        shutil.move(
            self.log_filepath,
            os.path.join(
                root, "WareHouse", "_".join([self.project_name, self.org_name, self.start_time]),
                os.path.basename(self.log_filepath),
            ),
        )

'''
Game control for chess, handling turns, checks, and game end conditions.
'''
from chessboard import ChessBoard
from player import Player
from utils import parse_move
class Game:
    def __init__(self):
        self.board = ChessBoard()
        self.players = [Player("white"), Player("black")]
        self.turn_index = 0
    def current_player(self):
        return self.players[self.turn_index]
    def next_player(self):
        self.turn_index = 1 - self.turn_index
        return self.current_player()
    def make_move(self, move_str):
        move = parse_move(move_str)
        if self.board.is_valid_move(move, self.current_player().color):
            self.board.apply_move(move)
            if self.board.is_checkmate(self.next_player().color):
                return
            self.next_player()
        else:
            raise ValueError("Invalid move")
    def is_game_over(self):
        return self.board.is_checkmate(self.current_player().color)
    def winner(self):
        if self.board.is_checkmate("white"):
            return "Black"
        elif self.board.is_checkmate("black"):
            return "White"
        return "Draw"
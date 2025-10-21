'''
Main module for chess game. Initializes and controls the game flow.
'''
from game import Game
def main():
    print("Welcome to Terminal Chess!")
    game = Game()
    while not game.is_game_over():
        print(game.board)
        try:
            move = input(f"{game.current_player().color.capitalize()} to move: ")
            game.make_move(move)
        except Exception as e:
            print(e)
    print("Game over!")
    print(f"Winner: {game.winner()}")
if __name__ == "__main__":
    main()
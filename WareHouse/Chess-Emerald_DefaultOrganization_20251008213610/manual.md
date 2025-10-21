```markdown
# Terminal Chess User Manual

Welcome to Terminal Chess, a simple yet fully functional chess game designed to be played directly from your Linux terminal. This manual will guide you through the installation process, game features, and how to play the game.

## System Requirements

- Python 3.6 or newer

## Installation

1. **Clone the Repository**: First, you need to clone the source code from our repository. Open your terminal and run:
   ```bash
   git clone https://github.com/ChatDev/TerminalChess.git
   cd TerminalChess
   ```

2. **Install Dependencies**: To run the game, you need to ensure that Python is installed on your system. You can install Python via:
   ```bash
   sudo apt-get update
   sudo apt-get install python3.6
   ```

3. **Run the Game**: Once Python is installed, you can start the game by running:
   ```bash
   python3 main.py
   ```

## Game Features

- **Two Player Game**: Terminal Chess is designed for two players, taking turns on the same machine.
- **Standard Chess Rules**: Includes all standard chess moves and rules such as pawn promotion, en passant, and castling.
- **Check and Checkmate Detection**: The game automatically detects check and checkmate conditions.
- **Terminal-Based UI**: All game interactions and the board display are handled directly in the terminal.

## How to Play

1. **Starting the Game**: After running `main.py`, the game will initialize and display the chess board with a welcome message.

2. **Making a Move**: 
   - Players take turns to input their moves using standard chess notation (e.g., `e2 to e4`).
   - The game will prompt each player for their move, indicating which color (White or Black) is to move.

3. **Game Progression**:
   - After each move, the board will update and display in the terminal.
   - If a move is invalid, an error message will be shown, and the player will be asked to try a different move.

4. **End of the Game**:
   - The game ends when one player checkmates the other.
   - The terminal will display "Game over!" along with the winner of the game.

5. **Exiting the Game**:
   - You can exit the game at any time by pressing `Ctrl+C` in the terminal.

## Troubleshooting

- **Python Not Found**: Ensure Python 3.6 or newer is installed on your system. You can check your Python version by running `python3 --version`.
- **Module Not Found Errors**: Make sure you are in the correct directory (`TerminalChess`) that contains all the game files before running `python3 main.py`.

## Support

For additional support, questions, or feedback, please contact our support team at support@chatdev.com. We are here to help you enjoy your Terminal Chess experience!

Thank you for choosing Terminal Chess. Enjoy the game!
```
This manual provides comprehensive instructions for users to install, understand, and play the Terminal Chess game directly from their Linux terminal. It includes details on system requirements, installation steps, game features, gameplay instructions, and support information.
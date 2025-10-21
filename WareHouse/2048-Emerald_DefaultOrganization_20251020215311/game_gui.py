'''
Graphical User Interface for the 2048 game using tkinter
'''
import tkinter as tk
from game_logic import Game2048
def main():
    class GameApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title('2048 Game')
            self.game = Game2048()
            self.grid_cells = []
            self.init_grid()
            self.update_grid_cells()
            self.bind("<Key>", self.key_press)
        def init_grid(self):
            background = tk.Frame(self, bg='azure3', width=400, height=400)
            background.grid()
            for i in range(4):
                grid_row = []
                for j in range(4):
                    cell_frame = tk.Frame(background, bg='azure4', width=100, height=100)
                    cell_frame.grid(row=i, column=j, padx=5, pady=5)
                    cell_number = tk.Label(cell_frame, text='', bg='azure2', justify=tk.CENTER, font=('Arial', 22, 'bold'), width=4, height=2)
                    cell_number.grid()
                    grid_row.append(cell_number)
                self.grid_cells.append(grid_row)
        def update_grid_cells(self):
            for i in range(4):
                for j in range(4):
                    cell_value = self.game.grid[i][j]
                    if cell_value == 0:
                        self.grid_cells[i][j].config(text='', bg='azure2')
                    else:
                        self.grid_cells[i][j].config(text=str(cell_value), bg='light goldenrod')
            self.update_idletasks()
        def key_press(self, event):
            key = event.keysym
            if key in ('Up', 'Down', 'Left', 'Right'):
                key = key.lower()
                self.game.move_tiles(key)
                self.update_grid_cells()
                if self.game.check_game_over():
                    self.game_over()
        def game_over(self):
            game_over_frame = tk.Frame(self, borderwidth=2)
            game_over_frame.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(game_over_frame, text="Game Over!", font=('Arial', 20, 'bold')).pack()
    app = GameApp()
    app.mainloop()
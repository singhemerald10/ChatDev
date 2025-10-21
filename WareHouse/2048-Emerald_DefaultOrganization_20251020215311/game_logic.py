'''
Game logic for 2048 game
'''
import random
class Game2048:
    def __init__(self):
        self.grid = [[0]*4 for _ in range(4)]
        self.score = 0
        self.add_new_tile()
        self.add_new_tile()
    def move_tiles(self, direction):
        def compress(grid):
            new_grid = [[0] * 4 for _ in range(4)]
            for i in range(4):
                cnt = 0
                for j in range(4):
                    if grid[i][j] != 0:
                        new_grid[i][cnt] = grid[i][j]
                        cnt += 1
            return new_grid
        def merge(grid):
            for i in range(4):
                for j in range(3):
                    if grid[i][j] == grid[i][j + 1] and grid[i][j] != 0:
                        grid[i][j] *= 2
                        grid[i][j + 1] = 0
                        self.score += grid[i][j]
            return grid
        def reverse(grid):
            new_grid = []
            for i in range(4):
                new_grid.append([])
                for j in range(4):
                    new_grid[i].append(grid[i][3 - j])
            return new_grid
        def transpose(grid):
            new_grid = [[0] * 4 for _ in range(4)]
            for i in range(4):
                for j in range(4):
                    new_grid[i][j] = grid[j][i]
            return new_grid
        moves = {'up': lambda grid: transpose(merge(compress(transpose(grid)))),
                 'down': lambda grid: transpose(reverse(merge(compress(reverse(transpose(grid)))))),
                 'left': lambda grid: compress(merge(compress(grid))),
                 'right': lambda grid: reverse(compress(merge(compress(reverse(grid)))))}
        if direction in moves:
            self.grid = moves[direction](self.grid)
            self.add_new_tile()
    def add_new_tile(self):
        empty_cells = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = random.choice([2, 4])
    def check_game_over(self):
        for i in range(4):
            for j in range(4):
                if self.grid[i][j] == 0:
                    return False
                if i < 3 and self.grid[i][j] == self.grid[i + 1][j]:
                    return False
                if j < 3 and self.grid[i][j] == self.grid[i][j + 1]:
                    return False
        return True
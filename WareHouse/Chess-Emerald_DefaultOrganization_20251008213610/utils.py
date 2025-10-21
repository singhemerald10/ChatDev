'''
Utility functions for chess game, including move parsing.
'''
def parse_move(move_str):
    # Parse a chess move from string notation to a move object
    return move_str
def parse_chess_notation(move_str):
    # Simplified parsing, assumes move_str is like 'e2 to e4'
    parts = move_str.split()
    src = parts[0]
    dst = parts[3]
    src_x, src_y = ord(src[0]) - ord('a'), int(src[1]) - 1
    dst_x, dst_y = ord(dst[0]) - ord('a'), int(dst[1]) - 1
    return src_x, src_y, dst_x, dst_y
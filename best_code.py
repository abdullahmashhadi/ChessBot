import pygame
import os

STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
pygame.init()
WIDTH, HEIGHT = 800, 800
SQUARE_WIDTH, SQUARE_HEIGHT = WIDTH // 8, HEIGHT // 8
LIGHT_COLOR, DARK_COLOR = (234,240,206), (187,190,100)
HIGHLIGHT_COLOR = (252, 3, 3)
CHECK_COLOR = (255, 0, 0)
screen = pygame.display.set_mode((WIDTH,HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Chess Board")
direction_offsets = {8,-8,-1,1,7,-7,9,-9}
num_squares_to_edge = {}

def precomputed_move_data():
    for file in range (8):
        for rank in range(8):
            num_north=7-rank
            num_south=rank
            num_west= file
            num_east= 7-file
            square_index=rank*8+file
            num_squares_to_edge[square_index] = [
                num_north,
                num_south,
                num_west,
                num_east,
                min(num_north,num_west),
                min(num_south,num_east),
                min(num_north,num_east),
                min(num_south,num_west)
            ]

class Piece():
    Empty = 0
    King = 1
    Pawn = 2
    Knight = 3
    Bishop = 4
    Rook = 5
    Queen = 6
    Light = 8
    Dark = 16

class Board():
    def __init__(self):
        self.squares = [None]*64
        self.turn = Piece.Light
        self.selected = None
        self.legal_moves = []
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_target = None

    def draw_pieces(self, dragging_info=None):
        for square_index in range(64):
            piece = self.squares[square_index]
            if piece:
                rank = square_index // 8
                file = square_index % 8
                piece_color = "Light" if piece & Piece.Light else "Dark"
                piece_type = piece & ~Piece.Light & ~Piece.Dark
                piece_name = {
                    Piece.King: "King",
                    Piece.Queen: "Queen",
                    Piece.Rook: "Rook",
                    Piece.Bishop: "Bishop",
                    Piece.Knight: "Knight",
                    Piece.Pawn: "Pawn",
                }[piece_type]
                piece_key = f"{piece_color}_{piece_name}"
                piece_image = pygame.transform.scale(piece_images[piece_key], (SQUARE_WIDTH, SQUARE_HEIGHT))
                if dragging_info and dragging_info["index"] == square_index:
                    continue
                screen.blit(piece_image, (file * SQUARE_WIDTH, (7 - rank) * SQUARE_HEIGHT))
        if dragging_info and dragging_info["piece"]:
            piece_image = pygame.transform.scale(piece_images[dragging_info["piece"]], (SQUARE_WIDTH, SQUARE_HEIGHT))
            mouse_x, mouse_y = pygame.mouse.get_pos()
            screen.blit(piece_image, (mouse_x - SQUARE_WIDTH//2, mouse_y - SQUARE_HEIGHT//2))

    def highlight_squares(self):
        for move in self.legal_moves:
            rank = move // 8
            file = move % 8
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, pygame.Rect(file*SQUARE_WIDTH, (7 - rank)*SQUARE_HEIGHT, SQUARE_WIDTH, SQUARE_HEIGHT), 4)

def load_piece_images():
    pieces = {}
    piece_names = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]
    colors = ["Light", "Dark"]
    for color in colors:
        for piece in piece_names:
            piece_key = f"{color}_{piece}"
            image_path = os.path.join("pieces", f"{piece_key}.png")
            pieces[piece_key] = pygame.image.load(image_path)
    return pieces

piece_images = load_piece_images()

def load_position_from_fen(fen, board):
    piece_type_from_symbol = {
        'k': Piece.King,
        'p': Piece.Pawn,
        'n': Piece.Knight,
        'b': Piece.Bishop,
        'r': Piece.Rook,
        'q': Piece.Queen
    }
    fen_board = list(fen.split()[0])
    file = 0
    rank = 7
    for char in fen_board:
        if char == '/':
            file = 0
            rank -= 1
        elif char.isdigit():
            file += int(char)
        else:
            piece_color = Piece.Light if char.isupper() else Piece.Dark
            piece_type = piece_type_from_symbol[char.lower()]
            board.squares[rank*8 + file] = piece_type | piece_color
            file += 1

def is_square_attacked(board, square, attacker_color):
    for i in range(64):
        piece = board.squares[i]
        if piece and (piece & attacker_color):
            if square in get_legal_moves(board, i, check_check=False):
                return True
    return False

def get_legal_moves(board, index, check_check=True):
    piece = board.squares[index]
    if not piece:
        return []
    moves = []
    piece_type = piece & ~Piece.Light & ~Piece.Dark
    color = Piece.Light if piece & Piece.Light else Piece.Dark

    if check_check:
        # Find king's position
        king_position = None
        for i in range(64):
            if board.squares[i] and (board.squares[i] & color) and (board.squares[i] & ~Piece.Light & ~Piece.Dark) == Piece.King:
                king_position = i
                break

    directions = []
    if piece_type == Piece.Pawn:
        direction = 8 if color == Piece.Light else -8
        forward = index + direction
        if 0 <= forward < 64 and board.squares[forward] is None:
            moves.append(forward)
            # Add two-square move from starting position
            starting_rank = 1 if color == Piece.Light else 6
            current_rank = index // 8
            if current_rank == starting_rank:
                double_forward = index + 2 * direction
                if 0 <= double_forward < 64 and board.squares[double_forward] is None:
                    moves.append(double_forward)
        # Add captures
        for offset in [7,9] if color == Piece.Light else [-7,-9]:
            target = index + offset
            if 0 <= target < 64 and board.squares[target] is not None and (board.squares[target] & color) != color:
                moves.append(target)
        # En passant
        if board.en_passant_target is not None:
            for offset in [7, 9] if color == Piece.Light else [-7, -9]:
                target = index + offset
                if target == board.en_passant_target:
                    moves.append(target)
    elif piece_type == Piece.Knight:
        offsets = [17, 15, 10, 6, -17, -15, -10, -6]
        for offset in offsets:
            target = index + offset
            if 0 <= target < 64:
                # Handle board edges
                if abs((index % 8) - (target % 8)) <= 2:
                    if board.squares[target] is None or (board.squares[target] & color) != color:
                        moves.append(target)
    elif piece_type in [Piece.Bishop, Piece.Rook, Piece.Queen]:
        if piece_type == Piece.Bishop:
            directions = [7,9,-7,-9]
        elif piece_type == Piece.Rook:
            directions = [8,-8,1,-1]
        else:
            directions = [7,9,-7,-9,8,-8,1,-1]
        for direction in directions:
            target = index
            while True:
                target += direction
                if target < 0 or target >= 64:
                    break
                # Handle board edges more robustly
                if abs((target % 8) - ((target - direction) % 8)) > 1:
                    break
                if board.squares[target] is None:
                    moves.append(target)
                else:
                    if (board.squares[target] & color) != color:
                        moves.append(target)
                    break
    elif piece_type == Piece.King:
        offsets = [8, -8,1,-1,7,9,-7,-9]
        for offset in offsets:
            target = index + offset
            if 0 <= target < 64:
                if abs((index % 8) - (target % 8)) <=1:
                    if board.squares[target] is None or (board.squares[target] & color) != color:
                        moves.append(target)
        # Castling
        if color == Piece.Light:
            if board.castling_rights['K'] and all(board.squares[i] is None for i in [61, 62]) and not any(is_square_attacked(board, i, Piece.Dark) for i in [60, 61, 62]):
                moves.append(62)
    if check_check:
        # Filter moves that would leave the king in check
        valid_moves = []
        for move in moves:
            # Make temporary move
            original_piece = board.squares[move]
            original_position = board.squares[index]
            board.squares[move] = original_position
            board.squares[index] = None

            # Check if king is in check
            king_pos = move if piece_type == Piece.King else king_position
            is_safe = not is_square_attacked(board, king_pos, Piece.Dark if color == Piece.Light else Piece.Light)

            # Undo temporary move
            board.squares[index] = original_position
            board.squares[move] = original_piece

            if is_safe:
                valid_moves.append(move)
        return valid_moves
    return moves




def create_board():
    for rank in range(7, -1, -1):
        for file in range(8):
            is_light_square = ((rank+file) % 2) != 0
            square_color = LIGHT_COLOR if is_light_square else DARK_COLOR
            pygame.draw.rect(
                screen,
                square_color,
                pygame.Rect(file*SQUARE_WIDTH, (7-rank)*SQUARE_HEIGHT, SQUARE_WIDTH, SQUARE_HEIGHT)
            )

def main():
    precomputed_move_data()
    running = True
    board = Board()
    load_position_from_fen(STARTING_FEN, board)
    dragging_info = {"index": None, "piece": None}

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                file = mx // SQUARE_WIDTH
                rank = 7 - (my // SQUARE_HEIGHT)
                index = rank*8 + file
                piece = board.squares[index]
                if piece and (piece & board.turn):
                    board.selected = index
                    board.legal_moves = get_legal_moves(board, index)
                    dragging_info["index"] = index
                    dragging_info["piece"] = {
                        "Light_King": "Light_King",
                        "Light_Queen": "Light_Queen",
                        "Light_Rook": "Light_Rook",
                        "Light_Bishop": "Light_Bishop",
                        "Light_Knight": "Light_Knight",
                        "Light_Pawn": "Light_Pawn",
                        "Dark_King": "Dark_King",
                        "Dark_Queen": "Dark_Queen",
                        "Dark_Rook": "Dark_Rook",
                        "Dark_Bishop": "Dark_Bishop",
                        "Dark_Knight": "Dark_Knight",
                        "Dark_Pawn": "Dark_Pawn",
                    }.get(f"{'Light' if piece & Piece.Light else 'Dark'}_" + {
                        Piece.King: "King",
                        Piece.Queen: "Queen",
                        Piece.Rook: "Rook",
                        Piece.Bishop: "Bishop",
                        Piece.Knight: "Knight",
                        Piece.Pawn: "Pawn",
                    }[piece & ~Piece.Light & ~Piece.Dark], None)
                    board.squares[index] = None

            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging_info["piece"]:
                    mx, my = pygame.mouse.get_pos()
                    file = mx // SQUARE_WIDTH
                    rank = 7 - (my // SQUARE_HEIGHT)
                    new_index = rank*8 + file
                    if new_index in board.legal_moves:
                        board.squares[new_index] = {
                            "Light_King": Piece.King | Piece.Light,
                            "Light_Queen": Piece.Queen | Piece.Light,
                            "Light_Rook": Piece.Rook | Piece.Light,
                            "Light_Bishop": Piece.Bishop | Piece.Light,
                            "Light_Knight": Piece.Knight | Piece.Light,
                            "Light_Pawn": Piece.Pawn | Piece.Light,
                            "Dark_King": Piece.King | Piece.Dark,
                            "Dark_Queen": Piece.Queen | Piece.Dark,
                            "Dark_Rook": Piece.Rook | Piece.Dark,
                            "Dark_Bishop": Piece.Bishop | Piece.Dark,
                            "Dark_Knight": Piece.Knight | Piece.Dark,
                            "Dark_Pawn": Piece.Pawn | Piece.Dark,
                        }.get(dragging_info["piece"], None)
                        board.turn = Piece.Dark if board.turn == Piece.Light else Piece.Light
                    else:
                        board.squares[board.selected] = {
                            "Light_King": Piece.King | Piece.Light,
                            "Light_Queen": Piece.Queen | Piece.Light,
                            "Light_Rook": Piece.Rook | Piece.Light,
                            "Light_Bishop": Piece.Bishop | Piece.Light,
                            "Light_Knight": Piece.Knight | Piece.Light,
                            "Light_Pawn": Piece.Pawn | Piece.Light,
                            "Dark_King": Piece.King | Piece.Dark,
                            "Dark_Queen": Piece.Queen | Piece.Dark,
                            "Dark_Rook": Piece.Rook | Piece.Dark,
                            "Dark_Bishop": Piece.Bishop | Piece.Dark,
                            "Dark_Knight": Piece.Knight | Piece.Dark,
                            "Dark_Pawn": Piece.Pawn | Piece.Dark,
                        }.get(dragging_info["piece"], None)
                    dragging_info["index"] = None
                    dragging_info["piece"] = None
                    board.selected = None
                    board.legal_moves = []

        create_board()
        board.highlight_squares()
        board.draw_pieces(dragging_info)
        pygame.display.flip()

    pygame.quit()

main()

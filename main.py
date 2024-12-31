import pygame
import os
import math
import copy

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

def show_victory_popup(winner):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont("Arial", 72, bold=True)
    text = font.render(f"{winner} Wins!", True, (255, 215, 0))
    shadow = font.render(f"{winner} Wins!", True, (0, 0, 0))
    
    rect = text.get_rect(center=(WIDTH // 2 + 2, HEIGHT // 2 + 2))
    screen.blit(shadow, rect)
    
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, rect)
    
    pygame.display.flip()
    pygame.time.delay(3000)
    pygame.quit()
    exit()


def show_promotion_popup(color):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont("Arial", 36, bold=True)
    options = ["Queen", "Rook", "Bishop", "Knight"]
    option_rects = []
    for i, option in enumerate(options):
        text = font.render(option, True, (255, 215, 0))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50 + i * 50))
        screen.blit(text, rect)
        option_rects.append(rect)
    
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(mx, my):
                        return options[i]

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
            if 0 <= target < 64:
                from_file = index % 8
                to_file = target % 8
                if abs(to_file - from_file) == 1:
                    if board.squares[target] is not None and (board.squares[target] & color) != color:
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

def evaluate_board(board):
    piece_values = {
        Piece.King: 1000,
        Piece.Queen: 9,
        Piece.Rook: 5,
        Piece.Bishop: 3,
        Piece.Knight: 3,
        Piece.Pawn: 1,
    }

    # Piece-square tables for positional evaluation
    # These tables give a bonus or penalty for placing a piece on a specific square
    piece_square_tables = {
        Piece.Pawn: [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 5, 5, -5, -5, 5, 5, 5,
            1, 1, 2, 3, 3, 2, 1, 1,
            0.5, 0.5, 1, 2.5, 2.5, 1, 0.5, 0.5,
            0, 0, 0, 2, 2, 0, 0, 0,
            0.5, -0.5, -1, 0, 0, -1, -0.5, 0.5,
            0.5, 1, 1, -2, -2, 1, 1, 0.5,
            0, 0, 0, 0, 0, 0, 0, 0
        ],
        Piece.Knight: [
            -5, -4, -3, -3, -3, -3, -4, -5,
            -4, -2, 0, 0, 0, 0, -2, -4,
            -3, 0, 1, 1.5, 1.5, 1, 0, -3,
            -3, 0.5, 1.5, 2, 2, 1.5, 0.5, -3,
            -3, 0, 1.5, 2, 2, 1.5, 0, -3,
            -3, 0.5, 1, 1.5, 1.5, 1, 0.5, -3,
            -4, -2, 0, 0.5, 0.5, 0, -2, -4,
            -5, -4, -3, -3, -3, -3, -4, -5,
        ],
        Piece.Bishop: [
            -2, -1, -1, -1, -1, -1, -1, -2,
            -1, 0, 0, 0, 0, 0, 0, -1,
            -1, 0, 0.5, 1, 1, 0.5, 0, -1,
            -1, 0.5, 0.5, 1, 1, 0.5, 0.5, -1,
            -1, 0, 1, 1, 1, 1, 0, -1,
            -1, 1, 1, 1, 1, 1, 1, -1,
            -1, 0.5, 0, 0, 0, 0, 0.5, -1,
            -2, -1, -1, -1, -1, -1, -1, -2,
        ],
        Piece.Rook: [
            0, 0, 0, 0, 0, 0, 0, 0,
            0.5, 1, 1, 1, 1, 1, 1, 0.5,
            -0.5, 0, 0, 0, 0, 0, 0, -0.5,
            -0.5, 0, 0, 0, 0, 0, 0, -0.5,
            -0.5, 0, 0, 0, 0, 0, 0, -0.5,
            -0.5, 0, 0, 0, 0, 0, 0, -0.5,
            -0.5, 0, 0, 0, 0, 0, 0, -0.5,
            0, 0, 0, 0.5, 0.5, 0, 0, 0,
        ],
        Piece.Queen: [
            -2, -1, -1, -0.5, -0.5, -1, -1, -2,
            -1, 0, 0, 0, 0, 0, 0, -1,
            -1, 0, 0.5, 0.5, 0.5, 0.5, 0, -1,
            -0.5, 0, 0.5, 0.5, 0.5, 0.5, 0, -0.5,
            0, 0, 0.5, 0.5, 0.5, 0.5, 0, -0.5,
            -1, 0.5, 0.5, 0.5, 0.5, 0.5, 0, -1,
            -1, 0, 0.5, 0, 0, 0, 0, -1,
            -2, -1, -1, -0.5, -0.5, -1, -1, -2,
        ],
        Piece.King: [
            -3, -4, -4, -5, -5, -4, -4, -3,
            -3, -4, -4, -5, -5, -4, -4, -3,
            -3, -4, -4, -5, -5, -4, -4, -3,
            -3, -4, -4, -5, -5, -4, -4, -3,
            -2, -3, -3, -4, -4, -3, -3, -2,
            -1, -2, -2, -2, -2, -2, -2, -1,
            2, 2, 0, 0, 0, 0, 2, 2,
            2, 3, 1, 0, 0, 1, 3, 2,
        ],
    }

    score = 0
    for index, piece in enumerate(board.squares):
        if piece:
            piece_type = piece & ~Piece.Light & ~Piece.Dark
            piece_position = piece_square_tables.get(piece_type, [0]*64)[index]
            if piece & Piece.Light:
                score += piece_values.get(piece_type, 0) + piece_position
            elif piece & Piece.Dark:
                score -= piece_values.get(piece_type, 0) + piece_position

    # Additional factors
    # Mobility
    light_moves = sum(len(get_legal_moves(board, i)) for i in range(64) if board.squares[i] and (board.squares[i] & Piece.Light))
    dark_moves = sum(len(get_legal_moves(board, i)) for i in range(64) if board.squares[i] and (board.squares[i] & Piece.Dark))
    score += (light_moves - dark_moves) * 0.1  # Mobility weight

    # King safety
    # Penalize exposed kings
    light_king = next((i for i, p in enumerate(board.squares) if p == (Piece.King | Piece.Light)), None)
    dark_king = next((i for i, p in enumerate(board.squares) if p == (Piece.King | Piece.Dark)), None)
    if light_king is not None:
        surrounding = get_surrounding_squares(light_king)
        defended = sum(1 for sq in surrounding if board.squares[sq] and (board.squares[sq] & Piece.Light))
        score -= (8 - defended) * 0.5  # Less defended kings are worse
    if dark_king is not None:
        surrounding = get_surrounding_squares(dark_king)
        defended = sum(1 for sq in surrounding if board.squares[sq] and (board.squares[sq] & Piece.Dark))
        score += (8 - defended) * 0.5  # Less defended kings are worse

    return score

def get_surrounding_squares(index):
    surrounding = []
    rank = index // 8
    file = index % 8
    for dr in [-1, 0, 1]:
        for df in [-1, 0, 1]:
            if dr == 0 and df == 0:
                continue
            new_rank = rank + dr
            new_file = file + df
            if 0 <= new_rank < 8 and 0 <= new_file < 8:
                surrounding.append(new_rank * 8 + new_file)
    return surrounding

transposition_table = {}
def negamax(board, depth, alpha, beta, color):
    # Generate a unique key for the current board position
    board_key = generate_board_key(board)

    if board_key in transposition_table:
        return transposition_table[board_key]

    if depth == 0:
        eval = color * evaluate_board(board)
        transposition_table[board_key] = eval
        return eval

    max_value = -math.inf
    moves = get_all_moves(board, color)
    for move in moves:
        new_board = copy.deepcopy(board)
        apply_move(new_board, move)
        value = -negamax(new_board, depth - 1, -beta, -alpha, -color)
        if value > max_value:
            max_value = value
        alpha = max(alpha, value)
        if alpha >= beta:
            break

    transposition_table[board_key] = max_value
    return max_value
def generate_board_key(board):
    key = 0
    for i, piece in enumerate(board.squares):
        if piece:
            key ^= hash((i, piece))
    key ^= hash(board.turn)
    return key

def get_all_moves(board, color):
    all_moves = []
    for index in range(64):
        piece = board.squares[index]
        if piece and (piece & color):
            legal_moves = get_legal_moves(board, index)
            for move in legal_moves:
                capture = board.squares[move] is not None
                all_moves.append((index, move, capture))
    # Order moves: captures first, then others
    all_moves.sort(key=lambda x: x[2], reverse=True)  # Captures before non-captures
    return [(move[0], move[1]) for move in all_moves]

def apply_move(board, move):
    from_index, to_index = move
    piece = board.squares[from_index]
    board.squares[to_index] = piece
    board.squares[from_index] = None
    
    # Handle pawn promotion for AI (Dark)
    piece_type = piece & ~Piece.Light & ~Piece.Dark
    color = "Light" if piece & Piece.Light else "Dark"
    target_rank = to_index // 8
    if piece_type == Piece.Pawn and ((color == "Light" and target_rank == 7) or (color == "Dark" and target_rank == 0)):
        if color == "Dark":
            board.squares[to_index] = Piece.Queen | Piece.Dark
        # For Light pawns, promotion is handled via popup as per existing logic
    
    # Switch turn
    board.turn = Piece.Dark if board.turn == Piece.Light else Piece.Light

def choose_best_move(board, depth):
    best_move = None
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf
    color = Piece.Dark  # AI plays as Dark

    moves = get_all_moves(board, color)
    for move in moves:
        new_board = copy.deepcopy(board)
        apply_move(new_board, move)
        value = -negamax(new_board, depth - 1, -beta, -alpha, -color)
        if value > best_value:
            best_value = value
            best_move = move
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return best_move

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

# ... existing imports and class definitions ...

def main():
    precomputed_move_data()
    running = True
    board = Board()
    load_position_from_fen(STARTING_FEN, board)
    dragging_info = {"index": None, "piece": None}
    ai_thinking = False  # Flag to indicate AI is processing a move
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not ai_thinking and board.turn == Piece.Light:
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

            # **Updated Conditional Below**
            elif event.type == pygame.MOUSEBUTTONUP and not ai_thinking and board.turn == Piece.Light:
                if dragging_info["piece"]:
                    mx, my = pygame.mouse.get_pos()
                    file = mx // SQUARE_WIDTH
                    rank = 7 - (my // SQUARE_HEIGHT)
                    new_index = rank*8 + file
                    if new_index in board.legal_moves:
                        piece_type = {
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
                        if (piece_type & ~Piece.Light & ~Piece.Dark) == Piece.Pawn and (
                            (piece_type & Piece.Light and new_index // 8 == 7) or
                            (piece_type & Piece.Dark and new_index // 8 == 0)
                        ):
                            promotion_choice = show_promotion_popup("Light" if piece_type & Piece.Light else "Dark")
                            piece_type = {
                                "Queen": Piece.Queen,
                                "Rook": Piece.Rook,
                                "Bishop": Piece.Bishop,
                                "Knight": Piece.Knight,
                            }[promotion_choice] | (Piece.Light if piece_type & Piece.Light else Piece.Dark)
                        board.squares[new_index] = piece_type
                        board.turn = Piece.Dark if board.turn == Piece.Light else Piece.Light

                        # Check for checkmate
                        opponent = board.turn
                        has_legal_moves = False
                        for i in range(64):
                            if board.squares[i] and (board.squares[i] & opponent):
                                legal_moves = get_legal_moves(board, i)
                                if legal_moves:
                                    has_legal_moves = True
                                    break
                        if not has_legal_moves:
                            # Find opponent's king position
                            king_position = None
                            for i in range(64):
                                piece = board.squares[i]
                                if piece and (piece & opponent) and (piece & ~Piece.Light & ~Piece.Dark) == Piece.King:
                                    king_position = i
                                    break
                            if king_position and is_square_attacked(board, king_position, Piece.Dark if opponent == Piece.Light else Piece.Light):
                                winner = "White" if opponent == Piece.Dark else "Black"
                                show_victory_popup(winner)
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
        
        # AI Move Execution
        if board.turn == Piece.Dark and not ai_thinking:
            ai_thinking = True
            pygame.display.set_caption("AI is thinking...")
            pygame.display.flip()
            
            # Choose AI move
            ai_move = choose_best_move(board, depth=4)  # Adjust depth as needed
            if ai_move:
                apply_move(board, ai_move)
                # Check for checkmate after AI move
                opponent = board.turn
                has_legal_moves = False
                for i in range(64):
                    if board.squares[i] and (board.squares[i] & opponent):
                        legal_moves = get_legal_moves(board, i)
                        if legal_moves:
                            has_legal_moves = True
                            break
                if not has_legal_moves:
                    # Find opponent's king position
                    king_position = None
                    for i in range(64):
                        piece = board.squares[i]
                        if piece and (piece & opponent) and (piece & ~Piece.Light & ~Piece.Dark) == Piece.King:
                            king_position = i
                            break
                    if king_position and is_square_attacked(board, king_position, Piece.Dark if opponent == Piece.Light else Piece.Light):
                        winner = "White" if opponent == Piece.Dark else "Black"
                        show_victory_popup(winner)
            ai_thinking = False
            
        create_board()
        board.highlight_squares()
        board.draw_pieces(dragging_info)
        pygame.display.set_caption("Chess Board")
        pygame.display.flip()

    pygame.quit()

main()

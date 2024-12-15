#imports
import pygame
import os 

#defining starting board fen string
STARTING_FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

#setting up the pygame display
pygame.init()
WIDTH, HEIGHT = 800, 800
SQUARE_WIDTH = WIDTH // 8
SQUARE_HEIGHT= HEIGHT//8
LIGHT_COLOR = (234,240,206)
DARK_COLOR = (187,190,100)
screen=pygame.display.set_mode((WIDTH,HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Chess Board")

#creating pieces class
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

#creating internal representation of board for game
class Board():
    def __init__(self):
        self.squares=[None]*64
    def draw_pieces(self):
        for square_index in range(64):
            piece=self.squares[square_index]
            if piece:
                rank=square_index//8
                file=square_index%8
                piece_color= "Light" if piece & Piece.Light else "Dark"
                piece_type=piece & ~Piece.Light & ~Piece.Dark
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
                screen.blit(piece_image, (file * SQUARE_WIDTH, (7 - rank) * SQUARE_HEIGHT))
                

#creating dictionary with key=piece name, value=piece image(png)
def load_piece_images():
    pieces={}
    piece_names=["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]
    colors=["Light", "Dark"]
    for color in colors:
        for piece in piece_names:
            piece_key=f"{color}_{piece}"
            image_path=os.path.join("pieces",f"{piece_key}.png")
            pieces[piece_key]=pygame.image.load(image_path)
    return pieces

piece_images = load_piece_images()

#loading position from fen string
def load_position_from_fen(fen,board):
    piece_type_from_symbol={
        'k': Piece.King,
        'p': Piece.Pawn,
        'n': Piece.Knight,
        'b': Piece.Bishop,
        'r': Piece.Rook,
        'q': Piece.Queen
    }
    fen_board=list(fen.split()[0])
    file=0
    rank=7
    for char in fen_board:
        if char=='/':
            file=0
            rank=rank-1
        elif char.isdigit():
            file+=int(char)
        else:
            piece_color=Piece.Light if char.isupper() else Piece.Dark
            piece_type=piece_type_from_symbol[char.lower()]
            board.squares[rank*8+file]=piece_type | piece_color
            file+=1
            

#creating board in GUI
def create_board():
    for rank in range (7,-1,-1):
        for file in range(8):
            is_light_square=((rank+file)%2)!=0
            square_color= LIGHT_COLOR if is_light_square else DARK_COLOR
            pygame.draw.rect(
                screen,
                square_color,
                pygame.Rect(file * SQUARE_WIDTH, (7-rank) * SQUARE_HEIGHT, SQUARE_WIDTH, SQUARE_HEIGHT)
            )
            
    
#main runner code
def main():
    running=True
    board=Board()
    load_position_from_fen(STARTING_FEN, board)
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
        create_board()
        board.draw_pieces()
        pygame.display.flip()

    pygame.quit()
    

main()

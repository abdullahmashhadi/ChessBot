import pygame

#setting up the pygame display
pygame.init()
WIDTH, HEIGHT = 800, 800
SQUARE_WIDTH = WIDTH // 8
SQUARE_HEIGHT= HEIGHT//8
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
screen=pygame.display.set_mode((WIDTH,HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Chess Board")

#creating board
def CreateBoard():
    for rank in range (7,-1,-1):
        for file in range(8):
            is_white_square=((rank+file)%2)!=0
            square_color= WHITE_COLOR if is_white_square else BLACK_COLOR
            pygame.draw.rect(
                screen,
                square_color,
                pygame.Rect(file * SQUARE_WIDTH, (7-rank) * SQUARE_HEIGHT, SQUARE_WIDTH, SQUARE_HEIGHT)
            )
            
    

def main():
    running=True
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
        CreateBoard()
        pygame.display.flip()

    pygame.quit()
    

main()

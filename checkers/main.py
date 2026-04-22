import pygame
from checkers.constants import RED, SQUARE_SIZE, WHITE, WIDTH, HEIGHT
from checkers.game import Game
from minimax.algorithm import minimax

pygame.init()

FPS = 60
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Checkers")

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col


def main():
    run = True
    clock = pygame.time.Clock()
    game = Game(WIN)

    while run:
        clock.tick(FPS)

        if game.turn == WHITE:
            value, new_board = minimax(game.get_board(), 3, WHITE, game)
            game.ai_move(new_board)
            

        winner = game.winner()
        if winner is not None:
            print("Red wins!" if winner == RED else "White wins!" if winner == WHITE else winner)
            run = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                row, col = get_row_col_from_mouse(event.pos)
                game.select(row, col)

        game.update()


    pygame.quit()

if __name__ == "__main__":
    main()

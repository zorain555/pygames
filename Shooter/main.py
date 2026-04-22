import pygame
import os

# Initialize Pygame
pygame.font.init()
pygame.mixer.init()
pygame.init()

# Constants
WIDTH, HEIGHT = 900, 500
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

FPS = 60
VEL = 5
BULLET_VEL = 7
MAX_BULLETS = 3

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)

# Game Layout
BORDER = pygame.Rect(WIDTH//2 - 5, 0, 10, HEIGHT)
YELLOW_HIT = pygame.USEREVENT + 1
RED_HIT = pygame.USEREVENT + 2

# Fonts
HEALTH_FONT = pygame.font.SysFont("comicsans", 40)
WINNER_FONT = pygame.font.SysFont("comicsans", 100)
MENU_FONT = pygame.font.SysFont("comicsans", 60)

# Spaceship Dimensions
SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 40

# Load Images
# Note: Ensure you have an 'Assets' folder with these files or update the paths
try:
    YELLOW_SPACESHIP_IMAGE = pygame.image.load(os.path.join("Assets", "spaceship_yellow.png"))
    RED_SPACESHIP_IMAGE = pygame.image.load(os.path.join("Assets", "spaceship_red.png"))
    SPACE = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "space.png")), (WIDTH, HEIGHT))
except:
    # Fallback if images are missing
    YELLOW_SPACESHIP_IMAGE = pygame.Surface((SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
    RED_SPACESHIP_IMAGE = pygame.Surface((SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
    SPACE = pygame.Surface((WIDTH, HEIGHT))
    SPACE.fill((20, 20, 40))

YELLOW_SPACESHIP = pygame.transform.rotate(
    pygame.transform.scale(YELLOW_SPACESHIP_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 270)

RED_SPACESHIP = pygame.transform.rotate(
    pygame.transform.scale(RED_SPACESHIP_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), -270)

def draw_window(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health):
    WIN.blit(SPACE, (0, 0))
    pygame.draw.rect(WIN, BLACK, BORDER)
    
    red_h_text = HEALTH_FONT.render("Health: " + str(red_health), 1, WHITE)
    yellow_h_text = HEALTH_FONT.render("Health: " + str(yellow_health), 1, WHITE)
    
    WIN.blit(red_h_text, (WIDTH - red_h_text.get_width() - 10, 10))
    WIN.blit(yellow_h_text, (10, 10))

    WIN.blit(YELLOW_SPACESHIP, (yellow.x, yellow.y))
    WIN.blit(RED_SPACESHIP, (red.x, red.y))

    for bullet in red_bullets:
        pygame.draw.rect(WIN, RED, bullet)
    for bullet in yellow_bullets:
        pygame.draw.rect(WIN, YELLOW, bullet)

    pygame.display.update()

def handle_movement(keys_pressed, yellow, red):
    # Yellow
    if keys_pressed[pygame.K_a] and yellow.x - VEL > 0: yellow.x -= VEL
    if keys_pressed[pygame.K_d] and yellow.x + VEL + yellow.width < BORDER.x: yellow.x += VEL
    if keys_pressed[pygame.K_w] and yellow.y - VEL > 0: yellow.y -= VEL
    if keys_pressed[pygame.K_s] and yellow.y + VEL + yellow.height < HEIGHT - 15: yellow.y += VEL
    # Red
    if keys_pressed[pygame.K_LEFT] and red.x - VEL > BORDER.x + BORDER.width: red.x -= VEL
    if keys_pressed[pygame.K_RIGHT] and red.x + VEL + red.width < WIDTH: red.x += VEL
    if keys_pressed[pygame.K_UP] and red.y - VEL > 0: red.y -= VEL
    if keys_pressed[pygame.K_DOWN] and red.y + VEL + red.height < HEIGHT: red.y += VEL

def handle_bullets(yellow_bullets, red_bullets, yellow, red):
    for bullet in yellow_bullets:
        bullet.x += BULLET_VEL
        if red.colliderect(bullet):
            pygame.event.post(pygame.event.Event(RED_HIT))
            yellow_bullets.remove(bullet)
        elif bullet.x > WIDTH:
            yellow_bullets.remove(bullet)

    for bullet in red_bullets:
        bullet.x -= BULLET_VEL
        if yellow.colliderect(bullet):
            pygame.event.post(pygame.event.Event(YELLOW_HIT))
            red_bullets.remove(bullet)
        elif bullet.x < 0:
            red_bullets.remove(bullet)

def draw_text_centered(text, font, color, y_offset=0):
    render = font.render(text, 1, color)
    WIN.blit(render, (WIDTH//2 - render.get_width()//2, HEIGHT//2 - render.get_height()//2 + y_offset))

def main_menu():
    run = True
    while run:
        WIN.blit(SPACE, (0,0))
        draw_text_centered("SPACE SHOOTER", WINNER_FONT, WHITE, -50)
        draw_text_centered("Press any key to Start", MENU_FONT, YELLOW, 50)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN:
                run = False
    return True

def main():
    red = pygame.Rect(700, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
    yellow = pygame.Rect(100, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
    red_bullets, yellow_bullets = [], []
    red_health, yellow_health = 10, 10

    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                return # Exit back to system

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL and len(yellow_bullets) < MAX_BULLETS:
                    bullet = pygame.Rect(yellow.x + yellow.width, yellow.y + yellow.height//2 - 2, 10, 5)
                    yellow_bullets.append(bullet)
                if event.key == pygame.K_RCTRL and len(red_bullets) < MAX_BULLETS:
                    bullet = pygame.Rect(red.x, red.y + red.height//2 - 2, 10, 5)
                    red_bullets.append(bullet)

            if event.type == RED_HIT: red_health -= 1
            if event.type == YELLOW_HIT: yellow_health -= 1

        winner_text = ""
        if red_health <= 0: winner_text = "Yellow Wins!"
        if yellow_health <= 0: winner_text = "Red Wins!"

        if winner_text != "":
            draw_window(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health)
            draw_text_centered(winner_text, WINNER_FONT, WHITE, -40)
            draw_text_centered("Press 'R' to Restart or 'M' for Menu", HEALTH_FONT, YELLOW, 60)
            pygame.display.update()
            
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r: # RESTART
                            main() 
                            return
                        if event.key == pygame.K_m: # MENU
                            if main_menu(): 
                                main()
                            return

        keys_pressed = pygame.key.get_pressed()
        handle_movement(keys_pressed, yellow, red)
        handle_bullets(yellow_bullets, red_bullets, yellow, red)
        draw_window(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health)

if __name__ == "__main__":
    if main_menu():
        main()
    pygame.quit() # This ensures the window closes cleanly
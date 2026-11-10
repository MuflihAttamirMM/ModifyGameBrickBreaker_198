import os  # -- [BARU] dipakai untuk membuat path asset yang aman dari folder mana pun game dijalankan
import pygame
import random

pygame.init()

# -- [BARU] mixer dibungkus try/except supaya game tetap jalan walau perangkat tidak punya audio
try:
    pygame.mixer.init()
    AUDIO_OK = True
except pygame.error:
    AUDIO_OK = False

# Dimensions of the screen
WIDTH, HEIGHT = 600, 500

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

font = pygame.font.Font('freesansbold.ttf', 15)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker - Face Edition")  # -- [UBAH] judul window

# Frame rate control
clock = pygame.time.Clock()
FPS = 30

# -- [BARU] lokasi folder assets (gambar muka dan sound effect)
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# -- [BARU] radius bola diperbesar dari 7 menjadi 20 supaya muka kelihatan jelas
BALL_RADIUS = 20

# -- [BARU] lama muka "kaget" tampil setelah kena blok (dalam frame, 8 frame = sekitar 0,27 detik di 30 FPS)
SHOCK_FRAMES = 8


# -- [BARU] fungsi untuk load gambar muka dan di-resize sesuai diameter bola
def loadFace(filename, size):
    try:
        img = pygame.image.load(os.path.join(ASSET_DIR, filename)).convert_alpha()
        return pygame.transform.smoothscale(img, (size, size))
    except (pygame.error, FileNotFoundError):
        return None  # -- fallback: kalau gambar tidak ada, bola digambar sebagai lingkaran biasa


# -- [BARU] fungsi untuk load sound effect
def loadSound(filename):
    if not AUDIO_OK:
        return None
    try:
        return pygame.mixer.Sound(os.path.join(ASSET_DIR, filename))
    except (pygame.error, FileNotFoundError):
        return None  # -- fallback: kalau sound tidak ada, game jalan tanpa suara


# Striker class
class Striker:
    def __init__(self, posx, posy, width, height, speed, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.speed = speed
        self.color = color
        self.strikerRect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def display(self):
        pygame.draw.rect(screen, self.color, self.strikerRect)

    def update(self, xFac):
        self.posx += self.speed * xFac

        if self.posx <= 0:
            self.posx = 0
        elif self.posx + self.width >= WIDTH:
            self.posx = WIDTH - self.width

        self.strikerRect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def getRect(self):
        return self.strikerRect


# Block Class
class Block:
    def __init__(self, posx, posy, width, height, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.color = color
        self.damage = 100

        if color == WHITE:
            self.health = 200
        else:
            self.health = 100

        self.blockRect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def display(self):
        if self.health > 0:
            pygame.draw.rect(screen, self.color, self.blockRect)

    def hit(self):
        self.health -= self.damage

    def getRect(self):
        return self.blockRect

    def getHealth(self):
        return self.health


# Ball Class
class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.xFac, self.yFac = 1, -1

    def display(self):
        pygame.draw.circle(screen, self.color, (int(self.posx), int(self.posy)), self.radius)

    def update(self):
        self.posx += self.xFac * self.speed
        self.posy += self.yFac * self.speed

        # Bounce off vertical walls
        if self.posx - self.radius <= 0 or self.posx + self.radius >= WIDTH:
            self.xFac *= -1

        # Bounce off top wall
        if self.posy - self.radius <= 0:
            self.yFac *= -1

        # Ball falls past bottom
        if self.posy >= HEIGHT:
            return True

        return False

    def reset(self):
        self.posx = WIDTH // 2
        self.posy = HEIGHT - 100
        self.xFac, self.yFac = 1, -1

    def hit(self):
        self.yFac *= -1

    def getRect(self):
        # MEMPERBAIKI BUG: Membuat bounding Rect yang valid untuk bola
        return pygame.Rect(
            int(self.posx - self.radius),
            int(self.posy - self.radius),
            self.radius * 2,
            self.radius * 2
        )


# Helper Functions
def collisionChecker(rect, ball):
    return rect.colliderect(ball)


def populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap):
    listOfBlocks = []
    for i in range(10, WIDTH - blockWidth, blockWidth + horizontalGap):
        for j in range(20, HEIGHT // 2, blockHeight + verticalGap):
            listOfBlocks.append(
                Block(i, j, blockWidth, blockHeight, random.choice([WHITE, GREEN]))
            )
    return listOfBlocks


def gameOver():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True


# Game Manager
def main():
    running = True
    lives = 3
    score = 0

    striker = Striker(WIDTH // 2 - 50, HEIGHT - 50, 100, 20, 10, WHITE)
    strikerXFac = 0

    ball = Ball(WIDTH // 2, HEIGHT - 100, 7, 5, WHITE)

    blockWidth, blockHeight = 40, 15
    horizontalGap, verticalGap = 20, 20

    listOfBlocks = populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap)

    while running:
        screen.fill(BLACK)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    strikerXFac = -1
                if event.key == pygame.K_RIGHT:
                    strikerXFac = 1
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    strikerXFac = 0

        # Repopulate blocks if empty
        if not listOfBlocks:
            listOfBlocks = populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap)

        # Game over check
        if lives <= 0:
            running = gameOver()
            if not running:
                break
            lives = 3
            score = 0
            ball.reset()
            listOfBlocks = populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap)

        # Collision check
        if collisionChecker(striker.getRect(), ball.getRect()):
            ball.hit()

        for block in listOfBlocks[:]:
            if collisionChecker(block.getRect(), ball.getRect()):
                ball.hit()
                block.hit()
                if block.getHealth() <= 0:
                    listOfBlocks.remove(block)
                    score += 5

        # Updates
        striker.update(strikerXFac)
        lifeLost = ball.update()

        if lifeLost:
            lives -= 1
            ball.reset()

        # Render UI
        scoreText = font.render(f"Score : {score}", True, WHITE)
        livesText = font.render(f"Lives : {lives}", True, WHITE)
        screen.blit(scoreText, (20, HEIGHT - 25))
        screen.blit(livesText, (120, HEIGHT - 25))

        # Display objects
        striker.display()
        ball.display()
        for block in listOfBlocks:
            block.display()

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
    pygame.quit()
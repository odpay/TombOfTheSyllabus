import pygame
import os
import json

# WIDTH = 1000
# HEIGHT = 600
WIDTH = 640
HEIGHT = 640
PADDING = 1
TILE_WIDTH = 9
FPS = 60
GRID_X = 64
GRID_Y = 64
CLI = False
LVL = 1

def clear():
    os.system("clear")

class Player():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.xVel = 0
        self.yVel = 0
        self.moving = False
        self.alive = True
        self.won = False
        self.starsCollected = 0
    def up(self):
        if not self.moving:
            self.yVel -= 1
            self.moving = True
    def down(self):
        if not self.moving:
            self.yVel += 1 
            self.moving = True
    def left(self):
        if not self.moving:
            self.xVel -= 1
            self.moving = True
    def right(self):
        if not self.moving:
            self.xVel += 1
            self.moving = True
    def tick(self, grid):
        if self.moving:
            desX = self.x + self.xVel
            desY = self.y + self.yVel
            # self.xVel = 0
            # self.yVel = 0
            legal = False
            if desX<GRID_X and desY<GRID_Y: 
                des = grid[desY][desX]
                if des in [0,4] and desX >= 0 and desY >= 0:
                    legal = True
                if des == 4:
                    self.starsCollected += 1
                    grid[desY][desX] = 0
                if des == 3:
                    self.alive = False
            if legal:
                self.moving = True
                self.x = desX
                self.y = desY
            else:
                self.moving = False
                self.xVel = 0
                self.yVel = 0
        # self.x += self.xVel
        # if self.x not in range(columns): self.x -= self.xVel
        # self.xVel = 0
        # self.y += self.yVel
        # if self.y not in range(rows): self.y -= self.yVel
        # self.yVel = 0



def draw(grid, player, lastFrame=""):
    view = ""
    view += "- - - - - - - - - - -\n"
    
    for rowN, row in enumerate(grid):
        view += "| "
        for tileN, tile in enumerate(row):
            if (tileN, rowN) == (player.x, player.y):
                if player.alive:
                    view += "@"
                    pygame.draw.rect(SCREEN, YELLOW, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING), TILE_WIDTH, TILE_WIDTH))
                else:
                    view += " "
            elif tile == 0:
                view += " "
            elif tile == 2:
                view += "#"
                pygame.draw.rect(SCREEN, WHITE, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING), TILE_WIDTH, TILE_WIDTH))
            elif tile == 3:
                view += "X"
                pygame.draw.rect(SCREEN, RED, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING), TILE_WIDTH, TILE_WIDTH))
            elif tile == 4:
                view += "+"
                pygame.draw.rect(SCREEN, PURPLE, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING), TILE_WIDTH, TILE_WIDTH))
            view += " "
        view += "|"
        view += "\n"
    view += "- - - - - - - - - - -\n"
    if lastFrame != view and CLI:
        clear()
        print(view)
    return view


## Constants

# Colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (93, 63, 211)



SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1)
CLOCK = pygame.time.Clock()



grid = []


# for y in range(GRID_Y):
#     row = []
#     for x in range(GRID_X):
#         row.append(0)
#     grid.append(row)

match LVL:
    case 0:
        grid = [[0, 0, 0, 2, 3, 2, 0, 0, 0], 
                [0, 0, 0, 2, 0, 2, 0, 0, 0], 
                [0, 0, 0, 2, 0, 2, 0, 0, 0], 
                [0, 2, 2, 2, 0, 2, 2, 2, 0], 
                [0, 2, 0, 0, 0, 0, 0, 2, 0], 
                [0, 2, 0, 0, 0, 2, 0, 2, 0], 
                [0, 2, 0, 0, 0, 2, 0, 2, 0], 
                [0, 2, 0, 0, 0, 2, 0, 2, 0], 
                [0, 2, 2, 2, 2, 2, 0, 2, 0]]
    case 1:
        with open("asd.json", "r") as f:
            levelData = json.loads(f.read())
            grid = levelData["levelMap"]
            pX, pY = tuple(levelData["playerSpawn"])

p1 = Player(pX, pY)

controls = {
    pygame.K_UP: p1.up,
    pygame.K_DOWN: p1.down,
    pygame.K_LEFT: p1.left,
    pygame.K_RIGHT: p1.right
}

run = True
lastFrame=""
while run:
    CLOCK.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_flag = True
            pygame.quit()
            exit()
    keys = pygame.key.get_pressed()
    for control in controls.keys():
        if keys[control]:
            controls.get(control)()
    p1.tick(grid)
    SCREEN.fill(BLACK)
    
    if CLI: lastFrame = draw(grid, p1, lastFrame)
    else:
        draw(grid, p1)
    pygame.display.flip()
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import json
from datetime import datetime, timedelta
import copy
import os.path

# WIDTH = 1000
# HEIGHT = 600
WIDTH = 640
HEIGHT = 700
HEADER_PADDING = 60
PADDING = 1
TILE_WIDTH = 9
FPS = 60
GRID_X = 64
GRID_Y = 64
CLI = False
UNLOCK_PROGRESSION = True
titlePrefix = "TOTS: "
LVL_dir = "levelFiles"
RUN_DIR = "run"
movementQueueMax = 1
debugMode = False

## Constants

numKeys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]

# Colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
SHALLOW_YELLOW = (132, 148, 113)
PURPLE = (93, 63, 211)
GREY = (128, 128, 128)
LIGHT_BLUE = (155, 255, 255)



SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1)
CLOCK = pygame.time.Clock()

pygame.init()
pygame.font.init()

def getFont(size=12, font="tomb-of-the-mask"):
    # return pygame.font.SysFont(None, size)
    if font == "": return pygame.font.SysFont(None, size)
    return pygame.font.Font(f"./assets/font/{font}/{font}.TTF", size)



def loadLevels(dir):
    levels = {}
    for file in os.scandir(dir):
        if file.is_file:
            name = file.name.split(".")[0]
            levels[name] = {}
            with open(f"{dir}/{file.name}", 'r') as f:
                levelData = json.loads(f.read())
                levels[name]["playerSpawn"] = tuple(levelData["playerSpawn"])
                levels[name]["levelMap"] = levelData["levelMap"]
    return levels


LVLs = loadLevels(LVL_dir)

def syncSave(saveFileName="save.json", write=True, reset=False):
    global SAVE
    fullDir = f"./{RUN_DIR}/{saveFileName}"

    if not os.path.isfile(fullDir):
        if not os.path.isdir(f"./{RUN_DIR}"):
            os.mkdir(RUN_DIR)

        with open(fullDir, "x") as newF:
            newF.write("{}")
            newF.close()

    with open(fullDir, "r+") as saveFile:
        if reset:
            saveFile.seek(0)
            saveFile.truncate()
            saveFile.write(json.dumps({}))
        elif write:
            saveFile.seek(0)
            saveFile.truncate()
            saveFile.write(json.dumps(SAVE, indent=4, sort_keys=True))
        else:
            saveFileData = json.loads(saveFile.read())
            SAVE = saveFileData
        saveFile.close()


syncSave(write=False)

def dprint(x):
    if debugMode: print(x)

def clear():
    os.system("clear")

def setTitle(text, prefix=True):
    pygame.display.set_caption(f"{titlePrefix if prefix else ''}{text}")

# class Button()
#     def __init__(self, pos, font, base_colour)

class Player():
    def __init__(self, pos):
        self.x, self.y = pos
        self.xVel = 0
        self.yVel = 0
        self.moving = False
        self.movementQueue = []
        self.lastMovement = (0,0)
        self.alive = True
        self.won = False
        self.starsCollected = 0
        self.aliveDuration = 0
        self.perishNextMove = []

    def addToMovementQueue(self, velDirection):
        if len(self.movementQueue) < movementQueueMax:
            if self.getLastMovement() != velDirection:
                self.lastMovement = velDirection
                self.movementQueue.append(velDirection)

    def getNextMovement(self, perish=False):
        if len(self.movementQueue) == 0:
            return None
        nextMovement = self.movementQueue[0]
        if perish:
            self.movementQueue = self.movementQueue[1:]
        return nextMovement
    
    def getLastMovement(self):
        if len(self.movementQueue) == 0: return self.lastMovement
        return self.movementQueue[len(self.movementQueue)-1]
    
    def consolidateMovementQueue(self):
        nextMovement = self.getNextMovement(perish=True)
        if nextMovement:
            nextMovementX, nextMovementY = nextMovement
            self.xVel += nextMovementX
            self.yVel += nextMovementY
            self.moving = True
        
    def getAliveDuration(self, formatted=True):
        td = timedelta(seconds=(self.aliveDuration / FPS))
        if formatted:
            return formatTimeDelta(td)
        return td
    

    def up(self):
        self.addToMovementQueue((0, -1))
        # if not self.moving:
        #     self.yVel -= 1
        #     self.moving = True
    def down(self):
        self.addToMovementQueue((0, 1))
        # if not self.moving:
        #     self.yVel += 1 
        #     self.moving = True
    def left(self):
        self.addToMovementQueue((-1, 0))
        # if not self.moving:
        #     self.xVel -= 1
        #     self.moving = True
    def right(self):
        self.addToMovementQueue((1, 0))
        # if not self.moving:
        #     self.xVel += 1
        #     self.moving = True
    def tick(self):
        if self.alive and not self.won: self.aliveDuration += 1
        # dprint(self.movementQueue)
        # dprint(self.getAliveDuration())
        if not self.moving:
            self.consolidateMovementQueue()
        if self.moving:
            for perishX, perishY in self.perishNextMove:
                grid[perishY][perishX] = 0
            desX = self.x + self.xVel
            desY = self.y + self.yVel
            # self.xVel = 0
            # self.yVel = 0
            legal = False
            if desX<GRID_X and desY<GRID_Y: 
                des = grid[desY][desX]
                if des in [0,4,5,6] and desX >= 0 and desY >= 0:
                    legal = True
                    if des == 4:
                        self.starsCollected += 1
                        grid[desY][desX] = 0
                    if des == 5:
                        self.won = True
                    if des == 6:
                        grid[desY][desX] = 2
                if des == 3:
                    self.alive = False
                if des == 7:
                    self.perishNextMove.append((desX, desY))

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

class Button():
    def __init__(self, pos, size, text_str, font, text_colour, bg_colour):
        self.x, self.y = pos
        self.width, self.height = size
        self.text_str = text_str
        self.font = font
        self.text_colour = text_colour
        self.text = self.font.render(self.text_str, True, self.text_colour)
        # if self.image is None: self.image = self.text
        self.bg_colour = bg_colour
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.text_rect = self.text.get_rect(center=(self.x, self.y))
    def update(self, screen):
        pygame.draw.rect(screen, self.bg_colour, self.rect, self.width)
        screen.blit(self.text, self.rect)
    
    def checkForInput(self, pos):
        return self.rect.collidepoint(pos)

def draw(grid, player, lastFrame=""):
    view = ""
    view += "- - - - - - - - - - -\n"
    
    for rowN, row in enumerate(grid):
        view += "| "
        for tileN, tile in enumerate(row):
            if (tileN, rowN) == (player.x, player.y):
                if player.alive:
                    view += "@"
                    pygame.draw.rect(SCREEN, YELLOW, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
                else:
                    view += " "
            elif tile == 0:
                view += " "
            elif tile == 2:
                view += "#"
                pygame.draw.rect(SCREEN, WHITE, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
            elif tile == 3:
                view += "X"
                pygame.draw.rect(SCREEN, RED, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
            elif tile == 4:
                view += "+"
                pygame.draw.rect(SCREEN, PURPLE, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
            elif tile == 5:
                view += "$"
                pygame.draw.rect(SCREEN, GREEN, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
            elif tile == 6:
                view += "O"
                pygame.draw.rect(SCREEN, GREY, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
            elif tile == 7:
                view += "~"
                pygame.draw.rect(SCREEN, LIGHT_BLUE, pygame.Rect(tileN*(TILE_WIDTH+PADDING), rowN*(TILE_WIDTH+PADDING)+HEADER_PADDING, TILE_WIDTH, TILE_WIDTH))
            view += " "
        view += "|"
        view += "\n"
    view += "- - - - - - - - - - -\n"
    if lastFrame != view and CLI:
        clear()
        print(view)
    return view


def formatTimeDelta(timeD):
    minutes = (timeD.seconds//60)%60
    seconds = timeD.seconds - minutes*60
    milliseconds = int((timeD.total_seconds()-timeD.seconds)*1000)
    return str(minutes).zfill(2) + ":" + str(seconds).zfill(2) + ":" + str(milliseconds).zfill(2)[:2]
    # e.g. "04:92"


def drawHUD(screen, player, LVL, buttons=[]):
    collectedFont = getFont(12)
    collectedSurface = collectedFont.render(f"Collected: {player.starsCollected}/3", False, PURPLE)

    currentTimeFont = getFont(12)
    currentTimeSurface = currentTimeFont.render(f"Time: {player.getAliveDuration()}", False, GREEN)

    if LVL in SAVE:
        HSFont = getFont(12)
        HSTime = timedelta(seconds=(SAVE[LVL]["timer"]/ FPS))
        HSTimeString = formatTimeDelta(HSTime)
        HSCollectedString = f"*  [{SAVE[LVL]['collected']}/3]"

        HSTimeSurface = HSFont.render(f"Record: {HSTimeString}", False, YELLOW)
        HSCollectedSurface = HSFont.render(HSCollectedString, False, PURPLE)

        screen.blit(HSTimeSurface, (0, 44))
        screen.blit(HSCollectedSurface, ((HSTimeSurface.get_width()), 44))

    
    for button in buttons:
        button.update(screen)
    backButtonLabelFont = getFont(8)
    backButtonLabelSurface = backButtonLabelFont.render("<esc>", True, YELLOW)
    screen.blit(backButtonLabelSurface, (WIDTH-48, 4))
    

    screen.blit(collectedSurface, (0, 4))
    screen.blit(currentTimeSurface, (0, 24))
    
            
    # dprint(player.timer)


def init(LVL="1"):
    global grid, p1, controls, backButton
    setTitle(f"Level: {LVL}")
    # grid = []
    
    
    grid = copy.deepcopy(LVLs[LVL]["levelMap"]) # deepcopy needed to prevent per-play tile updates from persisting across entire runtime
    pX, pY = LVLs[LVL]["playerSpawn"]

    # match LVL:
    #     case "0":
    #         grid = [[0, 0, 0, 2, 3, 2, 0, 0, 0], 
    #                 [0, 0, 0, 2, 0, 2, 0, 0, 0], 
    #                 [0, 0, 0, 2, 0, 2, 0, 0, 0], 
    #                 [0, 2, 2, 2, 0, 2, 2, 2, 0], 
    #                 [0, 2, 0, 0, 0, 0, 0, 2, 0], 
    #                 [0, 2, 0, 0, 0, 2, 0, 2, 0], 
    #                 [0, 2, 0, 0, 0, 2, 0, 2, 0], 
    #                 [0, 2, 0, 0, 0, 2, 0, 2, 0], 
    #                 [0, 2, 2, 2, 2, 2, 0, 2, 0]]
    #     case _:
    #         with open(f"levelFiles/{LVL}.json", "r") as f:
    #             levelData = json.loads(f.read())
    #             grid = levelData["levelMap"]
    #             pX, pY = tuple(levelData["playerSpawn"])

    p1 = Player((pX, pY))

    controls = {
        pygame.K_UP: p1.up,
        pygame.K_DOWN: p1.down,
        pygame.K_LEFT: p1.left,
        pygame.K_RIGHT: p1.right,

        pygame.K_w: p1.up,
        pygame.K_s: p1.down,
        pygame.K_a: p1.left,
        pygame.K_d: p1.right
    }

    backButton = Button((WIDTH-48, 16), (32, 32), "<", getFont(42, ""), BLACK, YELLOW)

def checkQuit():
    if pygame.event.get(eventtype=pygame.QUIT):
        pygame.quit()
        exit()

# entire menu assumes that all levels are named a unique int (e.g. "1.json", "2.json")
# future support for custom levels will entail a seperate menu entirely, and a different directory for storing them
def levelSelect(): 
    syncSave(write=False)
    setTitle("Level Select", True)
    levelList = sorted(LVLs.keys())
    levelButtons = []
    levelKeybinds = {}

    if UNLOCK_PROGRESSION:
        unlockedLevels = ["1"]
        for level in list(levelList)[1:]:
            if str(int(level)-1) in SAVE:
                unlockedLevels.append(level)
    else:
        unlockedLevels = levelList

    for level in levelList:
        if level in unlockedLevels:
            col = YELLOW
        else:
            col = SHALLOW_YELLOW
        levelButtons.append((Button((int(level)*100-60, 300), (60, 60), level, getFont(84, ""), BLACK, col), level))
        levelKeybinds[numKeys[int(level)-1]] = level
    LVL = None
    while True:
        CLOCK.tick(FPS)
        # LEVEL_SELECT_MOUSE_POS = pygame.mouse.get_pos()

        checkQuit()
        for event in pygame.event.get():
            match event.type:
                case pygame.MOUSEBUTTONDOWN:
                    for levelButton, level in levelButtons:
                        if levelButton.checkForInput(pygame.mouse.get_pos()): 
                            # init(level)
                            # play(level)
                            LVL = level
                            # return
                        # exit()
                case pygame.KEYDOWN:
                    if event.key in levelKeybinds.keys():
                        LVL = levelKeybinds[event.key]
                        # play(levelKeybinds[event.key])
                        # return
        if LVL in unlockedLevels:
            play(LVL=LVL)
            return
        else:
            pass

        SCREEN.fill(BLACK)

        for levelButton, _ in levelButtons:
            levelButton.update(SCREEN)
        pygame.display.flip()

def play(LVL="1"):
    init(LVL)

    run = True
    lastFrame=""

    while run and p1.alive and not p1.won:
        CLOCK.tick(FPS)
        checkQuit()
        for event in pygame.event.get():
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            levelSelect()
                            exit()
                        case pygame.K_r:
                            play(LVL=LVL)
                            exit()
                        case event.key if event.key in controls.keys():
                            controls.get(event.key)()
                case pygame.MOUSEBUTTONDOWN:
                    if backButton.checkForInput(pygame.mouse.get_pos()):
                        levelSelect()
                        exit()
        p1.tick()
        SCREEN.fill(BLACK)
        if CLI: lastFrame = draw(grid, p1, lastFrame)
        else:
            draw(grid, p1)
        drawHUD(SCREEN, p1, LVL, buttons=[backButton])
        pygame.display.flip()
    

    if p1.won:
        match win(LVL):
            case 1:
                play(LVL=LVL)
            case 0:
                levelSelect()
        exit()
    elif not p1.alive:
        match deathOverlay(SCREEN, p1):
            case 1:
                play(LVL=LVL)
            case 0:
                levelSelect()
        # levelSelect()

        exit()
        

def deathOverlay(screen, player):
    setTitle("GAME OVER")

    syncSave()
    retryText = getFont(16)
    retryTextSurface = retryText.render("<R> to retry.", False, YELLOW)
    SCREEN.blit(retryTextSurface, (WIDTH/2 - (retryTextSurface.get_width()/2), 10))

    # quitText = getFont(20)
    
    pygame.display.flip()
    while True:
        CLOCK.tick(FPS)
        checkQuit()
        for event in pygame.event.get(eventtype=[pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if backButton.checkForInput(pygame.mouse.get_pos()):
                    return 0
            else:
                match event.key:
                    case pygame.K_r:
                        return 1
                    case pygame.K_ESCAPE:
                        return 0
                

class CompletionRecord():
    def __init__(self, timer=0, collected=0, completedAt=None, recordDict=None):
        if recordDict:
            self.timer = recordDict["timer"]
            self.collected = recordDict["collected"]
            self.completedAt = recordDict["completedAt"]
        else:
            self.timer = timer
            self.collected = collected
            if not completedAt: 
                self.completedAt = int(datetime.now().timestamp())
            else: 
                self.completedAt = completedAt
    def toDict(self):
        return copy.deepcopy({
            "timer" : self.timer,
            "collected" : self.collected,
            "completedAt" : self.completedAt
        })

def win(LVL):
    syncSave(write=False)
    setTitle("Level complete!")
    completionRecord = CompletionRecord(p1.aliveDuration, p1.starsCollected)
    isHiScore = False
    if LVL not in SAVE:
        isHiScore = True
    else:
        savedRecord = CompletionRecord(recordDict=SAVE[LVL])
        # example Ordering of scores (best -> worst): (12s, any stars) > (15s, 3 stars) > (15s 0 stars) > (17s, any stars)
        # may implement system of valuing scores using both speed and star collection, 
        # also since scores are stored in ticks, the second comparison will practically never be checked
        if (completionRecord.timer < savedRecord.timer) or (completionRecord.timer == savedRecord.timer and completionRecord.collected > savedRecord.collected):
            isHiScore = True
    
    if isHiScore:
        SAVE[LVL] = completionRecord.toDict()
        syncSave()
    syncSave(write=False)

    levelCompleteFont = getFont(16)
    levelCompleteSurface = levelCompleteFont.render("<SPACE> to continue!", False, YELLOW, BLACK)
    SCREEN.blit(levelCompleteSurface, ((WIDTH/2 - (levelCompleteSurface.get_width()/2)), 8))
    
    if isHiScore:
        newRecordFont = getFont(16)
        newRecordSurface = newRecordFont.render("NEW RECORD!", False, GREEN, BLACK)
        SCREEN.blit(newRecordSurface, ((WIDTH/2 - (newRecordSurface.get_width()/2)), 32))
    pygame.display.flip()
    while True:
        CLOCK.tick(FPS)
        checkQuit()
        for event in pygame.event.get(eventtype=[pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if backButton.checkForInput(pygame.mouse.get_pos()):
                    return 0
            else:
                match event.key:
                    case pygame.K_SPACE | pygame.K_ESCAPE:
                        return 0
                    case pygame.K_r:
                        return 1






if __name__ == "__main__":
    if debugMode:
        play("3")
    else:
        levelSelect()

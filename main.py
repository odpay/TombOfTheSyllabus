import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # prevents pygame support message
import pygame
import json
from datetime import datetime, timedelta
import copy
import os.path
import platform
from pathlib import Path

### CONFIG

FPS = 60 # Frames Per Second, to be rendered. modifying this does not offer an advantage to beating scores.
CLI = False # CLI mode, not officially supported
FIXED_PROGRESSION = True # if levels must be unlocked progressively
LVL_DIR = "levelFiles" # directory for storing level files
RUN_DIR = "run" # directory for storing config & save data
movementQueueMax = 1 # limit for queueing movement actions
debugMode = False

### CONSTANTS:

PARENT_DIR = Path(__file__).resolve().parent # directory of the main.py file

# Window dimensions
WIDTH, HEIGHT = 640, 700
HEADER_PADDING = 60 # gap above level view for displaying unobstructed HUD components

# Gameplay rendering parameters
PADDING = 1 # pixel gap between tiles
TILE_SIZE = 9 # length of (square) tiles
GRID_X, GRID_Y = 64, 64 # tile dimensions of level plane 

titlePrefix = "TOTS: " # Constant prefix for window title 
SELF_PLATFORM = platform.system() # identified operating system of host, for cross compatability


numKeys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9] # used for level select keybinds

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





# Pygame initialisation boilerplate
pygame.init() # ensures better cross-compatability
pygame.font.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1)
CLOCK = pygame.time.Clock()


### CLASSES:


# Object representing the player (character) belonging to each level completion attempt
class Player():
    def __init__(self, pos):
        self.x, self.y = pos # coordinate position (x,y)
        self.xVel = 0 # x-axis velocity
        self.yVel = 0 # y-axis velocity
        self.moving = False # flag for if the player is currently moving
        self.movementQueue = [] # queue of movements to be applied in legal succession 
        self.lastMovement = (0,0) # the last recorded movement
        self.alive = True # is the player alive?
        self.won = False # has the end point been reached yet?
        self.starsCollected = 0 # how many 'stars' (purple blobs) have been collected so far
        self.aliveDuration = 0 # how long has the player been alive (in ticks)
        self.perishNextMove = [] # tiles in the level to be deleted after the next movement

    def addToMovementQueue(self, velDirection): # add a directional velocity to the queue of movements to be applied when next possible
        if len(self.movementQueue) < movementQueueMax: # limited to ensure optimal autonomy
            if self.getLastMovement() != velDirection: # ignores duplicate movement requests, prevents clogging of the queue and improves the FEEL of gameplay
                self.lastMovement = velDirection
                self.movementQueue.append(velDirection)

    def getNextMovement(self, perish=False): # returns the next movement in the queue, optionally deletes it.
        if len(self.movementQueue) == 0:
            return None
        nextMovement = self.movementQueue[0]
        if perish:
            self.movementQueue = self.movementQueue[1:]
        return nextMovement
    
    def getLastMovement(self): # gets the last movement added to the queue
        if len(self.movementQueue) == 0: return self.lastMovement
        return self.movementQueue[len(self.movementQueue)-1]
    
    def consolidateMovementQueue(self): # applies the next velocity change in the queue
        nextMovement = self.getNextMovement(perish=True) # gets the next velocity change, and deletes it from the queue
        if nextMovement: # if a queued action exists, apply the velocity change
            nextMovementX, nextMovementY = nextMovement
            self.xVel += nextMovementX
            self.yVel += nextMovementY
            self.moving = True
        
    def getAliveDuration(self, formatted=True): # returns an optionally formatted representation of how long the player has been alive
        td = timedelta(seconds=(self.aliveDuration / FPS))
        if formatted:
            return formatTimeDelta(td)
        return td
    

    # movement methods, these are called following a directional keypress
    def up(self):
        self.addToMovementQueue((0, -1)) # adds a velocity 'vector' to the movement queue, these are directional and translated to the convention of grid indexes.
    def down(self):
        self.addToMovementQueue((0, 1))
    def left(self):
        self.addToMovementQueue((-1, 0))
    def right(self):
        self.addToMovementQueue((1, 0))

    # updates the player, this is called every frame
    def tick(self):
        if self.aliveDuration == 0 and self.moving: self.aliveDuration += 1 # ensures the timer starts when the player moves
        if self.alive and not self.won and (self.aliveDuration > 0) : self.aliveDuration += 1 # incriment the aliveDuration ticker

        if not self.moving: # executes queued movement actions as soon as its legal (has landed on surface)
            self.consolidateMovementQueue()

        if self.moving:
            for perishX, perishY in self.perishNextMove: # removes previously touched 'cloud tiles' once the player has left them
                grid[perishY][perishX] = 0
            
            # location of tile player is about to move into
            desX = self.x + self.xVel
            desY = self.y + self.yVel
            legal = False # flag determining whether the player can actually move into said tile

            if desX<GRID_X and desY<GRID_Y: # bounds check
                des = grid[desY][desX] # gets tile type
                if des in [0,4,5,6] and desX >= 0 and desY >= 0: # tiles legal to move into (e.g. air, stars, etc.)
                    legal = True
                    if des == 4: # star
                        self.starsCollected += 1
                        grid[desY][desX] = 0 
                    if des == 5: # end point
                        self.won = True
                    if des == 6: # grey 'solidifying' tile
                        grid[desY][desX] = 2
                if des == 3: # red 'fire' tile
                    self.alive = False
                if des == 7: # 'cloud' tile
                    self.perishNextMove.append((desX, desY))

            if legal: # actually moves player
                self.moving = True
                self.x = desX
                self.y = desY
            else: # halts player velocity
                self.moving = False
                self.xVel = 0
                self.yVel = 0

# class used for clickable buttons
class Button():
    def __init__(self, pos, size, text_str, font, text_colour, bg_colour):
        self.x, self.y = pos
        self.width, self.height = size
        self.text_str = text_str # actual text contents of button
        self.font = font # font object to render text
        self.text_colour = text_colour
        self.text = self.font.render(self.text_str, True, self.text_colour) # text surface
        self.bg_colour = bg_colour
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height) # clickable rectangle drawn behind the text
    
    def update(self, screen): # draws the button box and text to screen
        pygame.draw.rect(screen, self.bg_colour, self.rect, self.width)
        screen.blit(self.text, self.rect)
    
    def checkForInput(self, pos): # checks if mouse is hovering over button
        return self.rect.collidepoint(pos)

# Object detailing information on a saved level completion
class CompletionRecord():
    def __init__(self, timer=0, collected=0, completedAt=None, recordDict=None):
        if recordDict: # in the case that this object is initialised from a dict (de-serialisation)
            self.timer = recordDict["timer"]
            self.collected = recordDict["collected"]
            self.completedAt = recordDict["completedAt"]
        else:
            self.timer = timer
            self.collected = collected
            if not completedAt: 
                self.completedAt = int(datetime.now().timestamp()) # miscellaneous timestamp for when the completion occured
            else: 
                self.completedAt = completedAt
    
    def toDict(self): # converts object into dict form (serialisation)
        return copy.deepcopy({
            "timer" : self.timer,
            "collected" : self.collected,
            "completedAt" : self.completedAt
        })


### FUNCTIONS:

## MISC FUNCTIONS:

def dprint(x): # conditional print, only for debug mode
    if debugMode: print(x)

def clear(): # clears all printed text in console, used for CLI mode
    if SELF_PLATFORM == "Windows":
        os.system("cls") # Windows
    else:
        os.system("clear") # Unix (Mac, Linux)

def setTitle(text, prefix=True): # function to set the game window title, useful for clearly indicating the current menu or level
    pygame.display.set_caption(f"{titlePrefix if prefix else ''}{text}")

# easy function to check and adhere to external quit requests (i.e. closing the game window)
def checkQuit():
    if pygame.event.get(eventtype=pygame.QUIT):
        pygame.quit()
        exit()


# formats timeDelta objects (durations) into a more readable format, (MM:SS:MS)
def formatTimeDelta(timeD):

    minutes = (timeD.seconds//60)%60
    seconds = timeD.seconds - minutes*60
    milliseconds = int((timeD.total_seconds()-timeD.seconds)*1000)

    return str(minutes).zfill(2) + ":" + str(seconds).zfill(2) + ":" + str(milliseconds).zfill(2)[:2] # Zero padding to ensure fixed string length, unless the run goes over 100 minutes haha.
    # e.g. "04:92"



## I/O FUNCTIONS:


# Load stored level designs from disk, (deserialised from json)
def loadLevels(dir):
    fullDir = PARENT_DIR.joinpath(dir)
    levels = {}
    # iterates through a directory of level files
    for file in os.scandir(fullDir):
        if file.is_file:
            name = file.name.split(".")[0] # treats filename as level name (e.g. "3.json" -> "3")
            levels[name] = {}
            with open(fullDir.joinpath(file.name), 'r') as f:
                levelData = json.loads(f.read())
                levels[name]["playerSpawn"] = tuple(levelData["playerSpawn"]) # specified coordinates to spawn the player
                levels[name]["levelMap"] = levelData["levelMap"] # nested array of tiles (the grid)
    return levels




# accesses and updates the saved progression data from storage
def syncSave(saveFileName="save.json", write=True, reset=False):
    # SAVE is used to access the records
    global SAVE
    fullDir = PARENT_DIR.joinpath(RUN_DIR, saveFileName)

    # creates directory and file if absent (first time run)
    if not os.path.isfile(fullDir):
        if not os.path.isdir(fullDir.parent):
            os.mkdir(fullDir.parent)
        with open(fullDir, "x") as newF:
            newF.write("{}")
            newF.close()

    # Reads contents of file (deserialises from json)
    with open(fullDir, "r+") as saveFile:
        if reset: # flag to reset all progression
            saveFile.seek(0)
            saveFile.truncate()
            saveFile.write(json.dumps({}))
        elif write: # flag to write modified save data to disk
            saveFile.seek(0)
            saveFile.truncate()
            saveFile.write(json.dumps(SAVE, indent=4, sort_keys=True))
        else: # only reading to update the SAVE object
            saveFileData = json.loads(saveFile.read())
            SAVE = saveFileData
        saveFile.close()



## RENDER FUNCTIONS:


# Returns a font object at a specified size and font, used for drawing all text, default font is stored in assets/font/... (along with license)
def getFont(size=12, font="tomb-of-the-mask"):
    if font == "": return pygame.font.SysFont(None, size) # System font
    return pygame.font.Font(PARENT_DIR.joinpath(f"assets/font/{font}/{font}.ttf"), size)



# draws the main game grid (player, tiles) with support for CLI (console) rendering.
def draw(grid, player, lastFrame=""):
    
    # 'view' is a large string of the level, to be printed when CLI mode is in use
    view = ""
    view += "- - - - - - - - - - -\n"
    


    # iterates through all tiles in grid to render
    # each tile type has a cooresponding character (for CLI mode) and respective 'rectangle' to be drawn on screen,

    # the reason behind alot of repeating code is so that it allows for future implementation of more special tiles that render differently and thus require more than drawing a single rectangle
    # ^^ (e.g. flashing spikes or an end-point omitting particles).

    # as of writing, all tile types are just static coloured rectangles, for now.
    for rowN, row in enumerate(grid):
        view += "| "
        for tileN, tile in enumerate(row):
            if (tileN, rowN) == (player.x, player.y): # is player
                if player.alive:
                    view += "@" 
                    pygame.draw.rect(SCREEN, YELLOW, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
                else:
                    view += " "
            elif tile == 0: # air
                view += " "
            elif tile == 2: # wall
                view += "#"
                pygame.draw.rect(SCREEN, WHITE, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
            elif tile == 3: # 'fire'
                view += "X"
                pygame.draw.rect(SCREEN, RED, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
            elif tile == 4: # collectable 'star'
                view += "+"
                pygame.draw.rect(SCREEN, PURPLE, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
            elif tile == 5: # end point
                view += "$"
                pygame.draw.rect(SCREEN, GREEN, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
            elif tile == 6: # grey 'solidifying' tile
                view += "O"
                pygame.draw.rect(SCREEN, GREY, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
            elif tile == 7: # disappearing 'cloud' tile
                view += "~"
                pygame.draw.rect(SCREEN, LIGHT_BLUE, pygame.Rect(tileN*(TILE_SIZE+PADDING), rowN*(TILE_SIZE+PADDING)+HEADER_PADDING, TILE_SIZE, TILE_SIZE))
            view += " "
        view += "|"
        view += "\n"
    view += "- - - - - - - - - - -\n"
    if lastFrame != view and CLI: # CLI: prevents reprinting of level every 'frame' if nothing has changed, prevents excessive flickering in console
        clear()
        print(view)
    return view



# Draws the HUD elements used in gameplay, that is;
# collection counter, run timer, best record view (if applicable), small <ESC> label above the back button
def drawHUD(screen, player, LVL, buttons=[]):

    collectedFont = getFont(12)
    collectedSurface = collectedFont.render(f"Collected: {player.starsCollected}/3", False, PURPLE) # All levels are designed with 3 collectables each, the counter denominator can be made dynamic following custom level support.  

    currentTimeFont = getFont(12)
    currentTimeSurface = currentTimeFont.render(f"Time: {player.getAliveDuration()}", False, GREEN) # formatted timer of how long the player has been alive

    if LVL in SAVE: # if the level has been previously completed, display the record time
        HSFont = getFont(12)
        HSTime = timedelta(seconds=(SAVE[LVL]["timer"]/ FPS))
        HSTimeString = formatTimeDelta(HSTime)

        HSCollectedString = f"*  [{SAVE[LVL]['collected']}/3]" # appended indicator showing how many 'stars' were collected for the record completion

        # the record time and it's respective collection counter must be different surfaces as they are different colours.
        HSTimeSurface = HSFont.render(f"Record: {HSTimeString}", False, YELLOW)
        HSCollectedSurface = HSFont.render(HSCollectedString, False, PURPLE)

        
        screen.blit(HSTimeSurface, (0, 44)) # renders record time
        screen.blit(HSCollectedSurface, ((HSTimeSurface.get_width()), 44)) # renders respective record collection count after the time

    # updates (renders) all buttons passed into the drawHUD function, (e.g. back button)
    for button in buttons:
        button.update(screen)
    
    # draws the tiny "<ESC>" label above the back button
    backButtonLabelFont = getFont(8)
    backButtonLabelSurface = backButtonLabelFont.render("<esc>", True, YELLOW)
    screen.blit(backButtonLabelSurface, (WIDTH-48, 4))
    
    # renders the current run timer and collection counters
    screen.blit(collectedSurface, (0, 4))
    screen.blit(currentTimeSurface, (0, 24))




## CORE/MENU FUNCTIONS:

# The Main menu, not neccesarily the 'mainline', but this is the first menu encountered each runtime.
def mainMenu():
    setTitle("Main Menu")

    # Title text
    titleFont = getFont(30)
    titleSurface = titleFont.render("Tomb Of The Syllabus", False, YELLOW)

    #Title subtext
    titleSubFont = getFont(20)
    titleSubSurface = titleSubFont.render("By Josh", False, PURPLE)
    
    # Play and quit button objects
    playButton = Button((WIDTH/2 - 90, HEIGHT/2 - 30), (180, 60), "PLAY", getFont(94, ""), BLACK, YELLOW)
    quitButton = Button((WIDTH/2 - 90, HEIGHT/2 + 75), (180, 60), "QUIT", getFont(94, ""), BLACK, YELLOW)

    # Render text & buttons
    SCREEN.fill(BLACK)
    SCREEN.blit(titleSurface, (WIDTH/2 - (titleSurface.get_width()/2), 32))
    SCREEN.blit(titleSubSurface, (WIDTH/2 - (titleSubSurface.get_width()/2), 32 + titleSurface.get_height() + 4))
    playButton.update(SCREEN)
    quitButton.update(SCREEN)
    pygame.display.flip()

    # Runtime loop, for responding to user input, consider each pass of the loop as a 'tick'
    while True:
        CLOCK.tick(FPS) # Limits the loop to not tick more than the specified framerate cap each second.
        
        checkQuit()

        pos = pygame.mouse.get_pos() # mouse cursor position
        for event in pygame.event.get(eventtype=[pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN]): # fetches and iterates through relevant events ONLY
            match event.type:
                case pygame.MOUSEBUTTONDOWN: # if mouse is clicked, check if cursor collides with any of the buttons

                    if playButton.checkForInput(pos): # play (enter level select)
                        levelSelect() # level select menu
                        exit() 
                        # Only time I will state this: the navigation through different 'Menus' of the program is (mostly) a return-less process.
                        # A proceeding exit() ensures that, in the event of an exception (or return) from a subroutine, the runtime cannot jump straight back into the run-loops of any menus priorly visited. And will instead cease execution entirely.
                        # This is mindfully contrary to the depictions made in adjacent system-level design specifications, as the functionality and UX is identical.
                    
                    elif quitButton.checkForInput(pos): # quit
                        exit()
                
                case pygame.KEYDOWN: # quick keybinds for experienced users to navigate the menu faster
                    match event.key:
                        case pygame.K_ESCAPE | pygame.K_q: # quit
                            exit()
                        case pygame.K_SPACE | pygame.K_RETURN | pygame.K_p: # play (enter level select)
                            levelSelect()
                            exit()


# This entire menu assumes that all levels are named a unique int (e.g. "1.json", "2.json")
# future support for custom levels will entail a seperate menu entirely, and a different directory for storing them
def levelSelect(): 
    # backButton is initialised and made global by the level select menu as levelSelect is the 'highest level' in the user navigation hierarchy to which the button appears.
    global backButton

    # Ensures cached save data is up to date
    syncSave(write=False)
    setTitle("Level Select", True)

    levelList = sorted(LVLs.keys()) # Names of the levels that exist
    levelButtons = [] # List of Button objects for each level
    levelKeybinds = {} # Map of macro keys and their cooresponding levels

    # Render "Level Select" header text.
    levelSelectText = getFont(32)
    levelSelectSurface = levelSelectText.render("Level Select", False, YELLOW)

    # initialise back button
    backButton = Button((WIDTH-48, 16), (32, 32), "<", getFont(42, ""), BLACK, YELLOW)


    if FIXED_PROGRESSION: # True by default, determines if levels should be only playable if the previous level has been completed.
        unlockedLevels = ["1"] # level 1 is always playable
        for level in list(levelList)[1:]:
            if str(int(level)-1) in SAVE: # checks save data for prior level completions.
                unlockedLevels.append(level)
    else:
        unlockedLevels = levelList # unlocks all levels 

    for level in levelList: # iterates through all levels
        if level in unlockedLevels: # if level is unlocked, the button will be a bright yellow
            col = YELLOW
        else:
            col = SHALLOW_YELLOW
        
        levelButtons.append((Button((int(level)*100-60, 300), (60, 60), level, getFont(84, ""), BLACK, col), level)) # assumes official levels have numeric names, useful for ordering
        levelKeybinds[numKeys[int(level)-1]] = level # adds an accepted number keybind for quick level selection
    
    LVL = None # level selected by user
    while True:
        CLOCK.tick(FPS)
        checkQuit()

        for event in pygame.event.get():
            match event.type:
                case pygame.MOUSEBUTTONDOWN: # if mouse clicked
                    for levelButton, level in levelButtons:
                        if levelButton.checkForInput(pygame.mouse.get_pos()): # if a level button is pressed, set the selected level accordingly
                            LVL = level
                        elif backButton.checkForInput(pygame.mouse.get_pos()):
                            mainMenu()
                            exit()
                case pygame.KEYDOWN: # if key pressed
                    if event.key in levelKeybinds.keys(): # if the pressed key cooresponds to a level, set the selected level accordingly
                        LVL = levelKeybinds[event.key]
                    elif event.key == pygame.K_ESCAPE:
                        mainMenu()
                        exit()
        if LVL in unlockedLevels: # check if the selected level is unlocked
            play(LVL=LVL) # enters the level, (the play menu)
            return

        # Renders text and buttons
        SCREEN.fill(BLACK)
        SCREEN.blit(levelSelectSurface, (WIDTH/2 - (levelSelectSurface.get_width()/2), 64))
        backButton.update(SCREEN)
        for levelButton, _ in levelButtons:
            levelButton.update(SCREEN)
        pygame.display.flip()


# initialises objects unique to each 'run' (level attempt)
def init(LVL="1"):
    # the grid, player, and player controls are made global as they only exist as one instance of themselves at any given time
    # and they are widely accessed
    # these globals will (mostly) still be passed subroutines to avoid race conditions 
    global grid, p1, controls

    setTitle(f"Level: {LVL}") # set window title text
    
    # deepcopy needed to prevent per-play tile updates from persisting across entire runtime, 
    # e.g. ensures that previously collected stars will re-appear each time the level is restarted.
    grid = copy.deepcopy(LVLs[LVL]["levelMap"])

    # gets the player starting coordinates
    pX, pY = LVLs[LVL]["playerSpawn"]

    p1 = Player((pX, pY)) # initialises the player at said starting coordinates

    # control mapping of (key : action)
    # must be re-declared in initialisation as the movement actions are dynamic to each new player instance (p1).
    controls = {
        # arrow keys
        pygame.K_UP: p1.up,
        pygame.K_DOWN: p1.down,
        pygame.K_LEFT: p1.left,
        pygame.K_RIGHT: p1.right,

        # WASD keys
        pygame.K_w: p1.up,
        pygame.K_s: p1.down,
        pygame.K_a: p1.left,
        pygame.K_d: p1.right
    }



# The gameplay 'menu', this is where the actual game is played
def play(LVL="1"):
    init(LVL) # initialises objects unique to each level attempt

    lastFrame="" # the text contents of the last printed frame (CLI MODE)

    while p1.alive and not p1.won: # Runtime only loops if player is not dead, and has not reached the end.
        CLOCK.tick(FPS) # limits tickrate (passes of this runtime loop) to FPS
        checkQuit() # checks for quit actions by player

        # iterate through recent events
        for event in pygame.event.get():
            match event.type:
                case pygame.KEYDOWN: # if key is pressed
                    match event.key:
                        case pygame.K_ESCAPE: # escape key functions identically to back button 
                            levelSelect()
                            exit()
                        case pygame.K_r: # Allows user to quickly (R)etry the level.
                            play(LVL=LVL)
                            exit()
                        case event.key if event.key in controls.keys():
                            controls.get(event.key)() # executes respective player movement actions if a movement key is pressed
                case pygame.MOUSEBUTTONDOWN: 
                    if backButton.checkForInput(pygame.mouse.get_pos()): # if back button is pressed, return to levelSelect menu
                        levelSelect()
                        exit()
        
        p1.tick() # updates the player (collision checking, movement, etc.)

        # Renders game contents (in game window and/or console (CLI MODE))
        SCREEN.fill(BLACK)
        if CLI: lastFrame = draw(grid, p1, lastFrame)
        else:
            draw(grid, p1)
        
        # Renders the HUD elements (timers, back button, etc.)
        drawHUD(SCREEN, p1, LVL, buttons=[backButton])

        pygame.display.flip()
    
    
    if p1.won: # if end point has been reached
        match win(LVL): # function to present a "level complete" overlay
            case 1: # returns 1 to retry level
                play(LVL=LVL)
            case 0: # returns 0 to continue to level select menu
                levelSelect()
        exit()


    elif not p1.alive: # if player has died
        match deathOverlay(): # function to present a restart prompt
            case 1: # retry level
                play(LVL=LVL)
            case 0: # return to level select menu
                levelSelect()
        exit()


# in the event of the player dying.
# ^ 'player' as in the character, the user is hopefully still alive.
def deathOverlay():
    setTitle("GAME OVER")

    syncSave()

    # Render retry prompt text (over the frozen game and hud)
    retryText = getFont(16)
    retryTextSurface = retryText.render("<R> to retry.", False, YELLOW)
    SCREEN.blit(retryTextSurface, (WIDTH/2 - (retryTextSurface.get_width()/2), 10))
    pygame.display.flip()


    while True:
        CLOCK.tick(FPS)
        checkQuit()

        for event in pygame.event.get(eventtype=[pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]): # Listen for input
            if event.type == pygame.MOUSEBUTTONDOWN:
                if backButton.checkForInput(pygame.mouse.get_pos()): # back button pressed
                    return 0
            else:
                match event.key:
                    case pygame.K_r: # r key pressed (retry level)
                        return 1
                    case pygame.K_ESCAPE: # escaoe key pressed (back button)
                        return 0


# in the event of a level's end point being reached
def win(LVL):
    syncSave(write=False) # Ensure cached save data is up to date.
    setTitle("Level complete!")

    # An object containing details about the completion (that just happened) for the current level
    completionRecord = CompletionRecord(p1.aliveDuration, p1.starsCollected)
    
    isHiScore = False # if the player has just beaten the record
    if LVL not in SAVE: # a previous record doesn't exist
        isHiScore = True
    else:
        savedRecord = CompletionRecord(recordDict=SAVE[LVL]) # An object of the saved record for the level


        # determines which completion is more valuable (quickest time).
        #
        # An example Ordering of scores: (best -> worst): (12s, any stars) > (15s, 3 stars) > (15s 0 stars) > (17s, any stars)
        # I may implement system of valuing scores using both speed and star collection.
        # Also since scores are stored in ticks, the second comparison (of star count) will practically never be checked.
        if (completionRecord.timer < savedRecord.timer) or (completionRecord.timer == savedRecord.timer and completionRecord.collected > savedRecord.collected):
            isHiScore = True
    
    # Set and update the save data
    if isHiScore:
        SAVE[LVL] = completionRecord.toDict()
        syncSave()
    syncSave(write=False)

    # text prompting the user to continue to the next level
    levelCompleteFont = getFont(16)
    levelCompleteSurface = levelCompleteFont.render("<SPACE> to continue!", False, YELLOW, BLACK)
    SCREEN.blit(levelCompleteSurface, ((WIDTH/2 - (levelCompleteSurface.get_width()/2)), 8))
    
    # text indicating that the record time has just been beaten
    if isHiScore:
        newRecordFont = getFont(16)
        newRecordSurface = newRecordFont.render("NEW RECORD!", False, GREEN, BLACK)
        SCREEN.blit(newRecordSurface, ((WIDTH/2 - (newRecordSurface.get_width()/2)), 32))
    pygame.display.flip()

    # checks for inputs, user can either continue (go back to level select), or retry the level.
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




# executes main menu when program is launched
if __name__ == "__main__":
    syncSave(write=False)
    LVLs = loadLevels(LVL_DIR)
    mainMenu()

from PIL import Image
import json
from pathlib import Path
PARENT_DIR = Path(__file__).resolve().parent # directory of the main.py file

LVL = input("LVL name? (./levelSprites/{?}.png): ") # level to convert


im = Image.open(PARENT_DIR.joinpath(f"levelSprites/{LVL}.png"), 'r') # image object


# Colours
RED = (255,0,0)
WHITE = (255,255,255)
BLUE = (0,0,255)
YELLOW = (255,255,0)
GREEN = (0,255,0)
BLACK = (0,0,0)
PURPLE = (93, 63, 211)
GREY = (128, 128, 128)
LIGHT_BLUE = (155, 255, 255)


levelData = {}
level = []

for rownum in range(64): # iterates through pixels in file, appends their cooresponding tile id
    row = []
    for pixelnum in range(64):
        col = im.getpixel((pixelnum, rownum))
        col = col[0:3]
        if col == WHITE:
            row.append(0)
        elif col == BLACK:
            row.append(2)
        elif col == RED:
            row.append(3)
        elif col == BLUE:
            levelData["playerSpawn"] = (pixelnum, rownum)
            row.append(0)
        elif col == PURPLE:
            row.append(4)
        elif col == GREEN:
            row.append(5)
        elif col == GREY:
            row.append(6)
        elif col == LIGHT_BLUE:
            row.append(7)
        else:
            row.append(0)
    level.append(row)

levelData["levelMap"] = level
with open(PARENT_DIR.joinpath(f"levelFiles/{LVL}.json"), "w") as f: # store as JSON
    f.write(json.dumps(levelData))
    f.close()

from PIL import Image
import json

LVL = "1"

im = Image.open(f'levelsprites/{LVL}.png', 'r')

RED = (255,0,0)
WHITE = (255,255,255)
BLUE = (0,0,255)
YELLOW = (255,255,0)
GREEN = (0,255,0)
BLACK = (0,0,0)
PURPLE = (93, 63, 211)
levelData = {}
level = []

for rownum in range(64):
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
        else:
            row.append(0)
    level.append(row)

levelData["levelMap"] = level
with open(f"levelFiles/{LVL}.json", "w") as f:
    f.write(json.dumps(levelData))

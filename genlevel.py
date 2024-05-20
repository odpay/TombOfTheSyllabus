from PIL import Image
import json

LVL = "1"

im = Image.open(f'levelsprites/{LVL}.png', 'r')

class colors:
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
        match col:
            case colors.WHITE:
                row.append(0)
            case colors.BLACK:
                row.append(2)
            case colors.RED:
                row.append(3)
            case colors.BLUE:
                levelData["playerSpawn"] = (pixelnum, rownum)
                row.append(0)
            case colors.PURPLE:
                row.append(4)
            case colors.GREEN:
                row.append(5)
            case _:
                row.append(0)
    level.append(row)

levelData["levelMap"] = level
with open(f"levelFiles/{LVL}.json", "w") as f:
    f.write(json.dumps(levelData))

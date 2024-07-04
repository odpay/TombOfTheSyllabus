# Tomb Of The Syllabus
Cute arcade game for my [HSC SDD](https://educationstandards.nsw.edu.au/wps/portal/nesa/11-12/stage-6-learning-areas/tas/software-design-development) major work.





## Setup

Python 3.10+ required, (written with Python 3.12.2)

install dependencies as needed using `pip`, 
- tested: pygame 2.5.2+
```zsh
pip3 install pygame
```
*(or 'pip' for Windows)*

*a `requirements.txt` will be generated in a future commit, if needed.*

## Running
`cd` into the script directory, ensure all other project files are present.

For Linux/MacOS (UNIX):
```zsh
python3 ./main.py
```
For Windows:
```zsh
python ./main.py
```


## Contributing

PRs are welcome, they should be meaningful.

### Level designs
Level designs would be most appreciated, just open [template.png](levelSprites/template.png) in a pixel-percision image editor (e.g. [LibreSprite](https://github.com/LibreSprite/LibreSprite)). 

The colours and their corresponding tile types can be easily inferred.

Save the png with a new name, and generate it's (.json) level file using [genlevel.py](genlevel.py).
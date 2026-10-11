# Hex Map Editor (prototype)

A hex map editor written in Python with pygame. It's the first step of a larger plan: map editor, then random map generation, then a turn-based strategy engine, then a game.

**Status:** early prototype. You can paint terrain on a hex map with different brush sizes, draw rivers, and save and load maps.

## Setup

1. Install **Python 3.12 or newer** from [python.org](https://www.python.org/downloads/). On Windows, tick **"Add python.exe to PATH"** in the installer.
2. Download this project (green **Code** button → **Download ZIP**, then unzip it) or clone it with Git.
3. Open a terminal in the project folder and install pygame:

   ```
   python -m pip install -r requirements.txt
   ```

## Running it

- **Windows:** double-click `run_editor.bat`.
- **Any system:** run `python editor_main.py` in the project folder.

## Controls

| Action | How |
|---|---|
| Pick a terrain | Click it in the palette on the left (scroll the palette with the mouse wheel) |
| Paint | Left-click a hex, or hold and drag |
| Brush size (1–10) | **[** and **]**, or the − / + buttons in the toolbar |
| New map (choose size) | Ctrl+N, or the **New** button |
| Open a map | Ctrl+O, or the **Open** button |
| Save / Save as | Ctrl+S / Ctrl+Shift+S, or the toolbar buttons |
| Move the view | Hold the right or middle mouse button and drag, or use WASD / arrow keys |
| Zoom | Mouse wheel (zooms toward the mouse pointer) |
| Show the whole map | Home |
| Grid lines on/off | G |

## Rivers

Pick a river from the **RIVERS** section at the bottom of the palette (scroll down). All rivers run *along the borders* between hexes, as obstacles to cross:

- **Stream / Creek**, **River** and **Major River**, each wider than the last. Click near a hex border, then drag: the river follows the borders corner to corner. Join a smaller river onto a bigger one to build a river system.
- **Erase rivers**: removes the river on the border nearest the mouse.

River types are listed in `data/rivers.json` (name, colour, width).

## Terrains

There are 17 terrains: the 14 WWF terrestrial biomes plus ocean, sea and lake. They're listed in `data/terrains.json`. Each one uses a 128×111 PNG in `ASSETS/textures/`, which you can replace with your own art. `generate_textures.bat` (or `python tools/generate_textures.py`) recreates any missing textures and leaves existing ones alone.

## Map files

Maps are saved as `.json` files in the `MAPS/` folder. They're plain text: each line of the `"terrain"` list is one row of hexes. The editor asks before closing or opening another map if there are unsaved changes, and the window title shows `*` when there are.

## Project layout

```
hexcore/     hex math, terrain list and map data (reused by later phases)
editor/      the editor window, camera, textures and UI panels
data/        terrain definitions
ASSETS/      all graphics, kept apart from the code
MAPS/        saved maps
tools/       helper scripts (texture generator)
tests/       automatic checks: python -m unittest
```

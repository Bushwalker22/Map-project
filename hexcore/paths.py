"""
Where things live on disk. Every other file asks this one, so if a folder
ever moves, only this file needs changing.
"""

import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(PROJECT_DIR, "data")            # game rules / definitions
ASSETS_DIR = os.path.join(PROJECT_DIR, "ASSETS")        # all graphics
TEXTURES_DIR = os.path.join(ASSETS_DIR, "textures")     # terrain hex images
MAPS_DIR = os.path.join(PROJECT_DIR, "maps")            # saved maps

TERRAINS_FILE = os.path.join(DATA_DIR, "terrains.json")

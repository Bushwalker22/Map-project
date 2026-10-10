"""
Loads the list of terrains from data/terrains.json.
"""

import json
from dataclasses import dataclass

from hexcore import paths


@dataclass
class Terrain:
    id: str              # internal name, e.g. "temperate_grassland"
    name: str            # shown to the player, e.g. "Temperate Grassland"
    color: tuple         # (r, g, b) used when no texture is available
    water: bool          # True for ocean, sea, lake...
    texture: str         # PNG file name inside ASSETS/textures


def load_terrains(path=paths.TERRAINS_FILE):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        Terrain(
            id=entry["id"],
            name=entry["name"],
            color=tuple(entry["color"]),
            water=entry.get("water", False),
            texture=entry.get("texture", entry["id"] + ".png"),
        )
        for entry in data["terrains"]
    ]

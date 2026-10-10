"""
Loads terrain textures from ASSETS/textures and keeps resized copies ready,
so each zoom level only has to resize an image once.
"""

import os

import pygame

from hexcore import paths


class TextureLibrary:
    MAX_CACHED = 600   # resized images kept in memory before starting over

    def __init__(self, terrains):
        self.originals = {}    # terrain id -> full-size image
        self.cache = {}        # (terrain id, width, height) -> resized image
        for terrain in terrains:
            path = os.path.join(paths.TEXTURES_DIR, terrain.texture)
            if not os.path.exists(path):
                print(f"No texture for '{terrain.id}' ({path}) - using its plain color.")
                continue
            try:
                self.originals[terrain.id] = pygame.image.load(path).convert_alpha()
            except pygame.error as error:
                print(f"Could not load {path}: {error}")

    def get(self, terrain_id, width, height):
        """The texture resized to width x height, or None if there is none."""
        original = self.originals.get(terrain_id)
        if original is None or width < 1 or height < 1:
            return None
        key = (terrain_id, width, height)
        image = self.cache.get(key)
        if image is None:
            if len(self.cache) >= self.MAX_CACHED:
                self.cache.clear()
            image = pygame.transform.smoothscale(original, (width, height))
            self.cache[key] = image
        return image

"""
Automatic checks for saving and loading maps.
"""

import json
import os
import tempfile
import unittest

from hexcore.mapdata import HexMap
from hexcore.mapfile import MapFileError, load_map, save_map


class TestMapFile(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "test map.json")

    def tearDown(self):
        self.folder.cleanup()

    def test_save_then_load_gives_the_same_map(self):
        original = HexMap(7, 5, "ocean")
        original.meta["name"] = "Test"
        original.set_terrain(0, 0, "tundra")
        original.set_terrain(6, 4, "desert_xeric")
        original.get(3, 2).elevation = 2
        original.get(3, 2).props = {"note": "hello"}
        save_map(original, self.path)

        loaded = load_map(self.path)
        self.assertEqual((loaded.cols, loaded.rows), (7, 5))
        self.assertEqual(loaded.meta["name"], "Test")
        for key, cell in original.cells.items():
            self.assertEqual(loaded.cells[key], cell, key)

    def test_rivers_survive_save_and_load(self):
        original = HexMap(6, 6, "temperate_grassland")
        original.set_edge_river(1, 1, 0, "stream")
        original.set_edge_river(2, 2, 4, "river")
        original.set_edge_river(3, 3, 1, "major_river")
        save_map(original, self.path)

        loaded = load_map(self.path)
        self.assertEqual(len(loaded.edges), 3)
        self.assertEqual(loaded.edges, original.edges)

    def test_old_version_1_file_still_loads(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('{"format": "hexmap", "version": 1, "meta": {"name": "Old"}, "cols": 2, "rows": 1,'
                    ' "terrain": [["ocean", "tundra"]], "cells": []}')
        loaded = load_map(self.path)
        self.assertEqual(loaded.get(1, 0).terrain, "tundra")
        self.assertEqual(loaded.edges, {})

    def test_saved_file_is_plain_json(self):
        save_map(HexMap(3, 2, "lake"), self.path)
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["terrain"], [["lake"] * 3, ["lake"] * 3])

    def test_unknown_terrain_is_kept(self):
        hex_map = HexMap(2, 2, "ocean")
        hex_map.set_terrain(1, 1, "something_new")
        save_map(hex_map, self.path)
        self.assertEqual(load_map(self.path).get(1, 1).terrain, "something_new")

    def test_broken_files_give_a_clear_error(self):
        for content in ["not json at all", '{"hello": 1}',
                        '{"format": "hexmap", "version": 1, "cols": 2, "rows": 2, "terrain": [["ocean"]]}']:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(content)
            with self.assertRaises(MapFileError):
                load_map(self.path)


if __name__ == "__main__":
    unittest.main()

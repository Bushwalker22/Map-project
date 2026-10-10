"""
Saving maps to files and loading them back.

A map file is plain JSON text (it opens in Notepad). It looks like this:

    {
      "format": "hexmap",
      "version": 1,
      "meta": {"name": "My Map"},
      "cols": 40,
      "rows": 30,
      "terrain": [
        ["ocean", "ocean", "tundra", ...],    <- row 0, one terrain id per column
        ["ocean", "tundra", "tundra", ...],   <- row 1
        ...
      ],
      "cells": []
    }

"cells" only lists hexes that have extra data (elevation, feature, props),
so files stay small until those are used.
"""

import json
import os

from hexcore.mapdata import HexMap

FORMAT_NAME = "hexmap"
FORMAT_VERSION = 1


class MapFileError(Exception):
    """The file isn't a map this program can read. The message explains why."""


def save_map(hex_map, path):
    # Written by hand (instead of one json.dump) so each map row is one line.
    lines = [
        "{",
        f'  "format": {json.dumps(FORMAT_NAME)},',
        f'  "version": {FORMAT_VERSION},',
        f'  "meta": {json.dumps(hex_map.meta)},',
        f'  "cols": {hex_map.cols},',
        f'  "rows": {hex_map.rows},',
        '  "terrain": [',
    ]
    for row in range(hex_map.rows):
        ids = [hex_map.get(col, row).terrain for col in range(hex_map.cols)]
        comma = "," if row < hex_map.rows - 1 else ""
        lines.append("    " + json.dumps(ids) + comma)
    lines.append("  ],")

    extras = []
    for (col, row), cell in sorted(hex_map.cells.items(), key=lambda item: (item[0][1], item[0][0])):
        if cell.elevation or cell.feature or cell.props:
            extras.append({"col": col, "row": row, "elevation": cell.elevation,
                           "feature": cell.feature, "props": cell.props})
    lines.append('  "cells": [')
    lines.append(",\n".join("    " + json.dumps(e) for e in extras))
    lines.append("  ]")
    lines.append("}")

    # Write to a temporary file first, then swap it in. If something goes
    # wrong halfway, the previous save is still intact.
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(temp_path, path)


def load_map(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise MapFileError(f"The file is damaged or isn't a map file.\n({e})")

    if not isinstance(data, dict) or data.get("format") != FORMAT_NAME:
        raise MapFileError("This file isn't a hex map.")
    if data.get("version", 0) > FORMAT_VERSION:
        raise MapFileError("This map was made by a newer version of the editor.")

    try:
        cols, rows = int(data["cols"]), int(data["rows"])
        terrain = data["terrain"]
        if len(terrain) != rows or any(len(line) != cols for line in terrain):
            raise MapFileError("The map's size doesn't match its terrain rows.")

        hex_map = HexMap(cols, rows, "ocean")
        hex_map.meta = dict(data.get("meta", {}))
        for row, line in enumerate(terrain):
            for col, terrain_id in enumerate(line):
                hex_map.get(col, row).terrain = str(terrain_id)
        for extra in data.get("cells", []):
            cell = hex_map.get(extra["col"], extra["row"])
            if cell is not None:
                cell.elevation = extra.get("elevation", 0)
                cell.feature = extra.get("feature")
                cell.props = extra.get("props", {})
    except (KeyError, TypeError, ValueError) as e:
        raise MapFileError(f"The map file is missing something or has a wrong value.\n({e})")
    return hex_map

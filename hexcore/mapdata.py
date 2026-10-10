"""
The map itself: a rectangle of hexes, each with its own data.

Hexes are stored by (col, row). Use hexmath.offset_to_axial when you need
neighbors or distances.
"""

from dataclasses import dataclass, field


@dataclass
class HexCell:
    terrain: str                 # terrain id, see data/terrains.json
    elevation: int = 0           # for hills/mountains later
    feature: str = None          # optional overlay later (e.g. "forest")
    props: dict = field(default_factory=dict)   # anything a future game needs


class HexMap:
    def __init__(self, cols, rows, terrain):
        self.cols = cols
        self.rows = rows
        self.meta = {"name": "Untitled"}
        self.cells = {
            (col, row): HexCell(terrain)
            for col in range(cols)
            for row in range(rows)
        }

    def in_bounds(self, col, row):
        return 0 <= col < self.cols and 0 <= row < self.rows

    def get(self, col, row):
        return self.cells.get((col, row))

    def set_terrain(self, col, row, terrain):
        """Change a hex's terrain. Returns True if something actually changed."""
        cell = self.cells.get((col, row))
        if cell is None or cell.terrain == terrain:
            return False
        cell.terrain = terrain
        return True

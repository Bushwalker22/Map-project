"""
The map itself: a rectangle of hexes, each with its own data.

Hexes are stored by (col, row). Use hexmath.offset_to_axial when you need
neighbors or distances.

Rivers run along the borders between hexes. They live in HexMap.edges,
keyed by rivers.edge_key(...) (see hexcore/rivers.py).
"""

from dataclasses import dataclass, field

from hexcore import rivers


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
        self.edges = {}     # edge key -> river type id (edge rivers only)

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

    # --- Rivers (along the border between two hexes) ---------------------------
    # Every change method returns True if something actually changed.

    def edge_in_bounds(self, key):
        a, b = rivers.edge_hexes(key)
        return self.in_bounds(*a) and self.in_bounds(*b)

    def get_edge_river(self, col, row, side):
        return self.edges.get(rivers.edge_key(col, row, side))

    def set_edge_river(self, col, row, side, river_type):
        key = rivers.edge_key(col, row, side)
        if not self.edge_in_bounds(key) or self.edges.get(key) == river_type:
            return False
        self.edges[key] = river_type
        return True

    def clear_edge_river(self, col, row, side):
        return self.edges.pop(rivers.edge_key(col, row, side), None) is not None

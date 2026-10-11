"""
River types (from data/rivers.json) and the geometry of hex edges.

All rivers (streams, rivers, major rivers) run along the border between two
hexes. Each type has a "kind" field, always "edge" for now, so a different
kind can be added later without changing the file format.

An edge is shared by two hexes: side 0 of one hex is side 3 of its neighbor.
So every edge gets ONE name, its "key": (col, row, side) with side 0, 1 or 2.
Sides 3, 4 and 5 are renamed to the neighbor's side 0, 1 or 2.
"""

import json
from dataclasses import dataclass

from hexcore import hexmath, paths


@dataclass
class RiverType:
    id: str          # internal name, e.g. "major_river"
    name: str        # shown in the editor
    kind: str        # "edge" or "hex"
    color: tuple     # (r, g, b)
    width: float     # map pixels at 100% zoom


def load_river_types(path=paths.RIVERS_FILE):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        RiverType(
            id=entry["id"],
            name=entry["name"],
            kind=entry["kind"],
            color=tuple(entry["color"]),
            width=entry.get("width", 4),
        )
        for entry in data["rivers"]
    ]


def opposite(side):
    return (side + 3) % 6


def neighbor_offset(col, row, side):
    """(col, row) of the hex across the given side."""
    q, r = hexmath.offset_to_axial(col, row)
    return hexmath.axial_to_offset(*hexmath.neighbor(q, r, side))


def edge_key(col, row, side):
    """The one shared name of this edge (see the top of this file)."""
    if side < 3:
        return (col, row, side)
    ncol, nrow = neighbor_offset(col, row, side)
    return (ncol, nrow, side - 3)


def edge_hexes(key):
    """The two (col, row) hexes on either side of an edge."""
    col, row, side = key
    return (col, row), neighbor_offset(col, row, side)


def side_corners(side):
    """Indexes (into hexmath.corner_offsets) of the two corners at the ends
    of a side. Side 0 (down-right) lies between corners 0 and 1, and each
    next side turns 60 degrees counter-clockwise."""
    return ((6 - side) % 6, (7 - side) % 6)


def side_midpoint(size, side):
    """Middle of a side, relative to the hex center."""
    corners = hexmath.corner_offsets(size)
    a, b = side_corners(side)
    return ((corners[a][0] + corners[b][0]) / 2, (corners[a][1] + corners[b][1]) / 2)


# --- Corners ("vertices") -----------------------------------------------------
# Edge rivers are drawn corner to corner: every edge joins two corners, and
# every corner touches three edges. Corners are named by their world position.

def corner_point(col, row, index, size):
    cx, cy = hexmath.hex_to_pixel(*hexmath.offset_to_axial(col, row), size)
    ox, oy = hexmath.corner_offsets(size)[index]
    return (round(cx + ox, 3), round(cy + oy, 3))


def nearest_corner(x, y, size):
    """The hex corner closest to world point (x, y), and how far away it is."""
    col, row = hexmath.axial_to_offset(*hexmath.pixel_to_hex(x, y, size))
    corners = [corner_point(col, row, i, size) for i in range(6)]
    best = min(corners, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
    return best, ((best[0] - x) ** 2 + (best[1] - y) ** 2) ** 0.5


def _same_point(a, b):
    return abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01


def edges_at_corner(point, size):
    """The 3 edges meeting at a corner, as (edge key, corner at the other end)."""
    hexes = set()
    for i in range(6):     # peek a little way around the corner in 6 directions
        ox, oy = hexmath.corner_offsets(size * 0.3)[i]
        q, r = hexmath.pixel_to_hex(point[0] + ox, point[1] + oy, size)
        hexes.add(hexmath.axial_to_offset(q, r))
    found = {}
    for col, row in hexes:
        for side in range(6):
            a, b = side_corners(side)
            pa, pb = corner_point(col, row, a, size), corner_point(col, row, b, size)
            if _same_point(pa, point):
                found[edge_key(col, row, side)] = pb
            elif _same_point(pb, point):
                found[edge_key(col, row, side)] = pa
    return list(found.items())


def edge_path(start, end, size, max_steps=60):
    """Edges leading from corner `start` toward corner `end`, always stepping to
    the next corner that is closest to `end`. Returns (edge keys, corner reached)."""
    def dist(p):
        return ((p[0] - end[0]) ** 2 + (p[1] - end[1]) ** 2) ** 0.5

    path, current = [], start
    for _ in range(max_steps):
        if _same_point(current, end):
            break
        key, nxt = min(edges_at_corner(current, size), key=lambda item: dist(item[1]))
        if dist(nxt) >= dist(current):
            break     # can't get closer (shouldn't happen on a hex grid)
        path.append(key)
        current = nxt
    return path, current


def side_toward(from_hex, to_hex):
    """The side of from_hex that touches to_hex, or None if not neighbors."""
    for side in range(6):
        if neighbor_offset(*from_hex, side) == tuple(to_hex):
            return side
    return None

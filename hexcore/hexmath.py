"""
Hex grid math for FLAT-TOP hexagons.

Two ways of naming a hex are used in this project:

1. OFFSET coordinates (col, row)
   Like a spreadsheet: column 0..width-1, row 0..height-1.
   Easy for humans and for rectangular maps. Odd columns sit half a hex lower
   ("odd-q" layout).

2. AXIAL coordinates (q, r)
   What the math uses. Neighbors, distances and lines are simple in axial,
   but messy in offset. We convert between them whenever needed.

Everything here is based on the excellent guide:
https://www.redblobgames.com/grids/hexagons/
"""

import math

SQRT3 = math.sqrt(3)

# The 6 neighbors of a hex, in axial (q, r) steps.
# For flat-top hexes with the screen's y axis pointing down:
DIRECTIONS = [
    (+1, 0),   # 0: down-right
    (+1, -1),  # 1: up-right
    (0, -1),   # 2: up
    (-1, 0),   # 3: up-left
    (-1, +1),  # 4: down-left
    (0, +1),   # 5: down
]


# --- Converting between offset (col, row) and axial (q, r) -----------------

def offset_to_axial(col, row):
    q = col
    r = row - (col - (col & 1)) // 2
    return (q, r)


def axial_to_offset(q, r):
    col = q
    row = r + (q - (q & 1)) // 2
    return (col, row)


# --- Neighbors and distance -------------------------------------------------

def neighbor(q, r, direction):
    dq, dr = DIRECTIONS[direction]
    return (q + dq, r + dr)


def neighbors(q, r):
    return [(q + dq, r + dr) for dq, dr in DIRECTIONS]


def distance(a, b):
    """Number of steps between two axial hexes."""
    dq = a[0] - b[0]
    dr = a[1] - b[1]
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


def line(a, b):
    """All axial hexes on a straight line from a to b (both included)."""
    steps = distance(a, b)
    if steps == 0:
        return [a]
    result = []
    for i in range(steps + 1):
        t = i / steps
        # The tiny nudge avoids landing exactly on a border between two hexes.
        q = a[0] + (b[0] - a[0]) * t + 1e-6
        r = a[1] + (b[1] - a[1]) * t + 2e-6
        result.append(hex_round(q, r))
    return result


# --- Converting between hexes and pixels ------------------------------------
# "size" is the distance from a hex's center to any of its corners.

def hex_to_pixel(q, r, size):
    """Center point of an axial hex, in world pixels. Hex (0,0) is at (0,0)."""
    x = size * 1.5 * q
    y = size * (SQRT3 / 2 * q + SQRT3 * r)
    return (x, y)


def pixel_to_hex(x, y, size):
    """Which axial hex contains this world pixel."""
    q = (2 / 3 * x) / size
    r = (-1 / 3 * x + SQRT3 / 3 * y) / size
    return hex_round(q, r)


def hex_round(q, r):
    """Round fractional axial coordinates to the nearest whole hex."""
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    # The three coordinates must add up to 0, so fix the one that rounded worst.
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    return (int(rq), int(rr))


def corner_offsets(size):
    """The 6 corner positions relative to a hex's center (flat-top)."""
    return [
        (size * math.cos(math.radians(60 * i)),
         size * math.sin(math.radians(60 * i)))
        for i in range(6)
    ]


# --- Sizes of a flat-top hex ------------------------------------------------

def hex_width(size):
    return 2 * size


def hex_height(size):
    return SQRT3 * size


def column_spacing(size):
    """Horizontal distance between neighboring columns."""
    return 1.5 * size

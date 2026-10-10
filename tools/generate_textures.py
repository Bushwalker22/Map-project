"""
Generates simple terrain textures as PNG files in ASSETS/textures.

Each texture is one flat-top hex (128 x 111 pixels, transparent outside the hex).

Existing PNGs are NOT overwritten, so your own edits are safe.
To regenerate everything anyway, run:
    python tools/generate_textures.py --overwrite

To tweak a texture: change its recipe in RECIPES below, delete its PNG, run again.
"""

import math
import os
import random
import sys

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

# Let this script find the project's own code when run from the tools folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hexcore import hexmath, paths
from hexcore.terrain import load_terrains

SIZE = 64                                   # hex center-to-corner, in pixels
WIDTH = round(hexmath.hex_width(SIZE))      # 128
HEIGHT = round(hexmath.hex_height(SIZE))    # 111


# --- Color helpers -----------------------------------------------------------

def shade(color, amount):
    """amount > 0 makes the color lighter, < 0 darker (range -1 .. 1)."""
    result = []
    for c in color[:3]:
        if amount >= 0:
            c = c + (255 - c) * amount
        else:
            c = c * (1 + amount)
        result.append(max(0, min(255, round(c))))
    return tuple(result)


# --- Hex shape helpers -------------------------------------------------------

INRADIUS = hexmath.hex_height(SIZE) / 2
# Directions pointing at the hex's edges (flat-top: 30, 90 and 150 degrees).
EDGE_NORMALS = [(math.cos(math.radians(a)), math.sin(math.radians(a)))
                for a in (30, 90, 150)]


def edge_closeness(x, y):
    """0 at the hex center, 1 on its border, above 1 outside the hex."""
    dx = x + 0.5 - WIDTH / 2
    dy = y + 0.5 - HEIGHT / 2
    return max(abs(dx * nx + dy * ny) for nx, ny in EDGE_NORMALS) / INRADIUS


# Worked out once, used by every texture.
CLOSENESS = [[edge_closeness(x, y) for y in range(HEIGHT)] for x in range(WIDTH)]


def random_spots(rng, count, gap, reach):
    """Up to 'count' random points inside the hex, at least 'gap' pixels apart.
    'reach' (0..1) is how close to the border points may go."""
    spots = []
    for _ in range(count * 40):
        if len(spots) >= count:
            break
        x = rng.uniform(0, WIDTH - 1)
        y = rng.uniform(0, HEIGHT - 1)
        if CLOSENESS[int(x)][int(y)] > reach:
            continue
        if all((x - sx) ** 2 + (y - sy) ** 2 >= gap * gap for sx, sy in spots):
            spots.append((x, y))
    return spots


# --- Ground --------------------------------------------------------------------

def noise_layer(rng, cells_x, cells_y):
    """Soft random blotches: a tiny random image stretched smoothly to full size."""
    small = pygame.Surface((cells_x, cells_y), 0, 32)
    for x in range(cells_x):
        for y in range(cells_y):
            v = rng.randint(0, 255)
            small.set_at((x, y), (v, v, v))
    return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))


def paint_ground(surf, rng, color, noise):
    big = noise_layer(rng, 4, 4)
    medium = noise_layer(rng, 11, 10)
    for x in range(WIDTH):
        for y in range(HEIGHT):
            amount = (big.get_at((x, y)).r - 128) / 128 * noise
            amount += (medium.get_at((x, y)).r - 128) / 128 * noise * 0.5
            amount += rng.uniform(-0.035, 0.035)         # fine grain
            edge = CLOSENESS[x][y]
            if edge > 0.82:                               # slightly darker rim
                amount -= (edge - 0.82) / 0.18 * 0.10
            surf.set_at((x, y), shade(color, amount))


def cut_to_hex(surf):
    """Make everything outside the hex shape transparent."""
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if CLOSENESS[x][y] > 1.0:
                surf.set_at((x, y), (0, 0, 0, 0))


# --- Details (each function draws ONE item at x, y) --------------------------

def draw_round_tree(surf, rng, x, y, color, size):
    r = rng.uniform(*size)
    pygame.draw.ellipse(surf, shade(color, -0.6), (x - r + 2, y + r * 0.2, r * 2, r * 1.1))
    pygame.draw.circle(surf, shade(color, -0.3), (x, y), r)
    pygame.draw.circle(surf, color, (x - 0.6, y - 0.6), r - 1)
    pygame.draw.circle(surf, shade(color, 0.2), (x - r * 0.35, y - r * 0.35), r * 0.4)


def draw_conifer(surf, rng, x, y, color, size):
    h = rng.uniform(*size)
    w = h * 0.38
    pygame.draw.ellipse(surf, shade(color, -0.55), (x - w * 0.5 + 2, y + h * 0.15, w * 1.6, h * 0.3))
    for base, top, width in ((y + h * 0.3, y - h * 0.35, w),            # lower tier
                             (y - h * 0.05, y - h * 0.75, w * 0.72)):   # upper tier
        pygame.draw.polygon(surf, shade(color, 0.12), [(x, top), (x - width, base), (x, base)])
        pygame.draw.polygon(surf, shade(color, -0.22), [(x, top), (x + width, base), (x, base)])


def draw_mangrove(surf, rng, x, y, color, size):
    r = rng.uniform(*size)
    root = shade(color, -0.45)
    for dx in (-r * 0.8, -r * 0.2, r * 0.4, r * 0.9):
        pygame.draw.line(surf, root, (x, y), (x + dx, y + r * 1.3))
    pygame.draw.circle(surf, shade(color, -0.3), (x, y - 1), r)
    pygame.draw.circle(surf, color, (x - 0.5, y - 1.5), r - 1)
    pygame.draw.circle(surf, shade(color, 0.18), (x - r * 0.3, y - r * 0.5), r * 0.35)


def draw_tuft(surf, rng, x, y, color, size):
    h = rng.uniform(*size)
    for dx in (-h * 0.5, 0, h * 0.5):
        pygame.draw.line(surf, color, (x, y), (x + dx, y - h))


def draw_shrub(surf, rng, x, y, color, size):
    r = rng.uniform(*size)
    pygame.draw.circle(surf, shade(color, -0.4), (x + 1, y + 1), r)
    pygame.draw.circle(surf, color, (x, y), r)


def draw_rock(surf, rng, x, y, color, size):
    s = rng.uniform(*size)
    points = [(x - s, y + s * 0.5), (x - s * 0.5, y - s * 0.6),
              (x + s * 0.6, y - s * 0.5), (x + s, y + s * 0.5)]
    pygame.draw.polygon(surf, color, points)
    pygame.draw.line(surf, shade(color, 0.35), points[1], points[2])
    pygame.draw.line(surf, shade(color, -0.45), points[0], points[3])


def draw_dune(surf, rng, x, y, color, size):
    w = rng.uniform(*size)
    rect = pygame.Rect(0, 0, w, w * 0.4)
    rect.center = (x, y)
    pygame.draw.arc(surf, shade(color, -0.12), rect.move(0, 2), 0.3, math.pi - 0.3, 2)
    pygame.draw.arc(surf, color, rect, 0.3, math.pi - 0.3, 2)


def draw_wave(surf, rng, x, y, color, size):
    w = rng.uniform(*size)
    rect = pygame.Rect(0, 0, w, w * 0.45)
    rect.center = (x, y)
    pygame.draw.arc(surf, color, rect, 0.4, math.pi - 0.4, 1)


def draw_pond(surf, rng, x, y, color, size):
    w = rng.uniform(*size)
    rect = pygame.Rect(0, 0, w, w * 0.5)
    rect.center = (x, y)
    pygame.draw.ellipse(surf, color, rect)
    pygame.draw.ellipse(surf, shade(color, 0.25), rect, 1)


# For each detail: how to draw it, default size, minimum spacing, how close to
# the border it may go, and whether it lies flat (flat things are drawn first).
DETAILS = {
    "round_tree": dict(draw=draw_round_tree, size=(5, 8),   gap=6,  reach=0.80, flat=False),
    "conifer":    dict(draw=draw_conifer,    size=(10, 15), gap=6,  reach=0.80, flat=False),
    "mangrove":   dict(draw=draw_mangrove,   size=(4, 6),   gap=7,  reach=0.78, flat=False),
    "tuft":       dict(draw=draw_tuft,       size=(3, 5),   gap=4,  reach=0.88, flat=False),
    "shrub":      dict(draw=draw_shrub,      size=(1.5, 3), gap=4,  reach=0.86, flat=False),
    "rock":       dict(draw=draw_rock,       size=(2, 4),   gap=6,  reach=0.84, flat=False),
    "dune":       dict(draw=draw_dune,       size=(16, 26), gap=12, reach=0.70, flat=True),
    "wave":       dict(draw=draw_wave,       size=(6, 11),  gap=9,  reach=0.80, flat=True),
    "pond":       dict(draw=draw_pond,       size=(10, 18), gap=16, reach=0.72, flat=True),
}


# --- Recipes: one per terrain id (see data/terrains.json) ---------------------
# "ground": base color, "noise": how blotchy the ground is,
# "details": list of (detail name, how many, color) or (..., size range).

RECIPES = {
    "desert_xeric": dict(ground=(212, 186, 126), noise=0.10, details=[
        ("dune", 7, (232, 210, 158)),
        ("shrub", 10, (122, 118, 70)),
        ("rock", 5, (166, 140, 104))]),
    "tropical_grassland": dict(ground=(186, 172, 88), noise=0.10, details=[
        ("tuft", 45, (150, 138, 58)),
        ("round_tree", 4, (98, 114, 50), (4, 6))]),
    "tropical_moist_forest": dict(ground=(38, 84, 36), noise=0.12, details=[
        ("round_tree", 34, (44, 120, 48), (6, 9))]),
    "boreal_taiga": dict(ground=(96, 108, 90), noise=0.08, details=[
        ("conifer", 26, (40, 76, 60), (10, 14)),
        ("rock", 3, (128, 130, 126))]),
    "temperate_broadleaf": dict(ground=(78, 112, 54), noise=0.10, details=[
        ("round_tree", 24, (76, 130, 54), (6, 8))]),
    "temperate_grassland": dict(ground=(128, 160, 78), noise=0.08, details=[
        ("tuft", 60, (102, 136, 58))]),
    "tundra": dict(ground=(148, 150, 128), noise=0.10, details=[
        ("shrub", 18, (118, 116, 92), (1.5, 2.5)),
        ("tuft", 16, (124, 128, 100)),
        ("rock", 9, (132, 132, 128))]),
    "montane_grassland": dict(ground=(122, 136, 96), noise=0.10, details=[
        ("tuft", 42, (98, 112, 74)),
        ("rock", 10, (140, 138, 132))]),
    "tropical_dry_forest": dict(ground=(164, 148, 90), noise=0.10, details=[
        ("tuft", 16, (140, 128, 72)),
        ("round_tree", 15, (112, 124, 58), (5, 7))]),
    "temperate_conifer": dict(ground=(84, 110, 70), noise=0.08, details=[
        ("conifer", 22, (36, 94, 62), (12, 16))]),
    "mediterranean": dict(ground=(178, 164, 112), noise=0.10, details=[
        ("shrub", 28, (96, 108, 58)),
        ("round_tree", 4, (88, 106, 56), (4, 6)),
        ("rock", 4, (190, 182, 160))]),
    "flooded_grassland": dict(ground=(110, 146, 92), noise=0.10, details=[
        ("pond", 7, (82, 132, 150)),
        ("tuft", 40, (84, 120, 70))]),
    "tropical_conifer": dict(ground=(96, 122, 62), noise=0.08, details=[
        ("tuft", 16, (80, 110, 52)),
        ("conifer", 16, (48, 110, 62), (11, 15))]),
    "mangroves": dict(ground=(64, 112, 106), noise=0.12, details=[
        ("wave", 5, (92, 140, 134)),
        ("mangrove", 16, (38, 88, 48))]),
    "ocean": dict(ground=(26, 58, 108), noise=0.16, details=[
        ("wave", 18, (46, 88, 142))]),
    "sea": dict(ground=(38, 92, 142), noise=0.14, details=[
        ("wave", 16, (68, 124, 172))]),
    "lake": dict(ground=(72, 134, 160), noise=0.08, details=[
        ("wave", 8, (104, 162, 186), (5, 8))]),
}


def make_texture(recipe, rng):
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    paint_ground(surf, rng, recipe["ground"], recipe.get("noise", 0.08))

    # Collect every item first, then draw flat ones first and the rest from
    # top to bottom, so things lower in the picture overlap things behind them.
    items = []
    for kind, count, color, *size in recipe.get("details", []):
        detail = DETAILS[kind]
        size = size[0] if size else detail["size"]
        for x, y in random_spots(rng, count, detail["gap"], detail["reach"]):
            items.append((0 if detail["flat"] else 1, y, x, detail["draw"], color, size))
    items.sort(key=lambda item: (item[0], item[1]))
    for _, y, x, draw, color, size in items:
        draw(surf, rng, x, y, color, size)

    cut_to_hex(surf)
    return surf


def main():
    overwrite = "--overwrite" in sys.argv
    os.makedirs(paths.TEXTURES_DIR, exist_ok=True)

    for terrain in load_terrains():
        out_path = os.path.join(paths.TEXTURES_DIR, terrain.texture)
        if os.path.exists(out_path) and not overwrite:
            print(f"  kept     {terrain.texture} (already exists)")
            continue
        # Terrains without a recipe get a plain textured ground in their color.
        recipe = RECIPES.get(terrain.id, dict(ground=terrain.color))
        rng = random.Random(terrain.id)   # same picture every time it's generated
        pygame.image.save(make_texture(recipe, rng), out_path)
        print(f"  created  {terrain.texture}")
    print("Done.")


if __name__ == "__main__":
    main()

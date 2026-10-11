"""
Draws rivers on the map. Plain shapes for now; the art style comes later.

All rivers run along the border between two hexes, drawn as a line from
one corner of the border to the other.
"""

import pygame

from hexcore import hexmath, rivers

MIN_WIDTH = 1


def _thick_line(surface, color, start, end, width):
    """A line with rounded ends, so joined pieces look like one river."""
    width = max(MIN_WIDTH, round(width))
    pygame.draw.line(surface, color, start, end, width)
    if width > 2:
        radius = width / 2
        pygame.draw.circle(surface, color, start, radius)
        pygame.draw.circle(surface, color, end, radius)


def draw_edge_river(surface, center, size, side, river_type, zoom):
    corners = hexmath.corner_offsets(size)
    a, b = rivers.side_corners(side)
    start = (center[0] + corners[a][0], center[1] + corners[a][1])
    end = (center[0] + corners[b][0], center[1] + corners[b][1])
    _thick_line(surface, river_type.color, start, end, river_type.width * zoom)

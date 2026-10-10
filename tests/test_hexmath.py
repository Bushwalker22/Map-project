"""
Automatic checks for the hex math.

Run all checks from the project folder with:   python -m unittest
"""

import unittest

from hexcore import hexmath

SIZE = 32


class TestHexMath(unittest.TestCase):

    def test_offset_axial_round_trip(self):
        for col in range(-5, 20):
            for row in range(-5, 20):
                q, r = hexmath.offset_to_axial(col, row)
                self.assertEqual(hexmath.axial_to_offset(q, r), (col, row))

    def test_pixel_round_trip(self):
        # The center of every hex must map back to that same hex.
        for q in range(-10, 10):
            for r in range(-10, 10):
                x, y = hexmath.hex_to_pixel(q, r, SIZE)
                self.assertEqual(hexmath.pixel_to_hex(x, y, SIZE), (q, r))

    def test_point_near_corner_stays_inside(self):
        # A point slightly inside each corner still belongs to the hex.
        x, y = hexmath.hex_to_pixel(3, -2, SIZE)
        for ox, oy in hexmath.corner_offsets(SIZE * 0.9):
            self.assertEqual(hexmath.pixel_to_hex(x + ox, y + oy, SIZE), (3, -2))

    def test_neighbors_are_distance_one(self):
        center = (2, 3)
        found = hexmath.neighbors(*center)
        self.assertEqual(len(set(found)), 6)
        for n in found:
            self.assertEqual(hexmath.distance(center, n), 1)

    def test_neighbor_centers_touch(self):
        # Neighboring hex centers are exactly one hex-height apart.
        cx, cy = hexmath.hex_to_pixel(0, 0, SIZE)
        for q, r in hexmath.neighbors(0, 0):
            nx, ny = hexmath.hex_to_pixel(q, r, SIZE)
            gap = ((nx - cx) ** 2 + (ny - cy) ** 2) ** 0.5
            self.assertAlmostEqual(gap, hexmath.hex_height(SIZE))

    def test_distance(self):
        self.assertEqual(hexmath.distance((0, 0), (0, 0)), 0)
        self.assertEqual(hexmath.distance((0, 0), (3, 0)), 3)
        self.assertEqual(hexmath.distance((0, 0), (2, -4)), 4)

    def test_line_has_no_gaps(self):
        start, end = (0, 0), (7, -3)
        hexes = hexmath.line(start, end)
        self.assertEqual(hexes[0], start)
        self.assertEqual(hexes[-1], end)
        for a, b in zip(hexes, hexes[1:]):
            self.assertEqual(hexmath.distance(a, b), 1)


if __name__ == "__main__":
    unittest.main()

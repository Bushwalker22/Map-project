"""
Automatic checks for river geometry and river editing.
"""

import unittest

from hexcore import hexmath, rivers
from hexcore.mapdata import HexMap

SIZE = 32


def corner_points(col, row, side):
    """World positions of the two corners at the ends of a side."""
    cx, cy = hexmath.hex_to_pixel(*hexmath.offset_to_axial(col, row), SIZE)
    corners = hexmath.corner_offsets(SIZE)
    return {(round(cx + corners[i][0], 6), round(cy + corners[i][1], 6))
            for i in rivers.side_corners(side)}


class TestEdges(unittest.TestCase):
    def test_same_edge_from_both_sides_has_one_key(self):
        for col, row in [(3, 3), (4, 3), (0, 0), (5, 8)]:
            for side in range(6):
                other = rivers.neighbor_offset(col, row, side)
                self.assertEqual(rivers.edge_key(col, row, side),
                                 rivers.edge_key(*other, rivers.opposite(side)))

    def test_side_corners_are_shared_by_both_hexes(self):
        # The two corners of a side must be the same points as seen from the neighbor.
        for col, row in [(3, 3), (4, 3)]:
            for side in range(6):
                other = rivers.neighbor_offset(col, row, side)
                self.assertEqual(corner_points(col, row, side),
                                 corner_points(*other, rivers.opposite(side)))

    def test_side_toward(self):
        for side in range(6):
            self.assertEqual(rivers.side_toward((4, 4), rivers.neighbor_offset(4, 4, side)), side)
        self.assertIsNone(rivers.side_toward((4, 4), (9, 9)))

    def test_every_corner_has_three_edges(self):
        for i in range(6):
            corner = rivers.corner_point(4, 4, i, SIZE)
            self.assertEqual(len(rivers.edges_at_corner(corner, SIZE)), 3)

    def test_edge_path_is_unbroken(self):
        start = rivers.corner_point(2, 2, 0, SIZE)
        end = rivers.corner_point(9, 6, 3, SIZE)
        path, reached = rivers.edge_path(start, end, SIZE)
        self.assertEqual(reached, end)
        # Walk the path: each edge must start where the previous one ended.
        current = start
        for key in path:
            ends = dict(rivers.edges_at_corner(current, SIZE))
            self.assertIn(key, ends)
            current = ends[key]
        self.assertEqual(current, end)

    def test_edge_rivers_on_map(self):
        m = HexMap(5, 5, "ocean")
        self.assertTrue(m.set_edge_river(2, 2, 4, "stream"))
        other = rivers.neighbor_offset(2, 2, 4)
        self.assertEqual(m.get_edge_river(*other, 1), "stream")     # seen from the neighbor
        self.assertFalse(m.set_edge_river(2, 2, 4, "stream"))        # nothing changed
        self.assertFalse(m.set_edge_river(0, 0, 3, "stream"))        # off the map edge
        self.assertTrue(m.clear_edge_river(*other, 1))
        self.assertEqual(m.edges, {})


class TestRiverTypes(unittest.TestCase):
    def test_river_types_load(self):
        types = {r.id: r for r in rivers.load_river_types()}
        self.assertEqual(types["stream"].kind, "edge")
        self.assertEqual(types["major_river"].kind, "edge")
        # Each river size is wider than the one before.
        self.assertLess(types["stream"].width, types["river"].width)
        self.assertLess(types["river"].width, types["major_river"].width)


if __name__ == "__main__":
    unittest.main()

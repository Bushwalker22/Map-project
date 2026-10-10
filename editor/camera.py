"""
The camera decides which part of the map is visible and how zoomed in it is.

"World" coordinates are positions on the map itself (they never change).
"Screen" coordinates are pixels in the window (they change when you pan/zoom).
"""


class Camera:
    MIN_ZOOM = 0.15
    MAX_ZOOM = 4.0

    def __init__(self):
        # World position shown at the window's top-left corner.
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0

    def world_to_screen(self, wx, wy):
        return ((wx - self.x) * self.zoom, (wy - self.y) * self.zoom)

    def screen_to_world(self, sx, sy):
        return (sx / self.zoom + self.x, sy / self.zoom + self.y)

    def pan(self, dx, dy):
        """Move the view by a number of SCREEN pixels (e.g. a mouse drag)."""
        self.x -= dx / self.zoom
        self.y -= dy / self.zoom

    def zoom_at(self, sx, sy, factor):
        """Zoom in/out while keeping the point under the mouse in place."""
        wx, wy = self.screen_to_world(sx, sy)
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom * factor))
        self.x = wx - sx / self.zoom
        self.y = wy - sy / self.zoom

    def fit(self, left, top, right, bottom, view_w, view_h, margin=40):
        """Zoom and move so the given world rectangle fills the view."""
        width = max(1, right - left)
        height = max(1, bottom - top)
        zoom_x = (view_w - 2 * margin) / width
        zoom_y = (view_h - 2 * margin) / height
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, min(zoom_x, zoom_y)))
        center_x = (left + right) / 2
        center_y = (top + bottom) / 2
        self.x = center_x - view_w / 2 / self.zoom
        self.y = center_y - view_h / 2 / self.zoom

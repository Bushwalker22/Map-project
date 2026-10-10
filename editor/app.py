"""
The main editor window: opens the window, reacts to mouse and keyboard,
and draws the map every frame.
"""

import math

import pygame

from hexcore import hexmath
from hexcore.mapdata import HexMap
from hexcore.terrain import load_terrains
from editor.camera import Camera
from editor.textures import TextureLibrary
from editor.ui.palette import PANEL_WIDTH, TerrainPalette

# --- Settings you can tweak --------------------------------------------------
WINDOW_SIZE = (1400, 860)
MAP_COLS = 40
MAP_ROWS = 30
START_TERRAIN = "ocean"    # what a new map is filled with
HEX_SIZE = 32              # center-to-corner distance of a hex, in world pixels
STATUS_BAR_HEIGHT = 28
KEY_PAN_SPEED = 700        # screen pixels per second when moving with WASD/arrows
ZOOM_STEP = 1.15           # how much one mouse-wheel click zooms
MIN_TEXTURE_SIZE = 8       # below this hex size (on screen) only plain colors are drawn
MIN_GRID_SIZE = 10         # below this hex size grid lines are hidden

# Colors as (red, green, blue), each 0-255
BACKGROUND = (24, 26, 30)
GRID_COLOR = (34, 38, 36)
MISSING_TERRAIN = (255, 0, 255)   # bright pink = terrain id not in terrains.json
HOVER_OUTLINE = (255, 220, 90)
STATUS_BG = (36, 38, 44)
STATUS_TEXT = (210, 212, 218)
STATUS_HINT = (130, 134, 145)


class EditorApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Hex Map Editor")
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 16)
        self.title_font = pygame.font.SysFont("segoeui", 22, bold=True)
        self.header_font = pygame.font.SysFont("segoeui", 13, bold=True)

        self.terrains = load_terrains()
        self.terrain_by_id = {t.id: t for t in self.terrains}
        self.textures = TextureLibrary(self.terrains)
        self.palette = TerrainPalette(self.terrains, self.textures,
                                      self.font, self.title_font, self.header_font)
        self.map = HexMap(MAP_COLS, MAP_ROWS, START_TERRAIN)

        self.camera = Camera()
        self.running = True
        self.dragging = False      # moving the view with the right/middle button
        self.painting = False      # left button held down on the map
        self.last_painted = None   # last hex painted in this stroke
        self.hovered = None        # (col, row) of the hex under the mouse, or None
        self.show_grid = True
        self.fit_map_to_view()

    # --- Helpers ---------------------------------------------------------------

    def view_rect(self):
        """The part of the window that shows the map."""
        width, height = self.screen.get_size()
        return pygame.Rect(PANEL_WIDTH, 0,
                           max(1, width - PANEL_WIDTH),
                           max(1, height - STATUS_BAR_HEIGHT))

    def hex_center(self, col, row):
        q, r = hexmath.offset_to_axial(col, row)
        return hexmath.hex_to_pixel(q, r, HEX_SIZE)

    def map_world_bounds(self):
        """Left, top, right, bottom edges of the whole map in world pixels."""
        spacing = hexmath.column_spacing(HEX_SIZE)
        hex_h = hexmath.hex_height(HEX_SIZE)
        left = -HEX_SIZE
        top = -hex_h / 2
        right = spacing * (self.map.cols - 1) + HEX_SIZE
        bottom = hex_h * self.map.rows
        return left, top, right, bottom

    def fit_map_to_view(self):
        view = self.view_rect()
        self.camera.fit(*self.map_world_bounds(), view.width, view.height)

    def hex_at_screen(self, sx, sy):
        """The (col, row) under a window point, or None if it's not on the map."""
        view = self.view_rect()
        if not view.collidepoint(sx, sy):
            return None
        wx, wy = self.camera.screen_to_world(sx - view.x, sy - view.y)
        q, r = hexmath.pixel_to_hex(wx, wy, HEX_SIZE)
        col, row = hexmath.axial_to_offset(q, r)
        if self.map.in_bounds(col, row):
            return (col, row)
        return None

    # --- Main loop -------------------------------------------------------------

    def run(self, screenshot_path=None):
        while self.running:
            dt = self.clock.tick(60) / 1000   # seconds since the last frame
            self.handle_events()
            self.handle_held_keys(dt)
            self.hovered = self.hex_at_screen(*pygame.mouse.get_pos())
            self.draw()
            pygame.display.flip()
            if screenshot_path:
                # Used for automatic checks: save one frame as an image and quit.
                pygame.image.save(self.screen, screenshot_path)
                self.running = False
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[0] < PANEL_WIDTH:
                    self.palette.handle_click(*event.pos)
                elif self.view_rect().collidepoint(event.pos):
                    self.painting = True
                    self.last_painted = None
                    self.paint_at(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.painting = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (2, 3):
                self.dragging = True        # middle or right button: start panning
            elif event.type == pygame.MOUSEBUTTONUP and event.button in (2, 3):
                self.dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.camera.pan(*event.rel)
                if self.painting:
                    self.paint_at(event.pos)

            elif event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_x < PANEL_WIDTH:
                    self.palette.handle_wheel(event.y, self.view_rect().height)
                else:
                    view = self.view_rect()
                    self.camera.zoom_at(mouse_x - view.x, mouse_y - view.y, ZOOM_STEP ** event.y)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_HOME:
                    self.fit_map_to_view()
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

    def handle_held_keys(self, dt):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx += 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx -= 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy += 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy -= 1
        if dx or dy:
            self.camera.pan(dx * KEY_PAN_SPEED * dt, dy * KEY_PAN_SPEED * dt)

    # --- Painting --------------------------------------------------------------

    def paint_at(self, pos):
        target = self.hex_at_screen(*pos)
        if target is None:
            self.last_painted = None
            return
        if self.last_painted is None:
            hexes = [target]
        else:
            # Fill in every hex between the last one and this one, so fast
            # mouse movements don't leave gaps.
            start = hexmath.offset_to_axial(*self.last_painted)
            end = hexmath.offset_to_axial(*target)
            hexes = [hexmath.axial_to_offset(q, r) for q, r in hexmath.line(start, end)]
        for col, row in hexes:
            self.map.set_terrain(col, row, self.palette.selected.id)
        self.last_painted = target

    # --- Drawing ---------------------------------------------------------------

    def draw(self):
        self.screen.fill(BACKGROUND)
        view = self.screen.subsurface(self.view_rect())
        self.draw_map(view)
        self.palette.draw(self.screen, self.view_rect().height, pygame.mouse.get_pos())
        self.draw_status_bar()

    def visible_range(self, view_w, view_h):
        """First/last column and row that can be seen. Only those get drawn,
        which keeps big maps fast."""
        wx0, wy0 = self.camera.screen_to_world(0, 0)
        wx1, wy1 = self.camera.screen_to_world(view_w, view_h)
        spacing = hexmath.column_spacing(HEX_SIZE)
        hex_h = hexmath.hex_height(HEX_SIZE)
        col_first = max(0, math.floor((wx0 - HEX_SIZE) / spacing))
        col_last = min(self.map.cols - 1, math.ceil((wx1 + HEX_SIZE) / spacing))
        row_first = max(0, math.floor(wy0 / hex_h) - 1)
        row_last = min(self.map.rows - 1, math.ceil(wy1 / hex_h) + 1)
        return col_first, col_last, row_first, row_last

    def draw_map(self, view):
        size_on_screen = HEX_SIZE * self.camera.zoom
        corners = hexmath.corner_offsets(size_on_screen)
        tex_w = round(hexmath.hex_width(size_on_screen))
        tex_h = round(hexmath.hex_height(size_on_screen))
        use_textures = size_on_screen >= MIN_TEXTURE_SIZE
        draw_grid = self.show_grid and size_on_screen >= MIN_GRID_SIZE

        col_first, col_last, row_first, row_last = self.visible_range(*view.get_size())
        for col in range(col_first, col_last + 1):
            for row in range(row_first, row_last + 1):
                cell = self.map.get(col, row)
                terrain = self.terrain_by_id.get(cell.terrain)
                cx, cy = self.camera.world_to_screen(*self.hex_center(col, row))
                points = [(cx + ox, cy + oy) for ox, oy in corners]

                # Plain color first (also fills any hairline gaps between textures).
                pygame.draw.polygon(view, terrain.color if terrain else MISSING_TERRAIN, points)
                if use_textures:
                    image = self.textures.get(cell.terrain, tex_w, tex_h)
                    if image:
                        view.blit(image, (round(cx - tex_w / 2), round(cy - tex_h / 2)))
                if draw_grid:
                    pygame.draw.aalines(view, GRID_COLOR, True, points)

        if self.hovered:
            cx, cy = self.camera.world_to_screen(*self.hex_center(*self.hovered))
            points = [(cx + ox, cy + oy) for ox, oy in corners]
            pygame.draw.lines(view, HOVER_OUTLINE, True, points, 3)

    def draw_status_bar(self):
        width, height = self.screen.get_size()
        bar = pygame.Rect(0, height - STATUS_BAR_HEIGHT, width, STATUS_BAR_HEIGHT)
        pygame.draw.rect(self.screen, STATUS_BG, bar)

        if self.hovered:
            col, row = self.hovered
            terrain_id = self.map.get(col, row).terrain
            terrain = self.terrain_by_id.get(terrain_id)
            info = f"Hex {col}, {row}: {terrain.name if terrain else terrain_id}"
        else:
            info = "Hex: -"
        info += (f"     Brush: {self.palette.selected.name}"
                 f"     Zoom: {self.camera.zoom * 100:.0f}%"
                 f"     Map: {self.map.cols} x {self.map.rows}"
                 f"     FPS: {self.clock.get_fps():.0f}")
        text = self.font.render(info, True, STATUS_TEXT)
        self.screen.blit(text, (10, bar.centery - text.get_height() // 2))

        hint = self.font.render(
            "Left: paint    Right-drag / WASD: move    Wheel: zoom    G: grid    Home: whole map",
            True, STATUS_HINT)
        hint_x = width - hint.get_width() - 10
        if hint_x > 10 + text.get_width() + 30:   # only if there's room
            self.screen.blit(hint, (hint_x, bar.centery - hint.get_height() // 2))

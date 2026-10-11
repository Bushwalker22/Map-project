"""
The main editor window: opens the window, reacts to mouse and keyboard,
and draws the map every frame.
"""

import math
import os

import pygame

from hexcore import hexmath, paths, rivers
from hexcore.mapdata import HexMap
from hexcore.mapfile import MapFileError, load_map, save_map
from hexcore.rivers import RiverType, load_river_types
from hexcore.terrain import Terrain, load_terrains
from editor import dialogs, rivers_draw
from editor.camera import Camera
from editor.textures import TextureLibrary
from editor.ui.palette import PANEL_WIDTH, TerrainPalette
from editor.ui.toolbar import TOOLBAR_HEIGHT, Toolbar

# --- Settings you can tweak --------------------------------------------------
WINDOW_SIZE = (1400, 860)
MAP_COLS = 40              # size of the map you get when the editor starts
MAP_ROWS = 30
START_TERRAIN = "ocean"    # what a new map is filled with
HEX_SIZE = 32              # center-to-corner distance of a hex, in world pixels
STATUS_BAR_HEIGHT = 28
KEY_PAN_SPEED = 700        # screen pixels per second when moving with WASD/arrows
ZOOM_STEP = 1.15           # how much one mouse-wheel click zooms
MIN_TEXTURE_SIZE = 8       # below this hex size (on screen) only plain colors are drawn
MIN_GRID_SIZE = 10         # below this hex size grid lines are hidden
MAX_BRUSH_SIZE = 10        # size 1 = one hex, 2 = 7 hexes, 3 = 19 hexes...

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
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 16)
        self.title_font = pygame.font.SysFont("segoeui", 22, bold=True)
        self.header_font = pygame.font.SysFont("segoeui", 13, bold=True)

        self.terrains = load_terrains()
        self.terrain_by_id = {t.id: t for t in self.terrains}
        self.river_types = load_river_types()
        self.river_by_id = {r.id: r for r in self.river_types}
        self.textures = TextureLibrary(self.terrains)
        self.palette = TerrainPalette(self.terrains, self.river_types, self.textures,
                                      self.font, self.title_font, self.header_font)
        self.toolbar = Toolbar(self.font)

        self.camera = Camera()
        self.running = True
        self.dragging = False      # moving the view with the right/middle button
        self.painting = False      # left button held down on the map
        self.last_painted = None   # last hex painted in this stroke
        self.last_corner = None    # last hex corner reached while drawing an edge river
        self.hovered = None        # (col, row) of the hex under the mouse, or None
        self.show_grid = True
        self.brush_size = 1

        self.set_map(HexMap(MAP_COLS, MAP_ROWS, START_TERRAIN), path=None)

    # --- Helpers ---------------------------------------------------------------

    def view_rect(self):
        """The part of the window that shows the map."""
        width, height = self.screen.get_size()
        return pygame.Rect(PANEL_WIDTH, TOOLBAR_HEIGHT,
                           max(1, width - PANEL_WIDTH),
                           max(1, height - TOOLBAR_HEIGHT - STATUS_BAR_HEIGHT))

    def toolbar_rect(self):
        width = self.screen.get_width()
        return pygame.Rect(PANEL_WIDTH, 0, max(1, width - PANEL_WIDTH), TOOLBAR_HEIGHT)

    def palette_height(self):
        return max(1, self.screen.get_height() - STATUS_BAR_HEIGHT)

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

    def edge_at_screen(self, sx, sy):
        """(col, row, side) of the hex edge closest to a window point, or None."""
        target = self.hex_at_screen(sx, sy)
        if target is None:
            return None
        view = self.view_rect()
        wx, wy = self.camera.screen_to_world(sx - view.x, sy - view.y)
        cx, cy = self.hex_center(*target)

        def distance_to_side(side):
            mx, my = rivers.side_midpoint(HEX_SIZE, side)
            return (cx + mx - wx) ** 2 + (cy + my - wy) ** 2

        side = min(range(6), key=distance_to_side)
        if not self.map.edge_in_bounds(rivers.edge_key(*target, side)):
            return None    # the outer border of the map has no neighbor
        return (*target, side)

    def tool_kind(self):
        """What the selected palette entry does: "terrain", "river" or "erase_rivers"."""
        tool = self.palette.selected
        if isinstance(tool, Terrain):
            return "terrain"
        if isinstance(tool, RiverType):
            return "river"
        return tool.id

    def brush_hexes(self, col, row):
        """Every (col, row) the brush covers when centered on this hex."""
        center = hexmath.offset_to_axial(col, row)
        result = []
        for q, r in hexmath.hexes_in_range(center, self.brush_size - 1):
            c, rw = hexmath.axial_to_offset(q, r)
            if self.map.in_bounds(c, rw):
                result.append((c, rw))
        return result

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
                if self.ok_to_discard_changes():
                    self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[0] < PANEL_WIDTH:
                    self.palette.handle_click(*event.pos)
                elif self.toolbar_rect().collidepoint(event.pos):
                    self.do_action(self.toolbar.handle_click(event.pos))
                elif self.view_rect().collidepoint(event.pos):
                    self.painting = True
                    self.last_painted = None
                    self.last_corner = None
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
                    self.palette.handle_wheel(event.y, self.palette_height())
                else:
                    view = self.view_rect()
                    self.camera.zoom_at(mouse_x - view.x, mouse_y - view.y, ZOOM_STEP ** event.y)

            elif event.type == pygame.KEYDOWN:
                self.handle_key(event)

    def handle_key(self, event):
        ctrl = event.mod & pygame.KMOD_CTRL
        shift = event.mod & pygame.KMOD_SHIFT
        if ctrl and event.key == pygame.K_s:
            self.do_action("save_as" if shift else "save")
        elif ctrl and event.key == pygame.K_o:
            self.do_action("open")
        elif ctrl and event.key == pygame.K_n:
            self.do_action("new")
        elif event.key == pygame.K_LEFTBRACKET:
            self.do_action("brush_smaller")
        elif event.key == pygame.K_RIGHTBRACKET:
            self.do_action("brush_bigger")
        elif event.key == pygame.K_HOME:
            self.fit_map_to_view()
        elif event.key == pygame.K_g and not ctrl:
            self.show_grid = not self.show_grid

    def handle_held_keys(self, dt):
        keys = pygame.key.get_pressed()
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            return    # Ctrl+S is "save", not "move down"
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

    def do_action(self, action):
        """Runs a toolbar button or keyboard shortcut."""
        if action == "new":
            self.new_map()
        elif action == "open":
            self.open_map()
        elif action == "save":
            self.save(ask_for_name=False)
        elif action == "save_as":
            self.save(ask_for_name=True)
        elif action == "brush_smaller":
            self.brush_size = max(1, self.brush_size - 1)
        elif action == "brush_bigger":
            self.brush_size = min(MAX_BRUSH_SIZE, self.brush_size + 1)

    # --- Painting --------------------------------------------------------------

    def paint_at(self, pos):
        """Called on mouse press and while dragging with the left button."""
        target = self.hex_at_screen(*pos)
        if target is None:
            self.last_painted = None
            return
        kind = self.tool_kind()
        stroke_start = self.last_painted is None
        changed = False

        if kind == "terrain":
            for center in self.stroke_hexes(target):
                for col, row in self.brush_hexes(*center):
                    changed |= self.map.set_terrain(col, row, self.palette.selected.id)

        elif kind == "river":
            changed = self.paint_edge_river(pos, stroke_start)

        elif kind == "erase_rivers":
            edge = self.edge_at_screen(*pos)
            if edge:
                changed = self.map.clear_edge_river(*edge)

        if changed:
            self.mark_changed()
        self.last_painted = target

    def paint_edge_river(self, pos, stroke_start):
        """Edge rivers go corner to corner. A click paints the nearest edge;
        dragging then follows the hex borders to whichever corner the mouse
        comes close to, painting every edge on the way."""
        river_id = self.palette.selected.id
        view = self.view_rect()
        wx, wy = self.camera.screen_to_world(pos[0] - view.x, pos[1] - view.y)
        changed = False

        if stroke_start or self.last_corner is None:
            edge = self.edge_at_screen(*pos)
            if edge:
                changed = self.map.set_edge_river(*edge, river_id)
                col, row, side = edge
                ends = [rivers.corner_point(col, row, i, HEX_SIZE) for i in rivers.side_corners(side)]
                self.last_corner = min(ends, key=lambda p: (p[0] - wx) ** 2 + (p[1] - wy) ** 2)
            return changed

        corner, distance = rivers.nearest_corner(wx, wy, HEX_SIZE)
        if distance < HEX_SIZE * 0.4 and corner != self.last_corner:
            path, reached = rivers.edge_path(self.last_corner, corner, HEX_SIZE)
            for key in path:
                changed |= self.map.set_edge_river(*key, river_id)
            self.last_corner = reached
        return changed

    def stroke_hexes(self, target):
        """The hexes from the last painted one up to target (both included),
        so fast mouse movements don't leave gaps."""
        if self.last_painted is None:
            return [target]
        start = hexmath.offset_to_axial(*self.last_painted)
        end = hexmath.offset_to_axial(*target)
        return [hexmath.axial_to_offset(q, r) for q, r in hexmath.line(start, end)]

    # --- New, open and save ----------------------------------------------------

    def set_map(self, hex_map, path):
        self.map = hex_map
        self.map_path = path          # file it was loaded from / saved to, or None
        self.unsaved = False
        self.fit_map_to_view()
        self.update_title()

    def mark_changed(self):
        if not self.unsaved:
            self.unsaved = True
            self.update_title()

    def update_title(self):
        star = "*" if self.unsaved else ""
        pygame.display.set_caption(f"{self.map.meta.get('name', 'Untitled')}{star} - Hex Map Editor")

    def after_dialog(self):
        """A pop-up window took the mouse and keyboard away. Forget any button
        that was held down, so painting or moving doesn't get stuck on."""
        self.painting = False
        self.dragging = False
        self.last_painted = None
        pygame.event.clear()
        pygame.key.set_mods(0)

    def ok_to_discard_changes(self):
        """If there are unsaved changes, ask what to do.
        Returns True if it's fine to throw the current map away."""
        if not self.unsaved:
            return True
        answer = dialogs.ask_save_changes(self.map.meta.get("name", "Untitled"))
        self.after_dialog()
        if answer is None:       # Cancel
            return False
        if answer:               # Yes, save first
            return self.save(ask_for_name=False)
        return True              # No, throw the changes away

    def new_map(self):
        if not self.ok_to_discard_changes():
            return
        size = dialogs.ask_new_map_size(self.map.cols, self.map.rows)
        self.after_dialog()
        if size:
            self.set_map(HexMap(size[0], size[1], START_TERRAIN), path=None)

    def open_map(self):
        if not self.ok_to_discard_changes():
            return
        path = dialogs.ask_open_path(paths.MAPS_DIR)
        self.after_dialog()
        if not path:
            return
        try:
            hex_map = load_map(path)
        except (MapFileError, OSError) as e:
            dialogs.show_error("Couldn't open map", str(e))
            self.after_dialog()
            return
        hex_map.meta["name"] = dialogs.file_stem(path)
        self.set_map(hex_map, path)

    def save(self, ask_for_name):
        """Saves the map. Returns True if it was saved."""
        path = self.map_path
        if ask_for_name or path is None:
            os.makedirs(paths.MAPS_DIR, exist_ok=True)
            path = dialogs.ask_save_path(paths.MAPS_DIR, self.map.meta.get("name", "Untitled"))
            self.after_dialog()
            if not path:
                return False
        self.map.meta["name"] = dialogs.file_stem(path)
        try:
            save_map(self.map, path)
        except OSError as e:
            dialogs.show_error("Couldn't save map", str(e))
            self.after_dialog()
            return False
        self.map_path = path
        self.unsaved = False
        self.update_title()
        return True

    # --- Drawing ---------------------------------------------------------------

    def draw(self):
        self.screen.fill(BACKGROUND)
        view = self.screen.subsurface(self.view_rect())
        self.draw_map(view)
        mouse = pygame.mouse.get_pos()
        self.toolbar.draw(self.screen, self.toolbar_rect(), mouse, self.brush_size)
        self.palette.draw(self.screen, self.palette_height(), mouse)
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

        # Rivers go on top of all terrain (a channel may reach into the next hex).
        self.draw_rivers(view, size_on_screen, col_first, col_last, row_first, row_last)
        self.draw_hover(view, size_on_screen, corners)

    def draw_rivers(self, view, size_on_screen, col_first, col_last, row_first, row_last):
        zoom = self.camera.zoom

        def visible(col, row):
            return col_first <= col <= col_last and row_first <= row <= row_last

        for (col, row, side), type_id in self.map.edges.items():
            river_type = self.river_by_id.get(type_id)
            other = rivers.neighbor_offset(col, row, side)
            if river_type and (visible(col, row) or visible(*other)):
                center = self.camera.world_to_screen(*self.hex_center(col, row))
                rivers_draw.draw_edge_river(view, center, size_on_screen, side, river_type, zoom)

    def draw_hover(self, view, size_on_screen, corners):
        """Yellow outline showing what a click would change."""
        if not self.hovered:
            return
        if self.tool_kind() != "terrain":
            # River tools work on borders: highlight the nearest one.
            edge = self.edge_at_screen(*pygame.mouse.get_pos())
            if edge:
                col, row, side = edge
                a, b = rivers.side_corners(side)
                cx, cy = self.camera.world_to_screen(*self.hex_center(col, row))
                pygame.draw.line(view, HOVER_OUTLINE, (cx + corners[a][0], cy + corners[a][1]),
                                 (cx + corners[b][0], cy + corners[b][1]), 5)
            return
        hexes = self.brush_hexes(*self.hovered)
        thickness = 3 if len(hexes) == 1 else 2
        for col, row in hexes:
            cx, cy = self.camera.world_to_screen(*self.hex_center(col, row))
            points = [(cx + ox, cy + oy) for ox, oy in corners]
            pygame.draw.lines(view, HOVER_OUTLINE, True, points, thickness)

    def draw_status_bar(self):
        width, height = self.screen.get_size()
        bar = pygame.Rect(0, height - STATUS_BAR_HEIGHT, width, STATUS_BAR_HEIGHT)
        pygame.draw.rect(self.screen, STATUS_BG, bar)

        if self.hovered:
            col, row = self.hovered
            terrain_id = self.map.get(col, row).terrain
            terrain = self.terrain_by_id.get(terrain_id)
            info = f"Hex {col}, {row}: {terrain.name if terrain else terrain_id}"
            edge = self.edge_at_screen(*pygame.mouse.get_pos())
            type_id = edge and self.map.get_edge_river(*edge)
            if type_id:
                river_type = self.river_by_id.get(type_id)
                info += f"  (nearest border: {river_type.name if river_type else type_id})"
        else:
            info = "Hex: -"
        size_note = f" (size {self.brush_size})" if self.tool_kind() == "terrain" else ""
        info += (f"     Tool: {self.palette.selected.name}{size_note}"
                 f"     Zoom: {self.camera.zoom * 100:.0f}%"
                 f"     Map: {self.map.cols} x {self.map.rows}"
                 f"     FPS: {self.clock.get_fps():.0f}")
        text = self.font.render(info, True, STATUS_TEXT)
        self.screen.blit(text, (10, bar.centery - text.get_height() // 2))

        hint = self.font.render(
            "Right-drag / WASD: move    [ ]: brush size    G: grid    Home: whole map    Ctrl+S: save",
            True, STATUS_HINT)
        hint_x = width - hint.get_width() - 10
        if hint_x > 10 + text.get_width() + 30:   # only if there's room
            self.screen.blit(hint, (hint_x, bar.centery - hint.get_height() // 2))

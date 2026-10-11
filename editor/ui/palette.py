"""
The palette: the panel on the left where you pick what to paint.

The selected entry (palette.selected) is one of:
- a Terrain           (paint terrain)
- a RiverType         (draw rivers, see hexcore/rivers.py)
- a Tool              (special actions: erase rivers)
"""

from dataclasses import dataclass

import pygame

from hexcore import hexmath

PANEL_WIDTH = 260
TITLE_HEIGHT = 48
ROW_HEIGHT = 40
SWATCH_SIZE = 17          # hex size (center to corner) of the little preview

PANEL_BG = (30, 32, 37)
PANEL_EDGE = (52, 55, 63)
TITLE_COLOR = (235, 236, 240)
HEADER_COLOR = (130, 136, 150)
TEXT_COLOR = (210, 212, 218)
HOVER_BG = (42, 45, 52)
SELECTED_BG = (56, 63, 80)
SELECTED_MARK = (255, 220, 90)
SWATCH_LAND = (120, 150, 90)      # background hex behind river previews
ERASE_COLOR = (230, 90, 80)


@dataclass
class Tool:
    id: str      # e.g. "erase_rivers"
    name: str


TOOLS = [Tool("erase_rivers", "Erase rivers")]


class TerrainPalette:
    def __init__(self, terrains, river_types, textures, font, title_font, header_font):
        self.textures = textures
        self.font = font
        self.title_font = title_font
        self.header_font = header_font
        self.selected = terrains[0]
        self.scroll = 0

        # The list shown: section headers and entries, in order.
        self.rows = [("header", "LAND")]
        self.rows += [("entry", t) for t in terrains if not t.water]
        self.rows += [("header", "WATER")]
        self.rows += [("entry", t) for t in terrains if t.water]
        self.rows += [("header", "RIVERS")]
        self.rows += [("entry", r) for r in river_types]
        self.rows += [("entry", tool) for tool in TOOLS]

    def row_at(self, y):
        """Index of the row at panel height y, or None."""
        if y < TITLE_HEIGHT:
            return None
        index = int((y - TITLE_HEIGHT + self.scroll) // ROW_HEIGHT)
        if 0 <= index < len(self.rows):
            return index
        return None

    def handle_click(self, x, y):
        index = self.row_at(y)
        if index is not None and self.rows[index][0] == "entry":
            self.selected = self.rows[index][1]

    def handle_wheel(self, wheel_y, panel_height):
        content = len(self.rows) * ROW_HEIGHT
        visible = panel_height - TITLE_HEIGHT
        self.scroll -= wheel_y * ROW_HEIGHT
        self.scroll = max(0, min(self.scroll, max(0, content - visible)))

    def draw(self, surface, panel_height, mouse_pos):
        panel = pygame.Rect(0, 0, PANEL_WIDTH, panel_height)
        pygame.draw.rect(surface, PANEL_BG, panel)
        pygame.draw.line(surface, PANEL_EDGE, (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, panel_height))
        title = self.title_font.render("Palette", True, TITLE_COLOR)
        surface.blit(title, (16, (TITLE_HEIGHT - title.get_height()) // 2))

        hovered = self.row_at(mouse_pos[1]) if panel.collidepoint(mouse_pos) else None
        surface.set_clip(pygame.Rect(0, TITLE_HEIGHT, PANEL_WIDTH - 1, panel_height - TITLE_HEIGHT))
        for index, (kind, value) in enumerate(self.rows):
            top = TITLE_HEIGHT + index * ROW_HEIGHT - self.scroll
            if top + ROW_HEIGHT < TITLE_HEIGHT or top > panel_height:
                continue    # scrolled out of sight
            row = pygame.Rect(0, top, PANEL_WIDTH - 1, ROW_HEIGHT)
            if kind == "header":
                text = self.header_font.render(value, True, HEADER_COLOR)
                surface.blit(text, (16, row.bottom - text.get_height() - 6))
            else:
                self.draw_entry_row(surface, row, value, index == hovered)
        surface.set_clip(None)

    def draw_entry_row(self, surface, row, entry, is_hovered):
        if entry is self.selected:
            pygame.draw.rect(surface, SELECTED_BG, row)
            pygame.draw.rect(surface, SELECTED_MARK, (row.x, row.y, 4, row.height))
        elif is_hovered:
            pygame.draw.rect(surface, HOVER_BG, row)

        self.draw_swatch(surface, row.x + 34, row.centery, entry)
        name = self.font.render(entry.name, True, TEXT_COLOR)
        surface.blit(name, (row.x + 60, row.centery - name.get_height() // 2))

    def draw_swatch(self, surface, cx, cy, entry):
        """Little hex preview of a palette entry."""
        corners = [(cx + x, cy + y) for x, y in hexmath.corner_offsets(SWATCH_SIZE)]
        kind = getattr(entry, "kind", None)

        if isinstance(entry, Tool) or kind is not None:
            pygame.draw.polygon(surface, SWATCH_LAND, corners)
        else:
            pygame.draw.polygon(surface, entry.color, corners)
            width = round(hexmath.hex_width(SWATCH_SIZE))
            height = round(hexmath.hex_height(SWATCH_SIZE))
            image = self.textures.get(entry.id, width, height)
            if image:
                surface.blit(image, (round(cx - width / 2), round(cy - height / 2)))
            return

        if kind == "edge":
            # A river along two sides of the hex.
            line_width = max(2, round(entry.width / 2.5))
            pygame.draw.line(surface, entry.color, corners[0], corners[1], line_width)
            pygame.draw.line(surface, entry.color, corners[5], corners[0], line_width)
        elif entry.id == "erase_rivers":
            pygame.draw.line(surface, ERASE_COLOR, (cx - 7, cy - 7), (cx + 7, cy + 7), 3)
            pygame.draw.line(surface, ERASE_COLOR, (cx - 7, cy + 7), (cx + 7, cy - 7), 3)

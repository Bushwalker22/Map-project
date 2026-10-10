"""
The terrain palette: the panel on the left where you pick what to paint.
"""

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


class TerrainPalette:
    def __init__(self, terrains, textures, font, title_font, header_font):
        self.textures = textures
        self.font = font
        self.title_font = title_font
        self.header_font = header_font
        self.selected = terrains[0]
        self.scroll = 0

        # The list shown: section headers and terrains, in order.
        self.rows = [("header", "LAND")]
        self.rows += [("terrain", t) for t in terrains if not t.water]
        self.rows += [("header", "WATER")]
        self.rows += [("terrain", t) for t in terrains if t.water]

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
        if index is not None and self.rows[index][0] == "terrain":
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
        title = self.title_font.render("Terrain", True, TITLE_COLOR)
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
                self.draw_terrain_row(surface, row, value, index == hovered)
        surface.set_clip(None)

    def draw_terrain_row(self, surface, row, terrain, is_hovered):
        if terrain is self.selected:
            pygame.draw.rect(surface, SELECTED_BG, row)
            pygame.draw.rect(surface, SELECTED_MARK, (row.x, row.y, 4, row.height))
        elif is_hovered:
            pygame.draw.rect(surface, HOVER_BG, row)

        # Little hex preview of the terrain.
        cx, cy = row.x + 34, row.centery
        corners = hexmath.corner_offsets(SWATCH_SIZE)
        pygame.draw.polygon(surface, terrain.color, [(cx + x, cy + y) for x, y in corners])
        width = round(hexmath.hex_width(SWATCH_SIZE))
        height = round(hexmath.hex_height(SWATCH_SIZE))
        image = self.textures.get(terrain.id, width, height)
        if image:
            surface.blit(image, (round(cx - width / 2), round(cy - height / 2)))

        name = self.font.render(terrain.name, True, TEXT_COLOR)
        surface.blit(name, (row.x + 60, row.centery - name.get_height() // 2))

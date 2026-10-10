"""
The toolbar along the top of the map: file buttons and brush size.

Clicking a button returns an action name (like "save"); the editor window
decides what that action does.
"""

import pygame

TOOLBAR_HEIGHT = 40
BUTTON_HEIGHT = 28
BUTTON_GAP = 6
GROUP_GAP = 28

BAR_BG = (36, 38, 44)
BAR_EDGE = (52, 55, 63)
BUTTON_BG = (52, 56, 66)
BUTTON_HOVER = (68, 74, 88)
TEXT_COLOR = (220, 222, 228)
LABEL_COLOR = (150, 155, 168)
VALUE_COLOR = (255, 220, 90)


class Toolbar:
    def __init__(self, font):
        self.font = font
        self.buttons = []   # (rect, action) pairs, rebuilt every draw

    def handle_click(self, pos):
        """The action of the button under pos, or None."""
        for rect, action in self.buttons:
            if rect.collidepoint(pos):
                return action
        return None

    def draw(self, surface, area, mouse_pos, brush_size):
        pygame.draw.rect(surface, BAR_BG, area)
        pygame.draw.line(surface, BAR_EDGE, (area.left, area.bottom - 1), (area.right, area.bottom - 1))
        self.buttons = []
        x = area.x + 10
        top = area.y + (TOOLBAR_HEIGHT - BUTTON_HEIGHT) // 2

        for label, action in [("New", "new"), ("Open", "open"),
                              ("Save", "save"), ("Save As", "save_as")]:
            x = self.draw_button(surface, x, top, label, action, mouse_pos) + BUTTON_GAP

        x += GROUP_GAP - BUTTON_GAP
        x = self.draw_text(surface, x, area.centery, "Brush size", LABEL_COLOR) + 10
        x = self.draw_button(surface, x, top, "-", "brush_smaller", mouse_pos, width=BUTTON_HEIGHT) + 8
        value = self.font.render(str(brush_size), True, VALUE_COLOR)
        value_x = x + (20 - value.get_width()) // 2
        surface.blit(value, (value_x, area.centery - value.get_height() // 2))
        x += 20 + 8
        self.draw_button(surface, x, top, "+", "brush_bigger", mouse_pos, width=BUTTON_HEIGHT)

    def draw_button(self, surface, x, top, label, action, mouse_pos, width=None):
        text = self.font.render(label, True, TEXT_COLOR)
        rect = pygame.Rect(x, top, width or text.get_width() + 24, BUTTON_HEIGHT)
        color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_BG
        pygame.draw.rect(surface, color, rect, border_radius=5)
        surface.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
        self.buttons.append((rect, action))
        return rect.right

    def draw_text(self, surface, x, center_y, label, color):
        text = self.font.render(label, True, color)
        surface.blit(text, (x, center_y - text.get_height() // 2))
        return x + text.get_width()

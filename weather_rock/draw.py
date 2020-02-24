"Draw the visual components"

import pygame


def lines(self, line_color, xmin, lines):
    "Draw the lines that create the display's borders"

    # The result of the lines below should be something
    # similar to this:
    # -------------------------
    # |                       |
    # -------------------------
    # |           |           |
    # |           |           |
    # -------------------------
    # |     |     |     |     |
    # |     |     |     |     |
    # |     |     |     |     |
    # -------------------------

    # Top
    pygame.draw.line(self.screen, line_color,
                     (xmin, 0),
                     (self.xmax, 0), lines)
    # Left
    pygame.draw.line(self.screen, line_color,
                     (xmin, 0),
                     (xmin, self.ymax), lines)
    # Bottom
    pygame.draw.line(self.screen, line_color,
                     (xmin, self.ymax),
                     (self.xmax, self.ymax), lines)
    # Right
    pygame.draw.line(self.screen, line_color,
                     (self.xmax, 0),
                     (self.xmax, self.ymax + 2), lines)

    # Bottom of top box
    pygame.draw.line(self.screen, line_color,
                     (xmin, self.ymax * 0.15),
                     (self.xmax, self.ymax * 0.15), lines)
    # Bottom of middle box
    pygame.draw.line(self.screen, line_color,
                     (xmin, self.ymax * 0.5),
                     (self.xmax, self.ymax * 0.5), lines)

    # Bottom row, left vertical
    pygame.draw.line(self.screen, line_color,
                     (self.xmax * 0.25, self.ymax * 0.5),
                     (self.xmax * 0.25, self.ymax), lines)
    # Bottom row, center vertical
    pygame.draw.line(self.screen, line_color,
                     (self.xmax * 0.5, self.ymax * 0.15),
                     (self.xmax * 0.5, self.ymax), lines)
    # Bottom row, right vertical
    pygame.draw.line(self.screen, line_color,
                     (self.xmax * 0.75, self.ymax * 0.5),
                     (self.xmax * 0.75, self.ymax), lines)

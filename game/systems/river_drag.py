"""Grab the visible river tip and pull it to the sea edge."""
import pygame


class RiverDragSystem:
    def __init__(self, config, size):
        self.config = config
        self.width, self.height = size
        self.leading_x = self.width * (1.0 - float(config.get('initial_visible_fraction', 0.05)))
        self.dragging = False
        self.connected = False
        self.drag_offset = 0.0
        self.last_mouse_x = None

    def handle_event(self, event):
        if self.connected:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            radius = float(self.config.get('grab_radius', 35.0))
            center_y = self.height * float(self.config.get('river_center_fraction', 0.50))
            if abs(x - self.leading_x) <= radius and abs(y - center_y) <= self.height * 0.11:
                self.dragging = True
                self.drag_offset = self.leading_x - x
                self.last_mouse_x = x
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            self.last_mouse_x = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Scale incremental mouse motion so the river moves more deliberately
            # without jumping to the cursor position on the first motion.
            dx = event.pos[0] - self.last_mouse_x
            self.last_mouse_x = event.pos[0]
            sensitivity = float(self.config.get("drag_sensitivity", 1.0))
            self.leading_x = max(0.0, min(self.width * 0.95, self.leading_x + dx * sensitivity))
            if self.leading_x <= self.width * float(self.config.get('sea_edge_fraction', 0.31)):
                self.leading_x = 0.0
                self.connected = True
                self.dragging = False

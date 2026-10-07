import pygame

class InputManager:
    """Expose frame-edge key events alongside continuous held-key state.

    Scenes that care about an exact KEYDOWN (for example Scene 11) still handle
    raw events; continuous movement can query this wrapper through ``held``.
    """

    def __init__(self):
        self.keys_pressed = set()
        self.keys_released = set()
        self.mouse_position = (0, 0)
        self.mouse_buttons = (False, False, False)

    def begin_frame(self):
        self.keys_pressed.clear()
        self.keys_released.clear()
        self.mouse_position = pygame.mouse.get_pos()
        self.mouse_buttons = pygame.mouse.get_pressed()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_released.add(event.key)

    def pressed(self, key):
        return key in self.keys_pressed

    def released(self, key):
        return key in self.keys_released

    def held(self, key):
        return bool(pygame.key.get_pressed()[key])

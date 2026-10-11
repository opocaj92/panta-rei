"""Translate SDL finger events to existing scene input, without changing desktop controls.

Coordinates are in the game's 640x360 logical canvas. Only the first finger owns a gesture except in Scene 08, where two fingers
control pinch-to-zoom. Extra fingers cannot trigger dialogue or dragging.
"""
import math
import pygame


class TouchGestures:
    TAP_DISTANCE = 12.0
    SWIPE_DISTANCE = 35.0

    def __init__(self, game):
        self.game = game
        self.active_id = None
        self.start = None
        self.last = None
        self.moved = 0.0
        self.pinch_fingers = {}
        self.pinch_active = False
        self.pinch_distance = None

    def cancel(self):
        self.active_id = None
        self.start = self.last = None
        self.moved = 0.0
        self.pinch_fingers.clear()
        self.pinch_active = False
        self.pinch_distance = None

    def _position(self, event):
        width, height = self.game.display.get_size()
        return self.game.logical_mouse((event.x * width, event.y * height))

    @staticmethod
    def _mouse(kind, position, previous=None):
        if kind == pygame.MOUSEMOTION:
            return pygame.event.Event(kind, pos=position,
                rel=(position[0] - previous[0], position[1] - previous[1]),
                buttons=(1, 0, 0))
        return pygame.event.Event(kind, pos=position, button=1)

    def _handle_scene08(self, event, position):
        """Two-finger pinch; a lone stationary finger can still tap dialogue."""
        fid = event.finger_id
        if event.type == pygame.FINGERDOWN:
            if len(self.pinch_fingers) >= 2:
                return [], False, (0, 0)
            self.pinch_fingers[fid] = position
            if len(self.pinch_fingers) == 1:
                self.start = self.last = position
                self.moved = 0.0
            else:
                self.pinch_active = True
                self.pinch_distance = math.dist(*self.pinch_fingers.values())
            return [], False, (0, 0)
        if fid not in self.pinch_fingers:
            return [], False, (0, 0)
        if event.type == pygame.FINGERMOTION:
            self.pinch_fingers[fid] = position
            if len(self.pinch_fingers) == 2:
                distance = math.dist(*self.pinch_fingers.values())
                if self.pinch_distance is not None:
                    scene = self.game.scenes.current
                    if scene is not None:
                        scene.pinch_touch(distance - self.pinch_distance)
                self.pinch_distance = distance
            elif not self.pinch_active:
                self.moved = max(self.moved, math.dist(self.start, position))
            return [], False, (0, 0)
        if event.type == pygame.FINGERUP:
            was_tap = (not self.pinch_active and len(self.pinch_fingers) == 1
                       and max(self.moved, math.dist(self.start, position)) <= self.TAP_DISTANCE)
            del self.pinch_fingers[fid]
            self.pinch_distance = None
            if not self.pinch_fingers:
                self.pinch_active = False
                self.start = self.last = None
                self.moved = 0.0
            return [], was_tap, (0, 0)
        return [], False, (0, 0)

    def handle(self, event):
        """Return (scene events, dialogue tap, scene04 camera delta)."""
        scene_name = self.game.scenes.current_name
        position = self._position(event)
        if scene_name == "scene_08":
            return self._handle_scene08(event, position)
        if event.type == pygame.FINGERDOWN:
            if self.active_id is not None:
                return [], False, (0, 0)
            self.active_id = event.finger_id
            self.start = self.last = position
            self.moved = 0.0
            if scene_name in ('scene_05', 'scene_09', 'scene_10'):
                return [self._mouse(pygame.MOUSEBUTTONDOWN, position)], False, (0, 0)
            return [], False, (0, 0)
        if event.finger_id != self.active_id:
            return [], False, (0, 0)
        previous = self.last
        self.last = position
        self.moved = max(self.moved, math.dist(self.start, position))
        delta = (position[0] - previous[0], position[1] - previous[1])
        if event.type == pygame.FINGERMOTION:
            if scene_name == 'scene_04':
                return [], False, delta
            if scene_name in ('scene_05', 'scene_09', 'scene_10'):
                return [self._mouse(pygame.MOUSEMOTION, position, previous)], False, (0, 0)
            return [], False, (0, 0)
        if event.type == pygame.FINGERUP:
            events = []
            if scene_name in ('scene_05', 'scene_09', 'scene_10'):
                events.append(self._mouse(pygame.MOUSEBUTTONUP, position))
            elif scene_name in ('scene_02', 'scene_07', 'scene_11') and self.moved >= self.SWIPE_DISTANCE:
                dx = position[0] - self.start[0]
                dy = position[1] - self.start[1]
                if abs(dx) > abs(dy):
                    key = pygame.K_RIGHT if dx < 0 else pygame.K_LEFT
                else:
                    key = pygame.K_UP if dy < 0 else pygame.K_DOWN
                events.append(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode=''))
            tapped = self.moved <= self.TAP_DISTANCE
            # Menu taps become button releases; command taps retain the normal
            # dialogue-advance path. Never deliver both for one gesture.
            if scene_name == 'scene_01' and tapped and self.game.scenes.current.state == 'menu':
                events.append(self._mouse(pygame.MOUSEBUTTONUP, position))
                tapped = False
            self.cancel()
            return events, tapped, (0, 0)
        return [], False, (0, 0)

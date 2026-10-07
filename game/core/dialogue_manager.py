import json

from .config import DATA_DIR


class DialogueManager:
    """Own dialogue data, player-controlled progression, and typewriter state.

    Dialogue never advances on a timer. The first advance request while a line is
    typing reveals it immediately; a subsequent request advances to the next line.
    """

    def __init__(self, language="en"):
        self.language = language
        self.lines = []
        self.index = 0
        self.visible_characters = 0.0
        self.finished = True

    def load(self, scene_name):
        localized = DATA_DIR / "dialogue" / self.language / f"{scene_name}.json"
        fallback = DATA_DIR / "dialogue" / "en" / f"{scene_name}.json"
        path = localized if localized.exists() else fallback
        if not path.exists():
            raise FileNotFoundError(f"Missing dialogue for {scene_name!r}: {localized} (fallback: {fallback})")

        with path.open("r", encoding="utf-8") as f:
            self.lines = json.load(f).get("lines", [])

        self.index = 0
        self.visible_characters = 0.0
        self.finished = not bool(self.lines)

    @property
    def current_line(self):
        if self.finished or self.index >= len(self.lines):
            return None
        return self.lines[self.index]

    @property
    def current_text_complete(self):
        line = self.current_line
        return line is None or self.visible_characters >= len(line["text"])

    @property
    def visible_text(self):
        line = self.current_line
        if line is None:
            return ""
        return line["text"][: int(self.visible_characters)]

    def update(self, dt):
        line = self.current_line
        if line is None:
            return
        if not self.current_text_complete:
            speed = float(line.get("speed", 40.0))
            self.visible_characters = min(
                len(line["text"]),
                self.visible_characters + speed * dt,
            )

    def advance(self):
        if self.finished:
            return
        if not self.current_text_complete:
            self.visible_characters = len(self.current_line["text"])
            return
        self.index += 1
        self.visible_characters = 0.0
        if self.index >= len(self.lines):
            self.finished = True

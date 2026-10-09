"""Small timers for conditions that must remain continuously true."""


class CompletionTimer:
    """Count elapsed time only while a completion condition is active."""

    def __init__(self):
        self.elapsed = 0.0

    def update(self, dt: float, *, active: bool) -> float:
        self.elapsed = self.elapsed + max(0.0, dt) if active else 0.0
        return self.elapsed

    def reset(self) -> None:
        self.elapsed = 0.0

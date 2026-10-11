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


def approach_linear(current: float, target: float, dt: float, rate: float) -> float:
    """Frame-rate-scaled linear interpolation with a clamped, nonnegative step.

    ``rate`` is the fraction approached per second for small ``dt``; a long
    frame may complete the interpolation. This preserves the existing music
    ramp behavior used in Scenes 09 and 10.
    """
    factor = min(1.0, max(0.0, dt) * max(0.0, rate))
    return current + (target - current) * factor


def smoothstep(value: float) -> float:
    """Clamped cubic ease-in/out, shared by camera and audio animations."""
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)

class LoopingAnimation:
    """Small presentation helper for fixed-rate looping frame sequences.

    It deliberately knows nothing about assets, scenes, or rendering. A renderer
    owns the frames and asks this object which frame should currently be shown.
    """

    def __init__(self, frames, fps):
        if not frames:
            raise ValueError("LoopingAnimation requires at least one frame")
        if fps <= 0:
            raise ValueError("LoopingAnimation fps must be positive")

        self.frames = list(frames)
        self.fps = float(fps)
        self.reset()

    @property
    def current_frame(self):
        return self.frames[self.frame_index]

    def reset(self):
        self.elapsed = 0.0
        self.frame_index = 0

    def update(self, dt):
        self.elapsed += dt
        frame_duration = 1.0 / self.fps
        steps = int(self.elapsed / frame_duration)
        if steps:
            self.elapsed -= steps * frame_duration
            self.frame_index = (self.frame_index + steps) % len(self.frames)

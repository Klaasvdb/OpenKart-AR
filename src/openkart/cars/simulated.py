"""A fake car: video from a webcam or video file, commands are only logged.

Lets us build and test the whole game (markers, HUD, splitscreen) before the
real car protocol is known. Hold printed markers in front of the webcam to
"drive" through gates.

`video_source = "pattern"` needs no camera at all: it draws a test image that
reacts to the commands, handy for checking splitscreen and input.
"""

from __future__ import annotations

import threading
import time

from openkart.cars.base import CarLink
from openkart.core.types import ControlCommand, VideoFrame


class SimulatedCar(CarLink):
    def __init__(self, config) -> None:
        super().__init__(config)
        self.last_command = ControlCommand()
        self._running = False
        self._thread: threading.Thread | None = None

    def connect(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def send(self, cmd: ControlCommand) -> None:
        self.last_command = cmd

    def close(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def _capture_loop(self) -> None:
        if self.config.video_source == "pattern":
            self._pattern_loop()
            return

        import cv2

        source = self.config.video_source or "0"
        cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
        try:
            while self._running:
                ok, image = cap.read()
                if not ok:
                    # Loop video files; for a webcam just retry.
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(0.05)
                    continue
                h, w = image.shape[:2]
                self._publish(VideoFrame(self.car_id, time.monotonic(), image, w, h))
        finally:
            cap.release()

    def _pattern_loop(self, width: int = 640, height: int = 480, fps: float = 30.0) -> None:
        """Horizon that tilts with steering and scrolls with throttle."""
        import numpy as np

        offset = 0.0
        ys = np.arange(height)[:, None]
        xs = np.arange(width)[None, :]
        while self._running:
            cmd = self.last_command
            offset = (offset + cmd.throttle * 12) % 40
            horizon = height / 2 + (xs - width / 2) * cmd.steering * 0.3
            ground = ys > horizon
            stripes = ((ys + offset) // 20 % 2).astype(bool) & ground
            image = np.empty((height, width, 3), np.uint8)
            image[:] = (200, 150, 90)  # sky (BGR)
            image[ground] = (70, 70, 70)
            image[stripes] = (95, 95, 95)
            self._publish(VideoFrame(self.car_id, time.monotonic(), image, width, height))
            time.sleep(1 / fps)

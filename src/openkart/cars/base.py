"""The interface every car protocol implements.

A CarLink owns the connection to one physical car: it sends control packets
and receives video. Implementations run their own receive thread and keep only
the latest frame, because for FPV low latency matters more than every frame.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod

from openkart.core.config import CarConfig
from openkart.core.types import ControlCommand, VideoFrame


class CarLink(ABC):
    # How often the app should call send(); many cars stop when packets stop.
    control_rate_hz: float = 30.0

    def __init__(self, config: CarConfig) -> None:
        self.config = config
        self._latest: VideoFrame | None = None
        self._lock = threading.Lock()

    @property
    def car_id(self) -> int:
        return self.config.id

    @abstractmethod
    def connect(self) -> None:
        """Open sockets/streams and start the video receive thread."""

    @abstractmethod
    def send(self, cmd: ControlCommand) -> None:
        """Send one control packet. Called at `control_rate_hz`."""

    @abstractmethod
    def close(self) -> None:
        """Stop the car and release resources."""

    def latest_frame(self) -> VideoFrame | None:
        with self._lock:
            return self._latest

    def _publish(self, frame: VideoFrame) -> None:
        with self._lock:
            self._latest = frame

    def __enter__(self) -> CarLink:
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

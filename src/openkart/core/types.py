"""Shared data types passed between modules.

Kept free of third-party imports so every module (and the tests) can use them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CarId = int
PlayerId = int


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class ControlCommand:
    """What we send to a car. Both axes are normalised to [-1, 1]."""

    throttle: float = 0.0  # -1 = full reverse, 1 = full forward
    steering: float = 0.0  # -1 = full left, 1 = full right

    def clamped(self) -> ControlCommand:
        return ControlCommand(clamp(self.throttle), clamp(self.steering))


STOP = ControlCommand()


@dataclass(frozen=True)
class PlayerInput:
    """Gamepad state for one player, already mapped to game actions."""

    throttle: float = 0.0
    steering: float = 0.0
    use_item: bool = False
    pause: bool = False


@dataclass(frozen=True)
class VideoFrame:
    """A decoded camera frame. `image` is a BGR numpy array (H, W, 3)."""

    car_id: CarId
    timestamp: float
    image: Any
    width: int
    height: int


@dataclass(frozen=True)
class MarkerSighting:
    """An ArUco marker seen by a car's camera."""

    car_id: CarId
    marker_id: int
    timestamp: float
    width_px: float  # apparent size, a proxy for distance
    corners: tuple[tuple[float, float], ...] = field(default=(), compare=False)


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

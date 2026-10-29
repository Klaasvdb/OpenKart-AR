"""Effects that change how a car responds, by rewriting its ControlCommand.

The real car cannot be made to slip, but we control every packet it receives.
Normal driving is capped below full throttle so a boost has headroom.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from openkart.core.types import ControlCommand


@dataclass
class ControlModifier:
    started: float
    duration: float

    def expired(self, now: float) -> bool:
        return now - self.started >= self.duration

    def apply(self, cmd: ControlCommand, now: float) -> ControlCommand:
        return cmd

    def max_throttle(self, base: float) -> float:
        """Lets a modifier raise or lower the throttle cap."""
        return base


@dataclass
class Boost(ControlModifier):
    duration: float = 1.5

    def apply(self, cmd: ControlCommand, now: float) -> ControlCommand:
        # Holding any forward throttle during a boost gives full speed.
        if cmd.throttle > 0:
            return ControlCommand(1.0, cmd.steering)
        return cmd

    def max_throttle(self, base: float) -> float:
        return 1.0


@dataclass
class Slowdown(ControlModifier):
    duration: float = 2.0
    cap: float = 0.2

    def max_throttle(self, base: float) -> float:
        return min(base, self.cap)


@dataclass
class Wobble(ControlModifier):
    """Steering shakes left/right, e.g. after hitting a banana."""

    duration: float = 1.0
    amplitude: float = 0.6
    frequency_hz: float = 4.0

    def apply(self, cmd: ControlCommand, now: float) -> ControlCommand:
        t = now - self.started
        offset = self.amplitude * math.sin(2 * math.pi * self.frequency_hz * t)
        return ControlCommand(cmd.throttle, cmd.steering + offset)


@dataclass
class SpinOut(ControlModifier):
    """Player loses control and the car stops."""

    duration: float = 1.2

    def apply(self, cmd: ControlCommand, now: float) -> ControlCommand:
        return ControlCommand(0.0, 0.0)


@dataclass
class ModifierStack:
    base_max_throttle: float = 0.7
    active: list[ControlModifier] = field(default_factory=list)

    def add(self, modifier: ControlModifier) -> None:
        self.active.append(modifier)

    def apply(self, cmd: ControlCommand, now: float) -> ControlCommand:
        self.active = [m for m in self.active if not m.expired(now)]

        # Lowering caps (slowdowns) win over raising ones (boosts).
        caps = [m.max_throttle(self.base_max_throttle) for m in self.active]
        lowered = [c for c in caps if c < self.base_max_throttle]
        if lowered:
            cap = min(lowered)
        else:
            cap = max(caps, default=self.base_max_throttle)

        for m in self.active:
            cmd = m.apply(cmd, now)
        # Scale rather than clip, so the stick keeps its full analog range.
        return ControlCommand(cmd.throttle * cap, cmd.steering).clamped()

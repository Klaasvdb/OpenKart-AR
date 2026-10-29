"""Per-car progress tracking based on which gate markers the camera sees.

A car always waits for *the next* gate. Other gates are ignored, which stops
shortcuts and driving backwards. A gate only counts once its marker has been
seen close enough (large enough in the frame) for `confirm_frames` sightings
within `confirm_window` seconds, so one noisy detection does not count.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from openkart.core.types import MarkerSighting
from openkart.game.track import Track


@dataclass(frozen=True)
class GatePassed:
    gate_index: int
    timestamp: float
    lap_completed: bool
    lap_time: float | None = None


@dataclass
class LapCounter:
    track: Track
    confirm_frames: int = 3
    confirm_window: float = 0.5

    laps_completed: int = 0
    gates_passed: int = 0  # total since the start, used for ranking
    last_gate_time: float | None = None
    lap_times: list[float] = field(default_factory=list)
    _next_gate: int = 0
    _lap_start: float | None = None
    _pending: list[float] = field(default_factory=list)

    @property
    def next_gate(self) -> int:
        return self._next_gate

    def start(self, timestamp: float) -> None:
        """Race start: the car sits behind the start gate, so gate 0 counts
        as the first passage without completing a lap."""
        self._lap_start = timestamp

    def feed(self, sighting: MarkerSighting) -> GatePassed | None:
        gate = self.track.gate_for_marker(sighting.marker_id)
        if gate is None or gate.index != self._next_gate:
            return None
        if sighting.width_px < self.track.min_marker_px:
            return None

        now = sighting.timestamp
        self._pending = [t for t in self._pending if now - t <= self.confirm_window]
        self._pending.append(now)
        if len(self._pending) < self.confirm_frames:
            return None

        return self._pass_gate(gate.index, now)

    def _pass_gate(self, index: int, now: float) -> GatePassed:
        self._pending.clear()
        self.gates_passed += 1
        self.last_gate_time = now
        self._next_gate = self.track.next_index(index)

        # Crossing gate 0 completes a lap, except the very first time.
        if index != 0 or self.gates_passed == 1:
            return GatePassed(index, now, lap_completed=False)

        lap_time = now - self._lap_start if self._lap_start is not None else None
        if lap_time is not None:
            self.lap_times.append(lap_time)
        self.laps_completed += 1
        self._lap_start = now
        return GatePassed(index, now, lap_completed=True, lap_time=lap_time)

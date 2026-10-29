"""Track definition: an ordered loop of gates, each recognised by ArUco ids."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Gate:
    index: int
    marker_ids: frozenset[int]
    # Driving through this gate gives an item (like the item boxes in Mario Kart).
    item_box: bool = False


@dataclass
class Track:
    name: str
    gates: list[Gate]
    min_marker_px: float = 60
    _by_marker: dict[int, Gate] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.gates) < 2:
            raise ValueError("a track needs at least 2 gates")
        self._by_marker = {}
        for gate in self.gates:
            for marker_id in gate.marker_ids:
                if marker_id in self._by_marker:
                    raise ValueError(f"marker {marker_id} used by more than one gate")
                self._by_marker[marker_id] = gate

    def gate_for_marker(self, marker_id: int) -> Gate | None:
        return self._by_marker.get(marker_id)

    def next_index(self, index: int) -> int:
        return (index + 1) % len(self.gates)

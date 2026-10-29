"""Things that happen during a race, for the HUD, sound and (later) the log.

The Race appends these as they happen; the app drains them once per tick.
Game logic never depends on them, so dropping events is harmless.
"""

from __future__ import annotations

from dataclasses import dataclass

from openkart.core.types import CarId
from openkart.game.items import ItemKind


@dataclass(frozen=True)
class RaceEvent:
    timestamp: float
    car_id: CarId


@dataclass(frozen=True)
class GateCrossed(RaceEvent):
    gate_index: int


@dataclass(frozen=True)
class LapCompleted(RaceEvent):
    lap: int  # the lap just finished, 1-based
    lap_time: float | None
    best: bool  # fastest lap of this racer so far


@dataclass(frozen=True)
class Finished(RaceEvent):
    position: int
    race_time: float


@dataclass(frozen=True)
class ItemReceived(RaceEvent):
    item: ItemKind


@dataclass(frozen=True)
class ItemUsed(RaceEvent):
    item: ItemKind
    targets: tuple[CarId, ...]  # empty for traps and misses


@dataclass(frozen=True)
class TrapPlaced(RaceEvent):
    item: ItemKind
    gate_index: int


@dataclass(frozen=True)
class Hit(RaceEvent):
    """`car_id` got hit by an `item` that racer `by` used."""

    item: ItemKind
    by: CarId

"""Items a player can pick up and use. Each item turns into ControlModifiers.

Pickup (driving through an "item box" marker) and targeting (who gets hit)
are still to be designed; this module defines the shape.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from openkart.game.modifiers import Boost, ControlModifier, Slowdown, SpinOut, Wobble


class ItemKind(Enum):
    MUSHROOM = "mushroom"  # self: boost
    BANANA = "banana"  # next racer to reach this gate: wobble + slowdown
    SHELL = "shell"  # racer directly ahead: spin out
    LIGHTNING = "lightning"  # everyone else: slowdown


@dataclass(frozen=True)
class ItemEffect:
    target: str  # "self" | "ahead" | "others" | "trap"
    modifiers: tuple[type[ControlModifier], ...]


EFFECTS: dict[ItemKind, ItemEffect] = {
    ItemKind.MUSHROOM: ItemEffect("self", (Boost,)),
    ItemKind.BANANA: ItemEffect("trap", (Wobble, Slowdown)),
    ItemKind.SHELL: ItemEffect("ahead", (SpinOut,)),
    ItemKind.LIGHTNING: ItemEffect("others", (Slowdown,)),
}


def roll_item(position: int, racer_count: int, rng: random.Random | None = None) -> ItemKind:
    """Rubber-banding: players further behind get stronger items."""
    rng = rng or random.Random()
    behind = (position - 1) / max(1, racer_count - 1)  # 0 = leader, 1 = last
    weights = {
        ItemKind.BANANA: 1.0 - 0.6 * behind,
        ItemKind.MUSHROOM: 0.6 + 0.4 * behind,
        ItemKind.SHELL: 0.2 + 0.6 * behind,
        ItemKind.LIGHTNING: 0.05 * behind,
    }
    kinds = list(weights)
    return rng.choices(kinds, weights=[weights[k] for k in kinds])[0]

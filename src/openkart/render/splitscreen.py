"""Splitscreen layout: where each player's view goes on the TV."""

from __future__ import annotations

from openkart.core.types import Rect


def viewports(players: int, width: int, height: int, gap: int = 4) -> list[Rect]:
    """One rect per player. With 3 players the 4th quadrant stays free for the
    standings/minimap; use `spare_viewport` to get it."""
    if not 1 <= players <= 4:
        raise ValueError("1 to 4 players supported")
    if players == 1:
        return [Rect(0, 0, width, height)]
    if players == 2:
        w = (width - gap) // 2
        return [Rect(0, 0, w, height), Rect(width - w, 0, w, height)]
    return _quadrants(width, height, gap)[:players]


def spare_viewport(players: int, width: int, height: int, gap: int = 4) -> Rect | None:
    return _quadrants(width, height, gap)[3] if players == 3 else None


def _quadrants(width: int, height: int, gap: int) -> list[Rect]:
    w = (width - gap) // 2
    h = (height - gap) // 2
    right, bottom = width - w, height - h
    return [Rect(0, 0, w, h), Rect(right, 0, w, h), Rect(0, bottom, w, h), Rect(right, bottom, w, h)]


def fit(src_w: int, src_h: int, area: Rect) -> Rect:
    """Largest rect with the source aspect ratio, centred in `area` (letterbox)."""
    scale = min(area.w / src_w, area.h / src_h)
    w, h = round(src_w * scale), round(src_h * scale)
    return Rect(area.x + (area.w - w) // 2, area.y + (area.h - h) // 2, w, h)

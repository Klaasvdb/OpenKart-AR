"""Loading config/default.toml (optionally overridden by config/local.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from openkart.game.track import Gate, Track

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO_ROOT / "config" / "default.toml"
LOCAL_CONFIG = REPO_ROOT / "config" / "local.toml"


@dataclass(frozen=True)
class CarConfig:
    id: int
    name: str
    protocol: str
    interface: str | None = None
    host: str | None = None
    video_source: str | None = None


@dataclass(frozen=True)
class PlayerConfig:
    name: str
    car: int
    gamepad: int


@dataclass(frozen=True)
class RaceConfig:
    laps: int = 3
    countdown_seconds: float = 3.0
    base_max_throttle: float = 0.7


@dataclass(frozen=True)
class DisplayConfig:
    width: int = 1920
    height: int = 1080
    fullscreen: bool = True


@dataclass(frozen=True)
class Config:
    race: RaceConfig
    display: DisplayConfig
    cars: list[CarConfig]
    players: list[PlayerConfig]
    track: Track = field(compare=False)


def load(path: Path | None = None) -> Config:
    if path is None:
        path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else DEFAULT_CONFIG
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return parse(raw)


def parse(raw: dict) -> Config:
    cars = [CarConfig(**c) for c in raw.get("cars", [])]
    players = [PlayerConfig(**p) for p in raw.get("players", [])]

    car_ids = {c.id for c in cars}
    for p in players:
        if p.car not in car_ids:
            raise ValueError(f"player {p.name!r} uses unknown car {p.car}")

    track_raw = raw.get("track", {})
    track = Track(
        name=track_raw.get("name", "track"),
        gates=[Gate(index=i, marker_ids=frozenset(g["markers"]))
               for i, g in enumerate(track_raw.get("gates", []))],
        min_marker_px=track_raw.get("min_marker_px", 60),
    )

    return Config(
        race=RaceConfig(**raw.get("race", {})),
        display=DisplayConfig(**raw.get("display", {})),
        cars=cars,
        players=players,
        track=track,
    )

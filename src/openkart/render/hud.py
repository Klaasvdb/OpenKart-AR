"""HUD text per player view: position, lap, lap time, countdown.

Formatting lives here as plain functions so it can be tested without pygame;
drawing is done by the renderer in app.py.
"""

from __future__ import annotations

from openkart.game.race import RacePhase, RaceSnapshot, RacerSnapshot

ORDINALS = {1: "1e", 2: "2e", 3: "3e", 4: "4e"}


def format_time(seconds: float) -> str:
    minutes, rest = divmod(max(0.0, seconds), 60)
    return f"{int(minutes)}:{rest:06.3f}"


def hud_lines(race: RaceSnapshot, racer: RacerSnapshot) -> list[str]:
    if race.phase is RacePhase.COUNTDOWN:
        n = int(race.countdown_remaining) + 1
        return [str(n) if race.countdown_remaining > 0 else "GO!"]
    if racer.finish_time is not None:
        return [f"FINISH! {ORDINALS.get(racer.position, racer.position)}",
                format_time(racer.finish_time)]
    return [
        ORDINALS.get(racer.position, str(racer.position)),
        f"Ronde {racer.lap}/{race.total_laps}",
        format_time(race.elapsed),
    ]

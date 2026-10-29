"""HUD text per player view: position, lap, lap time, countdown, item, messages.

Formatting lives here as plain functions so it can be tested without pygame;
drawing is done by render/renderer.py.
"""

from __future__ import annotations

from openkart.game import events as ev
from openkart.game.items import ItemKind
from openkart.game.race import RacePhase, RaceSnapshot, RacerSnapshot

ORDINALS = {1: "1e", 2: "2e", 3: "3e", 4: "4e"}

ITEM_NAMES = {
    ItemKind.MUSHROOM: "Turbo",
    ItemKind.BANANA: "Banaan",
    ItemKind.SHELL: "Schild",
    ItemKind.LIGHTNING: "Bliksem",
}


def ordinal(position: int) -> str:
    return ORDINALS.get(position, f"{position}e")


def format_time(seconds: float) -> str:
    minutes, rest = divmod(max(0.0, seconds), 60)
    return f"{int(minutes)}:{rest:06.3f}"


def hud_lines(race: RaceSnapshot, racer: RacerSnapshot) -> list[str]:
    if race.phase is RacePhase.LOBBY:
        return ["Vrij rijden", "Start = race beginnen"]
    if race.phase is RacePhase.COUNTDOWN:
        n = int(race.countdown_remaining) + 1
        return [str(n) if race.countdown_remaining > 0 else "GO!"]
    if racer.finish_time is not None:
        return [f"FINISH! {ordinal(racer.position)}", format_time(racer.finish_time)]
    return [
        ordinal(racer.position),
        f"Ronde {racer.lap}/{race.total_laps}",
        format_time(race.elapsed),
    ]


def item_label(racer: RacerSnapshot) -> str | None:
    return ITEM_NAMES[racer.item] if racer.item is not None else None


def standings_lines(race: RaceSnapshot) -> list[str]:
    """Shown in the spare quadrant (3 players) and on the results screen."""
    lines = []
    for r in race.racers:
        if r.finish_time is not None:
            detail = format_time(r.finish_time)
        else:
            detail = f"ronde {r.lap}/{race.total_laps}"
        best = f"  beste {format_time(min(r.lap_times))}" if r.lap_times else ""
        lines.append(f"{ordinal(r.position)}  {r.name}  {detail}{best}")
    return lines


def event_messages(event: ev.RaceEvent, names: dict[int, str]) -> dict[int, str]:
    """Short pop-up texts per car_id for one event. Empty = nothing to show."""
    car = event.car_id
    match event:
        case ev.LapCompleted(lap_time=t, best=best) if t is not None:
            return {car: f"{format_time(t)}{'  beste ronde!' if best else ''}"}
        case ev.ItemReceived(item=item):
            return {car: f"{ITEM_NAMES[item]}!"}
        case ev.Hit(item=item, by=by):
            return {car: f"Geraakt door {names.get(by, '?')} ({ITEM_NAMES[item]})",
                    by: f"Raak: {names.get(car, '?')}!"}
        case ev.ItemUsed(item=ItemKind.SHELL, targets=()):
            return {car: "Mis!"}
        case ev.Finished(position=p):
            return {car: f"Finish – {ordinal(p)}!"}
    return {}

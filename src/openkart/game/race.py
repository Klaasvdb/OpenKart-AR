"""Race state machine: lobby → countdown → racing → finished.

Pure logic. The app feeds it player inputs and marker sightings and gets back
the commands to send to each car, a snapshot to render and a list of events.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto

from openkart.core.types import STOP, CarId, ControlCommand, MarkerSighting, PlayerInput
from openkart.game import events as ev
from openkart.game.items import EFFECTS, ItemKind, roll_item
from openkart.game.lap_counter import GatePassed, LapCounter
from openkart.game.modifiers import ControlModifier, ModifierStack
from openkart.game.track import Track


class RacePhase(Enum):
    LOBBY = auto()
    COUNTDOWN = auto()
    RACING = auto()
    FINISHED = auto()


@dataclass
class Racer:
    name: str
    car_id: CarId
    laps: LapCounter
    modifiers: ModifierStack
    finish_time: float | None = None
    item: ItemKind | None = None
    _item_button: bool = False  # last button state, to act on press only

    @property
    def finished(self) -> bool:
        return self.finish_time is not None


@dataclass(frozen=True)
class Trap:
    item: ItemKind
    gate_index: int
    owner: CarId


@dataclass(frozen=True)
class RacerSnapshot:
    name: str
    car_id: CarId
    position: int  # 1-based
    lap: int  # current lap, 1-based, capped at total laps
    next_gate: int
    lap_times: tuple[float, ...]
    finish_time: float | None
    item: ItemKind | None
    effects: tuple[str, ...]  # active modifier names, e.g. ("Boost",)


@dataclass(frozen=True)
class RaceSnapshot:
    phase: RacePhase
    total_laps: int
    countdown_remaining: float
    elapsed: float
    racers: tuple[RacerSnapshot, ...]
    traps: tuple[Trap, ...]


@dataclass
class Race:
    track: Track
    total_laps: int = 3
    countdown_seconds: float = 3.0
    base_max_throttle: float = 0.7
    items_enabled: bool = True
    rng: random.Random = field(default_factory=random.Random)

    phase: RacePhase = RacePhase.LOBBY
    racers: dict[CarId, Racer] = field(default_factory=dict)
    traps: list[Trap] = field(default_factory=list)
    events: list[ev.RaceEvent] = field(default_factory=list)
    _phase_started: float = 0.0
    _race_started: float | None = None

    def add_racer(self, name: str, car_id: CarId) -> None:
        if self.phase is not RacePhase.LOBBY:
            raise RuntimeError("racers can only join in the lobby")
        self.racers[car_id] = Racer(
            name=name,
            car_id=car_id,
            laps=LapCounter(self.track),
            modifiers=ModifierStack(self.base_max_throttle),
        )

    def start_countdown(self, now: float) -> None:
        if not self.racers:
            raise RuntimeError("no racers")
        self.phase = RacePhase.COUNTDOWN
        self._phase_started = now

    def update(self, now: float) -> None:
        if self.phase is RacePhase.COUNTDOWN and now - self._phase_started >= self.countdown_seconds:
            self.phase = RacePhase.RACING
            self._phase_started = now
            self._race_started = now
            for racer in self.racers.values():
                racer.laps.start(now)
        elif self.phase is RacePhase.RACING and all(r.finished for r in self.racers.values()):
            self.phase = RacePhase.FINISHED
            self._phase_started = now

    def drain_events(self) -> list[ev.RaceEvent]:
        out, self.events = self.events, []
        return out

    # --- vision -----------------------------------------------------------

    def on_sighting(self, sighting: MarkerSighting) -> GatePassed | None:
        racer = self.racers.get(sighting.car_id)
        if self.phase is not RacePhase.RACING or racer is None or racer.finished:
            return None
        event = racer.laps.feed(sighting)
        if event is not None:
            self._on_gate(racer, event)
        return event

    def _on_gate(self, racer: Racer, passed: GatePassed) -> None:
        now, car = passed.timestamp, racer.car_id
        self.events.append(ev.GateCrossed(now, car, passed.gate_index))
        self._spring_traps(racer, passed.gate_index, now)

        if passed.lap_completed:
            times = racer.laps.lap_times
            best = passed.lap_time is not None and passed.lap_time <= min(times)
            self.events.append(ev.LapCompleted(now, car, racer.laps.laps_completed, passed.lap_time, best))
            if racer.laps.laps_completed >= self.total_laps:
                racer.finish_time = now - (self._race_started or 0.0)
                racer.item = None
                position = sum(r.finished for r in self.racers.values())
                self.events.append(ev.Finished(now, car, position, racer.finish_time))
                return

        gate = self.track.gates[passed.gate_index]
        if self.items_enabled and gate.item_box and racer.item is None:
            racer.item = roll_item(self.position_of(car), len(self.racers), self.rng)
            self.events.append(ev.ItemReceived(now, car, racer.item))

    def _spring_traps(self, racer: Racer, gate_index: int, now: float) -> None:
        for trap in list(self.traps):
            if trap.gate_index == gate_index and trap.owner != racer.car_id:
                self.traps.remove(trap)
                self._hit(racer, trap.item, trap.owner, now)
                return  # one trap per gate passage

    # --- items ------------------------------------------------------------

    def use_item(self, car_id: CarId, now: float) -> None:
        racer = self.racers[car_id]
        if self.phase is not RacePhase.RACING or racer.item is None or racer.finished:
            return
        item, racer.item = racer.item, None
        effect = EFFECTS[item]

        if effect.target == "trap":
            # The gate just passed is behind the user, so the racers behind
            # will reach it next.
            gate = (racer.laps.next_gate - 1) % len(self.track.gates)
            self.traps.append(Trap(item, gate, car_id))
            self.events.append(ev.TrapPlaced(now, car_id, item, gate))
            self.events.append(ev.ItemUsed(now, car_id, item, ()))
            return

        targets = self._targets(effect.target, car_id)
        self.events.append(ev.ItemUsed(now, car_id, item, tuple(t.car_id for t in targets)))
        for target in targets:
            if target.car_id == car_id:
                self._apply(target, item, now)
            else:
                self._hit(target, item, car_id, now)

    def _targets(self, kind: str, car_id: CarId) -> list[Racer]:
        if kind == "self":
            return [self.racers[car_id]]
        if kind == "others":
            return [r for r in self.racers.values() if r.car_id != car_id and not r.finished]
        if kind == "ahead":
            order = self.standings()
            i = next(i for i, r in enumerate(order) if r.car_id == car_id)
            ahead = order[i - 1] if i > 0 else None
            return [ahead] if ahead is not None and not ahead.finished else []
        raise ValueError(f"unknown item target {kind!r}")

    def _hit(self, racer: Racer, item: ItemKind, by: CarId, now: float) -> None:
        if racer.finished:
            return
        self.events.append(ev.Hit(now, racer.car_id, item, by))
        self._apply(racer, item, now)

    def _apply(self, racer: Racer, item: ItemKind, now: float) -> None:
        for modifier_type in EFFECTS[item].modifiers:
            racer.modifiers.add(modifier_type(started=now))

    def add_modifier(self, car_id: CarId, modifier: ControlModifier) -> None:
        self.racers[car_id].modifiers.add(modifier)

    # --- control ----------------------------------------------------------

    def handle_input(self, car_id: CarId, player: PlayerInput, now: float) -> ControlCommand:
        """Per tick and per player: act on button presses, return the command."""
        racer = self.racers[car_id]
        if player.use_item and not racer._item_button:
            self.use_item(car_id, now)
        racer._item_button = player.use_item
        return self.command_for(car_id, player, now)

    def command_for(self, car_id: CarId, player: PlayerInput, now: float) -> ControlCommand:
        racer = self.racers[car_id]
        # Lobby is free driving so players can position their cars.
        if self.phase is RacePhase.COUNTDOWN or racer.finished:
            return STOP
        cmd = ControlCommand(player.throttle, player.steering)
        return racer.modifiers.apply(cmd, now)

    # --- standings --------------------------------------------------------

    def standings(self) -> list[Racer]:
        def key(r: Racer):
            if r.finished:
                return (0, r.finish_time, 0.0)
            # More gates first; on a tie whoever got there earliest.
            return (1, -r.laps.gates_passed, r.laps.last_gate_time or float("inf"))

        return sorted(self.racers.values(), key=key)

    def position_of(self, car_id: CarId) -> int:
        return next(i + 1 for i, r in enumerate(self.standings()) if r.car_id == car_id)

    def snapshot(self, now: float) -> RaceSnapshot:
        countdown = 0.0
        if self.phase is RacePhase.COUNTDOWN:
            countdown = max(0.0, self.countdown_seconds - (now - self._phase_started))
        elapsed = now - self._race_started if self._race_started is not None else 0.0
        racers = tuple(
            RacerSnapshot(
                name=r.name,
                car_id=r.car_id,
                position=i + 1,
                lap=min(r.laps.laps_completed + 1, self.total_laps),
                next_gate=r.laps.next_gate,
                lap_times=tuple(r.laps.lap_times),
                finish_time=r.finish_time,
                item=r.item,
                effects=tuple(type(m).__name__ for m in r.modifiers.active if not m.expired(now)),
            )
            for i, r in enumerate(self.standings())
        )
        return RaceSnapshot(self.phase, self.total_laps, countdown, elapsed, racers, tuple(self.traps))

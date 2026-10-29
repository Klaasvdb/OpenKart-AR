"""Race state machine: lobby → countdown → racing → finished.

Pure logic. The app feeds it player inputs and marker sightings and gets back
the commands to send to each car plus a snapshot to render.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from openkart.core.types import STOP, CarId, ControlCommand, MarkerSighting, PlayerInput
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

    @property
    def finished(self) -> bool:
        return self.finish_time is not None


@dataclass(frozen=True)
class RacerSnapshot:
    name: str
    car_id: CarId
    position: int  # 1-based
    lap: int  # current lap, 1-based, capped at total laps
    next_gate: int
    lap_times: tuple[float, ...]
    finish_time: float | None


@dataclass(frozen=True)
class RaceSnapshot:
    phase: RacePhase
    total_laps: int
    countdown_remaining: float
    elapsed: float
    racers: tuple[RacerSnapshot, ...]


@dataclass
class Race:
    track: Track
    total_laps: int = 3
    countdown_seconds: float = 3.0
    base_max_throttle: float = 0.7

    phase: RacePhase = RacePhase.LOBBY
    racers: dict[CarId, Racer] = field(default_factory=dict)
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

    def on_sighting(self, sighting: MarkerSighting) -> GatePassed | None:
        racer = self.racers.get(sighting.car_id)
        if self.phase is not RacePhase.RACING or racer is None or racer.finished:
            return None
        event = racer.laps.feed(sighting)
        if event and event.lap_completed and racer.laps.laps_completed >= self.total_laps:
            racer.finish_time = event.timestamp - (self._race_started or 0.0)
        return event

    def add_modifier(self, car_id: CarId, modifier: ControlModifier) -> None:
        self.racers[car_id].modifiers.add(modifier)

    def command_for(self, car_id: CarId, player: PlayerInput, now: float) -> ControlCommand:
        racer = self.racers[car_id]
        # Lobby is free driving so players can position their cars.
        if self.phase is RacePhase.COUNTDOWN or racer.finished:
            return STOP
        cmd = ControlCommand(player.throttle, player.steering)
        return racer.modifiers.apply(cmd, now)

    def standings(self) -> list[Racer]:
        def key(r: Racer):
            if r.finished:
                return (0, r.finish_time, 0.0)
            # More gates first; on a tie whoever got there earliest.
            return (1, -r.laps.gates_passed, r.laps.last_gate_time or float("inf"))

        return sorted(self.racers.values(), key=key)

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
            )
            for i, r in enumerate(self.standings())
        )
        return RaceSnapshot(self.phase, self.total_laps, countdown, elapsed, racers)

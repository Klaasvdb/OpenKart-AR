"""The game engine without any display: cars ↔ vision ↔ race.

Front ends (the Godot bridge, or the pygame debug view) call `tick()` once per
frame with the players' inputs and draw whatever it returns. Nothing in here
knows how or where the game is shown.
"""

from __future__ import annotations

from dataclasses import dataclass

from openkart import cars
from openkart.core.config import Config
from openkart.core.types import STOP, CarId, ControlCommand, MarkerSighting, PlayerInput, VideoFrame
from openkart.game.events import RaceEvent
from openkart.game.race import Race, RacePhase, RaceSnapshot


@dataclass(frozen=True)
class Tick:
    now: float
    frames: dict[CarId, VideoFrame | None]  # latest frame per car (may repeat)
    new_frames: dict[CarId, VideoFrame]  # frames not seen in an earlier tick
    sightings: dict[CarId, list[MarkerSighting]]  # markers in `new_frames`
    snapshot: RaceSnapshot
    events: list[RaceEvent]


class Engine:
    def __init__(self, config: Config, detector=None) -> None:
        self.config = config
        self.links = {c.id: cars.create(c) for c in config.cars}
        self.race = self.new_race()
        self._detector = detector
        self._last_frame_time: dict[CarId, float] = {}
        self._last_sent: dict[CarId, float] = {}

    def new_race(self) -> Race:
        race = Race(
            track=self.config.track,
            total_laps=self.config.race.laps,
            countdown_seconds=self.config.race.countdown_seconds,
            base_max_throttle=self.config.race.base_max_throttle,
            items_enabled=self.config.race.items,
        )
        for player in self.config.players:
            race.add_racer(player.name, player.car)
        return race

    def start(self) -> None:
        if self._detector is None:
            from openkart.vision.markers import MarkerDetector

            self._detector = MarkerDetector()
        for link in self.links.values():
            link.connect()

    def close(self) -> None:
        for link in self.links.values():
            link.send(STOP)
            link.close()

    def press_start(self, now: float) -> None:
        """The Start button: lobby → countdown, results → new race."""
        if self.race.phase is RacePhase.LOBBY:
            self.race.start_countdown(now)
        elif self.race.phase is RacePhase.FINISHED:
            self.race = self.new_race()
        # During countdown/racing Start is reserved for a pause menu (todo).

    def tick(self, inputs: dict[CarId, PlayerInput], now: float) -> Tick:
        # 1. Vision, only on frames we have not looked at yet: the loop runs
        #    faster than the cameras, and counting one frame twice would
        #    weaken the lap counter's "seen in N frames" check.
        frames = {car_id: link.latest_frame() for car_id, link in self.links.items()}
        new_frames: dict[CarId, VideoFrame] = {}
        sightings: dict[CarId, list[MarkerSighting]] = {}
        for car_id, frame in frames.items():
            if frame is None or self._last_frame_time.get(car_id) == frame.timestamp:
                continue
            self._last_frame_time[car_id] = frame.timestamp
            new_frames[car_id] = frame
            sightings[car_id] = self._detector.detect(frame)
            for sighting in sightings[car_id]:
                self.race.on_sighting(sighting)

        # 2. Game state.
        self.race.update(now)

        # 3. Input → (modified) commands → cars. Cars without input stop.
        for car_id in self.links:
            player = inputs.get(car_id, PlayerInput())
            if car_id in self.race.racers:
                cmd = self.race.handle_input(car_id, player, now)
            else:
                cmd = STOP
            self._send(car_id, cmd, now)

        return Tick(now, frames, new_frames, sightings, self.race.snapshot(now), self.race.drain_events())

    def _send(self, car_id: CarId, cmd: ControlCommand, now: float) -> None:
        link = self.links[car_id]
        if now - self._last_sent.get(car_id, float("-inf")) >= 1 / link.control_rate_hz:
            link.send(cmd)
            self._last_sent[car_id] = now

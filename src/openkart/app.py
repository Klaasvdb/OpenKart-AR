"""Main loop wiring: cars ↔ game ↔ input ↔ render.

Flow: lobby (free driving) → Start → countdown → race → results → Start →
new race in the lobby. Esc quits.
"""

from __future__ import annotations

import time

from openkart import cars
from openkart.core.config import Config
from openkart.core.types import STOP
from openkart.game.race import Race, RacePhase
from openkart.render.hud import event_messages

TICK_HZ = 60
MESSAGE_SECONDS = 2.0


class App:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.links = {c.id: cars.create(c) for c in config.cars}
        self.names = {p.car: p.name for p in config.players}
        self.race = self._new_race()
        self._last_sent: dict[int, float] = {}
        self._messages: dict[int, tuple[str, float]] = {}  # car → (text, until)
        self._start_held = False

    def _new_race(self) -> Race:
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

    def run(self, duration: float | None = None) -> None:
        """Run until Esc or window close (or `duration` seconds, for tests)."""
        import pygame

        from openkart.input.gamepad import Gamepads
        from openkart.render.renderer import Renderer, View
        from openkart.vision.markers import MarkerDetector

        renderer = Renderer(self.config.display)
        views = [View(p.name, p.car) for p in self.config.players]
        for link in self.links.values():
            link.connect()
        pads = Gamepads()
        detector = MarkerDetector()
        stop_at = time.monotonic() + duration if duration is not None else None
        try:
            while True:
                now = time.monotonic()
                if stop_at is not None and now >= stop_at:
                    break
                if any(e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)
                       for e in pygame.event.get()):
                    break

                # 1. Vision: feed new marker sightings into the race.
                frames = {car_id: link.latest_frame() for car_id, link in self.links.items()}
                for frame in frames.values():
                    if frame is not None:
                        for sighting in detector.detect(frame):
                            self.race.on_sighting(sighting)

                # 2. Game state and menu flow.
                inputs = {p.car: pads.read(p.gamepad) for p in self.config.players}
                start = any(i.pause for i in inputs.values())
                if start and not self._start_held:
                    self._on_start(now)
                self._start_held = start
                self.race.update(now)
                for event in self.race.drain_events():
                    for car, text in event_messages(event, self.names).items():
                        self._messages[car] = (text, now + MESSAGE_SECONDS)

                # 3. Input → (modified) commands → cars, at each car's own rate.
                for car_id, player in inputs.items():
                    cmd = self.race.handle_input(car_id, player, now)
                    self._send(car_id, cmd, now)

                # 4. Render.
                messages = {car: text for car, (text, until) in self._messages.items() if until > now}
                renderer.draw(views, frames, self.race.snapshot(now), messages)

                time.sleep(max(0.0, 1 / TICK_HZ - (time.monotonic() - now)))
        finally:
            for link in self.links.values():
                link.send(STOP)
                link.close()
            renderer.close()

    def _on_start(self, now: float) -> None:
        if self.race.phase is RacePhase.LOBBY:
            self.race.start_countdown(now)
        elif self.race.phase is RacePhase.FINISHED:
            self.race = self._new_race()
        # During countdown/racing Start is reserved for a pause menu (todo).

    def _send(self, car_id: int, cmd, now: float) -> None:
        link = self.links[car_id]
        if now - self._last_sent.get(car_id, 0.0) >= 1 / link.control_rate_hz:
            link.send(cmd)
            self._last_sent[car_id] = now

"""Main loop wiring: cars ↔ game ↔ input ↔ render.

Skeleton: the order of operations per tick is fixed here, the pygame drawing
is filled in during roadmap step 2 (one player, fullscreen).
"""

from __future__ import annotations

import time

from openkart import cars
from openkart.core.config import Config
from openkart.game.race import Race

TICK_HZ = 60


class App:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.links = {c.id: cars.create(c) for c in config.cars}
        self.race = Race(
            track=config.track,
            total_laps=config.race.laps,
            countdown_seconds=config.race.countdown_seconds,
            base_max_throttle=config.race.base_max_throttle,
        )
        for player in config.players:
            self.race.add_racer(player.name, player.car)

    def run(self) -> None:
        from openkart.input.gamepad import Gamepads
        from openkart.vision.markers import MarkerDetector

        for link in self.links.values():
            link.connect()
        pads = Gamepads()
        detector = MarkerDetector()
        try:
            while True:
                now = time.monotonic()

                # 1. Vision: feed new marker sightings into the race.
                for link in self.links.values():
                    frame = link.latest_frame()
                    if frame is not None:
                        for sighting in detector.detect(frame):
                            self.race.on_sighting(sighting)

                # 2. Game state.
                self.race.update(now)

                # 3. Input → (modified) commands → cars.
                for player in self.config.players:
                    cmd = self.race.command_for(player.car, pads.read(player.gamepad), now)
                    self.links[player.car].send(cmd)

                # 4. Render splitscreen + HUD from self.race.snapshot(now).
                # TODO(roadmap 2): pygame window, render.splitscreen, render.hud

                time.sleep(max(0.0, 1 / TICK_HZ - (time.monotonic() - now)))
        finally:
            for link in self.links.values():
                link.close()

"""Draws the TV picture: one camera view per player plus HUD, with pygame.

Only drawing lives here; what to show comes from the RaceSnapshot and
render/hud.py. Camera frames are scaled to fit their viewport, never stretched.
"""

from __future__ import annotations

from dataclasses import dataclass

from openkart.core.config import DisplayConfig
from openkart.core.types import CarId, Rect, VideoFrame
from openkart.game.race import RacePhase, RaceSnapshot
from openkart.render import hud
from openkart.render.splitscreen import fit, spare_viewport, viewports

BACKGROUND = (12, 12, 16)
TEXT = (255, 255, 255)
SHADOW = (0, 0, 0)
ACCENT = (255, 200, 40)
NO_SIGNAL = (40, 40, 48)


@dataclass(frozen=True)
class View:
    """One player's slot on screen."""

    name: str
    car_id: CarId


class Renderer:
    def __init__(self, display: DisplayConfig) -> None:
        import pygame

        self._pg = pygame
        pygame.display.init()
        pygame.font.init()
        flags = pygame.FULLSCREEN if display.fullscreen else 0
        self.screen = pygame.display.set_mode((display.width, display.height), flags)
        pygame.display.set_caption("OpenKart AR")
        pygame.mouse.set_visible(not display.fullscreen)
        self._fonts: dict[int, object] = {}

    def font(self, size: int):
        if size not in self._fonts:
            self._fonts[size] = self._pg.font.Font(None, size)
        return self._fonts[size]

    def draw(
        self,
        views: list[View],
        frames: dict[CarId, VideoFrame | None],
        race: RaceSnapshot,
        messages: dict[CarId, str],
    ) -> None:
        pg = self._pg
        w, h = self.screen.get_size()
        self.screen.fill(BACKGROUND)
        by_car = {r.car_id: r for r in race.racers}

        for view, area in zip(views, viewports(len(views), w, h)):
            self._draw_camera(frames.get(view.car_id), area, view.name)
            racer = by_car.get(view.car_id)
            if racer is None:
                continue
            scale = area.h / 1080
            big = race.phase is RacePhase.COUNTDOWN
            for i, line in enumerate(hud.hud_lines(race, racer)):
                size = int((220 if big else 64) * scale * (1 if i == 0 else 0.7)) + 12
                if big:
                    self._text_centered(line, size, area)
                else:
                    self._text(line, size, (area.x + 16, area.y + 12 + i * int(70 * scale + 12)))
            label = hud.item_label(racer)
            if label:
                self._text(f"[{label}]", int(60 * scale) + 12, (area.x + area.w - 16, area.y + 12),
                           color=ACCENT, anchor="topright")
            if racer.effects:
                self._text(" ".join(racer.effects), int(40 * scale) + 10,
                           (area.x + area.w - 16, area.y + area.h - 16), anchor="bottomright")
            if view.car_id in messages:
                self._text(messages[view.car_id], int(70 * scale) + 12,
                           (area.x + area.w // 2, area.y + area.h - 24), color=ACCENT, anchor="midbottom")

        spare = spare_viewport(len(views), w, h)
        if spare is not None or race.phase is RacePhase.FINISHED:
            self._draw_standings(race, spare or Rect(w // 4, h // 4, w // 2, h // 2))

        pg.display.flip()

    def _draw_camera(self, frame: VideoFrame | None, area: Rect, name: str) -> None:
        pg = self._pg
        if frame is None:
            pg.draw.rect(self.screen, NO_SIGNAL, (area.x, area.y, area.w, area.h))
            self._text_centered(f"{name}: geen beeld", 48, area)
            return
        # OpenCV frames are BGR; flip the channel axis to get RGB.
        rgb = frame.image[:, :, ::-1].copy()
        surface = pg.image.frombuffer(rgb.tobytes(), (frame.width, frame.height), "RGB")
        target = fit(frame.width, frame.height, area)
        self.screen.blit(pg.transform.smoothscale(surface, (target.w, target.h)), (target.x, target.y))

    def _draw_standings(self, race: RaceSnapshot, area: Rect) -> None:
        pg = self._pg
        panel = pg.Surface((area.w, area.h), pg.SRCALPHA)
        panel.fill((0, 0, 0, 190))
        self.screen.blit(panel, (area.x, area.y))
        title = "Uitslag" if race.phase is RacePhase.FINISHED else "Klassement"
        self._text(title, 64, (area.x + 24, area.y + 20), color=ACCENT)
        for i, line in enumerate(hud.standings_lines(race)):
            self._text(line, 44, (area.x + 24, area.y + 90 + i * 50))
        if race.phase is RacePhase.FINISHED:
            self._text("Start = nieuwe race", 36, (area.x + 24, area.y + area.h - 20), anchor="bottomleft")

    def _text(self, text: str, size: int, pos: tuple[int, int], color=TEXT, anchor: str = "topleft") -> None:
        font = self.font(size)
        shadow = font.render(text, True, SHADOW)
        label = font.render(text, True, color)
        rect = label.get_rect(**{anchor: pos})
        self.screen.blit(shadow, rect.move(2, 2))
        self.screen.blit(label, rect)

    def _text_centered(self, text: str, size: int, area: Rect) -> None:
        self._text(text, size, (area.x + area.w // 2, area.y + area.h // 2), anchor="center")

    def close(self) -> None:
        self._pg.display.quit()

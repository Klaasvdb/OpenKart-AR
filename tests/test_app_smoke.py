"""Runs the real main loop headless for a moment, with test-pattern cars."""

import os
from dataclasses import replace

import pytest

pytest.importorskip("pygame")
pytest.importorskip("cv2")

from openkart.app import App  # noqa: E402
from openkart.core.config import DEFAULT_CONFIG, load  # noqa: E402


def test_main_loop_runs_headless(monkeypatch):
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    cfg = load(DEFAULT_CONFIG)
    cfg = replace(
        cfg,
        cars=[replace(c, protocol="simulated", video_source="pattern") for c in cfg.cars],
        display=replace(cfg.display, fullscreen=False, width=640, height=360),
    )
    app = App(cfg)
    app.run(duration=0.5)
    assert app.links[0].last_command.throttle == 0  # STOP sent on exit

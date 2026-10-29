import random

import pytest

from openkart.core.config import DEFAULT_CONFIG, load
from openkart.core.types import ControlCommand, MarkerSighting, PlayerInput, Rect, STOP
from openkart.game.items import ItemKind, roll_item
from openkart.game.lap_counter import LapCounter
from openkart.game.modifiers import Boost, ModifierStack, Slowdown, SpinOut
from openkart.game.race import Race, RacePhase
from openkart.game.track import Gate, Track
from openkart.render.hud import format_time
from openkart.render.splitscreen import fit, spare_viewport, viewports


def make_track(gates=3):
    return Track("test", [Gate(i, frozenset({i * 2, i * 2 + 1})) for i in range(gates)], min_marker_px=50)


def see(counter_or_race, marker, t, car=0, px=100, frames=3):
    """Simulate a marker being visible for a few consecutive frames."""
    result = None
    for i in range(frames):
        s = MarkerSighting(car, marker, t + i * 0.05, px)
        r = counter_or_race.feed(s) if isinstance(counter_or_race, LapCounter) else counter_or_race.on_sighting(s)
        result = r or result
    return result


def drive_lap(target, start_t, gates=3, car=0):
    t = start_t
    for g in [*range(1, gates), 0]:
        see(target, g * 2, t, car=car)
        t += 1.0
    return t


class TestTrack:
    def test_duplicate_marker_rejected(self):
        with pytest.raises(ValueError):
            Track("x", [Gate(0, frozenset({1})), Gate(1, frozenset({1}))])

    def test_wraps(self):
        assert make_track(3).next_index(2) == 0


class TestLapCounter:
    def test_full_lap(self):
        c = LapCounter(make_track())
        c.start(0.0)
        see(c, 0, 0.1)  # cross start line
        assert c.laps_completed == 0 and c.next_gate == 1
        see(c, 2, 2.0)
        see(c, 4, 4.0)
        event = see(c, 1, 6.0)  # other marker of gate 0
        assert event.lap_completed
        assert c.laps_completed == 1
        assert c.lap_times == [pytest.approx(6.1)]

    def test_skipping_gates_does_not_count(self):
        c = LapCounter(make_track())
        c.start(0.0)
        see(c, 0, 0.1)
        assert see(c, 4, 1.0) is None  # gate 2 before gate 1
        assert c.next_gate == 1

    def test_far_away_marker_ignored(self):
        c = LapCounter(make_track())
        assert see(c, 0, 0.0, px=10) is None

    def test_single_glitch_frame_ignored(self):
        c = LapCounter(make_track())
        assert see(c, 0, 0.0, frames=1) is None
        assert see(c, 0, 5.0, frames=2) is None  # old sighting expired

    def test_needs_consecutive_frames(self):
        c = LapCounter(make_track())
        assert see(c, 0, 0.0, frames=3) is not None


class TestModifiers:
    def test_base_cap_scales_throttle(self):
        stack = ModifierStack(base_max_throttle=0.7)
        assert stack.apply(ControlCommand(1.0, 0.3), 0).throttle == pytest.approx(0.7)
        assert stack.apply(ControlCommand(0.5, 0), 0).throttle == pytest.approx(0.35)

    def test_boost_gives_full_throttle_then_expires(self):
        stack = ModifierStack(0.7)
        stack.add(Boost(started=0.0))
        assert stack.apply(ControlCommand(0.2, 0), 0.5).throttle == 1.0
        assert stack.apply(ControlCommand(1.0, 0), 2.0).throttle == pytest.approx(0.7)
        assert stack.active == []

    def test_slowdown_beats_boost(self):
        stack = ModifierStack(0.7)
        stack.add(Boost(started=0.0))
        stack.add(Slowdown(started=0.0, cap=0.2))
        assert stack.apply(ControlCommand(1.0, 0), 0.1).throttle == pytest.approx(0.2)

    def test_spin_out_stops_car(self):
        stack = ModifierStack(0.7)
        stack.add(SpinOut(started=0.0))
        assert stack.apply(ControlCommand(1.0, 1.0), 0.5) == ControlCommand(0.0, 0.0)


class TestRace:
    def make_race(self):
        race = Race(make_track(), total_laps=2, countdown_seconds=3)
        race.add_racer("A", 0)
        race.add_racer("B", 1)
        return race

    def test_flow_and_standings(self):
        race = self.make_race()
        race.start_countdown(0.0)
        assert race.command_for(0, PlayerInput(throttle=1), 1.0) == STOP
        race.update(3.0)
        assert race.phase is RacePhase.RACING

        for car in (0, 1):
            see(race, 0, 3.1, car=car)
        t = drive_lap(race, 4.0, car=0)
        snap = race.snapshot(t)
        assert snap.racers[0].name == "A"
        assert snap.racers[0].lap == 2

        t = drive_lap(race, t, car=0)
        assert race.racers[0].finished
        assert race.command_for(0, PlayerInput(throttle=1), t) == STOP

        drive_lap(race, t, car=1)
        drive_lap(race, t + 10, car=1)
        race.update(t + 30)
        assert race.phase is RacePhase.FINISHED
        assert [r.position for r in race.snapshot(t + 30).racers] == [1, 2]

    def test_sightings_ignored_before_start(self):
        race = self.make_race()
        assert see(race, 0, 0.0) is None


class TestSplitscreen:
    @pytest.mark.parametrize("n", [1, 2, 3, 4])
    def test_viewports_inside_screen_and_disjoint(self, n):
        rects = viewports(n, 1920, 1080)
        assert len(rects) == n
        for r in rects:
            assert r.x >= 0 and r.y >= 0 and r.x + r.w <= 1920 and r.y + r.h <= 1080
        for a in rects:
            for b in rects:
                if a is not b:
                    assert a.x + a.w <= b.x or b.x + b.w <= a.x or a.y + a.h <= b.y or b.y + b.h <= a.y

    def test_spare_quadrant_only_for_three(self):
        assert spare_viewport(3, 1920, 1080) is not None
        assert spare_viewport(4, 1920, 1080) is None

    def test_fit_keeps_aspect(self):
        r = fit(640, 480, Rect(0, 0, 958, 1080))
        assert r.w / r.h == pytest.approx(640 / 480, rel=0.01)
        assert r.w <= 958 and r.h <= 1080


def test_rubber_banding_favours_last_place():
    rng = random.Random(1)
    first = [roll_item(1, 4, rng) for _ in range(2000)]
    last = [roll_item(4, 4, rng) for _ in range(2000)]
    assert last.count(ItemKind.SHELL) > first.count(ItemKind.SHELL)
    assert ItemKind.LIGHTNING not in first


def test_format_time():
    assert format_time(83.5) == "1:23.500"


def test_default_config_loads():
    cfg = load(DEFAULT_CONFIG)
    assert len(cfg.track.gates) >= 2
    assert {p.car for p in cfg.players} <= {c.id for c in cfg.cars}


def test_event_messages():
    from openkart.game import events as ev
    from openkart.render.hud import event_messages

    names = {0: "A", 1: "B"}
    msgs = event_messages(ev.Hit(1.0, 1, ItemKind.SHELL, by=0), names)
    assert set(msgs) == {0, 1} and "A" in msgs[1]
    assert event_messages(ev.GateCrossed(1.0, 0, 2), names) == {}

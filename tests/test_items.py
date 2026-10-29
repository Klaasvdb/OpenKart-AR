import random

from openkart.core.types import ControlCommand, MarkerSighting, PlayerInput
from openkart.game import events as ev
from openkart.game.items import ItemKind
from openkart.game.modifiers import Boost, Slowdown, SpinOut
from openkart.game.race import Race
from openkart.game.track import Gate, Track


def item_track():
    # Gate 1 is an item box.
    return Track("t", [Gate(0, frozenset({0})), Gate(1, frozenset({1}), item_box=True),
                       Gate(2, frozenset({2}))], min_marker_px=10)


def pass_gate(race, car, gate, t):
    for i in range(3):
        race.on_sighting(MarkerSighting(car, gate, t + i * 0.05, 100))


def racing(cars=(0, 1, 2)):
    race = Race(item_track(), total_laps=2, countdown_seconds=0, rng=random.Random(0))
    for c in cars:
        race.add_racer(f"P{c}", c)
    race.start_countdown(0.0)
    race.update(0.0)
    for c in cars:
        pass_gate(race, c, 0, 0.1)
    return race


def kinds(events, kind):
    return [e for e in events if isinstance(e, kind)]


def test_item_box_gives_item_once():
    race = racing()
    pass_gate(race, 0, 1, 1.0)
    assert race.racers[0].item is not None
    assert len(kinds(race.drain_events(), ev.ItemReceived)) == 1

    first = race.racers[0].item
    pass_gate(race, 0, 2, 2.0)
    pass_gate(race, 0, 0, 3.0)
    pass_gate(race, 0, 1, 4.0)  # slot still full: no new item
    assert race.racers[0].item is first


def test_mushroom_boosts_self():
    race = racing()
    race.racers[0].item = ItemKind.MUSHROOM
    race.use_item(0, 1.0)
    assert race.racers[0].item is None
    assert any(isinstance(m, Boost) for m in race.racers[0].modifiers.active)
    assert race.command_for(0, PlayerInput(throttle=1), 1.1).throttle == 1.0


def test_shell_hits_racer_directly_ahead():
    race = racing()
    pass_gate(race, 0, 1, 1.0)
    pass_gate(race, 0, 2, 2.0)  # car 0 leads
    pass_gate(race, 1, 1, 2.5)  # car 1 second, car 2 last
    race.drain_events()
    race.racers[2].item = ItemKind.SHELL
    race.use_item(2, 3.0)
    hits = kinds(race.drain_events(), ev.Hit)
    assert [h.car_id for h in hits] == [1]
    assert any(isinstance(m, SpinOut) for m in race.racers[1].modifiers.active)


def test_shell_in_first_place_misses():
    race = racing()
    pass_gate(race, 0, 1, 1.0)
    race.drain_events()
    race.racers[0].item = ItemKind.SHELL
    race.use_item(0, 2.0)
    assert kinds(race.drain_events(), ev.Hit) == []


def test_lightning_hits_everyone_else():
    race = racing()
    race.racers[2].item = ItemKind.LIGHTNING
    race.use_item(2, 1.0)
    assert {h.car_id for h in kinds(race.drain_events(), ev.Hit)} == {0, 1}
    assert race.command_for(0, PlayerInput(throttle=1), 1.1).throttle == Slowdown.cap


def test_banana_trap_hits_next_racer_through_that_gate_only():
    race = racing()
    pass_gate(race, 0, 1, 1.0)
    race.racers[0].item = ItemKind.BANANA
    race.use_item(0, 1.5)
    assert race.traps and race.traps[0].gate_index == 1

    race.drain_events()
    pass_gate(race, 1, 1, 2.0)
    assert [h.car_id for h in kinds(race.drain_events(), ev.Hit)] == [1]
    assert race.traps == []

    pass_gate(race, 2, 1, 3.0)  # trap is gone
    assert kinds(race.drain_events(), ev.Hit) == []


def test_own_trap_is_harmless():
    race = racing()
    pass_gate(race, 0, 1, 1.0)
    race.racers[0].item = ItemKind.BANANA
    race.use_item(0, 1.5)
    pass_gate(race, 0, 2, 2.0)
    pass_gate(race, 0, 0, 3.0)
    pass_gate(race, 0, 1, 4.0)
    assert kinds(race.drain_events(), ev.Hit) == []
    assert len(race.traps) == 1


def test_item_button_acts_on_press_not_hold():
    race = racing()
    race.racers[0].item = ItemKind.MUSHROOM
    race.handle_input(0, PlayerInput(use_item=True), 1.0)
    race.racers[0].item = ItemKind.MUSHROOM
    race.handle_input(0, PlayerInput(use_item=True), 1.1)  # still held
    assert race.racers[0].item is ItemKind.MUSHROOM
    race.handle_input(0, PlayerInput(use_item=False), 1.2)
    race.handle_input(0, PlayerInput(use_item=True), 1.3)
    assert race.racers[0].item is None


def test_items_disabled():
    race = Race(item_track(), countdown_seconds=0, items_enabled=False)
    race.add_racer("A", 0)
    race.start_countdown(0.0)
    race.update(0.0)
    pass_gate(race, 0, 0, 0.1)
    pass_gate(race, 0, 1, 1.0)
    assert race.racers[0].item is None


def test_lap_and_finish_events():
    race = racing(cars=(0,))
    t = 1.0
    for _ in range(2):
        for g in (1, 2, 0):
            pass_gate(race, 0, g, t)
            t += 1.0
    events = race.drain_events()
    laps = kinds(events, ev.LapCompleted)
    assert [e.lap for e in laps] == [1, 2]
    finished = kinds(events, ev.Finished)
    assert len(finished) == 1 and finished[0].position == 1
    assert race.racers[0].item is None

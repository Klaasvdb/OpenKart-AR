"""Gamepads → PlayerInput, using pygame's SDL controller support.

Uses the SDL "game controller" mapping so Xbox, PlayStation, Switch and Steam
Input pads all have the same layout: right trigger = gas, left trigger =
brake/reverse, left stick = steering, A = item, Start = pause.

For developing without controllers, the keyboard plays the first gamepad slot
that has no pad: arrows = gas/brake/steer, space = item, Enter = start.
"""

from __future__ import annotations

from openkart.core.types import PlayerInput

DEADZONE = 0.12


def apply_deadzone(value: float, deadzone: float = DEADZONE) -> float:
    if abs(value) < deadzone:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - deadzone) / (1.0 - deadzone)


def trigger_to_unit(raw: float) -> float:
    """SDL triggers report -1..1 on some backends and 0..1 on others."""
    return max(0.0, min(1.0, raw if raw >= 0 else (raw + 1) / 2))


class Gamepads:
    def __init__(self) -> None:
        import pygame
        from pygame._sdl2 import controller

        self._pg = pygame
        self._controller = controller
        controller.init()
        self.pads = [controller.Controller(i) for i in range(controller.get_count())
                     if controller.is_controller(i)]

    def read(self, index: int) -> PlayerInput:
        if index == len(self.pads):
            return self._keyboard()
        if index > len(self.pads):
            return PlayerInput()
        pad = self.pads[index]
        pg = self._pg
        axis = lambda a: pad.get_axis(a) / 32767  # noqa: E731
        gas = trigger_to_unit(axis(pg.CONTROLLER_AXIS_TRIGGERRIGHT))
        brake = trigger_to_unit(axis(pg.CONTROLLER_AXIS_TRIGGERLEFT))
        return PlayerInput(
            throttle=gas - brake,
            steering=apply_deadzone(axis(pg.CONTROLLER_AXIS_LEFTX)),
            use_item=bool(pad.get_button(pg.CONTROLLER_BUTTON_A)),
            pause=bool(pad.get_button(pg.CONTROLLER_BUTTON_START)),
        )

    def _keyboard(self) -> PlayerInput:
        pg = self._pg
        keys = pg.key.get_pressed()
        return PlayerInput(
            throttle=float(keys[pg.K_UP]) - float(keys[pg.K_DOWN]),
            steering=float(keys[pg.K_RIGHT]) - float(keys[pg.K_LEFT]),
            use_item=bool(keys[pg.K_SPACE]),
            pause=bool(keys[pg.K_RETURN]),
        )

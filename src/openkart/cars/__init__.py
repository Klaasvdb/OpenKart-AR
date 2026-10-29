"""Car protocol registry. Add new protocols to PROTOCOLS once reverse-engineered."""

from __future__ import annotations

from openkart.cars.base import CarLink
from openkart.cars.simulated import SimulatedCar
from openkart.core.config import CarConfig

PROTOCOLS: dict[str, type[CarLink]] = {
    "simulated": SimulatedCar,
}


def create(config: CarConfig) -> CarLink:
    try:
        cls = PROTOCOLS[config.protocol]
    except KeyError:
        raise ValueError(
            f"unknown car protocol {config.protocol!r}; known: {', '.join(PROTOCOLS)}"
        ) from None
    return cls(config)

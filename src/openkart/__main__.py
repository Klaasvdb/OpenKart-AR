from __future__ import annotations

import argparse
from pathlib import Path

from openkart.core import config as config_mod


def main() -> None:
    parser = argparse.ArgumentParser(prog="openkart")
    parser.add_argument("--config", type=Path, help="pad naar een .toml-config")
    parser.add_argument("--check-config", action="store_true",
                        help="config inlezen, samenvatting tonen en stoppen")
    args = parser.parse_args()

    cfg = config_mod.load(args.config)
    if args.check_config:
        print(f"Track {cfg.track.name!r}: {len(cfg.track.gates)} poorten, {cfg.race.laps} rondes")
        for car in cfg.cars:
            print(f"  auto {car.id} {car.name}: {car.protocol} via {car.interface} → {car.host}")
        for p in cfg.players:
            print(f"  {p.name}: auto {p.car}, gamepad {p.gamepad}")
        return

    from openkart.app import App

    App(cfg).run()


if __name__ == "__main__":
    main()

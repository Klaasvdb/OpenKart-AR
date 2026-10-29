# OpenKart AR

Een open-source variant van *Mario Kart Live*: race met echte FPV-wifi-autootjes
door je woonkamer, met splitscreen op de tv, rondetelling via geprinte
markers en AR-items die het gedrag van je auto beïnvloeden.

> Status: **skelet / ontwerpfase.** De spellogica (track, rondeteller, items,
> race) en de weergave (splitscreen, HUD) zijn geïmplementeerd en getest; met
> `--demo` draait het spel al zonder auto's. De koppeling met de
> echte auto's wacht op het uitzoeken van hun protocol – zie
> [docs/HARDWARE.md](docs/HARDWARE.md).

## Documentatie

- [docs/ARCHITECTUUR.md](docs/ARCHITECTUUR.md) – hoe de onderdelen samenwerken
- [docs/HARDWARE.md](docs/HARDWARE.md) – auto's, wifi-dongles, protocol reverse-engineeren
- [docs/WEERGAVE.md](docs/WEERGAVE.md) – tv, splitscreen en Steam Link
- [docs/SPELONTWERP.md](docs/SPELONTWERP.md) – spelregels, items, open vragen

## Projectstructuur

```
config/default.toml        auto's, spelers, track
src/openkart/
  core/                    gedeelde datatypes + config
  cars/                    verbinding met de auto's (CarLink), simulator
  vision/                  ArUco-markerdetectie, camera-kalibratie
  input/                   gamepads → PlayerInput
  game/                    spellogica zonder I/O (track, rondes, items, race, events)
  render/                  splitscreen, HUD, renderer (pygame), AR-overlay
  app.py                   hoofdloop
tools/
  probe_car.py             onderzoek welke poorten/streams een auto heeft
  generate_markers.py      printbare ArUco-poortmarkers
tests/                     unit tests voor de spellogica
```

## Aan de slag

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

```bash
pytest
```

```bash
python -m openkart --check-config
```

Zonder auto's of camera spelen (testbeeld, toetsenbord = eerste speler zonder
gamepad: pijltjes, spatie = item, Enter = start, Esc = stoppen):

```bash
python -m openkart --demo --windowed
```

## Roadmap

1. **Protocol** – één auto: video zien en laten rijden vanaf de pc.
2. **Eén speler** – gamepad → auto, live beeld fullscreen.
3. **Track** – markers printen, rondes tellen, rondetijden in HUD.
4. **Multi-auto** – 4 dongles, 2–4 spelers in splitscreen.
5. **Race** – countdown, posities, finish, resultatenscherm.
6. **Items** – boost, schild, banaan… via `ControlModifier`s.
7. **AR** – items en effecten 3D op de markers projecteren (kalibratie).
8. **Afwerking** – menu's, geluid, Steam-integratie als "non-Steam game".

## Licentie

GPL-3.0, zie [LICENSE](LICENSE).

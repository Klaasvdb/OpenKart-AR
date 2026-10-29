# Architectuur

## Het idee in één zin

Elke speler bestuurt een echt FPV-autootje met een gamepad; de pc ontvangt de
camerabeelden van alle auto's, legt er een AR-laag over (items, HUD, rondetijd)
en toont alles in splitscreen op de tv. De "track" bestaat uit geprinte
**ArUco-markers** op poortjes in de woonkamer: zodra de camera van een auto de
volgende poort ziet, telt die als gepasseerd.

Zo doet Mario Kart Live het ook: er is geen externe camera of positiebepaling
nodig, de auto "ziet" zelf waar hij is.

## Datastroom

```
 gamepad ──► input/ ──► PlayerInput
                            │
                            ▼
                     game/modifiers   (boost, slow, spin… past het stuursignaal aan)
                            │
                            ▼  ControlCommand
                     cars/CarLink ──UDP──► auto (via eigen wifi-dongle)
                                                │
 auto ──video──► cars/CarLink ──► VideoFrame ◄──┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
              vision/markers                   render/splitscreen
              (ArUco-detectie)                 (beeld + AR + HUD)
                     │                               ▲
                     ▼  MarkerSighting               │
              game/lap_counter ──► game/race ────────┘
                                   (fase, posities, rondes)
```

## Modules

| Map | Verantwoordelijkheid | Afhankelijk van hardware? |
|---|---|---|
| `core/` | Gedeelde datatypes (`ControlCommand`, `VideoFrame`, `MarkerSighting`, …) en config-laden. Geen externe libraries. | Nee |
| `cars/` | `CarLink`-interface + implementaties per protocol. `simulated` werkt met webcam of videobestand, zodat we zonder auto's kunnen ontwikkelen. | **Ja** – protocol nog te reverse-engineeren |
| `vision/` | ArUco-markers detecteren in een frame, camera-kalibratie. | Nee (OpenCV) |
| `input/` | Gamepads uitlezen en vertalen naar `PlayerInput`. | Nee (pygame) |
| `game/` | Pure spellogica: track, rondeteller, items/modifiers, race-statemachine. **Geen I/O**, volledig testbaar. | Nee |
| `render/` | Splitscreen-layout, HUD, AR-overlay. | Nee (pygame) |
| `app.py` | Verbindt alles in één hoofdloop. | – |

Belangrijk ontwerpprincipe: **`game/` weet niets van auto's, video of pygame.**
Het krijgt `PlayerInput` en `MarkerSighting` binnen en geeft `ControlCommand` en
een `RaceSnapshot` terug. Daardoor kunnen we alle regels unit-testen en later
eventueel de renderer vervangen (bv. door Godot) zonder de spellogica te raken.

## Threads / processen

Video decoderen is het zwaarste werk (4 streams). Plan:

- Per auto **één thread** die video ontvangt + decodeert en het laatste frame
  in een buffer zet (oude frames weggooien: lage latency > alle frames).
- Marker-detectie draait op een verkleinde kopie, ook per auto.
- De hoofdthread (60 fps) doet input → game → besturing versturen → renderen
  met wat er op dat moment in de buffers staat.
- Besturingspakketten gaan op een vaste frequentie (± 30–50 Hz, afhankelijk van
  wat de originele app doet), ook als er niets verandert – veel van deze
  auto's stoppen als ze een tijd niets horen (failsafe).

Als Python's GIL een bottleneck blijkt, verhuizen we decoding naar
`multiprocessing` met shared memory. De interfaces blijven hetzelfde.

## Items en effecten: via het stuursignaal

We kunnen de auto niet echt laten "slippen", maar wel het stuursignaal
manipuleren, net zoals Mario Kart Live:

- **Normale topsnelheid** = bv. 70% gas. Zo is er ruimte voor een boost.
- **Boost** = tijdelijk 100% gas toegestaan.
- **Geraakt door een schild** = gas begrensd tot 20% + stuur wiebelt.
- **Spin-out** = korte tijd geen controle.

Elk effect is een `ControlModifier` die `ControlCommand → ControlCommand`
transformeert. Ze worden gestapeld en vervallen vanzelf.

## Track

Een track is een geordende lijst `Gate`s. Elke poort heeft één of meer
marker-id's (bv. een markertje links én rechts op de poort). De rondeteller
verwacht altijd *de volgende* poort; andere poorten negeren we (tegen
valsspelen/achteruit rijden). Een poort telt pas als de marker groot genoeg in
beeld is (= de auto is dichtbij), en dat een paar frames na elkaar.

`tools/generate_markers.py` maakt printbare markers.

## Configuratie

`config/default.toml` beschrijft de auto's (welke wifi-dongle, welk IP, welk
protocol), de spelers en de track. Zie dat bestand voor commentaar.

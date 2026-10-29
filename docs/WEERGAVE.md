# Weergave: tv, splitscreen en Steam Link

## Waar zit de vertraging?

Bij FPV-racen telt elke milliseconde tussen "stuur draaien" en "beeld ziet de
bocht". Grove schattingen (te meten met de echte auto's):

| Stap | Typisch |
|---|---|
| Camera + encoding in de auto + wifi | 100–250 ms (dit is de grootste post en ligt vast) |
| Decoderen + AR + renderen op de pc | 15–35 ms |
| HDMI rechtstreeks naar de tv (game-modus) | 10–30 ms |
| **Extra bij Steam Link** (encode → netwerk → decode) | **+15–50 ms**, meer bij wifi |

## Aanbeveling

**Beste:** een (Linux-)pc of mini-pc vlak bij de tv, met een HDMI-kabel.
Redenen:

1. Geen extra streaming-latency bovenop de al trage autocamera's.
2. De wifi-dongles moeten sowieso **in de woonkamer** zitten, binnen bereik
   van de auto's. Dan is de pc daar ook handig.
3. Geen extra wifi-verkeer: 4 videostreams van de auto's op 2,4 GHz plus
   een Steam Link-stream is vragen om haperingen.
4. Linux maakt het werken met 4 dongles die allemaal hetzelfde IP-adres
   aanspreken een stuk eenvoudiger dan Windows.

**Steam Link kan ook**, als:

- de game-pc ergens anders staat en je die wilt gebruiken;
- de pc **bekabeld** is én het Steam Link-apparaat (tv/box) bekabeld of op
  5 GHz zit;
- de wifi-dongles via USB-verlengkabels/hub toch in de woonkamer kunnen
  (of je kiest optie B uit HARDWARE.md: een bridge per auto).

Het spel is gewoon een fullscreen-programma met gamepad-ondersteuning, dus je
voegt het in Steam toe als **"Non-Steam game"**. Steam Input zet dan alle
controllers die op de Link zitten door naar de pc. We hoeven er niets speciaals
voor te bouwen; we houden het dus als optie open en beslissen na het meten
van de echte latency.

## Splitscreen-layout

| Spelers | Layout |
|---|---|
| 1 | volledig scherm |
| 2 | naast elkaar (elk beeld met letterbox, behoudt 16:9 / 4:3) |
| 3 | 2×2, het vierde vak toont klassement/minimap |
| 4 | 2×2 |

Camerabeelden worden nooit uitgerekt: ze worden passend geschaald en
gecentreerd in hun vak. Zie `src/openkart/render/splitscreen.py`.

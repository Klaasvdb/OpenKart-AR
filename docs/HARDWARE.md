# Hardware en netwerk

## De auto's

Goedkope FPV-wifi-auto's van AliExpress werken bijna altijd zo:

- De auto is zelf een **wifi-access-point** (SSID zoals `WIFI_UFO_xxxx`,
  `FPV_xxxx`, `HD-720P-xxxx`), meestal op 2,4 GHz.
- De auto heeft een vast IP, vaak `192.168.0.1`, `192.168.1.1` of `172.16.10.1`.
  **Alle vier de auto's hebben waarschijnlijk hetzelfde IP.**
- Video komt als MJPEG of H.264 binnen over UDP, RTSP of HTTP.
- Besturing gaat via kleine UDP-pakketjes (een paar bytes: header, gas,
  stuur, checksum) die de app tientallen keren per seconde stuurt.

Welk protocol *jouw* auto's gebruiken moeten we nog uitzoeken. Dat is stap 1.

## Stap 1: protocol achterhalen

1. Noteer merk/model en de naam van de bijhorende telefoon-app.
2. Verbind een laptop met de wifi van één auto en draai
   `python tools/probe_car.py 192.168.x.1` – die zoekt open poorten en
   bekende videostreams.
3. Neem verkeer op terwijl de originele app rijdt:
   - Android: [PCAPdroid](https://github.com/emanuele-f/PCAPdroid) (geen root nodig) → `.pcap`.
   - Of laptop als hotspot/brug + Wireshark.
4. Rijd bewust: alleen gas, alleen links, alleen rechts – zo zie je welke byte
   wat doet.
5. Optioneel: de APK decompileren met `jadx`; vaak staat het protocol er
   letterlijk in.
6. Zet de bevindingen in `docs/protocol/<model>.md` en implementeer een
   `CarLink` in `src/openkart/cars/`.

Veel van deze apps gebruiken dezelfde paar chipsets (bv. "Lewei", "WiFi UFO",
"HD FPV"); er bestaan open-source projecten die die protocollen al
gedocumenteerd hebben. Eerst zoeken op de app-naam scheelt veel werk.

## Vier auto's tegelijk: één wifi-adapter per auto

Omdat elke auto zijn eigen access point is, kan één wifi-kaart maar met één auto
tegelijk verbonden zijn. Oplossingen, van eenvoudig naar robuust:

| Optie | Hoe | Voor/nadeel |
|---|---|---|
| **A. 4 USB-wifi-dongles** (aanbevolen) | Elke dongle verbindt met één auto. | Goedkoop (± €10/stuk). Omdat alle auto's hetzelfde IP hebben, moeten sockets aan een specifieke interface gebonden worden (`SO_BINDTODEVICE`, Linux) of gebruiken we per dongle een *network namespace*. Op Windows is dit erg lastig → Linux aangeraden. |
| B. Kleine bridge per auto | Raspberry Pi Zero 2 W / ESP32 per auto die wifi-auto ↔ je thuisnetwerk doorgeeft. | Pc hoeft niet in de buurt; maar extra hardware, extra latency en meer 2,4 GHz-verkeer. |
| C. Auto's in station-mode | Auto's loggen in op een router (zie hieronder). | **Voorkeur** als het lukt: geen dongles, elk een eigen IP. |

Tips voor dongles:
- Kies chipsets met goede Linux-driver (bv. MediaTek MT7601U / MT7612U, Realtek
  RTL8188/8812 met mainline driver).
- Gebruik een USB-hub met eigen voeding en een paar korte verlengkabels, zodat
  de antennes niet vlak naast elkaar zitten.
- Zet je eigen thuiswifi en eventuele Steam Link op **5 GHz** of bekabeld,
  zodat 2,4 GHz vrij blijft voor de auto's.

## Voorkeur: auto's laten inloggen op een netwerk (station-mode)

De originele app hoeft niet te blijven werken. Als de auto's als *client*
inloggen op een router in plaats van zelf een access point te zijn, krijgt
elke auto een eigen IP en vervallen de dongles en `SO_BINDTODEVICE`. In de
config laat je dan `interface` leeg en zet je per auto zijn eigen `host`.

### Welke chip zit erin?

Zonder openschroeven:

1. **MAC-adres** van de auto opzoeken (verbinden met zijn wifi, dan `ip neigh`)
   en de eerste 3 bytes via een "MAC vendor lookup" opzoeken.
   - **Espressif** → ESP32: eigen firmware flashen kan (route 2).
   - Beken, Jieli, Anyka, Ingenic, Allwinner, Realtek → route 1 of 3.
2. **Telnet** (poort 23) open? `tools/probe_car.py` checkt dat. Sommige
   Linux-camera's laten je zo binnen, soms zonder wachtwoord.

Met de auto open: een foto van de print met leesbare chipopschriften.

### Routes

| Route | Wanneer | Moeilijkheid |
|---|---|---|
| **1. Config aanpassen** | Camera draait Linux en je komt erin (telnet/UART): wifi-config omzetten naar client-mode. | Makkelijk áls het kan, maar zeldzaam |
| **2. Eigen firmware** | Chip is een ESP32: zelf firmware schrijven (wifi-client, MJPEG-stream, motoren aansturen). | Gemiddeld |
| **3. Camerabordje vervangen** | Werkt altijd: ESP32-S3 + camera (± €10–15) in de plaats, die de bestaande motordriver aanstuurt (via de MCU over UART of direct met PWM). | Solderen, maar het meest betrouwbaar en volledig open source |

Bij route 2 of 3 bepalen we zelf: stuurfrequentie, failsafe (stoppen bij
signaalverlies), resolutie en batterijspanning terugsturen. Nadeel: de
ESP32-camera haalt ongeveer 640×480, wat voor dit doel volstaat.

### Netwerk voor het spel

Gebruik een **apart routertje** (bv. een GL.iNet-reisrouter) in de
woonkamer, met de pc er bekabeld aan. Zo belasten 4 videostreams je thuiswifi
niet, is de setup meeneembaar, en mag de pc elders staan (dan wordt Steam Link
ook realistischer, zie WEERGAVE.md).

## Checklist als de auto's aankomen

- [ ] Merk/model en app-naam noteren
- [ ] Verbinden met de wifi van één auto, SSID en IP noteren
- [ ] MAC-adres → chipfabrikant opzoeken
- [ ] `python tools/probe_car.py <ip>` draaien (poorten, video, telnet)
- [ ] Verkeer van de originele app opnemen met PCAPdroid (gas / links / rechts apart)
- [ ] Foto van de printplaat (chips leesbaar)
- [ ] Beslissen: route 1, 2 of 3 – of terugvallen op de dongles

## Gamepads

Alles wat pygame/SDL herkent: Xbox-, PlayStation-, Switch Pro-controllers, of
Steam Input. 4 controllers via Bluetooth op één pc kan, maar een USB-dongle
(bv. Xbox Wireless Adapter) of kabels is stabieler.

## Benodigdheden (boodschappenlijst)

- 4× FPV-wifi-auto (heb je)
- 4× USB-wifi-dongle + gevoede USB-hub
- Pc met Linux (mini-pc of laptop) bij de tv, HDMI-kabel
- 2–4 gamepads
- Printer + karton/schuim voor poortjes met ArUco-markers

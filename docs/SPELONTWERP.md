# Spelontwerp

Wat het spel *is*, los van hoe het technisch werkt. Beslissingen die nog open
staan, zijn gemarkeerd met **❓**.

## Spelverloop

1. **Lobby** – iedereen rijdt vrij rond om de auto's achter de startpoort te
   zetten. Eén speler drukt op Start.
2. **Aftellen** – 3, 2, 1, GO! Tijdens het aftellen staan de auto's stil.
3. **Race** – de eerste keer door de startpoort (poort 0) start de eerste
   ronde. Daarna telt elke volgende poort, in volgorde.
4. **Finish** – na het laatste rondje stopt je auto en zie je je eindtijd.
   Als iedereen binnen is: uitslag. Start = nieuwe race (terug naar de lobby).

## Track

- Een track = een lus van poorten met ArUco-markers, in een vaste volgorde.
- Poorten overslaan of achteruit rijden telt niet: je moet altijd de volgende
  poort halen.
- Poorten met `item_box = true` geven een item.

## Items

Eén itemslot per speler. Door een itempoort rijden met een leeg slot geeft een
willekeurig item; wie verder achterligt, krijgt vaker sterke items
(*rubber banding*). Gebruiken met de A-knop.

| Item (code) | Naam in HUD | Doelwit | Effect |
|---|---|---|---|
| `MUSHROOM` | Turbo | jezelf | 1,5 s volgas (boven de normale 70%) |
| `BANANA` | Banaan | val bij de poort die je net passeerde | volgende tegenstander die daar passeert: 1 s slingeren + 2 s traag |
| `SHELL` | Schild | speler vlak vóór je | 1,2 s stilstand; mis als je eerste bent |
| `LIGHTNING` | Bliksem | alle anderen | 2 s traag (max 20% gas) |

De auto kan niet echt slippen: alle effecten werken door het stuursignaal te
veranderen (zie ARCHITECTUUR.md).

## Scherm

- Splitscreen per speler: eigen camerabeeld, positie, ronde, racetijd, item
  rechtsboven, korte meldingen onderaan ("Geraakt door …", rondetijd).
- Bij 3 spelers toont het vierde vak het klassement.
- Na de race: uitslag met eindtijden en beste rondes.

## Open vragen

- **❓ Namen en thema** – Mario Kart-achtig (paddenstoel, banaan, schild) of
  een eigen thema? Dat bepaalt ook de HUD-teksten, geluiden en AR-figuurtjes.
- **❓ Spelmodi** – alleen race, of ook tijdrit (solo, beste ronde), battle
  (punten door te raken), …?
- **❓ Spelers** – 2, 3 of 4 tegelijk? Ook computergestuurde tegenstanders
  zijn niet mogelijk (echte auto's), maar wel "spookrondes" bij een tijdrit.
- **❓ Itemset** – welke items erbij/eraf? Bv. schild om jezelf te beschermen,
  driedubbele turbo, "inkt" (beeld van anderen deels zwart maken),
  omgekeerde besturing.
- **❓ Bescherming na een treffer** – een paar seconden onkwetsbaar, zodat je
  niet twee keer na elkaar geraakt kunt worden?
- **❓ Bananen** – blijft een val de hele race liggen tot iemand erin rijdt,
  of verdwijnt hij na een tijd/ronde?
- **❓ Item bij de start** – krijgt iedereen al iets bij de eerste poort?
- **❓ Rondes en tracks** – meerdere tracks bewaren en kiezen in een menu?
- **❓ Moeilijkheid/handicap** – topsnelheid per speler instelbaar (kinderen
  vs. volwassenen)?
- **❓ Valsspeel-situaties** – wat als een auto omvalt of vastzit? Een
  "reset"-knop die je terugzet naar de vorige poort is in AR niet mogelijk;
  wel bv. een tijdstraf of het item kwijt.

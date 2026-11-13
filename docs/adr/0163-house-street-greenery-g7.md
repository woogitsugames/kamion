# ADR 0163 — zieleń ulic domów wg pomiarów G7 (korekta ADR 0154)

Status: PROPOSED na gałęzi `veg-0163` (2026-11-13, s16); nie scalone. Liczby w „Weryfikacja” zmierzone na świecie
zregenerowanym na tej gałęzi (build 3, baza `origin/main` ff9777e2d). Telefon: NIE mierzony (robi lider). Recenzja
`visual-critic` jeszcze wymagana (subagent nie uruchamia subagentów).
Źródła: `research/g7-street-greenery/README.md` (tabela „Parametry dla generatora”, dalej „G7 #n”), recenzja
`docs/reports/REVIEW-2026-11-13-s16-codex-0154.md`, ADR 0132 r4b, D51.

## Problem

ADR 0154 poszerzył (×1,2–1,35) i podniósł do 11,3–20,4 m korony 116 instancji biblioteki drzew w ogrodach. Prototypy
biblioteki (`make_trees.py`: klon v2, lipa v0, brzoza v1, sosna v1) to rzadkie kępy liści na gołym pniu — po
powiększeniu czytają się jak pinie. Te instancje mają `tier: high`, więc na Low (A16) nie były rysowane wcale; Low
dostało tylko 257 m żywopłotów. Pomiary G7 pokazują inny obraz ulic domów: 0 drzew w pasie drogowym, drzewa ogrodowe
5–8 m z koroną zaczynającą się nisko, dużo iglaków, żywopłoty z tui 2,0–2,5 m na 40 % posesji.

## Decyzja

1. **Drzewa ogrodowe liściaste są geometrią kitu posesji (`plot_kit`), nie instancjami biblioteki** — na wszystkich
   tierach. `plantings.garden_trees` buduje je z koron ortofoto (`plot_canopy.json`):
   - gatunek wg G7 #11 (klon 25 %, brzoza 20 %, lipa 15 %, jesion/robinia 15 %, owocowe 20 %, kasztanowiec 5 %;
     owocowe tylko wśród koron r < 2,3 m — WORKING_VALUE);
   - wysokość H = D / (szerokość korony na wysokość gatunku, G7 #13: lipa 0,50–0,60, klon 0,65–0,75, kasztanowiec
     0,60–0,80, jesion 0,70–0,80, brzoza 0,40–0,60; owocowe 0,75–0,90 WORKING_VALUE), sufit wg G7 #12 (lipa 24, klon 22,
     kasztanowiec 22, jesion 25, **brzoza 20**, owocowe 8 m), minimum 4 m;
   - baza korony 0,15 H, nie niżej niż 1,3 m (G7 #7; drzewo na otwartym gruncie przy ulicy 1,6 m — WORKING_VALUE);
   - pokrój (G7 #14) z trzech nowych kart całych koron w atlasie kitu (`plot_kit._crown_card`): `crown_ovoid` (lipa,
     jajowata zwarta, W/H 0,63), `crown_round` (klon, kasztanowiec, jesion; kulista zwarta, 0,71), `crown_birch`
     (wąska, otwarta, zwisające liście, jasny pień, 0,44). Karty zajęły miejsce parasola `tree_a` (10,5 × 5,9 m);
     `tree_a` wskazuje teraz na `crown_round` (ścieżka regułowa `plots.big_tree`, w tym regionie nieużywana);
   - wariant pełny (High, drzewa ≤ 12 m od frontu): pień, 3 skrzyżowane karty korony, ciemny rdzeń i 7 gałązek
     wewnątrz sylwetki (≤ 44 trójkąty); wariant lite (Low/Medium i drzewa w głębi): 2 paski pnia + 2–3 karty
     (8–10 trójkątów). Karta nie jest rozciągana bardziej niż 0,8–1,3× względem pokroju (`CARD_STRETCH`).
2. **Żadnych drzew w pasie drogowym ulic domów (G7 #1).** Korona, której środek ortofoto pokazuje przed płotem
   (≤ 6 m od posesji, ≤ 10 m od jezdni), to drzewo ogrodowe z koroną nad płotem: pień staje ≥ 1 m za płotem
   (`claim_street_crowns`, najbliższy dopuszczalny punkt, przesunięcie ≤ 7,5 m, odstęp pni ≥ 1,6 m). `plots.build`
   stawiał takie drzewa na trawniku przed płotem albo je pomijał (blisko jezdni, małe korony, iglaki). Przy domach bez
   wygenerowanej posesji pień stoi tam, gdzie korona, odsunięty ≥ 3 m od jezdni. Iglaste korony przed płotem stają się
   świerkami kitu (`plots.spruce`, G7 #8–10).
3. **Fronty posesji wg kwot G7 #15–18** (`plantings.plan_house_greenery`, kwoty zamiast losowania): 40 % posesji z
   frontem — żywopłot ≥ 1,2 m, z tego 70 % tuja; 25 % — pas niskich krzewów 0,5–1,2 m; reszta sam płot. Żywopłot z
   tui (`thuja_hedge`): 2,0–2,5 m, do 3,0 m na narożniku posesji, szerokość 0,8–1,2 m, 0,3–0,6 m za płotem (G7 #19),
   wiersz `thuja` atlasu rysowany 1 : 1 (ping-pong UV, bez zbrązowiałego odcinka), przekrój z zaokrąglonym grzbietem,
   wariant Low o rzadszych stacjach (≤ 4,6 trójkąta/m). Liściasty: istniejący `plots.hedge`, 1,2–1,5 m (G7 #20
   obcięte do progu „żywopłot ≥ 1,2 m”), szer. 0,5–0,8 m. Niskie i liściaste trafiają najpierw za płoty przezierne.
   Bramy, furtki, podjazdy, strefy drzwi i dom są wyłączone; nic poza posesją.
4. **Wszystko w istniejących grupach chunków** warstw `plots` / `plots_low` (materiał `plot_kit`): geometria, która
   otworzyłaby nową grupę (nowe wywołanie rysowania), nie powstaje (`_emit`, licznik `new_renderer_group`).
5. Instancje biblioteki, które zostają w ogrodach (ścieżka regułowa regionów bez ortofoto): `vegetation.garden_canopies`
   tylko przycina wysokość do sufitu G7 #12; nic nie poszerza ani nie podnosi. Pole `garden_canopy_width` importera
   zostaje obsługiwane, generator go nie emituje.
6. `297817` (duże drzewa z lewej): **bez zmiany świata**. Drzewa ze zdjęcia z 2017 r. stały tam, gdzie ortofoto 2024
   pokazuje nową jezdnię (droga przebudowana). Zadrzewienie za nimi jest w świecie (222 drzewa z BDOT w prostokącie
   E −335…−250, N −150…−60), ale względem osi tej pozy leży pod kątem −53…−82° przy polu widzenia ±21,8°.
7. Młode drzewka na palikach przy Andersa (G7 #24): **nie dodane** — gęstość ma status UNVERIFIED, a przy jezdni
   nie ma grupy kitu (nowe wywołania rysowania na kamerach trasy).

8. **Horyzont kadrów 303305 / 320215 / 454716 (z live p1-0161): wycinka w poligonie lasu BDOT `2BE4B432-6BC0`.**
   Poligon OT_PTLZ_A (BDOT: zadrzewienie, liściaste; 1203 drzewa generatora, E −113…311, N −713…−446) na ortofoto GUGiK 2024-05-27 jest na wschód od
   E ≈ 220 piaskownią: gołym piaskiem z trzema kępami drzew i pasem drzew wzdłuż krawędzi SW. Nowy rodzaj
   `authored_overrides` — `kind: forest_clearing` (`overrides.yaml`, `bdot-forest-6bc0-sand-clearing`, klucz = id BDOT,
   przeżywa reimport; brak celu → `forest_clearings.stale` w `streetscape_qa.json`): pierścienie `cleared_epsg2180`
   minus `keep_epsg2180` (kępy), odrysowane na ortofoto ±2 m (`artifacts/veg-0163/forest/ortho_clearing.jpg`).
   `vegetation.place` generuje drzewostan jak dotąd na pełnym obrysie BDOT i dopiero potem usuwa drzewa z wycinki —
   reszta lasu zachowuje każde drzewo (ten sam strumień losowy); HLOD lasu i maska dna lasu dostają obrys przycięty,
   wycinka dostaje maskę gołej ziemi (kanał A). Reszta zadrzewienia na zachód od E ≈ 220 zostaje — jest na ortofoto. Id BDOT
   w źródłach ma sufiks części (`…D140:0`); override wskazuje obiekt bez sufiksu i obejmuje wszystkie jego części.
9. **Klomb EC (`ec-access-plantings`, gałąź p1-0161, nie ta gałąź).** Ortofoto HR (`artifacts/p1-0161/td/hr_klomb.png`)
   i zdjęcie cm92458760 pokazują jedną zwartą masę niskich czerwonobrązowych krzewów, która wypełnia prawie całą
   soczewkę wyspy (~16 × 4,5 m), nie pas 1,2 m. `plantings.build` już obsługuje `band_m: 0` (pełny klomb) — do dopisania
   w `beds` EC1 przy scalaniu p1-0161 (tu nie zmieniane, żeby nie konfliktować).

Zmiany poza plikami roślinności (addytywne, bez planu zachowanie bez zmian): `plots.build` czyta `rp["front_green"]` /
`rp["garden_trees"]` (nie buduje własnego żywopłotu frontowego, zapisuje korony liściaste zamiast je meshować) i
`plots.big_tree` ogranicza wysokość karty; `stage.py` — trzy wywołania i flaga ablacji `KAMION_GARDENS_0163=0`
(zastępuje `KAMION_GARDENS_0154`). Shadery bez zmian (`WorldPlotKit` wystarcza).

## Weryfikacja

Generator (build 3, `streetscape_qa.json`; „przed” = `origin/main`):

| Pozycja | Przed (0154) | Po (0163) | G7 |
|---|---|---|---|
| Posesje z żywopłotem ≥ 1,2 m / z frontem | 0154: 19 + reguła 0132 | 35 / 92 = 38 % | 40 % (25–55) |
| … w tym tuja | 0 | 24 / 35 = 69 % | 70 % |
| Pas niskich krzewów | — | 23 / 92 = 25 % (182 krzewy) | 25 % (15–30) |
| Żywopłot tuja: długość, wys., szer. | — | 344 m, 2,0–2,5 m, 0,8–1,2 m | 2,0–2,5; 0,8–1,2 |
| Drzewa ogrodowe liściaste | 116 instancji `tier: high` + 193 drzewka kitu 3,2–5,6 m | 698 drzew kitu (klon 179, owocowe 158, brzoza 121, lipa 108, jesion 101, kasztanowiec 31) | mix #11 ±3 pp |
| Iglaki (świerki kitu) | 53 | 137 (16 % drzew) | 25 % (15–40) |
| Wysokość drzew: mediana (p10–p90) | instancje 11,3–20,4 m | 5,65 m (3,7–11,4); ≥ 12 m: 9 % | typowo 5–8 m |
| Baza korony / H: mediana, max | prototyp ~0,3–0,45 | 0,21; 0,37 | 0,15 H, min 1,3 m |
| Pnie przeniesione za płot | — | 269 | 0 drzew w pasie drogowym |
| Drzewa / 100 m osi, 7 ulic G7 (1329 m), ≤ 8 m | 2,7 | 7,8 | 9,9 (ortofoto) |
| … ≤ 12 m | 4,1 | 11,7 | 12,7 (ortofoto) |
| Trójkąty kitu posesji High / Low (region) | 59 155 / 48 172 (+3580 frontów 0154) | 80 k / 53 k | — |

Gęstość ≤ 8 m jest niższa niż na ortofoto, bo pnie stoją za płotami (4,3 m od osi + ≥ 1 m), a nie pod środkiem
korony: część koron pasa 8 m ma pnie w pasie 8–12 m. Pominięte korony: brak miejsca za płotem 19, za blisko innego
pnia 5, środek nad jezdnią 10, brak wolnego gruntu 11, nowa grupa rysowania 4, drzewo regionu ≤ 2,5 m 4.

Estymata kadru generatora (`mesh_budget`, wszystkie kamery): High max +0,87 % (`route_onramp_andersa`), najcięższy kadr
`stretch_04` 1 979 137 → 1 995 291 (< 2,0 M); Low max +0,03 %.

Rendery, budżet edytora, testy: patrz sekcja „Rendery i budżet” (uzupełniana po imporcie).

## Otwarte / WORKING_VALUE

- Proporcje gatunków (G7 #11), udział tui (#18), pokrycie frontu (#21), owocowe tylko r < 2,3 m, baza korony 1,6 m na
  otwartym gruncie, `STREET_REACH_M` 10 m, `MOVE_MAX_M` 7,5 m — WORKING_VALUE; pozycje żywopłotów to reguła, nie
  inwentaryzacja (OSM nie ma `barrier=hedge` w kaflu).
- Prototypy biblioteki drzew (`make_trees.py`: korony-kępy na gołym pniu) zostają dla lasów i drzew przydrożnych —
  poza zakresem tego ADR; to one są źródłem „pinii”.
- Kit nie ma wiatru (`WorldPlotKit`); drzewa ogrodowe są statyczne jak reszta zieleni posesji.
- **P10 (`research/_incoming/p10-street-greenery-2`, przegląd `docs/reports/REVIEW-2026-11-13-s16-research-pack-02.md` §5):
  WORKING_VALUE, nie cel generatora.** Pokrycie osi ulic domów (próbki co 5 m, ≥ 1 korona ≤ 8 m) przeliczone
  niezależnie na naszej detekcji koron (`plot_canopy.json`, r ≥ 0,7 m; `artifacts/veg-0163/p10_coverage.py`, 12 ulic,
  3290 m osi): 61 % = średnia P10 61 % (na odcinkach liczby P10 są niereprodukowalne — nie używamy ich per odcinek).
  Same drzewa (r ≥ 1,25 m): ortofoto 51 %, gra (pnie drzew ogrodowych + iglaków) 38 % — pnie stoją za płotami, korony
  nie są przesunięte nad chodnik, żywopłotów metryka nie liczy. Otwarte: asymetryczna korona nad płotem.
- Młode drzewa Al. Tysiąclecia (P10-301…313, średnio ~5 / 100 m, 74 drzewa Strabag) i mieszanka przydrożna Andersa
  (Łaska 2015: klon jesionolistny, klon zwyczajny, głóg) — poza zakresem (drzewa przydrożne biblioteki, nie ulice domów);
  otwarte dla zadania drzew przydrożnych.
- Telefon (A16 Low): nie mierzony.

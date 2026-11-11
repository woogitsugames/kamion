# ADR 0077: Wysepki tylko tam, gdzie pokazują je OSM lub ortofoto; reszta szczelin między jezdniami to nawierzchnia

Status: przyjęty (world-builder, islands-r10), 2026-11-10. Powiązane: ADR 0074 (spójność nawierzchni), ADR 0075
(miara fidelity), ADR 0076 (równolegle: korytarz trasy, krawężniki niebędące wysepkami, latarnie).
Zgłoszenia właściciela: `artifacts/owner/bugs/2026-11-10-lane-into-island.webp`, nagranie 2026-11-10 („krawężniki są
w niektórych miejscach na środku drogi”, „malowana wysepka = sama farba”), wymaganie „drogi dosłownie jak w OSM”.

## Kontekst
Generator buduje jedną taśmę na każdą jezdnię OSM i łatę na każde skrzyżowanie. Wszystko, co zostawało między dwiema
taśmami, stawało się wysepką „z definicji”: krawężniki po obu stronach i teren/trawa w środku — także tam, gdzie OSM
tylko rysuje dwie osie zbiegające się w węźle (klin włączenia łącznicy, pas do skrętu w prawo narysowany osobną drogą,
powierzchnie wyłączone P-21). W terenie te miejsca są asfaltem albo samą farbą. OSM w kaflu nie ma żadnego obiektu
`area:highway` / `traffic_island`, więc sam OSM nie rozstrzyga; rozstrzyga ortofoto GUGiK (0,08 m WMS / 0,25 m arkusz).

Pomiar wyjściowy (ADR 0075, main ffcc7b7): 4 wysepki generatora bez pokrycia na ortofoto przy trasie, 3 pasy w wysepkę,
18 „brakujących” wysepek, krawędź p95 2,04 m. Każdy przypadek obejrzany na ortofoto 0,08 m
(`artifacts/islands-r10/before/*.jpg`):
- 2 z 3 „pas → wysepka” (wlot ronda Bieżeństwa, w188397875) były błędem miary: na wprost od wlotu ronda zawsze jest
  wyspa środkowa. Wysepka 570,7 / −688,2 istnieje naprawdę (brukowana wysepka rozdzielająca), klasyfikator koloru
  bierze bruk za asfalt; to samo z pierścieniem ronda (opaska z kostki).
- „18 brakujących” to głównie auta, autobusy, cienie i chodniki (udział zieleni 0). Realne różnice: nos mediany przy
  bramie Kwadrat Park jest dłuższy, mediana Andersa szersza (jezdnie generatora za szerokie), nosy mediany przy wyjeździe
  straży dłuższe o ~3,5 i ~6 m.
- Prawdziwie fałszywe wysepki: klin łącznica / Andersa (E −84 N −342, 101 m²), skrzyżowanie łącznic przy s 610
  (E 348 N −540 436 m², E 337 N −574 191 m² i cztery narożne resztki — na ortofoto pola P-21 i ciągły asfalt), północne
  ramię Ronda Putry (E −575 N 107, 235 m²).

## Decyzja
1. Nowy etap generatora `tools/worldgen/roads/gores.py` (po skrzyżowaniach i profilach, przed siatkami; nie zmienia
   `junctions.compute_corners` ani `network.align_forks`, które równolegle zmienia ADR 0076). Reguła:
   szczelina między jezdniami jest wysepką tylko, gdy wskazują ją dane —
   - OSM: oddzielne jezdnie jednokierunkowe z realną przerwą (mediana ≥ 2,0 m), środek ronda, obszary
     `area:highway=traffic_island` (brak w kaflu),
   - ortofoto: `kind: traffic_island` w `overrides.yaml` (poligon, wysepka z krawężnikiem położona na jezdni);
   pozostałe szczeliny są nawierzchnią:
   - wąskie kliny i paski: część szczeliny, w której nie mieści się wysepka 2,0 m (`GORE_MIN_ISLAND_W`), o długości
     ≤ 60 m (dłuższy wąski pas to mediana z barierą — zostaje),
   - kliny włączeń / rozwidleń: między dwiema jezdniami jednokierunkowymi biegnącymi w TĘ SAMĄ stronę nos wysepki
     zaczyna się dopiero przy 4,0 m prześwitu (`GORE_MIN_NOSE_W`), do 90 m długości; mediany (kierunki przeciwne)
     nie są ruszane,
   - zamknięte „dziury” < 5 m²,
   - `kind: paved_gore` w `overrides.yaml` (punkt `at_en` + `radius_m` + `close_m`, uzasadnienie i ortofoto): miejsca,
     które ortofoto pokazuje jako ciągły asfalt; `hatch: true` = powierzchnia wyłączona P-21 jako SAMA FARBA
     (ramka 0,24 m + ukośne pasy 0,5 / 1,0 m pod 45°, warstwa decali `markings`), bez krawężnika i bez kolizji.
   Wszystkie progi to `WORKING_VALUE` (do weryfikacji z WR-D / zdjęciami).
2. Wypełnienie: krawężniki taśm i narożników łat zwrócone do szczeliny chowają się 6 cm pod nawierzchnię (ten sam
   mechanizm co przy stykających się jezdniach), a szczelinę zamyka siatka asfaltu (triangulacja z ograniczeniami)
   z wysokościami odczytanymi z wygenerowanej nawierzchni sąsiadów; wersja wizualna 4 mm niżej i 6 cm pod sąsiadami
   (bez szpar i z-fightingu), wersja kolizyjna dokładnie w poziomie. Szczelina nie jest wypełniana, gdy jezdnie leżą
   na różnych wysokościach (krawędź wypełnienia stromsza niż 10 % + 0,15 m; dla override 0,35 m) — to mury ramp.
3. Miara (ADR 0075) poprawiona tam, gdzie kłamała: wloty rond nie są „pasem w wysepkę”; rozdzielenia dostają werdykty
   `roundabout_centre` (wewnątrz pierścienia) i `outline_notch` (wklęsłość obrysu domknięta 7-metrowym zamknięciem,
   jezdnia tylko z jednej strony) zamiast `absent_on_ortho`. Narzędzia: `fidelity/zoom.py` (nakładka w dowolnym
   miejscu), `fidelity/summary.py`, `fidelity/edge_sides.py` (odchyłka krawędzi osobno dla lewej i prawej strony).
4. Krawędzie jezdni: patrz „Wynik”.

## Wynik
Pomiar: `tools/worldgen/fidelity/run.py`, trasa startowa, ortofoto GUGiK 0,08 m; „przed" = ten sam kod z
`WORLDGEN_NO_GORES=1` i bez override (`artifacts/islands-r10/fidelity_before_qa.json`), „po" = 2026-11-11
(`Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json`, nakładki `artifacts/islands-r10/after5/*.jpg`,
`artifacts/islands-r10/fidelity/overlays/`).

| miara (trasa) | przed | po | cel właściciela |
|---|---|---|---|
| wysepki generatora bez pokrycia na ortofoto | 4 | **1** | 0 |
| pas wjeżdżający w wysepkę (błąd generatora) | 0 (3 wg starej miary) | 0 | 0 |
| krawędź jezdni vs ortofoto p50 / p95 (n) | 0,76 / 2,48 m (618) | **0,46** / 2,52 m (616) | p95 ≤ 0,75 — NIE |
| krawędź, wszystkie strony p50 / p95 | 0,70 / 4,25 m | 0,50 / 4,12 m | — |
| oś vs OSM p95 / max | 0,129 / 3,25 m | 0,13 / 3,25 m | ≤ 1,0 — tak |
| IoU jezdni, średnia z 11 okien | 0,723 | 0,731 | — |
| spójność dróg (kafel): obstacle_in_lane / marking_off_carriageway | 58 / 17 | 27 / 13 | 0 |
| strome ścianki terenu > 0,15 m (kafel; steep_grass) | 9 (4) | 9 (4) | 0 |

- Wypełnienia: 34 (10 z override 1083 m², w tym klin s 1060 bez P-21; 5 klinów włączeń 181 m², 4 z P-21; 19 pasków
  116 m²), 12 odrzuconych (różne
  wysokości jezdni), krawężnik schowany na 725 m.
- Jedyna pozostała „wysepka bez pokrycia" na trasie: E −366 N −119 (373 m², s ≈ 1440) — na ortofoto P-21 + bariera;
  to korytarz ADR 0076 (s 1432–1480), tu nie ruszany.
- s 610 (j:n1882887385): pola P-21 jako sama farba, bez krawężnika; środkowy trójkąt 32 m² został dopiero po poprawce
  `carriageway_union` (samoprzecinający się obrys łaty: `buffer(0)` liczył dziurę siatki jako jezdnię, więc override był
  „stale"; teraz te same płaty `make_valid`, co w `meshing._repair_fill`).
- MA-010 (Rondo Putry, pierścień S): oś OSM w180144451 biegnie po południowym krawężniku. Override
  `set: {center_offset: 2.9}` (nowy klucz, `network.prepare_chain`, wygładzenie 20 m) — jezdnia leży na jezdni z ortofoto,
  prawy pas nie leży już na trawniku (`after5/ma010.jpg`). 7 dalszych odcinków trasy dostało `center_offset`
  0,5–0,95 m z `fidelity/edge_sides.py` (mediany lewej / prawej krawędzi, n w uzasadnieniu każdego wpisu), łącznica
  w177861600 szerokość 7,5 m. Stąd p50 krawędzi 0,76 → 0,46 m.
- Dlaczego p95 krawędzi nie spadło: ogon to miejscowe poszerzenia, których generator nie buduje (jedna szerokość na
  odcinek OSM). Mediany stron z potwierdzoną krawędzią trawnika po zmianach: w188397874 L +2,32 m (n 14), w177861600
  R +2,36 (18), w1093579590 R +1,96 (11; +1,92 na 62 stacjach = dodatkowy pas), w266084693:12620261934 R +1,96 (5),
  w606396463 L −1,98 / R +3,72 (12 / 6, korytarz 0076), w173956083 p95 5,12 (rozwidlenie), w249640399:131612943
  L −1,06 (20). Naprawa = zmienna szerokość / pasy dodatkowe wzdłuż odcinka, nie kolejne override szerokości.
- Ratchet: `tests/gis/test_road_fidelity.py` BASELINE odświeżony na pomiarze (oś 0,13, krawędź 2,52, wysepki 1, błąd
  pasa 0) — poprzedni (0,032 / 2,04 / 4 / 3) pochodził z raportu sprzed scalenia ADR 0074 i był nie do odtworzenia na
  main. `tests/gis/test_gores.py`: każdy planowany klin zbudowany, override zastosowane, P-21 = tylko farba.

## Konsekwencje
- Nowa kategoria `authored_overrides` (`paved_gore`, `traffic_island`) — przeżywa reimport, nieaktualny cel trafia do
  `roads_qa.json → overrides_stale`. Raport etapu: `roads_qa.json → summary.gores` (lista wypełnień, odrzucone z powodem).
- Farba P-21 jest generowana tylko z override (ortofoto); układ pasów to WORKING_VALUE.
- Otwarte: (1) Krawędź p95 2,52 m (cel 0,75) — wymaga zmiennej szerokości jezdni / pasów dodatkowych (lista wyżej).
  (2) Wysepka P-21 przy s 1440 (E −366 N −119) i E −395 N −132 — po scaleniu ADR 0076. (3) ZAMKNIĘTE 2026-11-11: strome ścianki trawy 0,5–0,7 m na końcach wypełnień (E 786 N −831, E 321 N −603,
  E 48 N −460; steep_grass 4 → 16). Przyczyna: pas pobocza RURAL pożycza stację graniczną od sąsiedniego pasa URBAN
  (`meshing.build_side_strip`); przy klinie niosła ona h = −0,06 (schowany krawężnik), co `side_profile` czyta jako
  „rów domyślny 0,6 m", więc rów 0,2 m skakał do 0,6 m na jednej stacji (2 m). Teraz przy `gore_flush` pożyczona
  stacja kontynuuje wysokość własnego pasa: steep_grass 16 → 4, ścianki 21 → 9 (poziom bazy), obstacle_in_lane 27.
  (4) Skrajnia pod wiaduktem Putry: pierścień przesunięty
  o 2,9 m leży pod pomostem na 113 zamiast 81 stacjach, margines −0,154 m względem wymagania z zapasem 0,30 m
  (prześwit 4,65 m ≥ 4,50 m PTB2022 § 80); wyjątek z uzasadnieniem w `test_grade_separation_clearance`. (5) Latarnia
  lamp_12m na pomoście wiaduktu Bieżeństwa (E 525,3 N −711,5): w bazie ta sama reguła stawiała ją 4,8 m dalej i
  `props_off_carriageway` ją usuwał; logika w `streetscape/furniture.py` (ADR 0076). (6) Układ pasów P-21 i progi
  2,0 / 4,0 / 60 / 90 m = WORKING_VALUE. (7) 16 „brakujących" wysepek z ortofoto: głównie pojazdy / cienie; realne
  dłuższe nosy median (brama Kwadrat Park E 619 N −599, wyjazd straży) nie zrobione.
  (8) Farba P-21 z reguły klinów włączeń (≥ 12 m², bez override) nie jest sprawdzona na ortofoto dla E 773 N −847,
  E 792 N −836, E 313 N −597, E −228 N −1006; przy s 1060 (E −84 N −343) reguła malowała drabinkę 127 m² tam, gdzie
  ortofoto pokazuje jedną linię ciągłą — poprawione override `gore-andersa-merge-s1060-plain`.

## Kontrola wizualna (2026-11-11, WorldC, Medium, overcast)
13 kamer (`artifacts/islands-r10/renders/`, lista w `artifacts/islands-r10/cameras.json`) obejrzanych z
`after5/*_ortho.jpg`: s 610 — pola P-21 jako sama farba, bez krawężników na środku jezdni (układ pasów farby
przybliżony, 3 pola zamiast układu z ortofoto, brak separatorów U-25); włączenie s 1060 — po rundzie 2 jedna linia
ciągła jak na ortofoto; MA-010 — pierścień pod krawędzią wiaduktu, bez trawy w pasie; Putry N — jedna powierzchnia
asfaltu w miejscu dawnej wysepki. Nie oceniane przez `visual-critic` (agent bez prawa tworzenia subagentów) — dla lidera.


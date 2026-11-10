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
WYNIK_TBD

## Konsekwencje
- Nowa kategoria `authored_overrides` (`paved_gore`, `traffic_island`) — przeżywa reimport, nieaktualny cel trafia do
  `roads_qa.json → overrides_stale`. Raport etapu: `roads_qa.json → summary.gores` (lista wypełnień, odrzucone z powodem).
- Farba P-21 jest generowana tylko z override (ortofoto); układ pasów to WORKING_VALUE.
- Otwarte: OTWARTE_TBD

# ADR 0347 — Skrajnia jezdni dla drzew liczona z zmierzonej siatki biblioteki (tree-clearance-s24)

Status: Proposed, 2026-11-25 (agent tree-clearance-s24). Zastępuje §4 ADR 0308 (promienie nominalne).
Powiązane: ADR 0222 (szpalery DK65, `MIN_TRUNK_EDGE_M` 3,0 m), 0308 (korony z płatów), 0163 (drzewa ogrodowe), krytyk build #8
(`artifacts/critic-s24-build8/CRITIC.md`, P0 #3, klatka t=2260).

## Kontekst
Krytyk build #8: na t=2260 korona przydrożnego drzewa wchodzi w kabinę i zasłania prawą ćwiartkę szyby. Pozycja z `player.log`
(`[NAV]`, t nagrania = t logu − 9,65 s wg `sync.json`): kafel `knyszyn-w`, tuż przed szwem do `dw671-tykocin-01`, ciężarówka
~ (558; 1019) w układzie `dw671-tykocin-01` (północna krawędź), kurs 231°, 47 km/h.

ADR 0308 §4 miał już przebieg `road_clearance`, ale liczył zasięg korony z jednej liczby na gatunek (`CROWN_FORM`, „promień/H”).
Pomiar siatek `art-source/world/vegetation/trees.glb` pokazał, że korony są o 25–35 % szersze niż założono:

| gatunek | r_max/H zmierzone | r/H w `CROWN_FORM` | podstawa liści zmierzona |
|---|---|---|---|
| lipa | 0,42–0,46 | 0,33 | 1,6–2,3 m (nie 0,17 H) |
| klon | 0,46–0,50 | 0,375 | 1,3–1,7 m |
| brzoza | 0,29–0,31 | 0,235 | 3,1–3,5 m |
| olsza | 0,32–0,35 | 0,24 | 2,3–2,6 m |
| topola | 0,28–0,29 | 0,195 | ~4,8–5,1 m |

Do tego dopuszczalne „0,3 m nad krawędzią jezdni” oznaczało liście 1–2 m od burty kabiny (kamera kierowcy) — ciężarówka jedzie przy
linii krawędziowej, lusterka wystają 0,25 m. Krótkie drzewa (6 m, skala ~0,5) przy ulicy z chodnikiem przechodziły test, bo
test znał tylko „k·h”, a nie siatkę.

## Decyzja
1. **Zasięg z siatki** (`streetscape/tree_crown_profile.py` + `tree_crown_profile.json`): dla każdego prototypu `r_cum[k]` = największa
   odległość od osi pnia wierzchołka o wysokości < (k+1)·0,25 m. `low_radius(proto, skala, 4,7 m)` uwzględnia skalę instancji
   (`h / href_m`) i zagłębienie podstawy 0,15 m (InstanceImporter). Tabela jest generowana z GLB (`--write`), test pilnuje
   aktualności (sha256 GLB + meta). Gatunki bez siatki (wierzba) zostają przy `CROWN_FORM`; `tree_floor` (pokrywa gruntu) jest pomijany.
2. **Reguła** (`vegetation.road_clearance`, `WORKING_VALUE`): od wysokości 0 do `CLEAR_H_M` = 4,7 m (skrajnia 4,50 m wg rozp. MI z
   24.06.2022, Dz.U. 2022 poz. 1518, § 80 ust. 1 pkt 2, + 0,2 m zapasu; § 113 ust. 2 pkt 2 — zarządca usuwa ingerencję roślinności
   w skrajnię) żadna część drzewa (pień ani liść; wszystkie azymuty) nie może być bliżej niż `CLEAR_EDGE_MARGIN_M` = 1,5 m od
   krawędzi jezdni (asfalt, `road_footprint_polygon`; `WORKING_VALUE`: ciężarówka jedzie ~0,5 m od linii krawędziowej pasa 3,5 m, korpus
   2,55 m, lusterka +0,25 m, więc 1,5 m zostawia liście ~0,75 m od lusterka). Pierwsza wersja z marginesem 0,5 m zostawiała w klatce kabiny
   lipę 6 m stojącą 3,3 m od krawędzi (liście dokładnie 0,5 m od asfaltu) i nadal wypełniała prawą ćwiartkę szyby — render kabiny
   `cab-after-margin0p5`, odrzucony. Pień ≥ 3,0 m od krawędzi (§ 53 ust. 3 rozp. MTiGM, Dz.U. 2016 poz. 124)
   zostaje regułą szpalerów ADR 0222 — tu dochodzi korona.
3. **Naprawa w kolejności** (deterministycznie, ta sama lista kolejnością): (a) przesunięcie od jezdni po normalnej ≤ 1,2 m, tylko na
   komórkę niezablokowaną (maska `blocked` etapu: jezdnie, chodniki, budynki); (b) zmniejszenie wysokości do ≥ 75 % (krok 2 %);
   (c) przesunięcie ≤ 1,2 m (albo 0,6 m) + zmniejszenie do ≥ 60 %; (d) usunięcie. „Przycięcie od strony drogi” (podcięcie korony
   w siatce) nie jest możliwe na współdzielonym prototypie bez nowych wariantów w Blenderze — zostaje jako ewentualna przyszła praca.
4. **Dowód na końcu etapu**: `report["road_clearance"]["violations_after"]` (ma być 0), plus `road_carriage.wkt` (prosty obrys jezdni,
   `Data/raw/derived/<id>/world/`) dla testu regresji korytarza.

## Wynik (przebudowane kafle, margines 1,5 m)
Naruszenia skrajni 4,7 m / 1,5 m w instancjach przed (main) → po: `knyszyn-w` 122 → 0 (najgorsze wejście w margines 3,28 m),
`dw671-tykocin-01` 213 → 0 (3,37 m), `dk65-05` (aleja, 101 894 drzew) 330 → 0 (3,31 m). Zmiany generatora (`road_clearance`):
knyszyn-w 126 z 12 412 sprawdzonych (53 przesuniętych, 8 zmniejszonych, 30 przesuniętych i zmniejszonych, 35 usuniętych),
dw671-tykocin-01 220 z 10 816 (83/14/92/31), dk65-05 344 z 80 962 (177/17/84/66). Poza tymi instancjami zbiór jest bit-w-bit ten sam
(`only_before` 125/217/339 vs zmiany 126/220/344: różnica to przesunięcia o < 1 cm) — zmiana jest lokalna, nic nie zostało
przelosowane. Liczby: `artifacts/tree-clearance-s24/violations_before_after.json`. Render kabiny z miejsca klatki t=2260
(start trasy kafla dw671-tykocin-01, `startS` 90 m, kamera `cab-view-b-fov70`): `artifacts/tree-clearance-s24/sbs-cab-seam-final.jpg`
(przed | po) — korona po prawej cofnięta od krawędzi jezdni, prawa ćwiartka szyby otwarta.

## Testy
`tests/gis/test_trees_0347.py`: tabela = GLB; zmierzony zasięg > nominalny × 1,15 (przyczyna); drzewo daleko bez zmian; przesunięcie,
odmowa przesunięcia (maska) → zmniejszenie / usunięcie; drzewo na asfalcie usunięte; sosna (liście od ~5 m) liczy się pniem;
deterministyczność; gatunek bez siatki; **korytarz C → Tykocin** (28 kafli z `nav_trips.json`): żadna instancja `tree_*` nie wchodzi
w graniastosłup „jezdnia + 1,5 m, 0–4,7 m” (kafel bez `road_carriage.wkt` = skip do przebudowy).

## Do przebudowy (kafle korytarza, lista dla lidera)
Wszystkie kafle korytarza `tykocin` (trip `tykocin` w `nav_trips.json`), pilnie `knyszyn-w`, `dw671-tykocin-01` (miejsce klatki t=2260),
szpalery DK65 `dk65-01…11`; reszta przy najbliższej regeneracji (generator nie zmienia nic poza instancjami drzew).

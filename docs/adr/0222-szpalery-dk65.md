# ADR 0222 — szpalery drzew wzdłuż DK65 i dróg dojazdowych do Knyszyna (reguła `tree_rows`, opt-in per kafel)
Status: Proposed (agent chmurowy D1, s21, gałąź `treerows-0222`), 2026-11-15. Do scalenia przez lidera po przebudowie
kafli i visual-qa.
Powiązane: D64/D65 (`docs/11`), research K1 `research/dk65-knyszyn-refs/README.md` (g) + `manifest.csv` K1-132…134,
ADR 0012 (instancje/LOD drzew), 0015 (forest HLOD: szpaler ≤ 12 m od drogi nigdy nie jest zastępowany), 0069
(`tree_groups`), 0133 (`lamp_rows.json` — autorskie rzędy w osobnym pliku), 0173 (determinizm strumieni losowych),
0205/0207/0214 (kafle korytarza).

## Kontekst
Właściciel prowadzi trasę Białystok → Knyszyn starą DK65 (D64, D65 p.1). K1 (ortofoto GUGiK 2025-05-25, 0,1 m) widzi
szpalery: Ełcka km ~11,7 (jednostronny W, ~20–25 m rozstawu, 8–12 m od krawędzi), km ~14,6 (W ~15 m, 5–10 m; E pojedyncze),
DK65 km ~20,5 (grupa ~8 drzew przy zatoce). Gatunki: brak źródła (K1: UNVERIFIED).

### Stan dziś (pomiar z danych w gicie, `generated/streetscape_sources.json`, `roads.graph.json`)
`vegetation.place` (main): BDOT10k `OT_OIPR_L` „rząd drzew” → drzewo co **8 m** od 2 m, jeden gatunek na linię (lipa
albo klon), bez wiedzy o drodze poza siatką `blocked` (jezdnie/place/budynki + 3 m dylatacji); OSM `natural=tree`
(punkty) → 1 drzewo; **OSM `natural=tree_row` (linie) jest pobierany do `streetscape_sources.json`, ale ignorowany**.
Brak cięć przy skrzyżowaniach/zjazdach. OSM w snapshocie Geofabrik 261108 = OSM na żywo (sonda API 0.6, 2026-11-15,
`Data/Regions/<id>/tree_rows_osm.json`, ODbL): prawie pusto.

| kafel | BDOT rząd drzew n / m | OSM tree_row n / m | OSM tree | dziś: kandydaci 8 m / szac. poza jezdnią¹ | OSM tree w wyjściu¹ | 0222: linie / m | 0222: drzewa | z ortofoto K1 | cięcia widoczności | przesunięte do 3 m | stara reguła na tych liniach¹ | delta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dk65-01 | 23 / 2141 | 0 / 0 | 0 | 272 / 209 | 0 | 1 / 163 | 9 | 0 | 0 | 0 | 21 | −12 |
| dk65-02 | 26 / 2570 | 0 / 0 | 0 | 329 / 322 | 0 | 7 / 1065 | 60 | 4 | 0 | 2 | 114 | −54 |
| dk65-03 | 20 / 2095 | 0 / 0 | 0 | 267 / 257 | 0 | 2 / 322 | 19 | 0 | 0 | 0 | 41 | −22 |
| dk65-04 | 26 / 2762 | 0 / 0 | 0 | 353 / 341 | 0 | 7 / 1038 | 60 | 0 | 0 | 1 | 129 | −69 |
| dk65-05 | 31 / 3061 | 0 / 0 | 0 | 389 / 364 | 0 | 10 / 1027 | 53 | 10 | 4 | 0 | 90 | −37 |
| dk65-06 | 18 / 1634 | 0 / 0 | 24 | 208 / 189 | 11 | 1 / 48 | 3 | 0 | 0 | 0 | 6 | −3 |
| dk65-07 | 13 / 1046 | 0 / 0 | 0 | 135 / 116 | 0 | 5 / 365 | 19 | 0 | 2 | 3 | 39 | −20 |
| dk65-08 | 8 / 699 | 0 / 0 | 0 | 89 / 89 | 0 | 6 / 517 | 33 | 0 | 0 | 0 | 65 | −32 |
| dk65-09 | 11 / 901 | 0 / 0 | 0 | 116 / 116 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dk65-10 | 5 / 476 | 0 / 0 | 0 | 61 / 61 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dk65-11 | 3 / 462 | 0 / 0 | 0 | 59 / 59 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| knyszyn | 32 / 3798 | 1 / 74 | 66 | 482 / 450 | 64 | 3 / 164 | 10 | 0 | 1 | 0 | 12 | −2² |
| knyszyn-s | 9 / 955 | 0 / 0 | 0 | 121 / 121 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| knyszyn-w | 21 / 2047 | 3 / 601 | 2 | 262 / 246 | 1 | 13 / 1813 | 105 | 0 | 0 | 1 | 154 | −49² |

¹ ESTIMATED: bez NMT/rastra `blocked` (Data/raw) — „poza jezdnią” = > 4 m od krawędzi jezdni z grafu (połowa `width` +
~1 m pobocza + 3 m dylatacji jak `stage.py`). Dokładne liczby po `build_world`: `streetscape_qa.json` →
`vegetation.tree_rows.{planned,placed}`. ² w tym nowe drzewa z OSM `tree_row` (knyszyn 4, knyszyn-w 32), których stara
reguła nie stawiała. dk65-09…11 i knyszyn-s: rzędy BDOT leżą > 40 m od dróg głównych (pola/las) — bez zmian.

## Decyzja

### 1. Przepisy (tekst sprawdzony 2026-11-15)
- **Obowiązujące: rozporządzenie MI z 24.06.2022 w sprawie przepisów techniczno-budowlanych dotyczących dróg
  publicznych, Dz.U. 2022 poz. 1518** (PDF `api.sejm.gov.pl/eli/acts/DU/2022/1518/text.pdf`, sha256
  `fe1380ff…2da9c5`). **Nie podaje liczb** dla drzew ani pól widoczności:
  § 26 ust. 1 — droga > 50 km/h „powinna mieć strefę bez przeszkód”, ust. 2 — szerokość „w taki sposób, aby uwzględnić
  prędkość dopuszczalną na drodze, SDRR i zagospodarowanie otoczenia”; § 81 ust. 1 pkt 2 lit. a–b (skrzyżowanie: wolne
  pole widoczności przy zbliżaniu się i „przy ruszaniu z miejsca zatrzymania na wlocie drogi z obowiązkiem ustąpienia
  pierwszeństwa”), pkt 6 lit. b (zjazd: wolne pole przy ruszaniu), pkt 9 (przejazd kolejowo-drogowy); § 82 ust. 4 —
  „Przeszkodami w polu widoczności nie są pojedyncze drzewa […] jeżeli zostało to potwierdzone analizą widoczności”;
  § 80 ust. 1 pkt 2 — skrajnia jezdni GP/G/Z/L/D 4,50 m; § 113 ust. 2 pkt 2 — zarządca utrzymuje roślinność tak, by
  nie było „ingerencji w skrajnię lub ograniczania widoczności”.
- **Liczby: rozporządzenie MTiGM z 2.03.1999 (t.j. Dz.U. 2016 poz. 124; uchylone 21.09.2022)** — PDF
  `api.sejm.gov.pl/eli/acts/DU/2016/124/text.pdf` (sha256 `c83b35b8…5b410b1`). Istniejące szpalery DK65 rosły i były utrzymywane pod tym aktem:
  - **§ 53 ust. 3**: „Odległość pnia drzewa od krawędzi jezdni nie powinna być mniejsza niż 3,0 m, a w wypadku
    przebudowy albo remontu drogi dopuszcza się mniejszą odległość” → `MIN_TRUNK_EDGE_M = 3,0`.
  - **Zał. 3 ust. 5** (ruszanie z miejsca zatrzymania na wlocie drogi podporządkowanej **oraz przy wjeżdżaniu ze
    zjazdu**): punkt obserwacji „w odległości nie mniejszej niż 3,0 m od krawędzi jezdni”, widoczność na odległość L2:
    100→180, 90→160, 80→120, 70→100, 60→90, 50→70, 40→60, 30→40 m.
  - **Zał. 3 ust. 4.1** (zbliżanie się drogą podporządkowaną, poza terenem zabudowy): punkt 20 m (droga podp. GP/G)
    albo 10 m (Z/L/D) od krawędzi jezdni, L1: 100→210, 90→180, 80→160, 70→140, 60→120, 50→100, 40→80, 30→60 m.
  - Zał. 3 ust. 3.2: „Nie są przeszkodami […] pnie pojedynczych drzew” (jak § 82 ust. 4 z 2022).
- **WR-D-22-1** (Wytyczne projektowania odcinków dróg zamiejskich cz. 1; **wersja projektu do konsultacji 2025-07**
  z `map.piib.org.pl/uploads/files/686fe7e172413_WR-D-22-1-02-2025.07_07_do_konsultacji.pdf`, sha256 `0ee57e23…db875e`; wersji obowiązującej z gov.pl nie dało się pobrać — reset proxy) rozdz. 11.2 ust. 1 lit. a:
  drzewa o obwodzie > 0,20 m są przeszkodą w strefie bez przeszkód; tab. 11.4.1: LSBP0 „dopuszczalna na drogach
  istniejących” 80–90 km/h: 3,0 / 4,0 / 5,0 / 7,0 m dla SDRR < 2000 / 2–5 tys. / 5–10 tys. / > 10 tys.; tab. 10.1.1.1
  (Lz na płaskim: 90 km/h 142 m). Używane **tylko w raporcie** (`in_lsbp0_existing`): odtwarzamy istniejące drzewa,
  nie projektujemy nowej drogi. SDRR DK65 w repo brak → klasa „5000–10000” `UNVERIFIED`.

### 2. Dane: osobny plik kafla `Data/Regions/<id>/tree_rows.yaml` (+ `kind: tree_rows` w overrides.yaml)
Wpis jak `tree_groups`/`tree_stand` (`id`, `reason`, `confidence`, `verify`, parametry, `lines: [{line_epsg2180, …}]`),
ale w osobnym pliku jak `lamp_rows.json` (ADR 0133): (a) obecność pliku = opt-in kafla, czytelny w jednym miejscu;
(b) `overrides.yaml` kafli dk65-02…05 zmienia równolegle PR #80 (dopisy na końcu → konflikty); (c) przeżywa reimport
(dane autorskie, nie `generated/`). `streetscape.tree_rows.load_entries` przyjmuje też wpis `kind: tree_rows`
w overrides.yaml. Sonda OSM: `tools/worldgen/streetscape/tree_rows_probe.py` → `tree_rows_osm.json` (źródło, data,
licencja w pliku). Opt-in: 14 kafli korytarza; **C, Dojlidy i pozostałe regiony bez zmian** (test).

Parametry (WORKING_VALUE, poza przepisami): rozstaw 12–18 m (domyślny), linie z ortofoto K1: km 11,7 20–25 m,
km 14,6 W 13–17 m / E 18–30 m (`missing_share` 0,30); braki w rzędzie 12 %; rozrzut poprzeczny σ 0,5 m; mieszanka
klon 0,35 / lipa 0,30 / brzoza 0,20 / olsza 0,15 z gatunkiem dominującym 70 % na rząd (**UNVERIFIED**, K1 bez źródła);
wysokość 11–19 m; wylot drogi polnej (OSM `highway=track`, poza grafem) — bez drzew 3 m od osi na 25 m od drogi;
przepust (OSM `tunnel=culvert`) — 5 m na 25 m od drogi (WR-D-22-1 11.2 ust. 1 lit. j: ścianki przepustów są przeszkodą);
przejazd kolejowy — 20 m (§ 81 ust. 1 pkt 9 bez liczby; na trasie A brak przejazdów, K1 (g)).

### 3. Generator `tools/worldgen/streetscape/tree_rows.py`
- Linie: BDOT „rząd drzew” + OSM `tree_row` (snapshot + sonda, bez duplikatów) + linie autorskie, przycięte do bbox
  kafla (szew: każdy kafel swoją część). Przejmowane tylko linie o średniej odległości ≤ 40 m od osi drogi głównej
  (`primary/secondary/tertiary`); linia autorska zastępuje linię BDOT/OSM ≤ 8 m od niej. Reszta — stara reguła 8 m.
- Rytm: faza startu U(0, max), krok U(min, max), braki, gatunek; wszystkie losowania z `default_rng(sha1(klucz))` dla
  każdej stacji przed cięciami (cięcie nie przesuwa innych drzew — ADR 0173).
- Odsunięcie: odległość od krawędzi jezdni = odległość od osi − `width/2` (szerokość z overrides `set.width`, jak
  generator dróg); pień < 3,0 m → przesunięty prostopadle od najbliższej drogi na 3,0 m; nadal za blisko (między
  drogami) → usunięty.
- Pola widoczności: węzły grafu stopnia ≥ 3 z parą przelotową dróg głównych; każda inna krawędź to wlot
  (`service` = zjazd, reszta = skrzyżowanie) + wyloty `highway=track`. Trójkąt (obserwator na osi wlotu w
  `width/2 + 3,0 m` od osi drogi, oś pasa w punkcie wlotu, cel L2 dalej na pasie pojazdu nadjeżdżającego, ruch
  prawostronny), dla skrzyżowań dodatkowo obserwator `+10/20 m`, cel L1. Prędkość = `maxspeed` krawędzi przelotowych
  (brak → 90). Pojedyncze drzewa OSM/BDOT punktowe — bez cięć (§ 82 ust. 4).
- `vegetation.place(…, tree_rows=plan)`: przejęte linie BDOT pomijane w regule 8 m, drzewa planu przez `emit`
  (ta sama siatka `blocked`, te same prototypy/LOD/impostory). `stage.py`: `TRW.region_plan(rid, …)` (None bez opt-in).
  Raport: `streetscape_qa.json` → `vegetation.tree_rows`.

### 4. Budżet (ESTIMATED; LOD z `art-source/world/vegetation/trees_meta.json`, polityka z ADR 0012 / `QualityProfile.cs`)
Prototypy szpaleru: klon 2450–2520 / 524–586, lipa 3128–3272 / 684–720, brzoza 3380–3534 / 908–970, olsza 4024–4130 /
826–874 trójkątów LOD0 / LOD1; impostor 2. Średnia ważona mieszanką: **LOD0 ≈ 3130, LOD1 ≈ 720**. Karty drzew na każdym
tierze ze skalą LOD ≤ 0,5 → LOD0 do 10 m, LOD1 do 30 m; impostory do `treeCullM` 600 × lodBias; przerzedzanie co 2.
od 90 × bias, co 4. od 2,5×. Gęstość szpaleru obustronnego 15 m z 12 % braków: 0,117 drzewa / m drogi (górna granica;
na korytarzu przeważają szpalery jednostronne). Cień: tylko LOD0 (`treeShadowLodMask` = 1).

| tier (lodBias) | drzewa w kadrze LOD0 / LOD1 / impostor | trójkąty szpaleru w kadrze | % budżetu kadru (docs/06 §6) | instancje na kafel (delta) |
|---|---|---|---|---|
| Low (0,5) | 1,2 / 2,3 / 11 | ≈ 5,4 tys. | ≈ 1 % z 400–600 tys. | −69 … 0 (suma −300) |
| Medium (0,8) | 1,2 / 2,3 / 20 | ≈ 5,5 tys. | ≈ 1 % | jw. |
| High (1,5) | 1,2 / 2,3 / 41 | ≈ 5,5 tys. | ≈ 0,3 % z 1,5–2 mln | jw. |

Wywołania rysowania: +0 nowych prototypów (klon/lipa/brzoza/olsza są już w każdym kaflu korytarza), batch per
prototyp i komórka 64 m — ESTIMATED +0…+4 na komórkę z nowym gatunkiem. Liczba instancji na kafel **spada**
(rozstaw 12–18 m z brakami zamiast 8 m). Pomiar telefonu: przy bramce (lider).

## Konsekwencje
- Kafle korytarza wymagają przebudowy (`build_world` + import); bez niej nic się nie zmienia w grze.
- Trójkąty L1 (180 m przy 90 km/h, 10 m w głąb) czyszczą też istniejące drzewa przy wlotach (dk65-05 km 14,6: 3 pnie
  N końca rzędu W). To świadome: zadanie żąda cięć wg przepisów; jeśli zdjęcie właściciela pokaże drzewa w polu
  widoczności, override per linia (`sight_obs_m`/kolejne pole) — do decyzji po zdjęciach.
- Drzewa 3,0–~4,5 m od krawędzi mogą wypaść na siatce `blocked` (dylatacja 3 m od pobocza) — raport `placed < planned`.

## Otwarte
1. Gatunki (UNVERIFIED) — zdjęcia właściciela DK65 / Ełckiej; rozstaw linii BDOT bez ortofoto (12–18 m WORKING_VALUE).
2. Wersja obowiązująca WR-D-22-1 i WR-D-31-2 (skrzyżowania) z gov.pl — zastąpić wartości 1999, jeśli inne.
3. SDRR DK65 (GPR) do raportu strefy bez przeszkód.
4. Przebudowa kafli, kamery kontrolne, `visual-critic`, pomiar A16 — lider (komendy niżej). Render w chmurze niemożliwy.

## Odtworzenie / komendy dla lidera
```
uv run --project tools/worldgen python tools/worldgen/streetscape/tree_rows_probe.py      # tylko odświeżenie OSM
uv run --project tools/worldgen python -m pytest tests/gis -k "treerow or vegetation or planting" -q
# kafle ze zmianą: dk65-01 dk65-02 dk65-03 dk65-04 dk65-05 dk65-06 dk65-07 dk65-08 knyszyn knyszyn-w
foreach ($r in 'dk65-01','dk65-02','dk65-03','dk65-04','dk65-05','dk65-06','dk65-07','dk65-08','knyszyn','knyszyn-w') {
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r
  pwsh scripts/import-region.ps1 -Region $r
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir artifacts/visual-qa/treerows-0222/$r/low
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir artifacts/visual-qa/treerows-0222/$r/high
}
```

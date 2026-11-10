# ADR 0069: Wyposażenie drogi wg referencji Mapillary (ekrany, bramownice, sygnalizacja, drzewa w kępach)

Status: przyjęty (world-builder, street-r9 r9e), 2026-11-10. Źródło: `docs/reports/visual/REFS-MAPILLARY-FINDINGS-2026-11-10.md`
różnice 3, 4, 5, 6, 9; D42/D43; ADR 0065 (Mapillary = tylko referencja, bez pikseli w buildzie).

## Kontekst
Zdjęcia Mapillary p26–p55 (montaże `artifacts/refs/mapillary/bialystok-industrial-c/points/`) pokazują wyposażenie
inne niż w grze: ekrany przy łącznicy do Ronda Putry są przeszklone (cokół, ciemny pas, przezroczyste panele na
zielonoszarych słupkach), a gdzie indziej to ciemne pełne kasety (gra: jasnozielonoszare); przed rondem stoi portal
z dwiema tablicami, a za rozwidleniem wysięgnik z jednym słupem (gra: jeden portal, bez wysięgnika); sygnalizatory
wiszą na łukowych wysięgnikach także na wlotach 2-pasowych; drzewa przy drogach stoją kępami.
OSM ma 19 dróg `barrier=wall` + `wall=noise_barrier`, ale `sources.py` nie zachowywał tagu `wall`, więc te ekrany
były rysowane jak prefabrykowany płot betonowy 2 m.

## Decyzja (wszystko w `tools/worldgen`, odtwarzalne)
1. **Ekrany** (`streetscape/furniture.py` `noise_barriers`, `noise_wall`): źródła BDOT10k OT_OIKM_L + OSM
   wall=noise_barrier (części dalej niż 4 m od BDOT) + linie override `kind: noise_barrier`. Styl domyślny `solid`
   (cokół 0,5 m, ciemne kasety `noise_panel_dark` 0,068 lin. do 4,0 m), styl `glazed` (cokół 0,6 m, ciemny pas do
   `band_m`, szkło `noise_glass` z maską brudu jak ekrany wiaduktu, rygiel górny, słupki `noise_post` co 4 m) w strefach
   override `kind: noise_barrier_style` z identyfikatorami zdjęć jako provenance. Kolizja: jedna ściana do góry ekranu.
   Kolor kaset: pomiar p40 (kasety 36–40 sRGB obok cokołu 105 sRGB na tej samej pionowej ścianie → 0,135 × 0,30 = 0,04);
   przyjęte 0,07 (WORKING_VALUE), żeby relief kaset był czytelny na Low pochmurnym (r5: 0,17 + metal 0,3 = czarne).
2. **Bramownice** (`streetscape/landmarks.py`, `life_props.sign_cantilever`): `form: cantilever` — jeden kratowy
   słup 0,6 × 0,6 m poza jezdnią (`column_side` względem kierunku jazdy), kratowe ramię 0,8 m nad tablicami; LOD0 krata,
   LOD1 dwa prostopadłościany; zderzacz z `gantry_footing`. Treść tablic `from_osm`: `destination` +
   `destination:ref` drogi docelowej (graf drogowy zachowuje teraz `destination:ref`; mniej numerów niż nazw → numery
   do ostatnich nazw, jak na p37: „65 Ełk”, „19 Kuźnica”), `refs_extra` dla numerów z relacji tras (8, E67). Tarcze dróg
   wojewódzkich (3 cyfry) żółte z czarnym napisem. Krój: nadal DejaVu Sans Bold — **Drogowskaz nie jest w repo**
   (pobranie fontu wymaga zgody właściciela i sprawdzenia licencji).
3. **Sygnalizacja** (`props.signal_pole`, `standards.SIGNAL_CANTILEVER_LANES = 2`, `SIGNAL_MAST_BEND_R = 1,5 m`):
   maszt zgina się łukiem w poziomy wysięgnik (p42/p45/p47), od 2 pasów na wlocie.
4. **Drzewa** (`streetscape/vegetation.py`, tylko rozmieszczenie): override `kind: tree_groups` (linie, kępy 3–7
   drzew co 3–5,5 m, przerwy 15–40 m, jeden gatunek na kępę); rzędy BDOT bliżej niż 12 m od linii też idą w kępy.
5. Kamery w pozach zdjęć (`tools/worldgen/photolist/photo_cameras.py`): poza z lat/lon/kompasu zdjęcia, FOV wg
   aparatu autora (WORKING_VALUE), osadzenie na kolizji drogi (+1,7 m); montaż zdjęcie | przed | po (≤ 960 px).

6. **Zebry w łatach skrzyżowań** (`roads/markings.py` `_drape_crossing`, p40/p42, różnica #5): przejście, którego
   węzeł OSM leży w wygenerowanej łacie skrzyżowania, było pomijane (15) albo przesuwane do 8 m wzdłuż ramienia (23).
   Teraz jest sztywnym prostokątem (pasy równoległe do ramienia w punkcie przejścia, 0,5/0,5 m wg rys. 4.2.1.1)
   nałożonym na siatkę łaty (+ `MARKING_LIFT`); odmowa < 3 m od węzła albo nad stopniem krawężnika > 6 cm. Źródło
   `P-10J@` nie jest przycinane przez `drop_overlapping` (r9d: pasy ucięte po przekątnej).
7. **Audyt mapy r9 lidera** (`artifacts/map-audit-r9/BUGS.md`): MA-003 szlabany bramy Kwadrat Park podniesione
   (`life_props.barrier_arm(raised=True)`, 85°, bez kolizji ramienia jak dotąd); MA-008/MA-021 strefy `glazed`
   (cokół + ciemny pas 1,0 m) na łącznicy do Putry i al. Tysiąclecia wg Mapillary 1424981177846267, 995780104564541,
   312705613662497, 1340597302993462; dublowanie OSM/BDOT usuwa deduplikacja 4 m z pkt 1; MA-007/MA-021 zestawy
   znaków stojące < 0,9 m od ekranu przesuwane na stronę jezdni 0,9 m przed ekran (`_signs_off_walls`, 5 zestawów),
   a wartość B-33 brana z sekcji pod znakiem, nie ze środka łańcucha (s1820: 90 → 70 jak na zdjęciu).

## Liczby (r9e, `streetscape_qa.json`, `roads_qa.json`)
| | przed (r8) | po (r9e) |
|---|---|---|
| ekrany: długość / glazed / solid | 1884 m BDOT (płot 2 m dla OSM) | 2284 m / 824 m / 1460 m |
| P-10 ogółem / w łatach / pominięte | 59 / – / 15 | 72 / 36 / 2 |
| kępy drzew p26 (linie / kępy / drzewa) | – | 2 / 4 / 15 |
| bramownice override (stale) | 1 (0) | 3 (0) |
| stretch_04 trójkąty High / Low (limit High 2,0 M) | 1 997 615 / 962 150 | 1 995 549 / 964 498 |
| pamięć świata (import) Low / High | – | 112,6 MB / 249,2 MB |

Dowody: `artifacts/street-r9/` (render `before_snap`, `after` 29 kadrów × Low/High × overcast/lowsun; montaże
zdjęcie | przed | po w `montage/r9d-High-overcast`, `montage/after-*`; kadry audytu `montage/audit/`).
Obejrzane: p26 kępy po lewej jak na zdjęciu; p37 wysięgnik z tablicami; p40 jezdnia ze strzałkami P-8, ekran
przeszklony z ciemnym pasem; p42 zebra i P-14 przed wlotem; p55 bariery stalowe obustronnie; s1820 jeden ekran
szklany, B-33 „70” przed ekranem; s0240 szlabany podniesione.

## Konsekwencje
- Zmiany wspólnych plików: `stage.py` (2 argumenty `overrides`), `osm_extract.py`/`roadgraph.py` (tag
  `destination:ref`, klucz cache OSM zależny od listy tagów), `sources.py` (tag `wall`).
- Wszystkie wysokości, stacje bramownic i strefy ekranów to WORKING_VALUE odczytane ze zdjęć (confidence low/medium).
- Otwarte: MA-005 (sygnalizator bokiem na łącznicy s1420 — reguła `furniture.signals` stawia głowicę na ramieniu
  łącznicy węzła z `traffic_signals` 1847044938; do poprawy wybór ramion), B-26 nad B-33 na al. Tysiąclecia (s1820),
  krótki odcinek ekranu przy krawędzi na początku al. Tysiąclecia (s0920, OSM 1383532302?), kamery p43/p45 (pozy
  zdjęć trafiają pod wiadukt — kamera nie rozróżnia poziomu), zebra 233 sRGB (N-21, decyzja właściciela §9-3) i
  linia postojowa/kostka 1,35 (P2 — wymaga ciemniejszej kostki, nie farby; poza tym przebiegiem).
- Nie zrobione: latarnie dwuramienne na pasie dzielącym (p26 pokazuje Y na medianie — odnotowane), ekrany na
  wiadukcie (ADR 0067), nawierzchnia (ADR 0063).

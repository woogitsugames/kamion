# ADR 0069: Wyposażenie drogi wg referencji Mapillary (ekrany, bramownice, sygnalizacja, drzewa w kępach)

Status: WIP (world-builder, street-r9), 2026-11-10. Źródło: `docs/reports/visual/REFS-MAPILLARY-FINDINGS-2026-11-10.md`
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

## Konsekwencje
- Zmiany wspólnych plików: `stage.py` (2 argumenty `overrides`), `osm_extract.py`/`roadgraph.py` (tag
  `destination:ref`, klucz cache OSM zależny od listy tagów), `sources.py` (tag `wall`).
- Wszystkie wysokości, stacje bramownic i strefy ekranów to WORKING_VALUE odczytane ze zdjęć (confidence low/medium).
- Liczby budżetu i dowody: uzupełnić po przebudowie (`artifacts/street-r9/`).
- Nie zrobione: latarnie dwuramienne na pasie dzielącym (p26 pokazuje Y na medianie — odnotowane), ekrany na
  wiadukcie (ADR 0067), nawierzchnia (ADR 0063).

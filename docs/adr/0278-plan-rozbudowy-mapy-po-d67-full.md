# ADR 0278 — plan rozbudowy mapy po d67-full i pierścieniu 0231 („najpierw przejezdne”) + definicje 3 pierwszych kafli
Status: Proposed (chmura D r6, zadanie D19, gałąź `map-plan-0278`), 2026-11-16. Do scalenia przez lidera.
Powiązane: D63 (najpierw z grubsza), D64 (kierunek), D67/D71 (d67-full), D73/D74 (PC główny), ADR 0203 (siatka 2048 m),
0209/0212 (pin roku NMT), 0219 (powiaty z PRG), 0229/0267 (katalog regionów), 0231 (pierścień, PR #115 — w d67-full z
decyzji właściciela), 0234/0273 (paczki, streaming), 0275 (szwy, PR #143), research G10 (`research/g10-truck-restrictions/`).

## Kontekst
Po d67-full + pierścieniu 0231 świat to korytarz C → Knyszyn → Mońki/Tykocin/Jasionówka oraz wyspa Dojlidy (bez
połączenia drogowego z C). Właściciel (D63) chce kolejnych regionów najpierw w wersji przejezdnej. Zadanie D19: kolejność
10–20 kafli (Białystok dalej, Podlasie), kryteria: cele dla ciężarówki, koszt danych, budżet trójkątów, ciągłość tras i
szwy; definicje 3 pierwszych kafli wzorem #115. Sesja bez Data/raw, Unity i GPU; Overpass i pobranie pbf Geofabrik nie
odpowiadały (reset połączenia), więc dane OSM pochodzą z API 0.6 w małych bboxach.

## Decyzja
1. **Kafle = siatka ADR 0203** (x = 776971 + 2048·i, y = 595199 + 2048·j). 21 kandydatów w Białymstoku i okolicy
   (i −4…2, j −3…4, bez zbudowanych i bez pierścienia), nazwy z węzłów OSM `place=*` (bez nazw firm).
2. **Dane w gicie (ODbL)**: `Data/Plans/map-plan-0278/osm_plan_extract.json` z 29 odpowiedzi API 0.6 `map` (21 kandydatów, 3 kafle kalibracyjne, 2 miasta) (kafel lub
   ćwiartki, gdy API odmawia > 50 000 węzłów) + 5 relacji tras (`relation/<id>/full`: DK8 z S8, DK19, DK65, DW671,
   DW678); generyczny User-Agent, 1,5 s przerwy. Manifest `Data/SourceManifests/osm-api06-map-plan-0278.json` (SHA256
   każdej odpowiedzi i wycinka). Odpowiedzi surowe poza gitem. Wycinek ma **kategorie i punkty**, nie nazwy obiektów.
3. **Kategorie celów** (tylko tagi OSM; BDOT10k nie jest w gicie — są tylko manifesty):

   | kategoria | tagi OSM |
   |---|---|
   | `hall_1000m2` | `building=industrial|warehouse|manufacture`, obrys ≥ 1000 m² |
   | `warehouse` | `building=warehouse` lub `industrial=warehouse|logistics` |
   | `works` | `man_made=works` |
   | `fuel` / `fuel_hgv` | `amenity=fuel` / + `fuel:HGV_diesel=yes` lub `hgv=yes|designated` |
   | `truck_parking`, `services` | `amenity=parking` + `hgv=yes|designated` lub `parking=truck`; `highway=services|rest_area` |
   | `retail_delivery` | `shop=supermarket|mall|doityourself|wholesale|department_store|trade` (cele dostaw) |
   | `industrial_ha` | powierzchnia `landuse=industrial` w kaflu |

   `target_score` = hale + magazyny + zakłady + 2·paliwo HGV + 2·parking TIR + ha/10 (wagi WORKING_VALUE).
   Kompletność tagów OSM nieznana (paliwo HGV i parkingi TIR prawie nie występują — to luka OSM, nie brak obiektów).
4. **Budżet** z `generated/*` 21 zbudowanych kafli (migawka `docs/reports/map/map_plan_0278_budget.json`): klasy
   miasto (powiat 2061 + Knyszyn, 6 kafli), podmiejski (≥ 250 budynków, 7), zamiejski (8). Mediany High statyczne /
   klatka max / GLB / WORLD_MEMORY Low: miasto 10,76 M / 1,96 M / 621 MB / 120 MB; podmiejski 9,18 M / 1,19 M / 441 MB /
   60 MB; zamiejski 8,78 M / 1,56 M / 358 MB / 49 MB. Dla kafli miejskich także regresja po liczbie budynków
   (zakres kalibracji 406–1903; powyżej = ekstrapolacja `*`). Kalibracja OSM ↔ `buildings.geojson`: C 569/643, Maczka
   1683/1760, dk65-05 439/473. Wszystkie wartości dla nowych kafli: **ESTIMATED**.
5. **Koszt danych** (`docs/reports/map/map_plan_0278_gugik.json`, skorowidze GUGiK WFS 2026-11-16, nic nie pobrano):
   arkusze, które wybrałby `ingest.py` (te same reguły), podzielone na „na dysku lidera” (URL w manifeście
   `Data/SourceManifests`) i „do pobrania”. 14 kafli planu: NMT 34 nowe arkusze (≈ 1,26 GB, ESTIMATED 37,2 MB/arkusz =
   mediana 49 arkuszy z manifestów; skorowidz nie podaje rozmiaru), ORTO 0,25 m 1783 MB (z `wlk_pliku_mb`). BDOT10k,
   LoD1, LoD2: powiaty 2002 i 2061 już na dysku — 0 MB. Podlasie: nowe powiaty (HEAD `Content-Length`, 2026-11-16):
   2004 BDOT 26,2 + LoD1 6,3 + LoD2 11,0 MB; 2013 48,6 + 10,6 + 18,9 MB; 2014 19,2 + 5,1 + 9,1 MB.
6. **Kolejność (14 kafli)** — każdy styka się drogą numerowaną/główną z kaflem zbudowanym, pierścieniem lub wcześniejszym
   z listy (sprawdza plan: `order[].connected_via`):

   | # | kafel (i,j) | po co | cele H/M/Z, ha | bud. / klasa | klatka High max (ESTIMATED) |
   |---|---|---|---|---|---|
   | 1 | `bialystok-porosly` (−3,−1) | DK8 Kleeberga (40 t w planie miasta 2018) od S krawędzi knyszynskiej ku S8; największa strefa przemysłowa | 4/8/1, 72 ha | 1051 / podm. | 1,19 M |
   | 2 | `dk8-s8-jeroniki` (−4,−1) | węzeł DK8 → S8, szew z dk65-01 (S8 + łącznice): pętla S8–Kleeberga–Szosa Knyszyńska, wjazd od Warszawy | 2/1/1, 10 ha | 907 / podm. | 1,19 M |
   | 3 | `bialystok-dojlidy-gorne` (2,−3) | Kuronia (tranzyt > 3,5 t od 12.2025, G10) od E krawędzi Dojlid do DK19 na południe | 10/1/5, 25 ha | 1400 / miasto | 2,29 M |
   | 4 | `bialystok-krywlany` (0,−3) | Ciołkowskiego DW678 + Dywizjonu 303 przy W krawędzi Dojlid (tam startuje trasa Dojlid) | 2/0/1, 7 ha | 694 / miasto | 1,94 M |
   | 5 | `bialystok-mickiewicza` (1,−2) | DK19 Branickiego / rondo Meyera / Ciołkowskiego | 6/6/3, 13 ha | 4157 / miasto* | 3,67 M |
   | 6 | `bialystok-bojary` (1,−1) | DK19/DK65 Andersa–Sosabowskiego–Piastowska | 4/0/1, 26 ha | 3289 / miasto* | 3,23 M |
   | 7 | `bialystok-wygoda` (1,0) | narożnik: Andersa wychodzi z C przez 66 m tego kafla — zamyka C ↔ Dojlidy | 0/1/4, 7 ha | 4318 / miasto* | 3,75 M |
   | 8 | `bialystok-skorupy` (2,−2) | Ciołkowskiego / Sulika (DK65) / DK19 południe | 6/7/0, 49 ha | 3384 / miasto* | 3,28 M |
   | 9 | `bialystok-pieczurki` (2,−1) | DK65 Sulika, początek wylotu DK65 na wschód | 2/3/2, 22 ha | 2118 / miasto* | 2,65 M |
   | 10 | `dk8-dk19-pn-01` (0,1) | DK8/DK19 na północ od C (N krawędź C), tani | 0/0/0, 0 ha | 150 / zam. | 1,56 M |
   | 11 | `dk8-dk19-jurowce` (0,2) | DK8/DK19 północ | 2/2/0, 16 ha | 652 / podm. | 1,19 M |
   | 12 | `dk8-sochonie` (0,3) | DK8 ku Augustowowi; DK19 skręca na wschód | 0/0/0, 14 ha | 583 / podm. | 1,19 M |
   | 13 | `bialystok-bacieczki` (−2,−1) | łata pod kleeberga (DW669/DW676) | 3/0/1, 5 ha | 1032 / miasto | 2,11 M |
   | 14 | `bialystok-centrum` (0,−1) | S krawędź C, rejon dworca; najwyższy `target_score` (10/14/1, 38 ha), ale centrum = strefa 3,5 t planu 2018 (G10) | 10/14/1, 38 ha | 2050 / miasto* | 2,62 M |

   Uzasadnienie kolejności: (a) 1–2 łączą zbudowany korytarz C–Maczka–Kleeberga z S8 (główny wjazd ciężarówek od
   Warszawy) i zamykają pętlę z dk65-01 — 2 kafle, tanie (podmiejskie), największy przemysł; (b) 3–7 to trasa ciężarówki
   C ↔ Dojlidy po drogach numerowanych (planer: Andersa → Sosabowskiego → DK19 Piastowska/Branickiego → rondo Meyera →
   Ciołkowskiego → Dywizjonu 303, 8,3 km; bez odcinków `hgv=no`/`maxweight` < 40 t) i wjazd DK19 od południa przez Kuronię
   — Dojlidy przestają być wyspą; 5–7 to najgęstsza zabudowa (ryzyko budżetu, patrz Otwarte 1); (c) 8–9 drugi dojazd
   (Ciołkowskiego–Sulika) i wylot DK65; (d) 10–12 wyloty DK8/DK19 na północ (tanie, mało celów); (e) 13–14 łaty miejskie.
   Kandydaci poza listą (antoniuk, piaski, bagnówka, pietrasze, wasilkow, dk19-jakimy, dk8-woroszyly) — metryki w planie.
7. **Podlasie** (z relacji tras, ESTIMATED; mediany kafla zamiejskiego):
   - **Mońki → Grajewo (DK65)**: 20 kafli, 35,9 km, ≈ 7,2 GB GLB; droga krajowa, ciągła z pierścieniem (`monki`),
     kafel miasta Grajewo: 29 ha przemysłu, 2 hale, 5 magazynów. **Sensowna** jako następny etap Podlasia (po
     Białymstoku), powiaty 2008 + 2004 (2004 do pobrania, ≈ 44 MB).
   - **Tykocin → Zambrów**: nie ma bezpośredniej drogi ciężarowej; realnie DW671 Tykocin → węzeł S8 (5 kafli, 8,6 km) i
     S8 do Zambrowa (23 kafle, 35,6 km, sama ekspresówka). **Niezalecana teraz**: D64 (zwykłe drogi), monotonna S8,
     Zambrów ma tylko 11 ha przemysłu w kaflu miasta. Zamiast niej: pętla Białystok → S8 → węzeł przy DW671 → Tykocin
     → Knyszyn → DK65 → Białystok = 12 kafli S8 (21,2 km od dk65-01) + 5 kafli DW671 — do decyzji właściciela.
8. **Definicje 3 pierwszych kafli** (wzór #115): wpisy `regions.py` (generowane `--print-regions`), w katalogu kafla
   `overrides.yaml` (pusty: nic nie zmierzono, sąsiedzi nie mają override'ów przekroju na drogach szwów),
   `sources.authored.json` (pin NMT = rok sąsiada na szwie drogi przelotowej: porosly 2022 jak knyszynska, jeroniki
   2025 jak dk65-01, dojlidy-gorne 2025 jak Dojlidy) i `route_endpoints.json` (trasa kontrolna z planu: jeroniki S8 z N
   krawędzi → E; porosly W → N na Kleeberga; dojlidy-gorne Kuronia W → DK19 E). `region.yaml` pisze `build_region.py`
   z wpisu `regions.py` (jak w ADR 0231 „Po budowie”). Powiaty wg ADR 0219 (każdy nakładający się powiat, PRG w gicie):
   porosly 2002 + 2061 (59/41 %), jeroniki 2002, dojlidy-gorne 2061 + 2002 (0,4 %). `graph_filter.authored.json` nie
   dodany — zbudowani sąsiedzi w 2061/2002 go nie mają.

## Szwy (z planu, OSM 2026-11-16 vs `roads.graph.json` sąsiadów z pbf 2026-11-08)
- porosly | knyszynska (N): Kleeberga 2× trunk, 2 łącznice, NSZ DW669 2× — 6/6 węzłów brzegowych, odchyłka 0,0 m.
- jeroniki | dk65-01 (N): S8 2× + 6 przecięć łącznic + Warszawska — 7 way, 0,0 m.
- dojlidy-gorne | Dojlidy (W): Kuronia 2× + Grabowa — 3/3, 0,0 m. jeroniki | porosly: ta sama way 223394828 i punkt.
- Styk z pierścieniem 0231: brak (kafle planu leżą w Białymstoku). Kafle zablokowane (knyszynska, dk65-01, Dojlidy):
  nic po ich stronie nie zmienione.

## Walidacja
- `tests/gis/test_map_plan_0278.py` (26 testów, dane w gicie): plan deterministyczny == json, SHA256 wycinka == manifest,
  brak nazw/marek w celach, UA generyczny, wpisy == plan, kafel 2048 m na siatce, brak nakładania z 24 regionami i
  pierścieniem, istniejące wpisy == ich `region.yaml`, CRS i położenie (nazwy miejscowości w kaflach), kolejka rośnie po
  szwach, trasy kontrolne znalezione i połączone, szwy == węzły brzegowe grafów sąsiadów (< 0,5 m, obie strony), pliki
  authored dwustanowe (definicja / zbudowany), koszt GUGiK, Podlasie bez kafli pierścienia.
- `test_knyszynska_0208` (lista kafli wielopowiatowych + porosly, dojlidy-gorne) i `test_qa_tools_0219` zielone.
- Render kontrolny `docs/reports/map/map_plan_0278.png` (obejrzany: kafle, numery, trasy kontrolne, cele).

## Otwarte
1. **Budżet gęstych kafli miejskich** (mickiewicza, bojary, wygoda, skorupy, centrum: 2050–4318 budynków, poza zakresem
   kalibracji): klatka High max 2,6–3,75 M ESTIMATED (Maczka zmierzona 3,29 M). Mobilny bezpiecznik 2 M (D73) przekroczony;
   PC budżet do pomiaru (ADR 0266). Przed budową: decyzja lidera (LOD/cull zabudowy, uproszczony profil) albo zgoda na PC-only.
2. Trasa C ↔ Dojlidy po DK19 przez Piastowską/Branickiego: dopuszczalność 40 t niepotwierdzona (plan miasta 2018 ma tylko
   Andersa, Maczka, Tysiąclecia, Wasilkowska, Ciołkowskiego jako 40 t; strefa 3,5 t centrum nie jest w OSM — G10).
   Alternatywa przez Sulika–Ciołkowskiego = kafle 8–9.
3. Pin NMT porosly 2022 vs jeroniki 2025 — szew dwóch serii (jak już knyszynska|dk65-01); taper ADR 0275 albo wspólny pin.
4. Polityka latarń (LED jak knyszynska?) w nowych kaflach — decyzja; `overrides.yaml` puste.
5. Węzeł S8 w jeroniki: pierwszy kafel z dużą częścią łącznic poza dk65-01 — przejezdność łącznic do sprawdzenia po budowie.
6. Po scaleniu #115 test pierścienia `test_existing_entries_unchanged` (`len(OLD) == 21`) policzy też 3 kafle 0278 —
   trzeba go zmienić na `>= 21` (plik pierścienia, nie ruszany tutaj).
7. Podlasie: PRG w gicie pokrywa tylko część komórek korytarzy (AOI) — przypisanie powiatów poza AOI UNVERIFIED.

## Odtworzenie
```
uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py --png          # plan + render (bez sieci)
uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py --print-regions # wpisy regions.py (3 kafle)
uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py --init-regions  # brakujące pliki authored
#   ... --extract <raw> (odpowiedzi API 0.6 .json[.gz]), --gugik <indeks>, --budget-snapshot (z generated/*)
uv run --project tools/worldgen python -m pytest -q tests/gis/test_map_plan_0278.py tests/gis/test_knyszynska_0208.py tests/gis/test_qa_tools_0219.py
# budowa (lider), w kolejności: dk8-s8-jeroniki, bialystok-porosly, bialystok-dojlidy-gorne
uv run --project tools/worldgen tools/worldgen/ingest.py --region <id>
uv run tools/worldgen/build_region.py --region <id>
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>
uv run --project tools/worldgen python scripts/export-route.py --region <id>
#   ręcznie: wpis (id, label, group) w game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json
python scripts/export-region-catalog.py && python scripts/export-region-catalog.py --check
pwsh scripts/import-region.ps1 -Region <id> -Build
pwsh scripts/visual-qa.ps1 -Scene World_<id> -Tier Low -Lighting overcast -OutputDir artifacts/map-plan-0278/vqa/<id>
```

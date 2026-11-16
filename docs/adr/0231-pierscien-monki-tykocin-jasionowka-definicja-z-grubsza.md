# ADR 0231 — następny pierścień kafli za Knyszynem: DK65 do Moniek, DW671 do Tykocina, DW671 w stronę Jasionówki (definicja „z grubsza”)
Status: Proposed (chmura E, zadanie E4, gałąź `ring-0231`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64, D65 (`docs/11`), ADR 0203 (siatka 2048 m), 0204/0209 (Knyszyn), 0205 (`edge_lines`), 0208
(`teryt_powiat_extra`), 0210 (woda opt-in), 0212 (`dk65-monki-01`, `dw671-tykocin-01`, pin NMT roku), 0214 (wzór
wpisów korytarza), brief `docs/owner/S20-REGION-RING-BRIEF.md`.

## Kontekst
Po ADR 0212 świat kończy się na zachodniej krawędzi `dk65-monki-01` (DK65 na Mońki), południowej `dw671-tykocin-01`
(DW671 na Tykocin) i północnej `knyszyn` (DW671 Grodzieńska na Jasionówkę). Zadanie E4: zdefiniować kolejne kafle
(regions.py + pliki authored), bez ingestu i budowy (budowa = lider, komendy niżej). Sesja nie miała danych surowych
(Data/raw) ani GPU, więc nic nie zmierzono na ortofoto — wszystkie override'y mają `confidence: low`.

## Decyzja
1. **Kafle = siatka ADR 0203** (x = 776971 + 2048·i, y = 595199 + 2048·j), wybrane tak, żeby droga przelotowa szła
   przez nie w kolejności jazdy bez przerw na szwach. 18 nowych wpisów (bbox i origin z planu, nie ręcznie):
   - DK65 Mońki (12,92 km, z krawędzi W `dk65-monki-01`): `dk65-monki-02` (−10,9), `-03` (−10,10), `-04` (−11,10),
     `-05` (−11,11), `-06` (−12,11), `-07` (−12,12), `monki-e` (−12,13), `monki` (−13,13).
   - DW671 Tykocin (13,33 km, z krawędzi S `dw671-tykocin-01`): `dw671-tykocin-02` (−9,6), `-03` (−10,6), `-04` (−10,5),
     `-05` (−11,5), `-06` (−11,4), `-07` (−12,4), `-08` (−12,3), `-09` (−13,3), `tykocin` (−13,2).
   - DW671 Jasionówka (2,36 km, z krawędzi N `knyszyn`): `dw671-jasionowka-01` (−8,9).
   Kafle narożne z < 0,5 km drogi (`dk65-monki-03` 414 m, `-05` 163 m, `monki-e` 293 m, `dw671-tykocin-02` 108 m)
   istnieją tylko po to, by droga nie przecinała rogu siatki; alternatywa (kafel niewyrównany do siatki) łamie
   zasadę ADR 0203 i wspólne krawędzie terenu.
2. **Źródło = wycinek OSM w gicie**, nie PRG. `Data/Plans/ring-0231/osm_ring_extract.json` (Overpass 2026-11-15,
   3 zapytania, generyczny User-Agent, ODbL; manifest `Data/SourceManifests/osm-overpass-ring-0231.json` z SHA256
   odpowiedzi surowych i wycinka). Drogi z `ref` 65/671, kolej, rzeki, przejazdy, miejscowości oraz granice powiatów
   z relacji OSM `admin_level=6` (lustro z bazą 2026-07-24 — starsze niż drogi, zmiana granic UNVERIFIED).
   Pipeline nadal buduje z przypiętego pbf Geofabrik 2026-11-08; różnicę wykrywa `overrides_stale` w build_world.
3. **Plan deterministyczny**: `tools/worldgen/qa/ring_0231_plan.py` (bez sieci i zegara) → `docs/reports/map/ring_0231_plan.json`
   + render kontrolny `ring_0231_plan.png` (matplotlib z własnych danych). Wpisy regions.py generuje `--print-regions`,
   pliki authored `--init-regions` (nigdy nie nadpisuje istniejących).
4. **Powiat**: największy udział powierzchni kafla (poligony admin OSM); drugi powiat od 5 % (`WORKING_VALUE`;
   ADR 0214 liczył z pokrycia BDOT10k, tu niedostępnego). Wszystkie kafle 2008 (moniecki) poza:
   `dw671-tykocin-08` 2008 + 2002 (14,8 %), `dw671-tykocin-09` 2002 (73,5 %) + 2008, `tykocin` 2002 (96,1 %) — powiat
   białostocki. Test 0208 (`multi`) rozszerzony o te trzy kafle.
5. **NMT**: pin `nmt_year: 2022` we wszystkich nowych kaflach (jak `knyszyn-w`, `dk65-monki-01`, `dw671-tykocin-01`;
   `knyszyn` ma serię 2022 bez pinu). Skorowidz GUGiK (WFS, 2026-11-15, `ring_0231_nmt_coverage.json`): seria 2022
   (naloty 2022-07-29 + 2022-08-27; arkusze per kafel w json) pokrywa każdy kafel; bez pinu ingest wziąłby 2022–2025
   zależnie od kafla, czyli różne lata na wspólnych krawędziach.
6. **Override'y (styl 0205/0209/0212/0214)**:
   - DK65 poza zabudową (`highway=primary`, bez nazwy ulicy, nie rondo, dwukierunkowa): `dk65-carriageway-width`
     z tym samym `set` co `dk65-monki-01` (`lanes 2, lane_width 3.4, edge_strip 0.35, edge_lines both`) i
     `dk65-fields-unlit` (`lamps: false`) — kontynuacja szwu; `WORKING_VALUE`, nie zmierzone w tych kaflach.
   - DK65 w Mońkach (ulice z nazwą: Białostocka, Ełcka; m.in. odcinki `lanes=3`) — bez override'u, reguła generatora.
   - DW671 — brak override'ów (szerokość BDOT10k, bez linii krawędziowych), jak zmierzone w `dw671-tykocin-01` (ADR 0212).
   - `graph_filter.authored.json` jak wszystkie kafle powiatu 2008 (odrzucone `service=driveway`), `sources.authored.json`
     (pin NMT), `route_endpoints.json` (wjazd szwem → wyjazd kolejnym szwem / krawędzią końca pierścienia).
7. **`water` = False** we wszystkich (ADR 0210 opt-in). Do decyzji: Nareśl pod DK65 (`dk65-monki-02`, most 15,4 m),
   Narew pod DW671 (`tykocin`, most 194,8 m) — patrz Otwarte.

## Cechy dróg przelotowych (z wycinka OSM, do szlifu)
| kafel | droga | km korytarza | uwagi z OSM |
|---|---|---|---|
| dk65-monki-02 | DK65 | 0,00–2,11 | most na Nareśli (way 286989045, 15,4 m) |
| dk65-monki-04/-06/-07 | DK65 | 2,52–9,90 | linia kolejowa w kaflu (2,2–4,6 km torów), bez przejazdu na DK65 |
| monki | DK65 | 10,19–12,92 | przejazd kolejowy w poziomie szyn (node 1778182520, rail way 166369633, 752139 622219) |
| dw671-tykocin-04 | DW671 | 2,30–4,18 | przecięcie kanału (way 469073554) |
| tykocin | DW671 | 10,77–13,33 | most na Narwi (way 96942026, 194,8 m), most 8,6 m (way 274454650), kostka (`surface=sett`) na Puchalskiego / Pl. Czarnieckiego / Złotej, `maxspeed` 40–60 |
Budowa (`highway=construction|proposed`) w kaflach pierścienia: 0 m.

## Walidacja
- `tests/gis/test_ring_0231.py` (dane w gicie, bez Data/raw): plan == json (determinizm), SHA256 wycinka == manifest,
  wpisy == plan, unikalne id i tytuły, kafel 2048 × 2048 na siatce, origin = środek, brak nakładania i duplikatów
  z wszystkimi 21 wcześniejszymi regionami (także 0212), istniejące wpisy == ich `region.yaml`, CRS EPSG:2180 i położenie
  (Mońki/Tykocin w kaflach o tej nazwie), jedna ciągła droga na kafel, szwy wewnątrz pierścienia (ta sama way, ten sam
  punkt), szwy z kaflami zbudowanymi == węzeł brzegowy ich `roads.graph.json`, brak „zgubionych” przecięć DK65/DW671
  na jakiejkolwiek wspólnej krawędzi, pliki authored, NMT 2022, ten sam `set` przekroju po obu stronach każdego szwu.
- Render kontrolny: `docs/reports/map/ring_0231_plan.png` (obejrzany: kafle, szwy, przejazd w Mońkach, mosty).

## Otwarte
1. **Nic nie zbudowane**: ingest/build/import/visual-qa i pomiary (czas, WORLD_MEMORY, draws/tris) — lider, kafel po kaflu.
2. Override'y DK65 (`confidence: low`) do sprawdzenia na ortofoto 0,1 m po ingeście (narzędzie z ADR 0212); wsie wzdłuż
   DK65 mogą mieć latarnie (`lamps: false` wtedy błędne). Mońki: latarnie LED (D65 p.8 dotyczy „trasy DK65/Knyszyn”) —
   decyzja właściciela, czy `lamp_policy: led` także w Mońkach.
3. Przejazd kolejowy w Mońkach i (z ADR 0212 p.4) na DW671 — generator nie ma torów; droga przejezdna bez przejazdu.
4. Woda (`water`) dla Nareśli i Narwi — decyzja; most na Narwi 194,8 m to pierwszy duży most poza Białymstokiem.
5. Tykocin: kostka na DW671 w centrum — materiał nawierzchni z `surface` do sprawdzenia w generatorze.
6. Granice powiatów z lustra Overpass z 2026-07-24 (UNVERIFIED po tej dacie); próg 5 % `WORKING_VALUE`.
7. Koniec świata: krawędź W `monki` (DK65 dalej na Grajewo), S `tykocin` (DW671 dalej), N `dw671-jasionowka-01`.

## Po budowie kafli (FIX po recenzji s22 #115)
1. **`region.yaml`** nie jest plikiem authored: `build_region.py` pisze go w całości z wpisu `regions.py` (id, tytuł,
   `status`, bbox, origin x/y + z z NMT, powiaty) i z manifestów źródeł; plików authored (`graph_filter.authored.json`,
   `overrides.yaml`, `route_endpoints.json`, `sources.authored.json`) nie rusza. Sprawdzone w kodzie (`build_region.py`
   §region.yaml) — **nie uruchomione** (brak Data/raw w chmurze). Manifesty powiatów 2002 i 2008 (BDOT10k, LoD1, LoD2)
   są w gicie; manifesty `gugik-nmt-2022-<id>` i `gugik-orto-*-<id>` tworzy `ingest.py` (pin `nmt_year: 2022`).
   Poprawka: `status` wpisów pierścienia nie zawiera już „definition only, not built” — tekst trafiał dosłownie do
   `region.yaml`, więc po budowie byłby nieprawdziwy. Czy kafel jest zbudowany, wynika z dysku (`region.yaml`).
2. **Test dwustanowy** `test_authored_files_present_and_consistent`: kafel bez `region.yaml` = definicja (żaden
   produkt budowy w gicie, override'y `confidence: low`); kafel z `region.yaml` = zbudowany (`region.yaml` == wpis
   `regions.py`, kafel 2048 m, CRS EPSG:2180 / EVRF2007, źródła z manifestami w gicie, pin NMT 2022 uszanowany, pliki
   authored przetrwały). Wcześniej test wymagał braku `region.yaml` i padłby po pierwszej budowie. Stan „zbudowany”
   sprawdzony na syntetycznym `region.yaml` jednego kafla (nie w gicie).
3. **Katalog regionów (ADR 0229/0267):** `export-region-catalog.py --check` zgłasza każdy region z `route_start.json`
   bez wpisu w katalogu; wpis (id, label, group) dodaje się ręcznie, pola pochodne przelicza skrypt. Wpisu nie można
   dodać przed budową (skrypt wymaga `route_start.json` i `roads.graph.json`). Propozycja: `group` = „Mońki” dla
   `dk65-monki-02…07`, `monki-e`, `monki`; „Tykocin” dla `dw671-tykocin-02…09`, `tykocin`; „Knyszyn” dla
   `dw671-jasionowka-01`; `label` = część tytułu z `regions.py` przed „ — ”. Zbiory (`d67`, `d67-full`) bez zmian —
   decyzja właściciela, czy pierścień wchodzi do zbioru. Strażnik: `test_built_ring_tiles_are_in_the_region_catalog`.
4. **Graf kafli streamingu (ADR 0235, PR #114 — w chwili FIX nie w main):** `tools/worldgen/streaming/tile_graph.py`
   czyta `Data/Regions/*/region.yaml`, więc kafle pierścienia pojawią się w `tile_graph.json` dopiero po budowie; do tego
   czasu #114 i #115 są od siebie niezależne (kolejność scalania dowolna). Po budowie: uruchomić `tile_graph.py`
   (inaczej pada `test_tile_graph_0235::test_committed_graph_is_fresh`) i dopisać zmierzone `WORLD_MEMORY` Low/High
   kafla do tabel `WORLD_MEMORY_LOW_MB` / `WORLD_MEMORY_HIGH_MB`; bez wpisu kafel liczy się jak najcięższy zmierzony
   (160,0 / 420,4 MB — wartości z gałęzi `streaming-0235`), co przy budżecie Low 200 MB blokuje wczytanie sąsiada.
5. **Kafle narożne < 0,5 km drogi** (`dk65-monki-03`, `-05`, `monki-e`, `dw671-tykocin-02`): generator nie ma
   uproszczonego profilu treści i ten ADR go nie wprowadza. Budować profilem ogólnym, **zmierzyć** `WORLD_MEMORY` Low
   i wpisać do tabel z p. 4. Jeśli suma dwóch sąsiednich kafli przekroczy budżet streamingu Low (200 MB, #114),
   uproszczenie (np. bez far-field poza korytarzem) wymaga osobnej decyzji — otwarte, UNVERIFIED do pomiaru.
5a. **Kafle narożne bez startu (s23, world2-finish, 2026-11-17).** `dk65-monki-05` (korytarz 163,23 m) i
   `dw671-tykocin-02` (107,78 m) mają trasę od krawędzi do krawędzi. Start za zamknięciem wjazdowym wymaga
   ≥ 60 + 0,75 + 11,30 + 0,5 = 72,55 m plus 100 m przed ciężarówką (`RegionStart.MinAheadM`) = 172,55 m (reguła eksportera:
   90 + 100 = 190 m), więc startu nie da się ustawić danymi; końce trasy (`route_endpoints.json`) to portale korytarza
   w `tile_graph` (ADR 0235) i nie mogą się zmienić. Decyzja: jawny znacznik authored `no_standalone_start: true`
   (+ `no_standalone_start_note`) w `route_endpoints.json` → `export-region-catalog.py` zapisuje `noStart: true`
   (odrzuca znacznik, gdy trasa mogłaby mieć start) → menu startowe pokazuje kafel jako „tylko przejazd” bez wyboru
   (`GameBootstrap.BuildRegionChoices`), importer loguje informację zamiast błędu braku strefy startu
   (`WorldSceneBuilder`), testy `test_start_clear_0262.py` i `StartClearanceTests` sprawdzają, że trasa naprawdę jest za
   krótka; strażnik `test_no_start_marker_only_on_corner_tiles_and_matches_route_endpoints` dopuszcza znacznik tylko
   na kaflach narożnych z p. 5. `dk65-monki-03` i `monki-e` mają start (414 / 293 m) — bez znacznika.
   Także: `tykocin` ma 3,95 % bboxa w powiecie 2008 (PRG) → `teryt_powiat_extra=('2008',)` w `regions.py`.
6. **Kolej:** od ADR 0217 generator ma etap kolei opt-in (`rail=True` we wpisie regionu). Wpisy pierścienia mają
   `rail=False`; przejazd w `monki` i tory w `dk65-monki-04/-06/-07`, `dw671-tykocin-02` — włączyć po scaleniu
   prac kolejowych DK65 (#102), decyzja lidera (zastępuje „Otwarte 3” w części „generator nie ma torów”).
7. `CLAUDE.md` (plik lidera) — sekcja „Regeneracja mapy” nie wymienia `export-region-catalog.py` ani `tile_graph.py`;
   do dopisania przez lidera (nie zmieniane w tym PR).

## Odtworzenie
```
uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py --png                  # plan + render (bez sieci)
uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py --print-regions        # wpisy regions.py
uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py --init-regions         # brakujące pliki authored
uv run --project tools/worldgen python -m pytest -q tests/gis/test_ring_0231.py tests/gis/test_knyszynska_0208.py
# budowa (lider), dla każdego <id> z listy p. 1, w kolejności jazdy:
uv run --project tools/worldgen tools/worldgen/ingest.py --region <id> --with orto10
uv run tools/worldgen/build_region.py --region <id>                                   # tworzy region.yaml (p. „Po budowie”)
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>
uv run --project tools/worldgen python scripts/export-route.py --region <id>          # route_start.json
#   ręcznie: wpis kafla (id, label, group) w game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json,
#   PRZED importem — importer zapisuje startS z katalogu jako spawn sceny (WorldSceneBuilder, ADR 0262)
python scripts/export-region-catalog.py                                               # routeLengthM / startS + zbiory pochodne
python scripts/export-region-catalog.py --check
pwsh scripts/import-region.ps1 -Region <id> -Build
pwsh scripts/visual-qa.ps1 -Scene World_<id> -Tier Low -Lighting overcast -OutputDir artifacts/ring-0231/vqa/<id>
# raz, po zbudowaniu partii kafli:
uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py         # tylko po scaleniu #114 (ADR 0235)
uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py --check
uv run --project tools/worldgen python -m pytest -q tests/gis/test_ring_0231.py tests/gis/test_region_catalog_0267.py tests/gis/test_start_clear_0262.py
```

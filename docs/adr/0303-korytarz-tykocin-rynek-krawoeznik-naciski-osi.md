# ADR 0303 — korytarz Białystok → Tykocin: koniec na Rynku, trasa kontrolna po DW671, naciski osi 10 t z OSM, magenta słupków

Status: Proposed (agent corridor-polish-s24, 2026-11-19). Numer nadany przez lidera.
Powiązane: ADR 0204 (punkty `via` trasy kontrolnej), 0231 (kafel `tykocin`), 0285 (trasy łączące, `replaces_route`),
0289 (swing linku w Knyszynie), 0293 (`noise_post_light`), 0300 (sonda `route_obstacles`, magenta w worktree),
0302 (podróże GPS przez kafle, limit nacisku osi do weryfikacji), D43 (wspólne `Data/raw/derived`).

## 1. Krawężnik 0,38 m w obwiedni ciężarówki (`tykocin`, trasa kafla s ≈ 1902 m)
**Przyczyna.** Trasa kontrolna kafla to najkrótsza ścieżka grafu (`route_polyline` / `export-route.py`). Na rogu
Sokołowska / Klasztorna (E 139 N −455) skracała przez dwie jednokierunkowe drogi `highway=service` (OSM w1426176071,
w1426176072 — zatoczka pod drzewami, ortofoto 0,25 m: `artifacts/corridor-polish-s24/ortho_curb_s1902.png`): 57 m
wobec 58 m po DW671. Generator buduje tam wyspę z krawężnikiem; jej krawężnik (0,02–0,38 m nad nawierzchnią) wpadał
w obwiednię ±1,2 m. To nie błąd geometrii skrzyżowania, tylko trasa, którą żadna ciężarówka nie pojedzie. Ta sama
reguła najkrótszej drogi wyprowadzała trasę z DW671 na Rynku (północna strona placu, `residential`, w630270670 +
w220327904) i — po pierwszym `via` — na Bernardyńską / Choroszczańską.
**Decyzja.** authored_override `Data/Regions/tykocin/route_endpoints.json → via_epsg2180` (jak ADR 0204 w Knyszynie):
węzły OSM 1123400983 (róg SE Rynku), 2791676438 (Złota), 1842358780 (Sokołowska/Klasztorna). Trasa kontrolna:
2558 m, 100 % krawędzi `secondary` ref 671 (test `test_tykocin_trip_ends_on_the_rynek_0303`).

**Znalezisko przy okazji — równoległe krawędzie.** `roadgraph.to_digraph` (networkx `DiGraph`, jedna krawędź na
kierunek) przy dwóch drogach między tą samą parą węzłów zostawiał ostatnią dodaną. W `dw671-tykocin-03` droga serwisowa
w553605081 (124 m) zastępowała krawędź DW671 w1111506762 (46 m) i trasa kontrolna jechała pętlą serwisową. Teraz
zostaje krótsza krawędź (test `test_parallel_edges_keep_the_shorter_0303`). Skan tras kontrolnych wszystkich regionów:
równoległe krawędzie na trasie w 3 regionach; zmiana trasy tylko w `dw671-tykocin-03` (2265 → 2191 m, cała po DW671,
`route_obstacles` 0/0); `bialystok-industrial-c`, `dk65-05` bez zmian; `route_links.json` bez zmian (`--check`).
Kamery kontrolne `dw671-tykocin-03` (`build_world` → `control_cameras.json`) przesuną się przy następnej przebudowie kafla.

## 2. Cel „Tykocin” = Rynek
**Miejsce postoju** (ortofoto 0,25 m, `ortho_rynek.png`, `ortho_rynek_south.png`): na placu nie ma zatoki ani parkingu
dla zestawu 16,5 m (parking przy Alumnacie i miejsca wzdłuż wschodniej pierzei — osobowe). Płyta placu z pomnikiem
Czarnieckiego nie jest drogą. Postój = pas zachodni DW671 na południowej pierzei placu, przy krawężniku od strony placu,
na 47 m prostej między zjazdami (węzły OSM 13718175880 i 13718175884): stop (751818,5 600215,1), cały zestaw stoi
za nim na prostej (test: ostatnie 20 m na zachód, odchyłka N < 3 m).
**Decyzja.**
- Link `tykocin-dw671-to-rynek` (`Data/Streaming/route_links.yaml`, destination `tykocin`, `replaces_route: tykocin`):
  wjazd ze szwu z `dw671-tykocin-09`, DW671 Puchalskiego, most na Narwi, róg SE placu, postój. Trasa kontrolna kafla
  (kamery, QA, spawn) zostaje do krawędzi kafla.
- Nowe pole linku `stop_epsg2180` (`route_links.py::_stop`): link jest ucinany w punkcie pasa najbliższym postojowi
  (≤ 3 m od osi pasa, nie na pierwszych/ostatnich 2 m) — autopilot staje na końcu ścieżki, GPS ma ten sam punkt.
- Skręt w prawo Puchalskiego → południowa pierzeja (jezdnia 5 m, BDOT10k): po osi pasa opony naczepy ścinały narożnik
  (30 punktów opon poza twardą nawierzchnią, `link_swept_check`). `swing` 1,5 m w lewo, ±25 m → 0 / 0 (przeszukane
  1,0–3,0 m × 15–30 m; 1,0 m / 20 m zostawia 9 punktów na krawężniku). WORKING_VALUE.
- `tools/ui/build_nav_trips.py`: cel podróży = koniec linku podróży, który zastępuje / kontynuuje trasę ostatniego kafla
  (`goal_of`); `nav_trips.json`: tykocin goal (751818,485 600215,101) zamiast krawędzi kafla (751346,7 599295,0).

## 3. Magenta na słupkach ekranów (`bialystok-knyszynska`)
**Przyczyna (sprawdzona na main 0eefa4c8f + wspólny derived).** `Data/raw/derived` jest junction do main (D43), a
`Data/Regions/<id>/generated/world_manifest.json` jest per gałąź. regen-wave-s24 przebudował kafle (GLB od razu
w main), manifesty czekają na scalenie. `RegionImporter` nie znajduje materiału w manifeście → pusty slot → magenta.
Brakuje w manifestach main: `bialystok-knyszynska` — `noise_post_light`, `wood_trim_white`; `tykocin`,
`dw671-tykocin-09` — `wood_trim_white`; w manifestach regen-wave-s24 — komplet. (`knyszyn`: 3 materiały brakują także
w regen-wave — kafel spoza fali, do właściciela kafla.) Materiał jako taki jest poprawny (`materials.py`).
**Decyzja.** Bez zmiany materiału: naprawą jest scalenie regen-wave-s24. Nowa sonda
`tools/worldgen/qa/manifest_materials.py --tiles …` (exit 1 = materiał z GLB nieobecny w manifeście tej gałęzi) —
uruchamiać przed importem kafla zbudowanego w innym worktree.
**Sprawdzone renderem:** import Win64 `bialystok-knyszynska` z manifestem regen-wave-s24 (GLB ze wspólnego derived),
visual-qa High / clear, kamera `seam_e_into_tile` (ekrany „clear” przy Kleeberga, E ~974 N ~−760): słupki jasnoszare,
panele przezroczyste, 0 pikseli magenty (próg R,B > 0,7, G < 0,3) — `vqa/knyszynska/seam-e-into-tile_posts.jpg`.

## 4. `maxaxleload=10` na DK65 (i DK64, DW671…) w OSM
**Źródła.**
- Historia OSM (API 0.6, 2026-11-19): tag dodany 2017-10-31 zestawem zmian 53384754 (m.in. w27718745, w286989049,
  w208187096, w232511647) z `source:maxaxleload = "Rozporządzenie Ministra Infrastruktury i Budownictwa z dnia
  21 kwietnia 2017 r"`; pojedyncze późniejsze drogi skopiowały tag i źródło (np. w1024956365, 2022-01-26).
- Overpass 2026-11-19, bbox 53,05–53,60 N × 22,70–23,30 E: 78 dróg z `maxaxleload=10`, **wszystkie** z tym źródłem
  (DK65 36, DK64 11, drogi bez ref 31); DK65 ma też 108 odcinków z 11,5 t (źródło Dz.U. 2011 nr 222 poz. 1321).
- Rozporządzenie = Dz.U. 2017 poz. 878 (wykaz dróg dla nacisku do 10 t na podstawie dawnego art. 41 ust. 2 ustawy
  o drogach publicznych); rekord ELI eli.gov.pl/eli/DU/2017/878: „uznany za uchylony”, 2021-03-13.
- Ustawa z 18 grudnia 2020 (Dz.U. 2021 poz. 54, ogłoszona 2021-01-11, w życie po 60 dniach, 13.03.2021 wg trans.info /
  bankier.pl): art. 41 ust. 1 — po drogach publicznych ruch pojazdów o nacisku pojedynczej osi napędowej do 11,5 t;
  niższy limit (10 t / 8 t) tylko znakiem zarządcy (B-19) lub uchwałą rady gminy (art. 41 ust. 2–3); 8 t na drogach
  nieutwardzonych (art. 41b). Znaki E-15a/E-15b przestały oznaczać sieć 11,5 t.
- Znaki B-19: brak w OSM w tym obszarze (Overpass 2026-11-19, `traffic_sign~B-19`). Zdjęć ulicznych nie sprawdzono:
  token Mapillary odrzucony 2026-11-19 („Invalid OAuth 2.0 Access Token”) — **UNVERIFIED** na zdjęciach.
**Wniosek.** Limit 10 t to nieaktualne dane OSM (podstawa prawna uchylona 13.03.2021), nie realne ograniczenie —
o ile nie stoi tam B-19, którego nic nie wskazuje.
**Decyzja.** authored_override `Data/Overrides/osm_tag_fixes.yaml` (78 dróg OSM, `maxaxleload` tylko gdy = "10" → brak
limitu), czytany przez `navgraph/build_route_graph.py` (`load_tag_fixes`, `fixed_attr`) przy każdej przebudowie
`<id>_route.bytes` (przeżywa reimport; siatek świata nie dotyczy). Przebudowane grafy 24 kafli. Mechanizm
`RelaxTruckLimits` z ADR 0302 zostaje dla realnych limitów. Drogę z prawdziwym B-19 trzeba usunąć z listy (albo
zmapować w OSM ze źródłem po 2021-03-13). Warto zgłosić poprawkę w OSM (`maxaxleload` usunąć / 11.5) — decyzja
właściciela (edycja publicznych danych).

## Liczby (zmierzone 2026-11-19, `artifacts/corridor-polish-s24/`)
| | przed | po |
|---|---|---|
| `route_obstacles --tiles tykocin` (GLB z regen-wave) | 1 collider (krawężnik 0,38 m, s 1902), 1 visual | **0 / 0** |
| trasa kontrolna `tykocin` | 2542 m, 5 krawędzi spoza DW671 | 2558 m, 0 |
| link `tykocin-dw671-to-rynek` | — | 1309 m; `link_swept_check` 0 punktów opon poza twardą nawierzchnią, 0 poza jezdnią |
| cel GPS `tykocin` | krawędź S kafla | Rynek (751818,5 600215,1) |
| krawędzie grafów tras z naciskiem < 11,5 t (15 kafli korytarza) | DK65 w 11 kaflach (ADR 0302) | **0** |
| pytest `tests/gis/test_route_links_s23.py` | | 13/13 (1 nowy) |
| pytest `tools/worldgen/navgraph/tests` | | 58/58 (3 nowe) |

Przejazd playerem Windows (exe `kamion-0.1.0-c41c3083a1-dirty-regions`: `dw671-tykocin-09` + `tykocin`, import Win64
z manifestami regen-wave-s24; Medium, 60 FPS cap, autopilot 50 km/h, `-stream 1 -route_to tykocin -shot_every 20
-nav_log 10`, 400 s, exit 0, 0 wyjątków, log `artifacts/corridor-polish-s24/run/win-run-20261119-061434.log`):
- `[NAV] trip tykocin planned: legs 27..28, length 2283 m, ETA 139 s`; `[STREAM] route continued by link
  tykocin-dw671-to-rynek in tykocin: +1309 m`; `[NAV] region switched to tykocin … pin=trip tykocin kept (leg 28/28,
  remaining 1295 m)`; wyładowanie kafla startowego bez zmian w GPS.
- t = 217 s: ciężarówka stoi na (451,1 −103,4) w ramce kafla `tykocin` — 3,6 m przed końcem linku (autopilot staje
  < 4 m przed końcem ścieżki, `PathFollowerDriverInput`), GPS `remaining 4 m`; do końca przebiegu bez ruchu.
- Zrzut t = 240 s (`run/run_t0240.jpg`): minimapa „Cel osiągnięty”, „Plac Stefana Czarnieckiego”, 0 km/h, pas przy
  krawężniku od strony placu; t = 200 s (`run_t0200.jpg`): „65 m” na południowej pierzei.
- p50/p95/p99 = 16,67 ms (cap 60 FPS) na końcu przebiegu — nie pomiar wydajności (maszyna dewelopera).

## Znalezisko: most na Narwi w Tykocinie (DW671) — limit dla zestawu
Log przejazdu: „legs over a truck limit 1” = odcinek `tykocin`. OSM w96942026 (most Puchalskiego, `start_date=1910`,
`bridge=yes`): `maxheight=3.7` (od 2017-01-23, zestaw zmian 45395651) i `maxweight:hgv=12 ton` (od 2026-08-22, zestaw
zmian 187860421, mapper lokalny). To nie jest ślad uchylonego rozporządzenia (inna wartość, inna data, inny tag) —
najpewniej B-18 / B-16 na moście kratownicowym. Zestaw 40 t / 4,0 m nie powinien tamtędy jechać: realny dojazd
ciężarówki na Rynek Tykocina jest od południa (DW671 Sokołowska od S8), nie od Knyszyna. Tu nic nie zmieniono (GPS
już oznacza odcinek, ADR 0302); świat nie ma kratownicy nad jezdnią (sonda B nic nie widzi na 3,7 m).
**UNVERIFIED** bez zdjęcia znaków; decyzja właściciela: (a) cel „Tykocin” od południa (korytarz przez S8 / węzeł
Tykocin, kafle niezbudowane), (b) zostawić dojazd od północy jako „zjazd z ograniczeniem” z ostrzeżeniem,
(c) zweryfikować znaki zdjęciem.

## Konsekwencje / otwarte
- Po scaleniu regen-wave-s24 sprawdzić `manifest_materials.py` dla wszystkich kafli korytarza (knyszyn: 3 materiały).
- Trasa kontrolna innych kafli może tak samo skracać przez `service` (np. `dw671-tykocin-03`: 118 m `service`
  w trasie kontrolnej) — sprawdzić tym samym skanem; industrial-c celowo (zajezdnia).
- Postój na Rynku to zatrzymanie przy krawężniku na drodze wojewódzkiej (brak miejsca parkingowego dla zestawu); gdy
  pojawi się logika zleceń/rozładunku, miejsce rozładunku powinno być autorskim punktem tej samej klasy.

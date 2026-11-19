# ADR 0300 — ekran akustyczny w pasie rampy wiaduktu Kleeberga; GPS i minimapa podążają za streamingiem kafli

Status: Proposed (agent walls-gps-s24, 2026-11-19). Numer nadany przez lidera.
Powiązane: ADR 0069 / 0293 (ekrany akustyczne), 0146 (ekrany na pomostach), 0208 (`DeckKeepout` dla płotów i murów),
0150 / 0283 (GPS, minimapa, ekran nawigacji), 0235 / 0273 / 0285 (streaming kafli, rebase origin, trasy łączące).

## Kontekst
Testowy przejazd właściciela autopilotem Białystok → Tykocin (exe `kamion-0.1.0-4f5e98a16f-regions`, `-stream 1
-route_to tykocin`, start `bialystok-industrial-c`, log `win-run-20261118-235459.log`, zrzut
`artifacts/lead-s24/video/wlasciciel-sciany-knyszynska.webp`) pokazał dwa błędy:
1. ciężarówka wjechała w ekran akustyczny stojący w jej pasie zaraz po logu „route continued into bialystok-knyszynska”;
2. minimapa pokazywała siatkę ulic za ciężarówką, pod nią pusto.

## Ustalenia
**1. Ekran.** Log „route continued into X” pada, gdy kafel X staje się Ready (~380 m przed szwem), więc ciężarówka
była jeszcze w `bialystok-kleeberga`. Nowa sonda `tools/worldgen/qa/route_obstacles.py` (siatki GLB High, obwiednia
nadwozia wzdłuż trasy kafla) znalazła jedną przeszkodę na całym korytarzu `bialystok-tykocin` (28 kafli, ~55 km):
`bialystok-kleeberga`, trasa kafla s 1806–1856 m (E −663…−700, N −509…−531), `collision_fence` + `noise_glass` /
`noise_post_light` od −3,9 do +3,9 m względem jezdni. Trasa biegnie tam po wiadukcie Kleeberga na zachód (OSM
w301702368, `bridge=viaduct`, `layer=1`); jego rampa zaczyna się ~1 m nad terenem. Ekran z BDOT10k/OSM stoi na ziemi
przy jezdni naziemnej obok rampy. `noise_barriers()` przycina ekrany tylko `roads_poly` — śladem jezdni naziemnych
(warstwa `road`); trójkąty pomostów (warstwa `bridge`) w nim nie występują, więc ekran wysoki na 3,5–4 m przebijał niski
koniec pomostu i stał w prawym pasie. Ta sama klasa błędu co mur oporowy w ADR 0208 — tam naprawiona tylko dla płotów
i murów. Problem jest w obecnym main (kafel przebudowany przez regen-wave-s24 19.11 00:07, ekrany już `clear` z ADR 0293).

**2. GPS.** `NavigationInstaller` tworzy `NavigationService` (i ekran nawigacji `CabScreens`) dla regionu startowego:
graf tras i mapa tego regionu, pozycja w ramce jego `WorldRoute`. Streaming nic im nie mówi: po rebase'ach pozycja
była liczona w ramce kafla startowego (poza jego mapą), a po wyładowaniu kafla startowego (`root destroyed`) ramka stała
się `null` i pozycja szła w ramce świata — punkt wypadał w środku mapy kafla startowego, stąd jego ulice „za
ciężarówką”. Dodatkowo mapa KNAV (`Resources/CabDisplay/Nav/<id>.bytes`) istniała tylko dla `bialystok-industrial-c`
(pozostałe 43 regiony miały tylko graf tras `_route.bytes`).

## Decyzja
### A — ekrany poza pasami pomostów (`streetscape/furniture.py`, `stage.py`)
`noise_barriers(..., decks=)` używa tego samego `DeckKeepout` co `fences()` (ADR 0208): punkt ekranu leżący na trójkącie
jezdni pomostu, którego wierzch (teren + wysokość ekranu + 0,1 m słupka) sięga powyżej `pas − LANE_FLOOR_M`, jest
wycinany (trójkąty + 0,3 m). Ekran pod pomostem, który go przewyższa, zostaje. Raport
`streetscape_qa.json → furniture.noise_barriers.cut_on_deck_carriageway_m`.

### B — QA przeszkód na trasie autopilota (`tools/worldgen/qa/route_obstacles.py`)
Dla każdego kafla korytarza (`route_links.json → corridors`) trasa kafla i linki leżące w kaflu są przemiatane obwiednią
ciężarówki (±1,2 m od osi pasa, 0,35–3,8 m nad powierzchnią kolizji pod osią — WORKING_VALUE) na siatkach GLB High:
trójkąty `road_collision` niebędące nawierzchnią = **collider** (exit 1), meble/most/budynki = **visual** (ostrzeżenie).
Poziom nawierzchni śledzi poprzednią próbkę (pomost nad drogą naziemną). ~10 s na kafel.

### C — GPS za streamingiem (`Gameplay/NavStreamFollower.cs`, `UI/Navigation/NavigationService.cs`, `NavLayout`, mapy)
- `NavStreamFollower` (co 0,25 s): kafel pod ciężarówką z `WorldStreamer` (`TileAt(anchor + pozycja)`); gdy jest inny niż
  kafel GPS i ciężarówka jest ≥ 15 m w jego środku (histereza szwu, WORKING_VALUE) albo ramka GPS zniknęła →
  `NavigationService.SwitchRegion(id, ramka, przesunięcie)`: graf + mapa nowego kafla, ramka = korzeń regionu kafla
  (`WorldStreamer.FrameOf`, przesuwany przez rebase razem z ciężarówką — pozycja bez skoku), cel przeniesiony do ramki
  nowego kafla i zachowany, gdy leży na jego drodze. `CabScreens` dostaje tę samą ramkę i mapę.
- Sąsiednie kafle Ready są rysowane wokół bieżącego (`NavMapData.Shifted` o różnicę originów, jedna siatka statyczna
  `NavLayout.BuildStatic(lista)`), przebudowa przy zmianie zbioru rezydentnych kafli. Widoki (minimapa, pełna mapa,
  ekran kabiny) pobierają siatkę ponownie po zmianie `MapVersion`.
- Mapy KNAV wygenerowane dla wszystkich 44 regionów z grafem tras (`tools/ui/build_nav_map.py`, ~2,5 MB w Resources;
  licencja jak `nav-map-data` w `docs/LICENSES.md`).
- Bez streamingu (jeden region, DrivingLab) nic się nie zmienia.

## Liczby (zmierzone 2026-11-19, `artifacts/walls-gps-s24/`)
| | przed | po |
|---|---|---|
| `route_obstacles` korytarz `bialystok-tykocin` (28 kafli, main) | kleeberga: 1 collider (s 1806–1856, 27 próbek); tykocin: 1 próbka krawężnika | — |
| `route_obstacles` kleeberga + knyszynska po przebudowie kleeberga | 1 collider | **0** |
| `bialystok-kleeberga` `noise_barriers.cut_on_deck_carriageway_m` | — | 69,9 m (ekrany 1158 m → zbudowane) |
| `build_world` kleeberga (slot heavy) | 3891 s (regen-wave) | 3196 s |
| testy pytest `tests/gis/test_walls_on_deck_0300.py` + 0208 + c_p2_s23 | | 4 nowe + 16 zielonych |
| PlayMode `NavStreamFollowTests` (5) + `NavHudTests` + `CabScreensTests` | | 20/21; `Capture_Devices` pada na brak prefabu TRAKT w worktree (środowisko) |
| mapy KNAV | 1 region | 44 regiony, 2,5 MB |

Przejazdy w playerze Windows (GTX 1070, Medium, 1600×900, autopilot 50 km/h, `-stream 1 -route_to tykocin`):
- exe `kamion-0.1.0-cd208786be-dirty-regions` (kleeberga przebudowana + knyszynska + dk65-01), start
  `bialystok-kleeberga -route_s 1700`, 380 s: przejazd rampą wiaduktu Kleeberga bez ekranu w pasie (zrzut t = 20 s
  w miejscu z nagrania właściciela), `[NAV] region switched to bialystok-knyszynska` → rebase #1 → `unload start region
  bialystok-kleeberga (root destroyed)` → `[NAV] region switched to dk65-01` → rebase #2; całe 2961 m knyszynska
  przejechane, 0 wyjątków. Minimapa na każdym zrzucie z drogą pod strzałką ciężarówki.
- exe `kamion-0.1.0-f2b35ba227-dirty-regions` (knyszynska + dk65-01), szew knyszynska → dk65-01: jak wyżej.

Uwaga (tylko worktree): magenta na słupkach ekranów w knyszynska — kafel zaimportowany z GLB regen-wave (z
`noise_post_light`, ADR 0293) przy starszym `world_manifest.json` z main (brak `M_noise_post_light.mat`); po scaleniu
regen-wave-s24 (zaktualizowane manifesty) do ponownego sprawdzenia.

## Konsekwencje
- Po scaleniu przebudować kafle z ekranami przy pomostach. Pewnie: `bialystok-kleeberga` (przebudowany tu do weryfikacji
  do wspólnego `Data/raw/derived`). Pozostałe kafle korytarza nie mają kolizji na trasie (sonda B), ale reguła działa
  na każdym kaflu z pomostami — przy następnej fali regeneracji wejdzie sama.
- Trasy GPS (cel z pełnej mapy) nadal planowane w obrębie jednego kafla (graf per kafel); cel poza kaflem jest
  porzucany przy przejściu przez szew. Planowanie między kaflami = osobne zadanie.
- `tykocin` — sonda B: 1 próbka krawężnika 0,38 m w obwiedni (s 1902, E 138,9 N −454,7) i słup budynku — do sprawdzenia
  przez właściciela kafla (poza zakresem).

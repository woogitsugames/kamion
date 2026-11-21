# STATUS route-start-s24 — trasa autopilota przy starcie w kafelku (build #3 P2 GPS „zawróć”, DK8)

Gałąź `route-start-s24` (od origin/main 2eab56e0f + lokalny merge `origin/gps-dk8-s24` cc54e7381 — nie była jeszcze w main).

## Zmiany
- `Data/Streaming/route_links.yaml:12-31` — `c-dk8-to-maczka`: `after_route` -> `replaces_route: bialystok-industrial-c`
  (od startu C, rondo Pamięci Bieżeństwa, Andersa, skręt na zachód na węźle DK8/DK19, DK8 Maczka do szwu);
  swing 2,0 m / ±30 m na rondzie jak w `c-andersa-to-wygoda` (bez niego 3 pkt opon poza nawierzchnią, s 363-367 m).
  `route_links.json` przeliczony: zmienił się tylko ten link (1510 m od końca trasy kontrolnej -> 2171 m od startu C;
  łącznie z trasą kontrolną było 3908 m), korytarze bez zmian (gap 0,0 m).
- `game/Assets/_Project/Core/StreamedRoute.cs:21-37` — nowy `IReplaceableStreamedRoute.TryReplacePath` (osobny interfejs,
  stare implementacje/fake'i się kompilują).
- `game/Assets/_Project/Input/PathFollowerDriverInput.cs:111-142` — `TryReplacePath`: podmiana ścieżki z zachowaniem
  postępu (najbliższy punkt nowej ścieżki do s+50 m; > maxOffset albo route_end -> false, nic nie zmienia).
- `game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:93-96, 381, 516-631` — `ReplaceStartRoute` (raz, przed
  pierwszym dołożeniem: link `replaces_route` kafla startowego zgodny z `-route_to` podmienia trasę startową, log
  `[STREAM] start route of <tile> replaced by link <id>`); `FindLink`: link z konkretnym `destination` wygrywa z `any`
  (też przy wjeździe z innego kafla); `routeReplaceMaxOffsetM = 3`.
- `game/Assets/_Project/World/Runtime/Streaming/RouteLinks.cs:86-92` — `IsAnyDestination`.
- `game/Assets/_Project/Gameplay/Resources/Nav/nav_trips.json` — przeliczony (`build_nav_trips.py` był stale już na main
  po przebudowie C; szwy przesunięte o cm).
- Testy: nav-runner `NavTripDk8MaczkaTests` (un-skip `ControlPath_ForTripTykocin_HasNoUTurnAndNoDetour`, nowa teoria
  `ControlPath_EveryTripFromC_TakesItsLink_NoUTurnNoDetour` x6), golden routes odświeżone (36 par, te same manewry,
  |Δdługości| <= 6,8 m, |ΔturnDeg| <= 1,1°), EditMode `WorldStreamerRouteLinksTests` (4 nowe, NIEURUCHOMIONE — lider),
  pytest `test_c_maczka_link_replaces_the_c_route_and_turns_west_at_dk8_dk19`, `test_road_widen_0306` (C = `link:`).

## Tripy przy starcie w C (ścieżka autopilota vs odcinek GPS do końca linku C)
| trip | przed (runtime main) | po |
|---|---|---|
| tykocin / s8 / monki / maczka | trasa C + `c-dk8-to-maczka` after_route: 3908 m, zawracanie w pasie dzielącym (-821, 861) | `c-dk8-to-maczka`: 2171 m (GPS 2172 m), brak U-turn |
| wasilkow | `replaces_route` ignorowane przy starcie -> trasa C + link Maczki (zły kierunek) | `c-dk8-north-to-wasilkow` 2755 m, brak U-turn |
| dojlidy | jw. (pojechałaby do Maczki) | `c-andersa-to-wygoda` 963 m, brak U-turn |

## Testy
- nav-runner: 107 pass / 1 fail (`NavVoiceTests.GoldenRoute_Roundabout_AnnouncesExitAndRingName` — znany, był przed zmianą,
  dotyczy głosu „na rondzie Putry”, nie trasy). Przed: 23 fail (22 golden + ten). `ZeroGc_PlanAndTrack` raz flaky w pełnym
  przebiegu, osobno zielony.
- pytest (`test_route_links_s23`, `test_dk8_north_s24`, `test_road_widen_0306`, `test_effective_graph_readers`,
  `test_roundabout_0274`): 144 pass (w tym bramka swept path dla wszystkich linków zbudowanych kafli) + nowy test 1 pass.
- `link_swept_check.py c-dk8-to-maczka`: 21550 pkt opon, 0 poza nawierzchnią, 0 poza jezdnią.
- `route_links.py --check` OK, `build_nav_trips.py --check` fresh.

## Uwagi dla lidera
- Zmiana zachowania także dla innych startów w kafelku z `replaces_route`: `-scene knyszyn` (tykocin/monki) jedzie teraz
  od razu linkiem przez rondo DK65/DW671 zamiast trasy kontrolnej do Rynku + `knyszyn-rynek-*` (te linki zostają jako
  zapas, gdy podmiana odmówi); `-scene tykocin` jedzie do postoju na Rynku. Pomiary z `route_end` (bramki) — bez zmian
  (podmiana nie działa przy route_end).
- Worktree ma junction `Data/raw` -> main `Data/raw` (do link_swept_check): odłączyć przed usunięciem worktree.

NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` (WorldStreamerRouteLinksTests +
NavRoutingTests z gps-dk8-s24), potem przejazd buildu: `pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene <C> -Autopilot route -Speed 50`
i w logu `[STREAM] start route of bialystok-industrial-c replaced by link c-dk8-to-maczka`, brak „zawróć” na al. Tysiąclecia.

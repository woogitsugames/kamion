# STATUS nav-route-s24 (ADR 0302 — GPS przez wiele kafli)

- 19.11: worktree + Library (robocopy z win-build). Kod: `UI/Navigation/NavTrip.cs` (trasa = łańcuch odcinków per kafel,
  sklejana w jedną RoutePath w ramce bieżącego kafla), `NavigationService` (StartTrip/StepTrip/ReplanTripLeg, SwitchRegion
  zachowuje cel), `NavStreamFollower` (auto-start celu z -route_to / PlayerPrefs / routeDestination), przycisk „Cel trasy”
  w pełnej mapie, ETA ekranu kabiny z NavEta. Dane `Gameplay/Resources/Nav/nav_trips.json` (`tools/ui/build_nav_trips.py`).
- Testy PlayMode `NavTripTests` (8) — w toku.
- NASTĘPNY KROK: `pwsh scripts/test.ps1 -Platform PlayMode -Filter "Game.Tests.NavTripTests|Game.Tests.NavStreamFollowTests" -BuildTarget Win64` (PlayMode NavTrip|NavStreamFollow), potem build 3 regionów.
- 04:25: PlayMode 33/33 (NavTrip 8, NavStreamFollow 5, NavHud, NavReachabilityService, CabScreens). nav-runner dotnet 94/94.
  Znalezisko: DK65 `maxaxleload=10` w OSM → ścisły planer NoPath; odcinek z `RelaxTruckLimits` + oznaczenie. Trasa tykocin z
  kleeberga 41 756 m, planowanie 1,2 ms w 26 klatkach (max 0,25 ms/odcinek, edytor), śledzenie 3,8 µs/krok, 0 B GC.
- Build 3 regionów w toku (`_Generated` kleeberga/knyszynska/dk65-01 + Truck/Trailer skopiowane z win-build, kafle z 17.11).
- NASTĘPNY KROK: `& .\scripts\build-windows.ps1 -SkipBuild -Exe <exe> -Run -Scene bialystok-kleeberga -Autopilot route -Speed 50 -RunSeconds 400 -ShotSeconds 20 -ExtraPlayerArgs @('-stream','1','-route_to','tykocin','-route_s','1900','-nav_log','5','-shot_every','20')`
- 04:40: build `artifacts/win/kamion-0.1.0-f72bf08d6e-dirty-regions` (3 regiony + WorldC z win-build) OK, 449 s. Przejazd 400 s w toku.

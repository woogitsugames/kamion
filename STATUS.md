# STATUS nav-route-s24 (ADR 0302 — GPS przez wiele kafli)

- 19.11: worktree + Library (robocopy z win-build). Kod: `UI/Navigation/NavTrip.cs` (trasa = łańcuch odcinków per kafel,
  sklejana w jedną RoutePath w ramce bieżącego kafla), `NavigationService` (StartTrip/StepTrip/ReplanTripLeg, SwitchRegion
  zachowuje cel), `NavStreamFollower` (auto-start celu z -route_to / PlayerPrefs / routeDestination), przycisk „Cel trasy”
  w pełnej mapie, ETA ekranu kabiny z NavEta. Dane `Gameplay/Resources/Nav/nav_trips.json` (`tools/ui/build_nav_trips.py`).
- Testy PlayMode `NavTripTests` (8) — w toku.
- NASTĘPNY KROK: `pwsh -File <scratchpad>/navroute/runtests.ps1` (PlayMode NavTrip|NavStreamFollow), potem build 3 regionów.

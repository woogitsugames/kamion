# STATUS walls-gps-s24 (ADR 0300)
- 19.11: przyczyna 1 (ściany): ekran z BDOT/OSM przy jezdni naziemnej obok rampy wiaduktu Kleeberga (w301702368,
  bialystok-kleeberga E -700..-663 N -545..-496, s 1806..1878 trasy kafla) przebijał niski koniec pomostu i stał w pasie;
  roads_poly nie ma trójkątów warstwy bridge. Poprawka: DeckKeepout (ADR 0208) także w noise_barriers. Test tests/gis/test_walls_on_deck_0300.py (4 zielone).
- NASTĘPNY KROK: narzędzie QA przeszkód na trasie korytarza (tools/worldgen/qa/route_obstacles.py), potem GPS.
- 19.11 01:4x: GPS: NavStreamFollower + SwitchRegion + mapy sąsiadów; KNAV dla 44 regionów; QA korytarza: 1 kolizja (kleeberga s1806-1856), tykocin 1 krawężnik. Build kleeberga z poprawką w toku (artifacts/walls-gps-s24/build_kleeberga.status), testy PlayMode w toku. ADR 0300 szkic.
- NASTĘPNY KROK: po exit= w build_kleeberga.status: pwsh scripts/import-region.ps1 -Region bialystok-kleeberga (+knyszynska, dk65-01), build-windows -Regions, przejazd.
- 02:15: PlayMode 20/21 (5 nowych zielone; Capture_Devices = brak prefabu TRAKT w worktree, nie moje). Build Win knyszynska+dk65-01: przejazd przez szew -> [NAV] region switched to dk65-01, rebase bez skoku, minimapa z drogą pod ciężarówką (artifacts/walls-gps-s24/after). Build kleeberga z poprawką w toku.
- NASTĘPNY KROK: po exit= w build_kleeberga.status: import-region kleeberga -BuildTarget Win64, build-windows -Regions kleeberga,knyszynska,dk65-01, przejazd od kleeberga -route_s 1700.

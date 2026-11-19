# STATUS walls-gps-s24 (ADR 0300)
- 19.11: przyczyna 1 (ściany): ekran z BDOT/OSM przy jezdni naziemnej obok rampy wiaduktu Kleeberga (w301702368,
  bialystok-kleeberga E -700..-663 N -545..-496, s 1806..1878 trasy kafla) przebijał niski koniec pomostu i stał w pasie;
  roads_poly nie ma trójkątów warstwy bridge. Poprawka: DeckKeepout (ADR 0208) także w noise_barriers. Test tests/gis/test_walls_on_deck_0300.py (4 zielone).
- NASTĘPNY KROK: narzędzie QA przeszkód na trasie korytarza (tools/worldgen/qa/route_obstacles.py), potem GPS.

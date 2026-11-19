# STATUS corridor-polish-s24

- 2026-11-19 05:1x: (1) kerb 0.38 m tykocin s 1902: przyczyna = trasa kontrolna skracała róg Sokołowska/Klasztorna przez jednokierunkowe drogi serwisowe w1426176071/72 (57 m vs 58 m po DW671), wyspa z krawężnikiem w obwiedni. Dodatkowo trasa omijała DW671 na Rynku (północna strona placu). Naprawa: `via_epsg2180` (3 punkty DW671) w `Data/Regions/tykocin/route_endpoints.json` (authored_override), `export-route` → cała trasa na ref 671, 2558 m. route_obstacles tykocin: colliders 0, visual 0 (przed: 1/1).

NASTĘPNY KROK: link `tykocin-dw671-to-rynek` (replaces_route tykocin, stop na Rynku) w `Data/Streaming/route_links.yaml` + `stop_epsg2180` w `tools/worldgen/streaming/route_links.py`; potem `uv run --no-project python tools/ui/build_nav_trips.py`.

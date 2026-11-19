# STATUS corridor-polish-s24

- 2026-11-19 05:1x: (1) kerb 0.38 m tykocin s 1902: przyczyna = trasa kontrolna skracała róg Sokołowska/Klasztorna przez jednokierunkowe drogi serwisowe w1426176071/72 (57 m vs 58 m po DW671), wyspa z krawężnikiem w obwiedni. Dodatkowo trasa omijała DW671 na Rynku (północna strona placu). Naprawa: `via_epsg2180` (3 punkty DW671) w `Data/Regions/tykocin/route_endpoints.json` (authored_override), `export-route` → cała trasa na ref 671, 2558 m. route_obstacles tykocin: colliders 0, visual 0 (przed: 1/1).

NASTĘPNY KROK: link `tykocin-dw671-to-rynek` (replaces_route tykocin, stop na Rynku) w `Data/Streaming/route_links.yaml` + `stop_epsg2180` w `tools/worldgen/streaming/route_links.py`; potem `uv run --no-project python tools/ui/build_nav_trips.py`.
- 05:4x: (2) link `tykocin-dw671-to-rynek` (replaces_route tykocin, destination tykocin, nowy `stop_epsg2180` w route_links.py) 1309 m, koniec (751818.5, 600215.1) = pas zachodni na płd. stronie Rynku między zjazdami; swing 1,5 m/±25 m na narożniku SE (bez niego 30 pkt opon naczepy poza nawierzchnią). nav_trips goal = koniec linku. pytest test_route_links_s23 13/13 (nowy test 0303).
NASTĘPNY KROK: magenta na słupkach (knyszynska) + research DK65 maxaxleload; potem build exe z tykocin + dw671-tykocin-09.

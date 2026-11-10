# roads-p0-r10 (ADR 0076) — STATUS

Galaz: worktree-agent-ad6af5501cb259d76.

- 21:50 Odtworzone na czystym buildzie (build_region + build_world, 4 min): test_route_corridor 64 stacje / 9 uskokow.
  Bisekcja: `network.align_forks` (ADR 0074) przesuwa lacznice w606396463 o 3,25 m w prawo (pod prawy pas Andersy, zgodnie
  z ortofoto), a `scripts/export-route.py` prowadzi trase po surowej osi OSM -> trasa biegnie 0,45 m za lewym kraweznikiem
  lacznicy (klin). Nie 0067/0069. Naprawa: trasa z geometrii generatora (pasy), nie z surowego OSM.
- MA-001/002/012: wspolna przyczyna = jezdnie jednokierunkowe wlaczenia/rozwidlenia nachodza na siebie (osie OSM zbiegaja sie
  w wezle), kazda ma swoj kraweznik -> kraweznik w jezdni sasiada; latka 45 m z roznica wysokosci 1,9 m (garb).
- test_road_fidelity::test_report_not_stale tez czerwony na main (raport sprzed 0074).
- Zakres rozszerzony przez lidera: latarnie/slupki na jezdni (takze przebijajace pomost wiaduktu), krawezniki w poprzek
  jezdni w calym regionie + ratchet, powierzchnie wylaczone = tylko farba.
- Funkcje, ktore zmieniam (dla ADR 0077): network.align_forks (+ nowa abreast), scripts/export-route.py, consistency.py,
  streetscape/furniture.py (lamps/clear_carriageway). NIE ruszam junctions.compute_corners.
- NASTEPNY KROK: uv run --project tools/worldgen python artifacts/roads-p0-r10/scripts/ortho_overlay.py artifacts/roads-p0-r10/after fork_putry:-355:-125:60 ma001:320:-578:45 ma012:-395:-140:60

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
- 23:00 Kod (bez pelnego buildu jeszcze): network.abreast_forks/_push_abreast (wlaczenia z przyrostem pasow ukladane obok
  siebie, poszerzenie jezdni pojedynczej + skos), pipeline.build_network (wspolne z export-route), roads/route.py (trasa =
  srodek prawego pasa wygenerowanej jezdni), drugi przebieg assign_sides(trims=True), flush = asfalt (MAT_FLUSH_ROAD),
  profile 1b (abreast ground), furniture.clear_under_decks (latarnie przebijajace pomost), consistency:
  prop_through_deck + kerb_on_carriageway. Nakladki: artifacts/roads-p0-r10/wip1/*.jpg (MA-012: latka 45 m -> ~15 m).
- NASTEPNY KROK: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c ; uv run --project tools/worldgen python tests/gis/route_corridor.py
- (przejecie po limicie) build_world #1 (283 s): route_corridor 0 przeszkod / 10 uskokow. Przyczyny: (a) trasa cofala sie
  1-2 m na stykach kawalkow pasa (wezel rozwidlenia, wjazd/zjazd z ronda) -> roads/route.py: _trim_joint + _round_corner;
  (b) koniec lacznicy przesuniety o 3,25 m od wezla startowal z wysokosci wezla (0,11 m nad jezdnia Andersa) ->
  profile.shifted_end_heights (krok 1c). build_world #2 (304 s): route_corridor 4792 stacje, 0 uskokow, 0 przeszkod.
- Otwarte z consistency: kerb_on_carriageway 29, prop_on_carriageway 2, furniture_in_lane 1, obstacle_in_lane 2 (poza trasa;
  kandydaci na zgloszenia z filmu: latarnia (-588.9, 19.5), furniture (-694, 69), kraweznik (-781.7, 77.5)).
- NASTEPNY KROK: uv run --project tools/worldgen pytest tests/gis -q

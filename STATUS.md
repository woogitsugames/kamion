# STATUS — seams-0224 (D3, cloud D s21)

- wip 1: `tools/worldgen/qa/seams.py` — szwy kafli (graf + overrides -> sieć generatora, bez builda): szerokość, pasy, linie
  krawędziowe (rozstaw, typ), linia środkowa, pobocza (assign_sides), oświetlenie, położenie osi, z_terrain, roads_qa.
  Pierwszy przebieg: 17 szwów, 62 drogi; porównanie z overrides PR #98 / #80 (`--compare-ref`).
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -k seams -q` + raport docs/reports/SEAMS-DK65-2026-11-15.md
- wip 2: testy `tests/gis/test_seams_0224.py` (11 pass + 1 xfail strict), A1 override tykocin (98071886), raport
  `docs/reports/SEAMS-DK65-2026-11-15.md` + `.json`, ADR 0224. Main: 32 FAIL / 5 UWAGA; po #98 25; po #80 29.
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen python -m tools.worldgen.qa.seams --compare-ref origin/dk65-k1-0220`; P1 po 0216.

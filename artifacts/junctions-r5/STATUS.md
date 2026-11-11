# STATUS — junctions-r5 (ADR 0117: węzły r5, priorytet bariery; wg REVIEW-2026-11-11-s10-0110 „Lista na r5”)

Gałąź `junctions-r5` (z main 60705006). Dowody: `artifacts/junctions-r5/` (renders_<tag>_<tier>_<światło>, logs, scripts, pairs = zdjęcie | render).

- krok 0: baseline b0 = main 60705006 (świat z kopii main, bez regeneracji): kamery węzłów Low clear + High overcast
  (`renders_b0_low_clear/`, `renders_b0_high_overcast/`, `stats.txt` w każdym). Library + zestawy PBR skopiowane z main.
- krok 1 (kod, przed buildem b1): `furniture.guardrail` przepisany — taśma W 310 × 83 mm jako 6 płaskich faset z własnymi
  wierzchołkami (twarde krawędzie), słupki C 100 × 55 z przekładką 0,10 m za belką (belka na licu słupka), na pomoście słupki
  C 120 × 64 na stopkach co 2 m + górna belka skrzynkowa (góra 0,98 m), słupki gruntowe co 4 m; materiał `barrier_steel`:
  0,55 / metal 0,9 → 0,25 / metal 0 + nowy zestaw `barrier_galv` (4,0 × 0,5 m, UV wzdłuż belki / rozwinięcie profilu:
  styk z śrubami, brud na fasetach „do góry”, zacieki, rdza). Pomost Bieżeństwa: `bridge_style.cap_w` 1,0 m (było 1,5),
  lico belki 0,70 m za licem krawężnika; poręcz z poziomymi prętami wraca do assetu hero (`rail_h_m` 1,10, tekstura
  `viaduct_steel.png` — pręty zamiast szczebelków). Reguła `pier_guardrails`: bariera W przy filarze ≤ 4 m od krawędzi jezdni.
  Testy `tests/gis/test_junctions_r4.py` (bariery): 3 passed.
  NASTĘPNY KROK: `bash artifacts/junctions-r5/scripts/fast.sh b1` → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
  → `bash artifacts/junctions-r5/scripts/qa.sh b1 Low clear` → obejrzeć `r4_deck_bz_eye`, `r4_link_bz_a`, `r4_pier_bz`.

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
- krok 2 (b1, sha poniżej): build b1 + import + rendery `renders_b1_low_clear/`, `renders_b1_high_overcast/` — OBEJRZANE: profil W,
  słupki C, górna belka i poręcz z prętami czytelne (`r4_deck_bz_eye`, `r4_link_bz_a`), kapa 1,0 m; ALE `barrier_steel` 0,25 nadal
  za jasny w kadrze (belka sRGB ~185 przy asfalcie 60; zdjęcie 454716: belka 74–102 przy asfalcie 63) → następna wartość ~0,11.
  keytests b1: 125 passed. `guardrails_m` b1: bridge 2916, structure 603, pier 0 (reguła po łańcuchach nie łapała ronda).
  Po b1 (kod, jeszcze NIE zbudowane): `pier_guardrails` przepisane na obrys asfaltu (test offline: 3 biegi, 58,5 m przy filarach
  hero 2,7–4,1 m od jezdni). Ustalenia: (a) `_Generated` skopiowane z main było importem SPRZED 0110 → `renders_b0_*` to nie jest
  uczciwe „przed”; prawdziwy baseline = świat main f260ab36: `bash artifacts/junctions-r5/scripts/baseline.sh m0` (W TOKU — na czas
  działania podmienia `Data/raw/derived/.../world`, `generated/world_manifest.json`, `route_start.json`, asset wiaduktu i
  `viaduct_steel.png` na wersje main, kopie w `artifacts/junctions-r5/_swap/` i `world_cur`; jeśli przerwane: przywrócić ręcznie
  wg końcówki skryptu albo po prostu przebudować `fast.sh`). (b) latarnia `p0_lamp_putry_eye`: w b1 nadal brak — do wyjaśnienia
  (`support_adjustments` na main = 20, nie 28→50; `props_off_carriageway.moved` 48→49). (c) pasmo jodełki wsch.: ortofoto 50 px/m
  (`junctions-r4/trace/e_split_band.jpg`) = klin 1,1 m (E −830,6) → 3,1 m (E −806,2), NIE stałe 2,5 m — geometrii nie zmieniam.
  (d) `p0_kerb_merge_eye`: bieg łańcucha `c:w1101181473…:L` i `authored:dk8-ramp-split-barrier` spotykają się przy E −765 z różnym
  offsetem (jeden z terminalem w ziemię, drugi ucięty) — plan: biegi autorskie pierwsze, ucięty koniec dociągany do sąsiedniego
  biegu (bez terminala), górna belka zawsze schodzi na końcu.
  NASTĘPNY KROK: poczekać na `baseline.sh m0` (log `logs/m0_*`), potem: `barrier_steel` color → ~0.11 w `tools/worldgen/roads/build_world.py`,
  łączenie biegów w `furniture._dedup_guardrail`, nos Putry N (wielokąt elipsy w overrides `putry-n-median-nose`), murek
  `r2_fork_link_eye`; `bash artifacts/junctions-r5/scripts/fast.sh b2 && bash artifacts/junctions-r5/scripts/imp.sh b2` →
  `python artifacts/junctions-r5/scripts/stats_cmp.py artifacts/junctions-r5/renders_m0_low_clear/stats.txt artifacts/junctions-r5/renders_b2_low_clear/stats.txt`
- krok 3 (b3, po resecie limitu): baseline `m0` = świat main f260ab36 zaimportowany w tym worktree (`renders_m0_*`). b3 (łączenie biegów,
  latarnie nie kasowane pod barierami, ocynk 0,11, cięcia trójkątów, nos Putry N): Low clear vs m0 na 102 kamerach: draws −12…+0,
  tris max +1,0 % (`python artifacts/junctions-r5/scripts/stats_cmp.py artifacts/junctions-r5/renders_m0_low_clear/stats.txt artifacts/junctions-r5/renders_b3_low_clear/stats.txt`).
  Swept G3-A −0,10 / −1,12, G3-B −0,14 (= main); fidelity p50 0,36 / p95 2,304 (= main). Latarnia w `p0_lamp_putry_eye` wróciła.
  OBEJRZANE pary `pairs_b3/photo_*` (zdjęcie | render): bariera pomostu ciemna, matowa, W czytelne, kapa wąska. NIE naprawione w b3:
  `p0_kerb_merge_eye` (nadal plątanina biegów po lewej), bariera przy filarze (reguła dała 0 m — dedup z istniejącymi biegami),
  murek `r2_fork_link_eye`.
  NASTĘPNY KROK: `uv run --project tools/worldgen python artifacts/junctions-r5/scripts/dbg_rails.py -765,76,20 560,-715,40` →
  poprawka łączenia → `bash artifacts/junctions-r5/scripts/cycle2.sh b4` → `bash artifacts/junctions-r5/scripts/pairs.sh b4`

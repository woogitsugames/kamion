# STATUS — junctions-r6 (ADR 0123: węzły r6, zamknięcie pkt 4 bramki 3 „bariery”; wg REVIEW-2026-11-11-s10-0117 „Lista na r6”)

Gałąź `junctions-r6` (z main 3540bbdf). Dowody: `artifacts/junctions-r6/` (renders_<tag>_<tier>_<światło>, logs, scripts, ortho, refs).

- krok 0 (baseline m0 = main 3540bbdf zregenerowany w tym worktree: build_world 21:22–21:30, import 21:44): `renders_m0_low_clear/`,
  `renders_m0_high_overcast/` (102 kamery, `stats.txt`); Low overcast / High clear w kolejce do slotu Unity.
  Uwaga: import m0 skompilował już importer z uśpionymi dodatkami r6 (`cast_shadows`, `vertex_grime`, `set_metal` — bez kluczy w manifeście
  m0 nic nie zmieniają); zestawy PBR m0 zbudowane ze starego `sets_facade.py`.
- krok 1 (kod, build b1 zrobiony 21:56 bez pkt d–f): 
  a) cień poręczy: manifest `viaduct_steel.cast_shadows: false` → `RegionImporter.CreateMaterial` wyłącza pass ShadowCaster;
  b) ocynk: `barrier_galv` MaskMap.r = maska metalu (cynk 1, brud/rdza 0), rough 0,56; `barrier_steel` 0,50 / metal → `set_metal` 0,9
     (WORKING, do kalibracji w kadrze); c) kapa: `bridge_concrete.vertex_grime` + COLOR_0.r na wierzchu kapy (`_VERTEX_GRIME` w
     Kamion/World PBR, bez nowego materiału / draw calla), lico bariery 0,70 → 0,42 m za licem krawężnika (pomiar w GLB: `xsec_glb.py`);
  d) `p0_kerb_merge_eye`: koniec bariery POMOSTU nie jest już dociągany do sąsiedniej (zygzak 2,5 m), druga szyna separatora
     `dk8-ramp-split-barrier-n` wg ortofoto, szyny autorskie nie deduplikują się nawzajem;
  e) nos Putry N: kołnierz z kostki na całą szerokość końca mediany + cięcie pasów trawy na obrysie wyspy (`gores._clip_tris`);
  f) murek `r2_fork_link_eye`: kołnierz betonowy na styku „pas trawy / brak pasa” → skarpa z trawy (w siatce terenu);
  g) RING-B: „2 propy na fartuchu” = latarnie `lamp_12m` na POMOŚCIE (z 145,84 / 145,95; rondo ~140) — analiza 2D; ortofoto: latarnie
     dwuramienne stoją między pomostami → `bridge_style.lamps: median` (`furniture.bridge_median_lamps`), a `swept_path_gate3.py`
     pomija propy > 4,5 m nad jezdnią; h) filary Bieżeństwa: rzędy z pomiaru (`pier_lines_en`: rząd przy każdej krawędzi wyspy,
     bez rzędu w środku), bariera przy filarze liczy fartuch jako jezdnię (stoi za krawężnikiem wyspy).
  NASTĘPNY KROK: `bash artifacts/junctions-r6/scripts/loop.sh b2` (po zakończeniu renderów m0) → `bash artifacts/junctions-r6/scripts/imp.sh b2`
  → `python artifacts/junctions-r6/scripts/stats_cmp.py artifacts/junctions-r6/renders_m0_low_clear/stats.txt artifacts/junctions-r6/renders_b2_low_clear/stats.txt`

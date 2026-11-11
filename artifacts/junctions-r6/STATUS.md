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
- krok 2 (b2, 22:04–22:33; build + import + rendery Low clear / High overcast, 102 kamery; `renders_b2_*`):
  budżet vs m0 (`stats_cmp.py`): Low clear max **+0 draws**, tris max +0,7 %; High overcast +0 / +0,8 %. Fidelity p50 0,36 / p95 2,304 (= main).
  Kluczowe testy (`test_junctions_r4, test_hero_bridge, test_gores, test_streetscape, test_world_roads, test_lane_edges`): 110 passed.
  Swept b2: NIE zmierzony (rc 127, pusty log — powtórzyć). Swept m0 = main (RING-B prop 1,31 / 1,79).
  Zmierzone w GLB (`xsec_glb.py 490 -674.6 -0.906 0.424 9 1.2 144 152`): lico krawężnika → lico taśmy 0,65 → ~0,45 m; oś linii
  krawędziowej → lico 1,02 → ~0,85 m. Murek `r2_fork_link_eye`: zniknął (`walls_at.py -350,-136,9`: brak `…:L:7`), jest skarpa z trawy.
  RING-B: latarnie z pomostu przeniesione między pomosty (10 podwójnych, 15 usuniętych), przy wyspie zostają 2 instancje (jedna para).
  Filary: rzędy przy krawędziach wyspy, `guardrails_m.pier` 132 → 172 m; w `r4_pier_bz` bariera jest w kadrze (lewy dół), filara nadal nie
  ma (stoi poza kadrem — żeby wszedł, kolumny musiałyby stać ~3,5–4 m od osi pomostu = przebudowa spodu wiaduktu, domena GPT).
  Luminancja sRGB / asfalt (`lum_set.sh`; zdjęcia: taśma 1,47 pochm. / 1,53 słońce / 0,58 cień; kapa 1,48 / 1,43–1,56; krawężnik 1,40 / 1,35):
  m0 taśma 1,36 (Low clear) / 1,18 (High overcast), kapa 1,64 / 1,77; b2 (metal 0,9) taśma 1,43–1,48 / 1,51–1,64, w cieniu 0,98 (za jasno).
  USTALENIA: (1) szachownica na kapie = cień PORĘCZY assetu (nie bariery); URP przy walidacji materiału Lit z powrotem włącza pass
  ShadowCaster, więc flaga idzie do `WorldInstanceSet.noShadowMaterials` (InstanceImporter / WorldInstances) — KOD JEST, jeszcze NIE
  zaimportowane ani obejrzane; (2) taśma: dodane `shadow_low: false` (`_LowNoShadow`, bariera nie rzuca cienia na Low) — do oceny po
  imporcie, czy potrzebne; (3) krawężnik pomostu jaśniejszy od kapy → eksport jako `bridge_kerb` (0,19; bez nowego draw calla) — kod jest,
  niezbudowane; (4) `p0_kerb_merge_eye`: szyna N skrócona do końca wyspy (E −756), bo nad niższym gruntem nurkowała; nadal bałagan przy
  początku pomostu łącznicy — CZĘŚCIOWO; (5) nos Putry N: kołnierz zamyka czarną szczelinę, ale od północy widać lico krawężnika wyspy
  ~0,15–0,2 m nad niższym poboczem — CZĘŚCIOWO. Iteracja materiału na .mat bez importu: `sub.sh t1` (sky_occ 0,65: taśma 1,27 / 1,1 — za
  ciemno), `sub.sh t2` (metal 0,7, sky_occ 0,35) w toku. Wartości docelowe przenieść do `build_world.MATERIALS["barrier_steel"]`
  (`set_metal`, `sky_occ: [0, y]`) i `bridge_concrete.vertex_grime` (teraz 0,135 w kodzie; t1 = 0,165).
  Brak: rendery m0 Low overcast / High clear (kolejka slotów Unity zagłodziła je 26 min — porzucone), swept b2, pełny pytest, EditMode /
  PlayMode, ADR 0123, pary zdjęcie | render.
  NASTĘPNY KROK: wpisać wartości z t2 do `tools/worldgen/roads/build_world.py`, potem
  `bash artifacts/junctions-r6/scripts/build.sh b3 && bash artifacts/junctions-r6/scripts/imp.sh b3 && bash artifacts/junctions-r6/scripts/post.sh b3 full`
  → `python artifacts/junctions-r6/scripts/stats_cmp.py artifacts/junctions-r6/renders_m0_low_clear/stats.txt artifacts/junctions-r6/renders_b3_low_clear/stats.txt`
  → `bash artifacts/junctions-r6/scripts/lum_set.sh b3` → obejrzeć `r4_deck_bz_eye2` (szachownica), `p0_kerb_merge_eye`, `r4_putry_nose_eye`.
- krok 3 (22:39, w toku): wartości z iteracji wpisane do `build_world.py` (`barrier_steel` 0,50 / `set_metal` 0,9 / `sky_occ` [0, 0,25];
  `vertex_grime` 0,165; t1 kapa / asfalt 1,35 Low clear, 1,46–1,50 High overcast; krawężnik 1,53–1,63 → stąd `bridge_kerb` 0,19),
  ADR 0123 szkic (`docs/adr/0123-junctions-r6-barriers.md`), build b3 + import + 4 zestawy renderów uruchomione jednym poleceniem
  (`logs/b3_all.out`). Polecenie właściciela: po tej operacji STOP.
  NASTĘPNY KROK (gdyby przerwało w trakcie): `bash artifacts/junctions-r6/scripts/build.sh b3 && bash artifacts/junctions-r6/scripts/imp.sh b3`

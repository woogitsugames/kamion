# STATUS — junctions-r3 (ADR 0100: węzły r3 wg REVIEW-2026-11-11-s10-0095)

Gałąź `junctions-r3` (z main 503c89ae). Dowody: `artifacts/junctions-r3/` (zones* = ortofoto | ortofoto + kwadraty P-21; trace = wycinki 1 m;
scripts = narzędzia r2 + zones_plan.py; logs). „Przed” = main b12 z ADR 0095 (b0 tej rundy zbudował się już z nowym kodem P-21).

- krok 1 (P0-1): `roads/p21_hatch.py` — P-21 jako analityczne czworokąty (pas = pudełko ∩ wielokąt → czworokąt między liniami krawędzi
  pasa; fragmenty < 0,35 m odrzucane), obramowanie = 1 czworokąt na krawędź (fazowane narożniki), kąt z jednej osi pola
  (`chevron_axis` + `chevron_apex`, `axis` + `stripe_rel_deg`, `stripe_w_m`/`stripe_gap_m`, `border_edges`), drapowanie komórkami 0,35 m
  z podniesieniem do najwyższej próbki (centroid + środki krawędzi; schodek > 3 cm = komórka odrzucona). Przyczyna połamań:
  długie trójkąty CDT drapowane tylko w narożnikach chowały się pod koroną jezdni (b0: do 2,6 cm pod asfaltem przy lift 6 mm).
  Override'y: DK8 front (jodełka do E −806, wierzchołek do nosa, 35°), s1440 nos (wielokąt przerysowany, oś przez środek), s1440 pasmo
  (równoległe −29° od osi, obramowanie tylko NE), n100 (gęste 0,25/0,25). Test `tests/gis/test_p21_hatch.py` (15).
  NASTĘPNY KROK: `bash artifacts/junctions-r3/scripts/loop.sh b1`
- krok 2 (sha 784b7fc5, 7468bf9c): `roads/aprons.py` (`kind: paved_apron` — analityczne przycięcie trójkątów jezdni do wielokąta,
  z, UV, UV1, COL barycentrycznie; test `tests/gis/test_aprons.py`), `kind: guardrail` (streetscape/furniture.py, bariera autorska),
  zebry / strzałki drapowane komórkami z podniesieniem (`p21_hatch.drape_lift`), UV w metrach dla pasa betonu szerszego niż 0,4 m
  (meshing.KERB_TOP_UV_MAX_W — smugi E −830…−770 N 82), materiał łaty = większość materiałów silnikowych ramion (szwy).
  Override'y: Putry N (2 × P-1 + P-7a × 2 + P-7b przez łatę przejazdu, plac `paved_apron` paving), MA-010 (P-1 pierścienia +
  wlot ramienia płd.), zatoka s 1060 (2 × `paved_apron` sett na „uszach”), rozdział jezdni wsch. E −831…−788 (paint_clear ukośnej
  linii, P-1 N 59,85, P-2b, jodełka do nosa E −805,6, wyspa, bariera, P-21 boczne, P-1e), bariera na wyspie E −782, n100 SE (4 ×
  paint_clear strzałek na wprost, 2 strzałki naprowadzające). Build b1 padł na aprons (np.cross 2D) — naprawione.
  NASTĘPNY KROK: `bash artifacts/junctions-r3/scripts/loop.sh b2`
- krok 3 (sha f3b4ece6 … cbaf26c3): krawężnik mediany — stacje wiejskie przerobione na miejską medianę brały głębokość rowu
  0,60 m jako wysokość krawężnika (DK8 E −888…−768, prawa strona w1101181473): teraz 0,13 m. `kerb_rise.py` (b2): wzniesienia
  krawężnika nad jezdnią ≥ 0,25 m: 1 (j:n1847317049:corner0, 0,6 m — otwarte); wszystkie pionowe ściany 0,25–0,40 m: 52 → 0,
  0,40–0,70 m: 79 630 → 79 009 (reszta = kołnierze pod terenem). b2 fast: plany `plan_b2/` obejrzane (Putry N linie + plac,
  rozdział wsch. jodełka/wyspa/linie, n100 SE strzałki), poprawki: zatoka (współrzędne z planu 8,75 px/m), ukośna linia, ostrze pola.
  W toku: `loop.sh b3` (pełny: pytest gis + swept), potem import Unity + rendery.
  NASTĘPNY KROK: `cat artifacts/junctions-r3/logs/b3_loop.out`; `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
- krok 4 (sha 558e4a88, 6bd07032): s610 — 4 pola P-21 przemierzone (kąt środka 19°, ramienia płn. 20° zamiast −15°, gęste
  0,28/0,28 m). b3 (pełny): fidelity edge p50 0,36 / p95 2,304 (jak przed), pytest gis 387 passed / 1 failed
  (`test_junction_seams_are_watertight`: aprony zatoki zmieniały `src` i dzieliły krawędź szwu łata/taśma → naprawione: ten sam
  `src`, trójkąt przecinany na obrysie części przenoszony w całości; testy `test_aprons.py` 2/2). PHONE_RUN aktywny — Unity czeka.
  W toku: swept b3, `pytest tests/physics tests/gate3`.
  NASTĘPNY KROK: `bash artifacts/junctions-r3/scripts/fast.sh b4`, potem (bez PHONE_RUN) `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
- b3/b4: swept b3 G3-A wide −0,10 / lane −1,12, G3-B −0,14 / −0,14, RING-B +1,61 (= r2 b12, bez pogorszenia). b4 fast: build OK,
  testy kluczowe 51/51, plany `plan_b4/` (s610 gęste P-21, zatoka: kostka na obu „uszach”). W toku: test_world_roads + physics/gate3
  na b4 (`logs/b4_*.log`). Unity czeka na zdjęcie PHONE_RUN (lider s10 gate3 A16).
  NASTĘPNY KROK: (bez PHONE_RUN) `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` → `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Gate3 Data/Regions/bialystok-industrial-c/junctions_cameras.json -OutputDir artifacts/junctions-r3/renders_b4`
- b4 testy: `test_world_roads.py` 15/15 (szwy szczelne po poprawce apronów), `pytest tests/physics tests/gate3` 47 passed / 1 failed
  (znana 0082). Kerb rise ≥ 0,25 m: 1 (j:n1847317049:corner0 E −983 N 66,5 — poza trasą). Override'y 94 zastosowane / 0 nieaktualnych;
  farba autorska 20/20. Czekam na zdjęcie PHONE_RUN (od 10:48).
  NASTĘPNY KROK: jak wyżej (import-region → visual-qa).
- b5 (sha 704c50d6): deduplikacja barier < 1 m (furniture `_dedup_guardrail`; pominięte 24 m, autorskie 36 m). Testy b5: kluczowe 51/51,
  `test_streetscape.py` + `test_world_roads.py` 74/74. ADR 0100 uzupełniony (liczby bez Unity). PHONE_RUN nadal aktywny.
  NASTĘPNY KROK: (bez PHONE_RUN) `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` → visual-qa jak wyżej (renders_b5).
- b6 (sha 21b222a5): UV pasów trawy obrócone/przesunięte hashem paska (powtarzalny „W” na medianach). b6 fast: build OK, testy 51/51.
  Dowody skopiowane do main `artifacts/junctions-r3/` (bez plan_cache.pkl). PHONE_RUN nadal (od 10:48).
  NASTĘPNY KROK: (bez PHONE_RUN) `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` → visual-qa (renders_b6).
- Unity b6: import OK (Low 111,5 / High 240,0 MB; r2: 110,0 / 237,9), 44 kamer High overcast `renders_b6_high/` (obejrzane, `view_b6/`):
  P-21 czyste (n100, DK8 obie strony, s1440, s610), Putry N linie + plac kostki, rozdział wsch. jodełka/wyspa, murek 0,6 m mediany
  zniknął (r2_kerb_merge_main_eye), szew łaty w r2_bay_eye zniknął. Poprawki po renderze: pas betonu N 82 nadal smużył (tekstura
  krawężnika) → `sidewalk_paving`; P-21 s1440 ramp → ukośne −30° od osi; obrót UV trawy cofnięty (wzór „W” bez zmian → to nie UV paska).
  W toku: b8 (fast) → import → rendery High overcast + Low clear (`renders_b8_*`).
  NASTĘPNY KROK: obejrzeć `renders_b8_high/`, PlayMode `pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests"`, EditMode, robocopy.
- b8 Unity: import OK (Low 111,6 / High 240,0 MB), rendery `renders_b8_high/` (44 kamer, High overcast) i `renders_b8_low/` (Low clear),
  PlayMode WorldCRoute|Barrier 3/3 (40 t |dv|/krok 0,121 m/s s=361, solo 0,080 — jak r2). Pas N 82 nadal smużył: reguła krawężnika
  patrzyła na szerokość w 1. stacji (0,06 m) → teraz max po stacjach (sha 02b26dd6). b9: build OK.
  W toku: import b9 → `renders_b9_high/` → EditMode.
  NASTĘPNY KROK: obejrzeć `renders_b9_high/p0_kerb_merge_top.png`; robocopy; raport.
- b10 (sha b82c0c42): wiersz paska jest „pionowy” tylko gdy ma 0 m we WSZYSTKICH stacjach (pas N 82 miał 0 m w 1. stacji → UV/materiał
  krawężnika); teraz `sidewalk_paving` w planie. Testy b10: kluczowe 51/51, terrain_walls + world_roads + streetscape 76/76.
  W toku: import b10 → `renders_b10_high/` → EditMode.
  NASTĘPNY KROK: obejrzeć `renders_b10_high/p0_kerb_merge_top.png`, robocopy, raport.
- KONIEC RUNDY (b10): import OK (Low 111,5 / High 240,0 MB), 44 kamery High overcast `renders_b10_high/` (+ `view_b10/` ≤ 960 px),
  pas N 82 = kostka z plamami (smugi zniknęły), EditMode 223/226 (3 × TruckDoorGlass, znane), PlayMode 3/3 (b8). ADR 0100 gotowy.
  Raport końcowy w odpowiedzi agenta (środowisko blokuje zapis plików raportów .md przez subagenta).
  NASTĘPNY KROK (lider): visual-critic na `artifacts/junctions-r3/view_b10/` + `plan_b10/` + `zones2/`; `git merge junctions-r3`;
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` → export-route →
  `uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q`; zrzut z telefonu.

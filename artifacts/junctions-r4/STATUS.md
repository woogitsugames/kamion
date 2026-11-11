# STATUS — junctions-r4 (ADR 0110: węzły r4 + bariery, wg REVIEW-2026-11-11-s10-0100 i priorytetów bramki 3 pkt 4)

Gałąź `junctions-r4` (z main 7a685901). Dowody: `artifacts/junctions-r4/` (trace = ortofoto z siatką, zones0 = pola P-21,
plan_* = ortofoto | generator, renders_* = kamery Unity, scripts = narzędzia r3 + plan.sh / unity.sh / patch0*.py, logs).

- krok 0: baseline b0 (build + route + fidelity + pytest gis + swept; `logs/b0_*`): fidelity edge p50 0,36 / p95 2,304;
  pytest gis 446 passed / 1 failed (`test_report_not_stale` — źródła zmienione w trakcie buildu b0) / 1 xfailed.
  Kopia świata b0: `Data/raw/derived/bialystok-industrial-c/world_b0` (poza gitem).
- krok 1 (P0, sha 02c2b0a8): pole P-21 północne n10015785253 przerysowane z ortofoto 120 px/m (`trace/n100n.jpg`,
  `zones0/n10015785253-p21-north.jpg`): wielokąt szerszy od wsch. (wierzchołki −216,13/−226,57; −212,21/−223,63; −214,71/−227,54),
  pasy 0,20 / 0,22 m pod 8° (było 0,25/0,25 pod 42° → 1 pas), obramowanie 0,15 m (`border_w_m`), `stripe_min_m` 0,2 → 6 pasów.
  Test `test_p21_hatch`: `stripes_built` ≥ 60 % analitycznych i pokrycie pasami ≥ 15 % pola (roads_qa `stripe_cover`).
- krok 2 (sha ed4abca1 … 9a2e4184): `meshing._emit_verge` — trawa za krawężnikiem bez chodnika na wysokości korony (1 m; w medianie
  do 3 m, nigdy za połowę odstępu do równoległej jezdni; `network._side_gap`), skarpa 1:1,5 zamiast pionowego kołnierza 0,5 m,
  narożniki / nosy też; końce wybiegają (szer. 1 m / 2 m, skarpa 0,06 m/m), po wewn. łuku płytsza skarpa o tym samym nachyleniu,
  brak na narożnikach o skaczącej niwelecie (j:n2591872092), ścisłe wycinanie nad jezdniami i wyspami autorskimi, Douglas–Peucker
  2,5 cm, kołnierz krawężnika niemeszowany tam, gdzie zakrywa go pas (budżet tris). `h` stacji wiejskiej w narożniku mieszanym =
  KERB_HEIGHT (murek 0,6 m n1847317049). Wyspa `putry-n-median-nose` (kostka; domknięcie tępego końca mediany Putry N).
  b1 → b3: terrain_walls 884 (max 1,99) → 450 (max 0,60; strome trójkąty wybiegu skarpy — poprawka 0,06 m/m wchodzi w b5),
  marking_off_carriageway 11 → 3, obstacle_in_lane 2 → 3.
- krok 3 (sha ed4abca1 … 9a2e4184): bariery — barieroporęcz na pomostach (słupki 1,10 m, taśma W, płaskownik 0,92, pochwyt 1,10;
  0,40 m od krawędzi kapy), bariery pomostu hero nie są kasowane przy podmianie wstęg, asset wiaduktu Bieżeństwa bez balustrady
  szczebelkowej (`rail_h_m` 0, Blender przebudował asset w buildzie), balustrada generyczna pominięta przy ekranie, bariera W przy
  jezdni biegnącej obok wiaduktu / rampy w murach (≤ 8 m, ≥ 1 m wyżej: 529 m), jeden ciągły bieg na krawędź (offset wygładzany
  9 m), wolne końce odgięte do gruntu (4 m), dedup gruntowy 2,5 m (pominięte 298 pkt), belka i poręcze po Douglasie–Peuckerze 1 cm.
- krok 4: `meshing._patch_uv1` — łaty skrzyżowań dostają UV1 (pas, odległość od krawędzi) drogi przelotowej (dotąd domyślne −1 / 5 m =
  brak kolein i brudu rynsztoka → jaśniejszy prostokąt); łańcuch < 120 m nie jest „świeżym” asfaltem (Putry N, N 100–120).
- krok 5: rozdział wsch. geometrią — jezdnia główna `lane_edges` [0,5; 3,95; 6,85] + szerokość 10,6 m (strefa P-21 / wyspy leży na
  niej), łącznica = 1 pas 3,8–4,3 m wzdłuż krawężnika płd. (profil offsetu z ortofoto), pole P-21 przód jako klin 0,75 → 3 m,
  wyspa do E −788, pasmo boczne 1 m. (b2: łącznica 4,1–6 m — dobre na planie, wyspa w pasie głównej; b3: przerwa z krawężnikiem
  między wstęgami — odrzucone.)
- krok 6: zatoka s1060 — `paved_apron` wzdłuż linii przerywanej od E −122 do −98 (bez zęba), 4 × `paint_clear` na osierocone łuki;
  strzałki P-9 n100 płd. jako glif `guide_left` z ortofoto 75 px/m (5,1 × 2,75 m).
- b3 (bez Unity): fidelity edge p50 0,36 / p95 2,304 (= b0); swept G3-A wide −0,10 / lane −1,12, G3-B −0,14, RING-B +1,61/+1,75,
  min. prześwit do propów 0,69–0,88 (= b0). Szacunek budżetu (`mesh_budget.frame_estimate`, Low): b2 +5…+15 %, b3 −6…+6,6 % —
  stąd niemeszowany kołnierz + tolerancja 2,5 cm w b4.
  NASTĘPNY KROK: `cat artifacts/junctions-r4/logs/b4_loop.out artifacts/junctions-r4/logs/b4_unity.out`; obejrzeć
  `artifacts/junctions-r4/renders_b4_high/*.png`; `python artifacts/junctions-r4/scripts/stats_cmp.py artifacts/junctions-r4/renders_b0_low/stats.txt artifacts/junctions-r4/renders_b4_low/stats.txt`

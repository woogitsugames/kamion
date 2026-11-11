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
- b4 (Unity: import + 53 kamery High overcast + Low clear, `renders_b4_*`, `view_b4/`): mediany równo z krawężnikiem, murki zniknęły
  (`p0_median_slot_eye`, `r2_fork_link_eye`, `eye_putry_n`), barieroporęcz na pomoście Bieżeństwa + bariera przy łącznicy
  (`r4_deck_bz_eye`, `r4_link_bz_a`), pole n100 N z pasami, strzałki P-9, rozdział wsch. wg ortofoto. Low `stats.txt`: draws +6…+10 na
  kamerach strony Bieżeństwa (materiał `verge_grass` w 23 chunkach drogi) → pasy trawy przeniesione do prymitywów terenu (b6).
- b6/b7: rozdział wsch. wraca na oś OSM na styku z wiaduktem (b4/b6: furniture_in_lane 9 / 2, linie na kapie); linia segregacyjna P-1
  autorska. b7: road_consistency 65 = b0 (7 / 54 / 2 / 2).
- b8 (sha 7d503935): skarpa pasa 1 : 2, pasy trawy w `terrain_walls_qa.verge_strips` (steep 226, skirt 18, max 0,627 m), ściany
  terenu 4 (b0: 3; yard_concrete 1 → 2, w ratchecie), szacunek siatek Low −9,9…+1,3 %, High −6,0…+0,5 % względem b0.
  Unity b8 czeka na zdjęcie blokad PHONE_RUN / GPT_UNITY_HOLD (od 15:53).
  NASTĘPNY KROK: `cat artifacts/junctions-r4/logs/b8_loop.out artifacts/junctions-r4/logs/b8_unity.out`; po renderach:
  `python artifacts/junctions-r4/scripts/stats_cmp.py artifacts/junctions-r4/renders_b0_low/stats.txt artifacts/junctions-r4/renders_b8_low/stats.txt`;
  potem `pwsh scripts/test.ps1 -Platform EditMode`, `pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests"`

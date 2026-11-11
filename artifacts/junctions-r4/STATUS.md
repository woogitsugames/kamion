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

## RAPORT KOŃCOWY (ADR 0110, gałąź `junctions-r4`, sha PENDING)

Wynik: **PARTIAL** — punkty 1–6 zlecenia zrobione w generatorze i zmierzone; brak zrzutu z telefonu i oceny `visual-critic`
(dla lidera); budżet draws na kamerach strony Bieżeństwa nie jest +0 (nowe bariery, patrz niżej).

### Liczby przed / po (build końcowy b11; „przed” = b0)
| miara | przed (b0 = main 7a685901 + pole P-21) | po |
|---|---|---|
| ściany terenu > 0,15 m (`terrain_walls_qa`: count / max) | 3 / 0.345 | 4 / 0.345 ({'skirt:yard_asphalt': 1, 'skirt:yard_concrete': 2, 'skirt:yard_slabs': 1}) |
| pasy trawy: strome trójkąty / pionowe ścianki / max (`verge_strips`) | — | {'max_m': 0.627, 'skirt': 18, 'steep_grass': 226} |
| road_consistency (wszystkie / na trasie) | 65 {'arrow_no_exit': 7, 'lane_blind_end': 54, 'marking_off_carriageway': 2, 'obstacle_in_lane': 2} / {'lane_blind_end': 1} | 65 {'arrow_no_exit': 7, 'lane_blind_end': 54, 'marking_off_carriageway': 2, 'obstacle_in_lane': 2} / {'lane_blind_end': 1} |
| override'y zastosowane / nieaktualne | 94 / 0 | 102 / 0 |
| pole P-21 n100 N: pasy (analityczne / w siatce), pole | main: 1 pas, 3,2 m² (sama ramka) | 6 / 6, 4.0 m², pokrycie 0.315 |
| pola P-21: pasy razem | 322 | 325 |
| bariery [m] (`guardrails_m`) | {'authored': 36, 'bridge': 2892, 'dedup_skipped_pts': 24, 'embankment': 472, 'median': 1126} | {'authored': 36, 'bridge': 2916, 'dedup_dropped_pts': 6, 'dedup_skipped_pts': 299, 'embankment': 482, 'median': 1133, 'structure': 529} |
| pasy trawy w terenie (trójkąty / chunki) | — | {'chunks': 37, 'tris': 48283} |
| szacunek siatek na kadr (`mesh_budget.frame_estimate`, 23 kamery): Low min…max / High min…max | 0 | -9.8…+0.7 % / -6.3…+0.1 % |
| tył krawężnika bez chodnika odsłonięty (za kołnierzem tylko teren; `scripts/kerb_back.py`, wierzchołki korony kołnierza) | 63 735 | 5 349 (−92 %) |
| wzniesienie krawężnika nad jezdnią, max (`scripts/kerb_rise.py`) | 0,60 m (j:n1847317049:corner0) | 0,24 m |
| fidelity trasy: krawędź jezdni vs ortofoto p50 / p95 | 0,36 / 2,304 m | 0,36 / 2,304 m |
| swept path, min. prześwit opon: G3-A wide / lane, G3-B, RING-B v25 / v15 | −0,10 / −1,12, −0,14, +1,61 / +1,75 m | −0,10 / −1,12, −0,14, +1,61 / +1,75 m |
| swept path, min. prześwit do propów: G3-A / G3-B / RING-B | 0,69–0,70 / 0,86–0,88 / 1,44–1,93 m | 0,69–0,70 / 0,86–0,88 / 1,88–2,28 m |
| `pytest tests/gis` | 446 passed, 1 failed (`test_report_not_stale`: źródła zmienione w trakcie buildu b0), 1 xfailed | 457 passed, 1 xfailed (w tym 10 nowych w `test_junctions_r4.py`) |
| `pytest tests/physics tests/gate3` | 47 passed, 1 failed (znana 0082) | 47 passed, 1 failed (ta sama `test_generator_reproduces_committed_scenarios`) |
| prymitywy (= draw) w chunkach Low (`scripts/glb_mats.py world_b0 world low`) | — | +6 `bridge/barrier_steel` (w tym 3 chunki wiaduktu hero, które nie miały barier), −9 `furniture/barrier_post`, −3 `furniture/barrier_steel`, −10 `road/road_asphalt_new`, −1 `road/bridge_concrete`; `verge_grass` +0 |

### Unity (edytor; kamery kontrolne WorldC, 2340 × 1080)
- b8 (stan pośredni: słupki barier jako osobny materiał, bariery w siatce `furniture`, pasy trawy na wszystkich LOD terenu):
  import OK, pamięć świata Low 114,6 / High 252,3 MB (b0: 114,6 / 251,0), 53 kamery High overcast + Low clear obejrzane
  (`view_b8/`); `stats.txt` Low względem b0 na kamerach trasy: draws −4…+4 (stretch-05-docks +8), trisK −10,6…+8,4 % (+11,3 %).
- build końcowy b11 (bariery pomostu i przy wiaduktach w siatce `bridge`, słupki w materiale belki, pasy trawy tylko na LOD0/1 terenu):
  import / rendery / EditMode / PlayMode czekają na zdjęcie blokad `PHONE_RUN` / `GPT_UNITY_HOLD` (od 17:34) — NIE ZMIERZONE.

### Rozliczenie punktów zlecenia
1. **P0 pole P-21 n100 N** — zrobione: 6 pasów 0,20 / 0,22 m pod 8°, wielokąt z ortofoto 120 px/m; test na pustą ramkę.
   PNG: `view_b11/r4_n100_n_top.jpg`, `view_b11/r4_n100_n_eye.jpg`, `zones0/n10015785253-p21-north.jpg`, `plan_b11/n100_north.jpg`.
2. **Nosy i koryta median** — zrobione generycznie: trawa za krawężnikiem na wysokości korony (teren + 48 283 trójkąty w siatce terenu),
   odsłonięte tyły krawężnika 63 735 → 5 349; nos Putry N domknięty wyspą z kostki (nie odwzorowanie 1:1 — otwarte 5 w ADR).
   PNG: `pairs_b11/p0_median_slot_eye.jpg`, `pairs_b11/r2_fork_link_eye.jpg`, `pairs_b11/eye_putry_n.jpg`, `pairs_b11/r2_n100_eye.jpg`,
   `view_b11/r4_putry_nose_eye.jpg`.
3. **Bariery** — zrobione: barieroporęcz na pomostach (Bieżeństwa: wcześniej brak jakiejkolwiek bariery; asset bez balustrady
   szczebelkowej), bariera W przy łącznicach obok wiaduktów (529 m), jeden bieg na krawędź + odgięte końce, bez balustrady przy
   ekranie. „Podwójne linie krawędziowe na wiadukcie”: nie odtworzone (jedna linia na krawędź na renderach pomostu).
   PNG: `pairs_b11/r4_deck_bz_eye.jpg`, `pairs_b11/r4_deck_bz_eye2.jpg`, `pairs_b11/r4_link_bz_a.jpg`, `pairs_b11/r4_link_bz_b.jpg`
   (lewa = render r0 bramki 3, prawa = po), `pairs_b11/p0_kerb_merge_eye.jpg`, `pairs_b11/p0_lamp_w1101181473_eye.jpg`,
   `pairs_b11/g3b-eye-s1482.jpg`.
4. **Szwy łat** — `eye_putry_n`: zrobione (krótki łańcuch nie jest „świeżym asfaltem”, łaty z UV1). `p0_fork_putry_eye`: prostokąt to
   `decal_patch` (łata remontowa z reguły dekali), nie szew — nie ruszone, opisane (otwarte 4 w ADR). PNG: `pairs_b11/eye_putry_n.jpg`,
   `pairs_b11/p0_fork_putry_eye.jpg`.
5. **Rozdział wsch. geometrią** — zrobione danymi (`lane_edges` + profile szerokości / offsetu): krawędź płd. na krawężniku z ortofoto,
   klin P-21 0,75 → 3 m, wyspa do E −788, pas łącznicy 3,8–4,3 m; road_consistency bez zmian (65). Odczyty ±0,5 m.
   PNG: `pairs_b11/r3_e_split_eye.jpg`, `pairs_b11/r3_e_split_top.jpg`, `plan_b11/east_split.jpg`, `trace/e_split_band.jpg`.
6. **Zatoka s1060 / strzałki n100** — zrobione: kostka do linii przerywanej (bez zęba), łuki farby wyczyszczone; strzałki P-9 jako glif
   z ortofoto. Kończący się pas / załom krawężnika / BUS: nie ruszone. PNG: `pairs_b11/r3_bay_w_top.jpg`, `plan_b11/bay_w.jpg`,
   `view_b11/r4_n100_se_top.jpg`, `pairs_b11/r3_n100_se_eye.jpg`, `trace/n100_arrow1.jpg`.

### Napisane / zbudowane / uruchomione / zmierzone
- napisane + zbudowane: generator (roads, streetscape, terrain_mesh), override'y, testy `tests/gis/test_junctions_r4.py` (10),
  `test_p21_hatch` (rozszerzony); asset `viaduct_biezenstwa` przebudowany Blenderem.
- uruchomione + zmierzone: build_world b0…b11, export-route, fidelity, swept path, pytest gis / physics / gate3, import Unity + rendery
  kamer kontrolnych (b0, b4, b8 i końcowy — patrz sekcja Unity), statystyki draws / tris edytora.
- nie uruchomione: telefon (zakaz adb), `visual-critic`.

### Otwarte / ryzyka
Lista w `docs/adr/0110-junctions-r4-barriers.md` („Otwarte”, 9 pozycji). Najważniejsze: draws +1 na chunk wiaduktu hero (nowa bariera),
kapa pomostu o ~1,5 m za szeroka (bariera 1,25 m od jezdni), `decal_patch` w `p0_fork_putry_eye`, nos Putry N jako domknięcie.

### Konflikty / pliki wspólne
`streetscape/furniture.py` (tylko funkcje barier; 0102 nietknięte poza nimi), `streetscape/hero_bridge.py` (1 stała + filtr części;
0105 `_apply_underdeck` nietknięte), `make_viaduct.py` (2 linie), `roads/meshing.py`, `roads/network.py`, `roads/gores.py`,
`roads/build_world.py` (addytywnie), `terrain_mesh/conform.py` (klucz `verge_strips`). `WorldPbrMaterials.cs`, shadery,
`materials.py`: bez zmian. Po scaleniu: regeneracja (build_world → export-route → fidelity) i render kamer `p0_*`, `r2_*`, `r3_*`, `r4_*`.

### Następny krok (lider)
`git merge junctions-r4` → `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` →
`uv run --project tools/worldgen python scripts/export-route.py --region bialystok-industrial-c` →
`uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c` →
`uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q` → `visual-critic` na
`artifacts/junctions-r4/view_b11/`, `pairs_b11/`, `plan_b11/` → pomiar A16 (draws / tris Low na trasie G3-A).

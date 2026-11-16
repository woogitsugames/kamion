# INTEGRATION 2026-11-16 — rail (ADR 0223 / 0268) + #138 (ADR 0272) na main z int-dk65-s22: jedna regeneracja 17 kafli
Agent `rail-dk65-s22`, gałąź `rail-dk65-s22` (worktree `.claude/worktrees/rail-dk65-s22`). Stan: końcowy. Werdykt na końcu.

## Co scalono
1. `git merge origin/main` (`f9a742f0d`, main 507a3406b z int-dk65-s22). Konflikty: `roads/network.py` (pola
   `maxspeed_src` + `lane_follow` — oba), `dk65-04/control_cameras_place.authored.json` (wersja main; kamery `rail_x*`
   dopisuje `cams.py` w łańcuchu).
2. `git merge origin/rural-xsec-0272` (`c44042de2`, #138 / ADR 0272, 9dd946be8). Konflikty: `roads/network.py`
   (argumenty `EdgeSection(...)`: `maxspeed_src`, `ref`, `osm_shoulder` — wszystkie; **P1-3**: jedna definicja
   `walk_mat`, `side_profile` używa `walk_mat(mat)`), `roads/build_world.py` (**P1-4**: filtr `shoulder_gravel` /
   `verge_grass` przeniesiony do `_rail_plan` przez `rail_zone_parts`, więc przebieg 1 i 2 planują ten sam przejazd).
3. Dopisane przy scalaniu:
   - test P1-4 w `tests/gis/test_rural_xsec_0272.py` (`BW._rail_plan`: przejazd na jezdni utwardzonej, 24 słupki);
   - słupki prowadzące przy przejeździe: na krawędzi bez krawężnika 0,25 m za poboczem gruntowym
     (`rail_approach.NetPath.guide_off`, `U1_BEHIND_SHOULDER_M` WORKING_VALUE); pierwszy słupek 1,5 m za urządzeniami
     (`U1_BARRIER_GAP_M`, było 1,0 — 2 z 24 słupków DW671 wypadały < 1 m od masztu lewego sygnalizatora);
   - decyzja lidera: `dk65-opaska-k1` (wariant A ADR 0272, `paved_m 0.35`, `ground_m 0.75` → asfalt 7,3 m) dosłownie
     w `overrides.yaml` kafli dk65-06…11 (PR go nie zawierał);
   - decyzja właściciela: start dk65-06 za rondem — `Data/Regions/dk65-06/route_endpoints.json` `start_s_m: 340`
     (autorskie, przeżywa regenerację), `scripts/export-region-catalog.py` czyta to pole (nigdy bliżej początku trasy
     niż reguła 90 m); katalog: `dk65-06.startS` 90 → 340; `--check` exit 0.

## Regeneracja r3 (`artifacts/rail-dk65-s22/tools/regen.ps1 -Tag r3`, statusy `artifacts/rail-dk65-s22/logs/regen-*.status`)
- **world**: 17 / 17 kafli `tile-<id>-r3 exit=0` (dw671-tykocin-01, dk65-01…11, dk65-monki-01, knyszyn, knyszyn-s,
  knyszyn-w, bialystok-knyszynska); dk65-01, 02, 04 z drugim buildem po `cams.py`; generated zacommitowane po każdym
  kaflu. Tykocin przebudowany jeszcze raz (r3b, exit 0) po zmianie odstępu pierwszego słupka.
- **unity**: import + VQA Low + VQA High — 51 / 51 kroków `exit=0` (r3).
- **final**: `export-route.py` 17 × exit 0; `export-region-catalog.py --check` exit 0; `pytest tests/gis` exit 1
  (5 failed, 1827 passed, 1 skipped, 2 xfailed); EditMode exit 0 (957 total, 956 passed, 0 failed, 1 skipped).
- Trasy startowe: `route_start.json` żadnego kafla się nie zmienił; zmieniły się pliki nawigacji kabiny
  `game/Assets/_Project/UI/Resources/CabDisplay/Nav/knyszyn_route.bytes` (M) i `dk65-01_route.bytes` (+ `.meta`, nowy)
  — zacommitowane (`artifacts/rail-dk65-s22/logs/final-route-diff-r3.txt`).

## pytest tests/gis — 5 faili
| test | ocena |
|---|---|
| `test_dk65_seam_knyszyn_0233.py::test_seam_built_geometry[dk65-11-knyszyn-s-pt1]` | **skutek decyzji lidera** (opaska tylko w 06…11): asfalt 7,3 m w dk65-11 vs 6,78 m w knyszyn-s (0,52 m, tolerancja 0,1 m) → skok krawędzi asfaltu 0,26 m na stronę; linie krawędziowe ciągłe. **Otwarte dla chmury D15.** Test zostawiony czerwony (nie osłabiany). |
| `test_road_fidelity.py::test_report_not_stale` | oczekiwany: `fidelity_qa.json` regionu C nie zna zmienionych plików generatora dróg — przelicza lider w main. |
| `test_far_field.py::test_generated_far_field_qa_and_manifests` | stan wspólnego `Data/raw` regionu C: sha tieru w `Data/raw/derived` ≠ manifest w gicie (C przebudowuje inny agent); kafle tej regeneracji nie biorą udziału. |
| `test_far_field_boundary.py::test_regenerated_building_rectangles_do_not_intersect_region` | jw.: `far_field_gis_cache.json` w `Data/raw/derived` ma schemat `/11`, kod `/12`. |
| `test_streetscape.py::test_instances_reference_existing_prototypes` | jw.: instancje C w `Data/raw` mają `sign_gantry_16_66`, którego nie ma w `world_manifest.json` C w gicie (0 wystąpień także na `origin/main`). |
Regresji własnych: 0 (poza szwem z decyzji). Uwaga: pełny pytest nadpisuje lokalnie generated regionu C i
`art-source/world/materials/materials_spec.json` — cofnięte (`git checkout`), nie commitowane.
Po zmianach po r3 uruchomione: `test_rail_approach_0268.py` 22 passed; `test_start_clear_0262.py` +
`test_region_catalog_0267.py` 47 passed; `test_rural_xsec_0272.py -k rail_zone` 1 passed.

## Oględziny r3 (High; podglądy `artifacts/rail-dk65-s22/vqa/r3/jpg/`, pełne `…/vqa/r3/<kafel>/{Low,High}/`)
- **Tykocin** (`rail-x0-near-a`, `rail-x0-side-eye`, `rail-x0-top`, `rail-x0-far-b`, `rail-xing-from-sw`): pobocze
  gruntowe i linie krawędziowe zamiast krawężnika (zgodnie z Mapillary 828893548045009), słupki prowadzące za
  poboczem, A-9 + tablica + G-1a na 150 m (już nie przy latarni), P-4, P-14, płyty. `rail.json` po r3b: `road_width_m`
  7,26, **24** słupki (5,1…20,1 m co 3 m), G-1c wlotu SW **47 m** (`shifted_m: -3` — poza wylotem drogi serwisowej;
  przy krawężniku w r2b było 45 m), `kerb_cut_m` 0,0 (brak krawężnika), `dropped` []. Render r3 pokazuje 22 słupki
  (stan sprzed r3b); kadry r3b — „Kroki domykające”.
- **Ełcka dk65-02, dk65-03** (`rev-elcka`, `top-elcka`, `drive-mid`): wąski asfalt z poboczem żwirowym, bariery stoją
  na krawędzi pobocza, nie w skarpie. Szerokości w metrach nie mierzyłem z kadru — liczby z testów ADR 0272
  (6,76 m). dk65-04, dk65-05 w ruchu ulicznym: nieoglądane osobno.
- **Przejazdy dk65-01, 02, 04** (`rail-x*-near-a`): krzyże G-3, słupki U-1a, znaki A-10 (wszystkie `speed_src:
  default` 50 km/h → 100 m; dk65-01 wlot b 49 m wg § 78 ust. 3; dk65-04 przejazd na krawędzi kafla: oba wloty
  „no room”, ostrzeżenie `markers_outside_tile`). Wyposażenie nadal z tagów OSM / domyślne (ADR 0223 Otwarte 2).
  Kamery `near` dk65-01/02 stoją na łatach dróg bocznych (kadr do poprawy, nie świat).
- **Szwy**: 01|02 i 05|06 — testy szwów (`test_dk65_seams_0207/0214`) zielone, na `top-seam-*` bez widocznego uskoku;
  11|knyszyn-s — skok 0,26 m na stronę z testu (wyżej); na `seam-s-top40` po drugiej stronie jest daleki plan, więc
  w kadrze kafla go nie widać.
- **Rondo knyszyn** (`rondo-dk65-top`): rondo kompaktowe z wyspami jak w main; kod ronda nie był ruszany przy
  scalaniu. Porównania piksel-do-piksela z r3 int-dk65 nie zrobiłem (w `artifacts/int-dk65-s22` znalazłem tylko
  starszy kadr `knyszyn-r1` sprzed ronda kompaktowego).

## Kroki domykające (zakończone)
1. **Tykocin r3b** (`regen-unity.status`: import, VQA Low, VQA High — exit 0; High `rendered=60`):
   `artifacts/rail-dk65-s22/vqa/r3b/dw671-tykocin-01/{Low,High}`. Obejrzane High `rail-x0-near-b`, `rail-x0-top`
   (podglądy `vqa/r3/jpg/r3b-tykocin-*.jpg`): po 6 słupków na stronę każdego wlotu (24), za poboczem gruntowym;
   przejazd, P-4, P-14, urządzenia bez zmian. G-1c wlotu SW 47 m — z `rail.json` (w tych kadrach słupek jest za kamerą).
2. **Start dk65-06** (`logs/start06.status`: import exit 0, VQA High exit 0, EditMode `-Filter StartClearanceTests`
   exit 0 — 45 / 45 passed): `artifacts/rail-dk65-s22/vqa/start06/dk65-06/High`. Obejrzane `chase`, `truck-rear34`
   (podglądy `vqa/r3/jpg/start06-*.jpg`): zestaw stoi na prawym pasie prostej za rondem, droga przed nim wolna.
   Zamknięcia krawędzi kafla za zestawem nie ma w tych kadrach — odległość ≥ 25 m za zamknięciem potwierdza test
   StartClearance, nie obraz.
3. `git merge origin/main` (eb00d41ea; pc-shadows, lamp-test, docs): konflikt tylko `docs/LICENSES.md` (wiersz
   `world-rail-0217` z main + wiersz `world-xsec-0272`). Z main przyszły zmiany C# renderingu
   (`PcTierTable.cs`, `PcTreeShadowReachTests`) i `fidelity_qa.json` C — **po tym scaleniu EditMode ani pytest nie
   były powtarzane** (zmiany nie dotykają `tools/worldgen` ani kafli tej regeneracji).

## Otwarte
- Szew 11|knyszyn-s (asfalt 7,3 / 6,78 m) + czerwony test 0233 — chmura D15.
- Zrzut z buildu Windows kamer przejazdu (zamiast telefonu) — lider po scaleniu; ocena `visual-critic` r3.
- `approach_speed_kmh: 90` DW671 = WORKING_VALUE do potwierdzenia zdjęciem / wizją lokalną (ADR 0268 p. 7).
- Fidelity C i stan `Data/raw` regionu C — lider.

## Werdykt
**Gotowe do scalenia: TAK.** Zastrzeżenia jawne: (1) czerwony `test_dk65_seam_knyszyn_0233` na szwie 11|knyszyn-s to
skutek decyzji lidera (otwarte D15); (2) 4 pozostałe faile pytest to fidelity C i stan wspólnego `Data/raw` regionu C;
(3) po ostatnim `git merge origin/main` testy nie były powtarzane.
Scalenie: `git merge --no-ff origin/rail-dk65-s22`, potem `uv run --project tools/worldgen python tools/worldgen/fidelity/run.py`.

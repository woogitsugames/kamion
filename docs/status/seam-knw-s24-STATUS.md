# seam-knw-s24 — STATUS

## 2026-11-21 krok 1
- Worktree gotowy (-CopyDerived), oba kafle zbudowane 21.11 00:52/00:59 (regen-wave-2).
- seams.py knyszyn|knyszyn-w: 1 FAIL (w300808749 service, oś 0,25 m); secondary w1478765548 (W wlot DW671) wg derived:network 11,75/11,75, oś identyczna — ale knyszyn 2x5,62 vs knyszyn-w 3x3,75 (UWAGA, kikut 6,7 m). Render pokazuje przesunięcie ⇒ siatka ≠ derived:network.
- NASTĘPNY KROK: pomiar przekroju GLB na szwie: `uv run --project tools/worldgen python -m tools.worldgen.qa.seam_section --help`

## krok 2 — przyczyna + poprawka (bez przebudowy)
- Przyczyna główna: meshing.build_ribbon kończy łańcuch przecięty szwem przekrojem PROSTOPADŁYM do osi; Tykocka w1478765548 i DK65 przecinają x=760587 pod ~41°/66° → w każdym kaflu trójkąt gołego terenu po jednej stronie osi i asfalt wchodzący do sąsiada po drugiej (teren sąsiada go przykrywa). Pomiar GLB (qa/seam_strip_probe.py, artifacts/seam-knw-s24/probe_before.json): x=seam∓0,3 m knyszyn-w asfalt N 611956,5–611964,85, knyszyn 611964,2–611972,5 (połówki).
- Poprawka: network._seam_dir (seam_u z bbox grafu) + meshing.seam_shear (końcowy rząd wzdłuż szwu, N'=u/(u·N), rampa ≥1,15×zasięg×|k|).
- Overrides: knyszyn-w w1478765548 lanes 2 / width 11.25 / asphalt_new (jak D95 w knyszyn); knyszyn center_offset 0.25 dla 300808749+98072226 (D94 shift z knyszyn-w).
- seams.py knyszyn,knyszyn-w: FAIL 1→0, UWAGA 2→0.
- NASTĘPNY KROK: przebudowa obu kafli (slot heavy): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn-w` potem knyszyn

## krok 3
- test_seam_shear_knw.py 3 passed; route_links odświeżone (tylko knyszyn-w-dw671, max 0,33 m).
- Przebudowa w tle: artifacts/seam-knw-s24/run-build.ps1 → build.log / build.exit (knyszyn-w, knyszyn, export-route, route_links, probe, combo).
- NASTĘPNY KROK: `Get-Content artifacts/seam-knw-s24/build.log -Tail 20`; po exit 0 import Win64 obu kafli + visual-qa knyszyn.

## krok 4
- Pierwsza przebudowa knyszyn-w (3,4 min): road_consistency 3→35 (marking_off_carriageway 6, obstacle_in_lane 26) — wszystkie na krawędziach kafla: farba i próbki pasów prostopadłe przy punkcie szwu wychodzą poza kafel, gdy asfalt kończy się na linii szwu.
- Poprawka: meshing.clip_layer_to_box (markings przycięte do bbox kafla, build_world po decals) + consistency: próbki pasa poza kaflem = teren sąsiada. Test 4 passed.
- NASTĘPNY KROK: ponowny run-build.ps1 po zakończeniu bieżącego (build.exit).

## krok 5
- Build #1 (bez clipu markings): knyszyn-w szew pełny (asfalt 611956,5–611971,95 przy x=szew-0,3, oba krawężniki/chodniki), 0 zawiniętych trójkątów.
- combo #1: knyszyn-w-dw671 opp 62 (nowe): link knyszyn kończył się 0,4 m od osi (zjazd z wyspy W wraca na oś w węźle split, 6,6 m przed szwem), 3 pasy w knyszyn-w to maskowały.
- Poprawka authored route_links.yaml: 2 swingi -2 m (±9 m / ±8 m) + cut_at_tile (koniec dokładnie na x=760587). combo: DK65→DW671 W 0/0/0, DK65→DK65 W 0/0/0, knyszyn-w-dw671 0/0/0, razem 67/0/0 (D95: 68/13/0).
- asphalt_new: materiał per łańcuch → override też na krawędzi w70329870:3047667183-4898928970 (do skrzyżowania).
- NASTĘPNY KROK: rm artifacts/seam-knw-s24/build.exit; pwsh -File artifacts/seam-knw-s24/run-build.ps1 (build #2)

## krok 6
- Build #1 knyszyn: szew ciągły (asfalt/krawężniki/chodniki obu stron, DK65 też), ale 3 odwrócone trójkąty chodnika N na krótkim kikucie W (6,6 m < potrzebne 8,6 m rampy).
- Poprawka: seam_shear per strona (NL/NR); strona cofana na za krótkim kikucie dostaje tylko ścinanie bez zawinięcia, nadmiar za szwem przycina build_world (clip_parts_to_box, chain.meta seam_clip). Test 5 passed.
- NASTĘPNY KROK: build #3 (run-build.ps1)

## krok 7
- Build #3 knyszyn-w: road_consistency 3 (= baseline, było 35 w #1), terrain walls 74 vs 61 (max 0,662 bez zmian, worst-15 identyczne).
- Library: robocopy z worktree win-build (Win64) do game/Library, żeby import -BuildTarget Win64 nie robił pełnego reimportu.
- NASTĘPNY KROK: po build.exit → pwsh -File artifacts/seam-knw-s24/run-import-vqa.ps1 (tło), potem obejrzeć vqa-knyszyn/*.png

## krok 8
- Polecenie lidera: merge origin/main (water-tykocin, ADR 0318: woda w knyszyn) → 5e6d50759; konflikty generated knyszyn = main. Przerwany build #3 knyszyn (bez wody), slot zwolniony.
- Build #4 tylko knyszyn (z wodą) w tle: run-build.ps1 -Regions knyszyn → build.log/build.exit. knyszyn-w z #3 (woda tam nie włączona). Import knyszyn-w Win64 w toku (import.log).
- NASTĘPNY KROK: po build.exit: pwsh -File artifacts/seam-knw-s24/run-import-vqa.ps1 -Regions knyszyn

## krok 9
- Build #4 knyszyn (z wodą, po merge): road_consistency 8 = 3 blind/5 obstacle (= D95), szew Tykocka: oba kafle road_asphalt_new, krawężniki+chodniki ciągłe; DK65 ciągła; 0 zawiniętych trójkątów (folds_after.txt).
- combo #4: DK65→DW671 W 0/0/0, DK65→DK65 W 0/0/0, knyszyn-w-dw671 0/0/0, razem 67/0/0 (D95 68/13/0). seams.py 0 FAIL / 0 UWAGA.
- Import knyszyn-w Win64 OK; import knyszyn + VQA w toku (import.log). pytest czeka w kolejce heavy (pytest.log).
- NASTĘPNY KROK: obejrzeć artifacts/seam-knw-s24/vqa-knyszyn/*.png

## krok 10 — koniec
- VQA knyszyn High Win64 z sąsiadem: rings_w_arm_top/rondo_dk65_top: szew niewidoczny; visual-critic PASS szwu (ciągłość 9, oznakowanie 7: linia środkowa kończy się kilka m przed nosem wyspy W — z D95, poza zakresem).
- pytest 13 modułów: 219 passed, 2 skipped, 3 failed → po tail_to link: 2 failed, oba też na main 54f071923 (test_tile_ratchet innego kafla, seam jeroniki|dk65-01 dlat 0,375). Szwy knyszyn: dlat 0,006 / dz -0,035 / kink 0,008.
- rynek-to-dw671 tail_to link:knyszyn-dk65-to-dw671-w (koniec = ten sam punkt szwu). combo final: 0/0/0, 0/0/0, knyszyn-w-dw671 0/0/0, razem 67/0/0.
- Dowody skopiowane do main artifacts/seam-knw-s24/. NIE scalono do main.

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

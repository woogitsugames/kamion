# STATUS — knyszyn-p1-s24 (P1 z REVIEW-2026-11-18-s24-knyszyn)

Worktree `.claude/worktrees/knyszyn-p1-s24`, gałąź `knyszyn-p1-s24`. Skrypty (poza gitem): `artifacts/knyszyn-p1-s24/{unity1,rebuild}.ps1`, `budget.py`.

## Zrobione (kod + testy, commit a2d6f31fa i następne)
- P1-1/P1-2 `streetscape/buildings_mesh.py` `wood_wall`: deski narożne, lisice, listwa cokołowa, szczyt pionowo, opaski + nadokienniki (`wood_trim_white`), wiatrownica w kolorze ściany; przebiegi desek < kafla 6 m z własną fazą UV. Knyszyn: 25 domów drewnianych, 256 przebiegów, najdłuższy 5,50 m, +12 360 tris LOD0 (zmierzone `BM.build`). Dom Klattów: ściana 21,1 m = 3,52 kafla → najdłuższy przebieg 4,65 m. `wood_siding` k 1,0→0,7: CV desek 0,0157→0,0502.
- P1-3 przyczyna = zamknięcie krawędzi świata 60 m przed krawędzią W; `Data/Regions/knyszyn/world_edge.authored.json` (12 m) + `WorldEdgeBuilder.ReadSetbackOverrides`. Render `artifacts/knyszyn-p1-s24/before/dk65-outlet-nw.jpg` (import „before” miał już tę zmianę): zapora ~60 m od kamery zamiast ~15 m.
- P1-4 `vegetation.field_mosaic`: mozaika pól w COLOR_0.b na OT_PTTR_A.
- Testy: `tests/gis/test_wood_house_p1_s24.py` 8 passed; EditMode `WorldEdgeSetbackOverrideTests` (jeszcze nie uruchomiony).
- Baseline: `artifacts/knyszyn-p1-s24/vqa-knyszyn-before/` (84 kamery, High clear, derived main sprzed przebudowy).

## W toku
`artifacts/knyszyn-p1-s24/rebuild.ps1 -Tag r1` (build_world knyszyn, potem knyszyn-w; status `logs/rebuild-r1.status`).

NASTĘPNY KROK: po `=== export-route knyszyn` w `logs/rebuild-r1.log`:
`pwsh artifacts/knyszyn-p1-s24/unity1.ps1 -Region knyszyn -Tag after -Vqa` → obejrzeć `vqa-knyszyn-after/{look-dom-klattow,dk65-outlet-nw,rondo-owner-11,rondo-dk65-top,tykocka-into-town}.png`, `uv run --project tools/worldgen python artifacts/knyszyn-p1-s24/budget.py artifacts/knyszyn-p1-s24/vqa-knyszyn-before/stats.txt artifacts/knyszyn-p1-s24/vqa-knyszyn-after/stats.txt`; potem import knyszyn-w, pytest tests/gis, EditMode Win64, uzupełnić ADR 0295 (TBD_*).

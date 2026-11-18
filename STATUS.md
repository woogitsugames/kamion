# STATUS — knyszyn-p1-s24 (P1 z REVIEW-2026-11-18-s24-knyszyn)

Worktree `.claude/worktrees/knyszyn-p1-s24`, gałąź `knyszyn-p1-s24`. Skrypty pomocnicze (poza gitem): `artifacts/knyszyn-p1-s24/unity1.ps1`.

## Krok 1 (kod, bez przebudowy)
- P1-1/P1-2 `tools/worldgen/streetscape/buildings_mesh.py`: `wood_wall` — deski narożne, lisice (przebiegi desek < kafla 6 m, własna faza UV na przebieg), listwa cokołowa, deska na linii okapu szczytu + deskowanie pionowe szczytu (UV zamienione), opaski okien/drzwi z nadokiennikiem (nowy materiał `wood_trim_white`), wiatrownica w kolorze ściany.
- P1-4 `vegetation.field_mosaic`: maska suchości (COLOR_0.b) na OT_PTTR_A = mozaika pól (układ ESTIMATED, funkcja pozycji EPSG:2180) zamiast szumu 8 m.
- P1-3 przyczyna: zamknięcie krawędzi świata (`WorldEdgeBuilder`, 60 m przed krawędzią kafla; rondo ~80 m od krawędzi W). Poprawka w toku.
- Baseline „przed”: import + VQA knyszyn z derived main w toku (`artifacts/knyszyn-p1-s24/logs/unity-knyszyn-before.status`).

NASTĘPNY KROK: po `exit=0` w `unity-knyszyn-before.status`:
`pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-p1; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-p1`
potem `pwsh artifacts/knyszyn-p1-s24/unity1.ps1 -Region knyszyn -Tag after -Vqa`.

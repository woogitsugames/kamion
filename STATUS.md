# STATUS — knyszyn-p1-s24 (P1 z REVIEW-2026-11-18-s24-knyszyn)

Worktree `.claude/worktrees/knyszyn-p1-s24`, gałąź `knyszyn-p1-s24`. Skrypty (poza gitem): `artifacts/knyszyn-p1-s24/{unity1,rebuild,editmode}.ps1`, `budget.py`, `field_noise.py`. ADR: `docs/adr/0295-…` (zmiana globalna).

## Zrobione
- P1-1/P1-2 `buildings_mesh.wood_wall` + `wood_trim_white`, `wood_siding` k 0,85 (CV 0,0157→0,0324). Knyszyn r1: 25 domów drewnianych, 256 przebiegów, max 5,50 m (< kafel 6 m), budynki LOD0 656 343 → 669 021 tris; Dom Klattów 21,1 m = 3,52 kafla → max przebieg 4,65 m.
- P1-3 `world_edge.authored.json` (DK65 W: 49,4 → 12 m przed krawędzią) + `WorldEdgeBuilder.ReadSetbackOverrides`; EditMode (filtr closure/StartClearance) 100 passed / 0 failed.
- P1-4 `vegetation.field_mosaic` (pola 72 % kafla; B śr. 0,624 → 0,327), ogrody na PTZB mieszkaniowej (kod, jeszcze nie w buildzie), shader `swardCalm` w WorldPBR. `field_noise.py` rondo-owner-11 pole NE: 0,0219 → 0,0165.
- Rendery r1: `artifacts/knyszyn-p1-s24/{before,after,shader,sbs}` (kopia w main `artifacts/knyszyn-p1-s24/`). Budżet r1 (83 kamery High clear, szacunek edytora): max draws 731 → 732, śr. +1,65; max tris 2 333 091 → 2 339 271 (kamera kabinowa, >2 mln już przed zmianą).
- Baseline 0238 kafla C przeliczony (3 domy drewniane, +102…+106 tris na 4 kamerach).
- Pełny EditMode: 1254 passed, 3 failed — 2 środowiskowe (ArtPrefabs_HavePinnedGuids, ImportedGlassSemantic… — jak w regen-c-s24), 1 mój test (poprawiony, przeszedł w przebiegu z filtrem).

## W toku
`rebuild.ps1 -Tag r2` czeka na slot heavy (ogrody + nowe kamery look_wooden_house_*), status `logs/rebuild-r2.status`.

NASTĘPNY KROK: po `exit=0` w `logs/rebuild-r2.status`:
`pwsh artifacts/knyszyn-p1-s24/unity1.ps1 -Region knyszyn -Tag after2 -Vqa; pwsh artifacts/knyszyn-p1-s24/unity1.ps1 -Region knyszyn-w -Tag after2`
→ obejrzeć `vqa-knyszyn-after2/{look-dom-klattow,look-wooden-house-brown,look-wooden-house-green,rondo-owner-11,rondo-dk65-top,dk65-outlet-nw}.png`, `budget.py before/after2`, potem `uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider` (slot heavy), commit `Data/Regions/knyszyn*/generated`, uzupełnić „Pomiary” w ADR 0295.

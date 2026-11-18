# STATUS — knyszyn-p2-s24 (P1 N1–N4 z REVIEW-2026-11-18-s24-cabin-lights-knyszyn, Knyszyn)

Worktree `.claude/worktrees/knyszyn-p2-s24`, gałąź `knyszyn-p2-s24`. Skrypty: `artifacts/knyszyn-p2-s24/unity.ps1` (import + VQA, status `unity-<tag>.status`), `addcams.py`.

## Diagnoza
- N1 szwy: (a) fartuch `WorldEdgeBuilder.ApronMask` = sinusowy szum B 0,35–0,82 + strefy lasu/gruntu z Białegostoku, bez mozaiki; (b) `KamionWorldGI` — mapa nieba kończy się skokiem `inside` na krawędzi kafla; (c) mozaika ADR 0295 zapisana w COLOR_0 na siatce 1 m, ale pas terenu High ma 8 m poza drogami → miedze znikają, pasy = smugi.
- N4: self-seeding drzew na OT_PTTR_A (pola w użyciu) co ~20 m → „brokuły” pojedynczo na polach; `plot_canopy.json` dla Knyszyna nie istniał → 0 drzew ogrodowych z koron ortofoto.

## Zrobione (WIP)
- `plot_canopy.json` knyszyn (18 801 koron, 11 087 drzew) i knyszyn-w (5 718).
- Python: pola = flaga COLOR_0.b (0,90 trawiaste / 1,00 orne), reszta ≤ 0,80; self-seeding na PTTR tylko przy miedzach (8 m, 35 %) + 2 % w środku; deski malowane red/graphite (zdjęcie 7).
- Shader/C# (patch `artifacts/knyszyn-p2-s24/wip-game.patch`, odłożony na czas bazowego importu): `KamionFieldMosaic.hlsl` (mozaika per piksel z EPSG), `_RegionOriginEN`, fartuch z maską krawędzi kafla + flaga pól, wygaszanie GI 120 m poza kaflem.

NASTĘPNY KROK: po `unity-before.status exit=0`: `git apply artifacts/knyszyn-p2-s24/wip-game.patch; copy KamionFieldMosaic.hlsl.wip -> game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl`, potem build_world knyszyn (slot heavy) + import + VQA tag after1.

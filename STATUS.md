# STATUS — knyszyn-p2-s24 (P1 N1–N4 z REVIEW-2026-11-18-s24-cabin-lights-knyszyn, Knyszyn)

Worktree `.claude/worktrees/knyszyn-p2-s24`, gałąź `knyszyn-p2-s24`. Skrypty: `artifacts/knyszyn-p2-s24/unity.ps1` (import + VQA, status `unity-<tag>.status`), `addcams.py`.

## Diagnoza
- N1 szwy: (a) fartuch `WorldEdgeBuilder.ApronMask` = sinusowy szum B 0,35–0,82 + strefy lasu/gruntu z Białegostoku, bez mozaiki; (b) `KamionWorldGI` — mapa nieba kończy się skokiem `inside` na krawędzi kafla; (c) mozaika ADR 0295 zapisana w COLOR_0 na siatce 1 m, ale pas terenu High ma 8 m poza drogami → miedze znikają, pasy = smugi.
- N4: self-seeding drzew na OT_PTTR_A (pola w użyciu) co ~20 m → „brokuły” pojedynczo na polach; `plot_canopy.json` dla Knyszyna nie istniał → 0 drzew ogrodowych z koron ortofoto.

## Zrobione (WIP)
- `plot_canopy.json` knyszyn (18 801 koron, 11 087 drzew) i knyszyn-w (5 718).
- Python: pola = flaga COLOR_0.b (0,90 trawiaste / 1,00 orne), reszta ≤ 0,80; self-seeding na PTTR tylko przy miedzach (8 m, 35 %) + 2 % w środku; deski malowane red/graphite (zdjęcie 7).
- Shader/C# (patch `artifacts/knyszyn-p2-s24/wip-game.patch`, odłożony na czas bazowego importu): `KamionFieldMosaic.hlsl` (mozaika per piksel z EPSG), `_RegionOriginEN`, fartuch z maską krawędzi kafla + flaga pól, wygaszanie GI 120 m poza kaflem.

- Bazowe VQA `artifacts/knyszyn-p2-s24/vqa-before` (+small-before): szew W 20,8 (mediana |Δluma|), pole owner-11 114/120/92 G−R +5,8, σ 14,6. Pierścienie potwierdzone (rings-w/ne-arm-top) → przyczyna `_patch_uv1` (odległość do końca łańcucha), poprawione + test.
- build_world knyszyn/knyszyn-w (r1): drzewa ogrodowe 3243 / 809 (High +113 732 / +30 692 tris), samosiew: brzoza młoda 3126→616, krzew 5281→2846, sosna młoda 1517→292 (knyszyn).

- r3 (after3): szew W systematyczny Δluma 17,1 → 1,0 (kontrola w kaflu 2,3), |Δ| mediana 20,2 → 9,4; pole owner-11 114/120/92 → 110/128/92, G−R +5,8 → +18,3 (zdjęcie +26,9), σ 14,6 → 18,6 (zdjęcie 16,9). Pierścienie N2 zniknęły (NE), W: zygzaki → poprawka r4 (płyta ronda kompaktowego = wszystkie ramiona).

NASTĘPNY KROK: czekaj `unity-after4.status` (build b4 + import + VQA wszystkich kamer), `pytest.status` (pytest tests/gis w tle), potem EditMode Win64 `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`, sbs `bash artifacts/knyszyn-p2-s24/sbs.sh after4`, kopia do main.

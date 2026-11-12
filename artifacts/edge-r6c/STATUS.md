# STATUS edge-r6c (ADR 0141) — krawędź mapy / tło

Gałąź `edge-r6c`, worktree `.claude/worktrees/edge-r6c`, baza main 76c88d4fd.

## 2026-11-12 17:45 — rozpoznanie
- Przeczytane: AGENT-RULES, gpt-handovers/edge-r6.md, BOUNDARY-P1.md, ADR 0082/0085/0121, recenzje batch A/C/E.
- Diagnoza B9 (skyline_probe.py 303305): bloki 48–56 m (el +2,5..+3,7°, d 645–741 m) zasłania las BDOT `2BE4B432-6BC0` (sosny h 21–23 m, d 160–240 m, el +4,4..+5,8°) — obiekty regionu (zieleń), nie far-field. Poza 303305 ma też ~11° błędu kursu (punkt zbiegu x 600 vs 490/960).
- Low far clip 900 m: z wiaduktu (E 458) sektor zachodni far-field (≥ E −1024) jest poza far clip → horyzont pusty.
- NASTĘPNY KROK: `pwsh artifacts/edge-r6c/run-vqa.ps1 -Name baseline` (Before Low clear+overcast), potem zmiana zapór/tła.

## 2026-11-12 18:50 — skyline (WIP, nieskompilowane w Unity)
- D51: kominy EC (120 m) w 4 kadrach G3-B (3281350, 150280, 297817, 1528935) są 1251–1475 m od kamery = poza far clip Low 900 m → znikają.
- far_field.py: węzeł `far_skyline` (budynki ringu h>=24 m, kominy h>=40 m, zastępniki 2 kominów EC) z flagą w TEXCOORD_1.x (-(x+16) clamp, -(x+4096) beyond). Low 24500 -> 24548 tris (skyline 2024), High 118524 -> 118588.
- WorldSurface.shader (_FAR_FACADE, tylko M_far_field_buildings): KamionFarSkyline trzyma oflagowane wierzchołki tuż przed far plane (ForwardLit + DepthOnly).
- WorldEdgeBuilder.BuildFarField: renderer `WorldEdge/FarSkyline` (bounds = cały kafel). Zapory (grupy, 2 materiały, U-20b + B-1) — patch jeszcze NIE zastosowany.
- Baseline (run-vqa.ps1 -Name baseline) czeka w kolejce Unity (PHONE_RUN).
- NASTĘPNY KROK: zastosować patch zapór w WorldEdgeBuilder.cs, potem `pwsh scripts/unity-slot.ps1 -Acquire -Owner claude-edge-r6c; Unity -executeMethod Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch; pwsh artifacts/edge-r6c/run-vqa.ps1 -Name after`.

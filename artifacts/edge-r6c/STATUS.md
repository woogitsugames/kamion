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

## 2026-11-12 ~18:15 — pierwszy After, poprawka głębi
- RebuildEdge OK: 36 zapór w 6 grupach renderu (8588 tris), far-field Low 24548 / High 118588. EditMode 405/407 (2 porażki CarPaintMaterialTests — cudza domena, te same w logach a16-perf); 4 nowe testy WorldEdgeClosureSkylineTests zaliczone. pytest tests/gis/test_far_field*.py 55 passed.
- Budżet Low (120 kamer, pierwszy After): draws mediana -13, min -51, max +3; shadow suma 0; trisK suma +116 z 33055 (+0,35 %).
- Skyline nie był widoczny za far plane: skybox Unity rysuje ~1e-6 NDC przed far, moje 3–6 m = 3,7e-7. Poprawka: 40..30 m + minimum 4e-6 NDC (dbg1 potwierdził kominy EC w 297817).
- W tle: `pwsh artifacts/edge-r6c/run-vqa.ps1 -Name after` (log after2.log).
- NASTĘPNY KROK: `bash artifacts/edge-r6c/make-pairs.sh Low-clear; bash artifacts/edge-r6c/make-pairs.sh Low-overcast; python artifacts/edge-r6c/stats-diff.py baseline after Low-clear`, potem `git merge main` (generated --ours) + build_world (-Pool heavy) + import-region + rendery + pytest gis+gate3 + ADR 0141.

## 2026-11-12 18:55 — pary, merge main, regeneracja
- Pary Low clear+overcast (101+101, artifacts/edge-r6c/pairs) obejrzane: 2 kominy EC w 297817, 3281350, 150280, 1528935; zapory w edge-*.
- git merge main 611f116c9 bez konfliktów; build_world 615 s OK (far_field Low 24548 / High 118588). pytest gis+gate3: 845 passed, 1 xfailed, 1 failed (fidelity_qa.json nieaktualny po fixie CRLF a4cb9995 z main) -> fidelity/run.py w toku.
- W tle: fidelity/run.py (heavy), run-merged.ps1 (import, EditMode, rendery merged).
- NASTĘPNY KROK: `bash artifacts/edge-r6c/make-pairs.sh Low-clear baseline merged; python artifacts/edge-r6c/stats-diff.py baseline merged Low-clear`, potem docs/adr/0141.

## 2026-11-12 19:57 — drugi merge main (0139 + 0143), pełna regeneracja w toku
- Pierwszy merge (611f116c9): build_world 615 s OK; pytest gis+gate3 845 passed + fidelity po run.py 9 passed; import padł na braku pamięci w build_all (maszyna), nie w kodzie.
- Lider: krytyk 0139 P1-2 — potwierdzić kominy EC na Low w 297817 i 150280 na pozach z main. Scalony main 97996ef6b (konflikty tylko generated -> ours).
- W tle: `pwsh artifacts/edge-r6c/run-merged.ps1` (PID pwsh 58288; logi *-merged.log).
- ADR szkic: docs/adr/0141-edge-skyline-closures.md (placeholdery @@...@@).
- NASTĘPNY KROK: po łańcuchu `bash artifacts/edge-r6c/make-pairs.sh Low-clear baseline merged; python artifacts/edge-r6c/stats-diff.py baseline merged Low-clear | tail -7`, uzupełnić ADR, commit generated, robocopy do main.

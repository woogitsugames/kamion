# STATUS edge-r6c (ADR 0141) — krawędź mapy / tło

Gałąź `edge-r6c`, worktree `.claude/worktrees/edge-r6c`, baza main 76c88d4fd.

## 2026-11-12 17:45 — rozpoznanie
- Przeczytane: AGENT-RULES, gpt-handovers/edge-r6.md, BOUNDARY-P1.md, ADR 0082/0085/0121, recenzje batch A/C/E.
- Diagnoza B9 (skyline_probe.py 303305): bloki 48–56 m (el +2,5..+3,7°, d 645–741 m) zasłania las BDOT `2BE4B432-6BC0` (sosny h 21–23 m, d 160–240 m, el +4,4..+5,8°) — obiekty regionu (zieleń), nie far-field. Poza 303305 ma też ~11° błędu kursu (punkt zbiegu x 600 vs 490/960).
- Low far clip 900 m: z wiaduktu (E 458) sektor zachodni far-field (≥ E −1024) jest poza far clip → horyzont pusty.
- NASTĘPNY KROK: `pwsh artifacts/edge-r6c/run-vqa.ps1 -Name baseline` (Before Low clear+overcast), potem zmiana zapór/tła.

# putry-andersa (ADR 0146) STATUS
2026-11-12 20:14 sha a9018d290 (main 1b002a730 merged). Worktree .claude/worktrees/putry-andersa, branch putry-andersa.
ZROBIONE: kod+dane (latarnie maszty 10,3 m na gruncie, 17/18 slupow; pobocze Putry; profile_ties + wypelnienie pasa; dwuteowniki; czerwony pas scian ramp), build_world 692 s exit 0 (consistency 65 jak przed), import-region exit 0 (20:14), przekroj z GLB przy E -420: jezdnia SE 134,4-134,5 / trawa 134,75 / jezdnia NW 134,5-134,4 (bylo 1,3-1,9 m roznicy).
W TLE: (1) rendery+pary+sondy: pwsh artifacts/putry-andersa/tools/run-renders.ps1 -> logs/renders-after.log, koniec = logs/renders-after.done; (2) pytest gis+gate3+swept: logs/pytest.log, koniec = logs/pytest.done. PHONE_RUN moze wstrzymywac Unity.
NASTEPNY KROK: obejrzec artifacts/putry-andersa/after/pairs/Low-*/sbs-g3-b-{494288258686575,810896133189484,275528677534382}.jpg i after/probe/Low-*/; potem pwsh artifacts/putry-andersa/tools/run-editmode.ps1; uzupelnic docs/adr/0146 (Validation/Open), robocopy artifacts/putry-andersa -> main.
OTWARTE: portal Andersa tablice +0,6 m (dane generatora zgodne: srodki 5,94/5,75 m, belka 5,5-6,1; sondy p146-portal-* rozstrzygna), beam _b6=0,6 vs 0,55, slup 16 rzedu pominiety (jezdnia), B-23 brak w atlasie.
Gotowe do scalenia: NIE (rendery/testy w toku).

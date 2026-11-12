# mistral-r3-int — 2026-11-12 21:15
- worktree: .claude/worktrees/mistral-r3-int, gałąź mistral-r3-int (origin), main scalony (d15b4012c)
- scalone: #16 SCAL, #15/#17/#20 SCAL po poprawkach (commity lidera), #18 SCAL (konflikt JSON -> main + expectedFailMetrics=[radius_error_m]); #19 NIE (TMP bez Essential Resources -> NRE w UiFonts.DefaultTmp)
- testy: audio 46; dotnet 226/226; Runner 112/112 (589); gis -m unit 72 + 2 xfail; Unity PlayMode HudTextAllocTests: TextBuffer 0 GC.Alloc/500, legacy 1003/500, TMP NRE
- raport: docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md; dowody #19: artifacts/mistral-r3-int/
- NASTĘPNY KROK (lider): git fetch && git merge --no-ff origin/mistral-r3-int && git push  (zamyka #15 #16 #17 #18 #20; #19 zamknąć ręcznie z komentarzem)
- Gotowe do scalenia: TAK

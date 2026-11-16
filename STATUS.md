# STATUS — D34 plots-k3b-analysis (chmura D r8)
- Prototyp K3b zmierzony (scratch): C build 228/228 identyczne, region_plan 108,6 → 9,1 s; kleeberga region_plan 1 420 → 89,8 s, build 2 698 → 1 414 s, 19/219 plików inne (5 działek z dziurą ≤ 0,35 m; +26 tris trawnika), płoty/bramy identyczne.
- Raport `docs/reports/WORLDGEN-K3B-2026-11-16.md` + dane `docs/reports/k3b/`; `tools/worldgen/qa/compare_plots.py` + test (2 passed).
- NASTĘPNY KROK (lider): `git apply docs/reports/k3b/k3b_prototype.diff` w osobnym worktree + komendy z raportu §7.

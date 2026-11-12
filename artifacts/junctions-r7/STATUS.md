# junctions-r7 (ADR 0144) — STATUS
- 2026-11-12 18:40 start: worktree od main 4816da8f; skrypty w artifacts/junctions-r7/scripts (wzór r6 / biezenstwa-island). Baza „przed” = rendery b7 (kamery węzła) i i3 (SBS) z main artifacts (main e79c5cc3 = b7 + i3, potem tylko docs).
- w tle: dbg_rails (heavy slot) -> artifacts/junctions-r7/logs/dbg0.log. PHONE_RUN aktywny (a16-perf) -> Unity czeka.
- NASTĘPNY KROK: analiza dbg0.log (szyny przy E -765 N 76), reguła wykluczenia W-beam < 1 m od poręczy w tools/worldgen/streetscape/furniture.py + pytest.

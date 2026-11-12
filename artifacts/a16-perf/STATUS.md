# a16-perf (ADR 0136) STATUS

- 15:40 worktree a16-perf od main 8b0d6ec7; generic A/B materiałów w ExtraViewCostMonitor (rq_ab off:/vec:/kwoff:/gkw:, ADR 0136).
  Baza s10 = 21a55c3fe4 (PRZED 0113), s12 = 11db0552fd. Pomiar: overcast, Low, G3-A/B.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/build.ps1 -Tag diag1` (APK diag), potem `pwsh artifacts/a16-perf/run-diag1.ps1 -Apk <apk>`.

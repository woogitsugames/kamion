# a16-perf (ADR 0136) STATUS

- 15:40 worktree a16-perf od main 8b0d6ec7; generic A/B materiałów w ExtraViewCostMonitor (rq_ab off:/vec:/kwoff:/gkw:, ADR 0136).
  Baza s10 = 21a55c3fe4 (PRZED 0113), s12 = 11db0552fd. Pomiar: overcast, Low, G3-A/B.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/build.ps1 -Tag diag1` (APK diag), potem `pwsh artifacts/a16-perf/run-diag1.ps1 -Apk <apk>`.
- 16:20 diag1 (APK 24ab345392, G3-B uncapped, rq_ab, Δ GPU p50 A-B): asph Low z/w +0.27, ground/kerb/seam +0.01, truck +4.03 (≈0106), props +0.16,
  trees +2.53 (0113 oczekiwane ~1,7-2,3), fsign +0.06, plot +0.38. ab_far: logcat nie zebrany (phone-diag zawisł po device-metrics 18 min),
  sweep przerwany na polecenie lidera, PHONE_RUN usunięty 16:16. Poprawka: PHONE_RUN tylko na czas pomiaru, timeout na adb po runie.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/run-diag1.ps1 -Only ab_far,ab_decal,ab_fab,ab_bld,ab_hedge,ab_noise,ab_carfilm` (APK już zainstalowany).

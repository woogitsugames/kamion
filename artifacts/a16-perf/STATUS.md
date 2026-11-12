# a16-perf (ADR 0136) STATUS

- 15:40 worktree a16-perf od main 8b0d6ec7; generic A/B materiałów w ExtraViewCostMonitor (rq_ab off:/vec:/kwoff:/gkw:, ADR 0136).
  Baza s10 = 21a55c3fe4 (PRZED 0113), s12 = 11db0552fd. Pomiar: overcast, Low, G3-A/B.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/build.ps1 -Tag diag1` (APK diag), potem `pwsh artifacts/a16-perf/run-diag1.ps1 -Apk <apk>`.
- 16:20 diag1 (APK 24ab345392, G3-B uncapped, rq_ab, Δ GPU p50 A-B): asph Low z/w +0.27, ground/kerb/seam +0.01, truck +4.03 (≈0106), props +0.16,
  trees +2.53 (0113 oczekiwane ~1,7-2,3), fsign +0.06, plot +0.38. ab_far: logcat nie zebrany (phone-diag zawisł po device-metrics 18 min),
  sweep przerwany na polecenie lidera, PHONE_RUN usunięty 16:16. Poprawka: PHONE_RUN tylko na czas pomiaru, timeout na adb po runie.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/run-diag1.ps1 -Only ab_far,ab_decal,ab_fab,ab_bld,ab_hedge,ab_noise,ab_carfilm` (APK już zainstalowany).
- 16:57 (s13) diag1 c.d. (Δ GPU p50 A-B, G3-B uncapped): far +0.23, decal +0.12, fab -0.12, bld -0.34, hedge +0.14, noise/gantry +0.08,
  carfilm -0.12, mirrors +0.93 (=0106). Drzewa per okno: 6.6-8.7 ms w oknach 3-4 (s≈1300-1450, las przy drodze) vs ~2.5 dalej -> piki p99.
  Uncapped dziś ≈ s10 capped; realna regresja ~+3 ms rozproszona (sum. małych +1.7 + drzewa). Ustawienia jakości/URP bez zmian s10->s12.
  NASTĘPNY KROK: czekaj na envcap/shadows/hlodedge/hlodcanopy/impostor (`python artifacts/a16-perf/abwin.py artifacts/a16-perf/diag1/ab_*`).
- 17:20 diag1 koniec: envcap +0.05, shadows +0.64 (=0106), hlodedge +1.81, hlodcanopy +0.16, impostor +1.37 śr., ale 6.6/4.8 ms w oknach 3-4
  (las przy G3-B s≈1300-1450) = źródło pików p99. Atlasy impostorów pokrywają tylko 6-13 % quada (90 % fragmentów = discard).
  Poprawka: ImpostorTrim (Game.World) + ImpostorTrimBake (import + batch in place): wielokąt 6 pasm wokół sumy alfy 6 widoków, ~34 % quada.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/trim.ps1 -Tag trim1` (vqa before -> bake -> vqa after -> EditMode -> APK Low).
- 17:35 trim2: 18 impostorów, śr. 37 % quada; vqa Low overcast 78 kamer PSNR ≥ 58 dB (pojedyncze piksele, `vqa/before|after`).
  EditMode 471/8 fail — tylko CarPaintMaterialTests.DepositionChannel (środowiskowe, też w audio-regen01; main zielony). APK `kamion-0.1.0-0e68ff8c5e-dirty.apk`.
  NASTĘPNY KROK: (w toku) `pwsh artifacts/a16-perf/run-final.ps1 -Before artifacts/apk/kamion-0.1.0-24ab345392.apk -After artifacts/apk/kamion-0.1.0-0e68ff8c5e-dirty.apk`
  potem `python artifacts/a16-perf/summarize.py 'artifacts/a16-perf/final1/*'`.
- 17:32 final1 (APK trim 0e68ff8c, limit 30): G3-B GPU p50/p95 31.42/33.86, p99 33.73, >40 16 (s12: 31.77/35.17, p99 50, >40 41; s10 p99 33.69).
  G3-A 32.44/35.53, p99 49.95, >40 26 (s12 32.32/35.54, 42) — G3-A bez zmiany GPU. Impostor A/B uncapped 1.37 -> 0.51 ms (okna lasu 6.6/4.8 -> 1.9/2.3).
  „before” na tym samym dniu niemożliwy: INSTALL_FAILED_VERSION_DOWNGRADE (4097 < 4105, -d nie działa na release) — baza = gate3 s12.
  Merge main 4c25ff20 (czysty). NASTĘPNY KROK: (w toku) ablacje G3-A `pwsh artifacts/a16-perf/run-diag1.ps1 -Segment A -OutTag diagA -Only ...`

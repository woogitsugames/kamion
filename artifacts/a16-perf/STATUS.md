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
- 17:56 diagA (G3-A uncapped, APK trim): props +2.48 GPU/+7.0 CPU (G3-B +0.16!), shadows +1.44, mirrors +1.32, asph +0.96 (szum), far +0.36,
  truck +4.14, trees/impostor/hlod ≈ 0, fsign −0.03, plot −0.44. G3-A regresja = instancjonowane propsy (auta/meble z s11–s12).
  NASTĘPNY KROK: dodać rozbicie propsów per prefiks (RenderOverrides.AbPropsOff -> filtr prefiksu) i zmierzyć na G3-A:
  `pwsh artifacts/a16-perf/run-diag1.ps1 -Segment A -OutTag diagA2 -Only <nowe klucze>`. Gałąź gotowa do scalenia warunkowo (G3-B).
- 18:29 (s14) r2 start: merge main (FF 9a1961db0). Klucze A/B per prefiks: rq_ab pp:/ps:/vc: (WorldInstances.SyncAbMasks). G3-A ≤300 m: ~600 pojazdów
  (stały cull 300 m na wszystkich tierach) vs G3-B ~50. Build APK diagA2 w tle.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/run-diag1.ps1 -Segment A -OutTag diagA2 -Apk <apk> -Only ab_veh,ab_vcar,ab_vtruck,ab_lamp,ab_signs,ab_fabp,ab_lmk,ab_misc,ab_pshadow,ab_vshadow,ab_vc150`
- 18:51 diagA2 (G3-A uncapped scale 0.75, APK 7ebb0151d1, Δ A-B p50 GPU/CPU ms): veh +1.94/+5.24, car+van+contact +1.29/+4.44,
  tractor/trailer/bus +0.10/+1.13, lamp -0.15/+0.65, signs -0.13/+0.30, fab -0.04/+0.13, landmark/facade +0.21/+0.93, misc -0.66/-0.72,
  prop shadows (ps:all) 0.00/+0.04, vehicle shadows -0.46/-0.11, vehicle cull 300->150 m +0.35/+2.41. => koszt = auta osobowe <150 m
  (LOD0 12 / LOD1 11 / LOD2 7 submeshy na prototyp, 24 prototypy). Cienie propsów nic nie kosztują.
  NASTĘPNY KROK: diagA3: contact patch / LOD aut / mirrorlow (klucze w run-diag1.ps1).
- 19:08 diagA3: cull 100 +0.36/+2.95, LOD aut x0.5 +0.22/+0.66, contact +0.13/+0.41, auta w lusterkach +0.06/+0.86, mirrorlow -0.26/+0.90.
  Uwaga: GPU p50 dziś ~24.5 (diagA 17:56 ~30) przy tej samej konfiguracji — dryf termiczny/DVFS; porównania tylko przeplatane w 1 APK.
  Zmiana Low: vehicleCullM 150 m (tier field, rq_vehcull override do przeplatanego before/after). Build r2a w kolejce.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/phone-diag.ps1 -Apk <r2a apk> -OutTag r2a -Segment A -Runs "A_before1=rq_vehcull=300;A_after1=;A_before2=rq_vehcull=300;A_after2="`
- 19:23 ODKRYCIE: od 18:32 A16 (leżący płasko) uruchamiał grę w PORTRECIE 1080x2340 (ADR 0135 AllowAuto) — diagA2/diagA3/baseA w portrecie.
  Obejście: rq_landscape=1 (DiagLandscape) w phone-diag.ps1. r2b (landscape, capped 30, APK 23dc12142c, przeplatane):
  before (rq_vehcull=300) GPU p95 35.70/35.93, after (Low vehicleCullM 150) 34.53/34.47 => -1.3 ms; p99 frame 50 bez zmian; >40: 26/40 -> 26/31.
  NASTĘPNY KROK: landscape uncapped A/B: run-diag1 -Segment A -OutTag diagA4 -Only ab_cc,ab_grime,ab_shadows,ab_shd25,ab_shr512,ab_mirrors,ab_mirres,ab_vc100,ab_veh
- 19:42 diagA4 (LANDSCAPE, uncapped, po vehcull 150; Δ A-B p50 GPU/CPU): mirrors +1.46/+2.74, shadows +1.11/+2.37, grime +0.68/+0.61,
  mirres x0.75 +0.47/+0.26, shd25 +0.39, shr512 +0.31, cc +0.15, vc 150->100 +1.29/+1.08, veh (reszta) +0.57/+2.88 (szum okien ±0.7).
  Zmiana Low #2: mirrorResolutionScale 0.75 (lusterko klasy II 224 -> 168 px = skala renderu Low). Build r2c + przeplatane capped x3 w tle.
  NASTĘPNY KROK: `python artifacts/a16-perf/summarize.py 'artifacts/a16-perf/r2c/*'`, potem `pwsh artifacts/a16-perf/vqa-r2.ps1 -Before 'rq_vehcull=300,rq_mirror_res=1'`
- 19:58 r2c (APK 56b0df6b91, 3x przeplatane capped) w toku; po nim merge main (ADR 0147) + weryfikacja orientacji. NASTĘPNY KROK: `python artifacts/a16-perf/summarize.py 'artifacts/a16-perf/r2c/*'`
- 20:04 r2c (APK 56b0df6b91, landscape, capped 30, 3x przeplatane): before GPU p95 36.09/35.51/35.62 -> after (vehcull 150 + lusterka x0.75)
  34.02/34.18/34.22 (-1.6 ms); frame p99 50/50/50 -> 50/33.75/33.77; >40 46/28/38 -> 26/16/18. Brak ~0.8 ms do 33.3 -> Low grime detail off (diagA4 +0.68).
  Merge main 2080745dd (ADR 0147 orientacja; generated ours). Build r2d + przeplatane BEZ rq_landscape (weryfikacja 0147) w tle.
  NASTĘPNY KROK: `python artifacts/a16-perf/summarize.py 'artifacts/a16-perf/r2d/*'`; potem `pwsh artifacts/a16-perf/vqa-r2.ps1 -Before 'rq_vehcull=300,rq_mirror_res=1,rq_grime=1'` + `pwsh scripts/test.ps1 -Platform EditMode`
- 20:16 r2d (APK 2080745dd4 = r2 + main/ADR 0147, BEZ rq_landscape — 0147 obraca płaski A16 do landscape OK; capped 30):
  before (rq_vehcull=300 rq_mirror_res=1 rq_grime=1) GPU p50/p95 32.43/35.70, 32.54/36.14; after 31.71/34.20, 31.44/33.73, 31.59/33.92 (śr. p95 35.9 -> 33.95, -2.0 ms).
  frame p99 50/50 -> 49.9/33.9/49.9; >40 30/50 -> 22/19/23; CPU p50 22.8 -> 21.9. Cel 33.3 nieosiągnięty o ~0.6 ms.
  NASTĘPNY KROK: `pwsh artifacts/a16-perf/vqa-r2.ps1 -Before 'rq_vehcull=300,rq_mirror_res=1,rq_grime=1'` ; `pwsh scripts/test.ps1 -Platform EditMode` (pod unity-slot)
- 20:54 r2e (APK 2080745dd4, G3-A capped, 12 przeplatanych): GPU p95 śr. Low r2 34.00, cull 100 33.83, cienie 25 m 34.08, 25 m+512 33.94 -> żaden nie zamyka 0.6 ms, Low bez zmian (ADR 0136 Runda 2c). Merge origin/main 6efbb76c1 (0141; generated/art-source = main). MirrorCostTests naprawiony.
  NASTĘPNY KROK: (w tle) `pwsh artifacts/a16-perf/prep-r2f.ps1` (import 0141 + EditMode + APK Low), potem skyline 0141 na A16 (qacam=sbs-g3-b-297817221966185 qacam_set=gate3).

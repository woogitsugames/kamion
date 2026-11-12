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

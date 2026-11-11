# STATUS — perf-low-r2 (ADR 0113, rendering-perf)

## 2026-11-11 16:00 — krok 1: kod forest fast path + PSO/spike (bez pomiaru)
- Library skopiowana z main (8,2 GB). Lider mierzy (PHONE_RUN 15:43) — czekam z Unity.
- `Kamion/Vegetation`: `_KAMION_VEG_FAST` (global multi_compile, kolor): ściany HLOD L2 SH per wierzchołek (L0+L1 per piksel),
  brak pobrania mapy cieni za zanikiem URP (fade jak URP Lit); `_VegZWrite`/`_VegOffset` = tryb jednoprzebiegowy ścian HLOD.
- Nowy `Kamion/Forest Canopy` (M_ForestCanopy, QualityProfile.canopyMaterial): BRDF URP Lit (metal 0), SH/env/fog per wierzchołek, bez cieni.
- `ForestFastPath` (Rendering/Runtime): Shipping = QualityProfile.forestFast (Low on, rev 113, migracja w ProjectSetup);
  A/B `rq_ab` forestfast|vegfast|hlod1pass|canopyfast|veganiso; `rq_forestfast 0|1`. Haki w WorldInstances (Register/Unregister/Canopy).
- `PsoWarmup`: GraphicsStateCollection warm-up z Resources/Pso (`pso_warm 0` = A/B), trace `pso_trace <s> pso_tag <t>`,
  `spike_probe 1` → `[SPIKE]` (markery profilera w buildzie Development).
- NASTĘPNY KROK: (po zwolnieniu PHONE_RUN) `pwsh scripts/test.ps1 -Platform EditMode` (kompilacja), potem
  `pwsh scripts/build-android.ps1 -Tier Low` → `pwsh -NoProfile -File artifacts/perf-low-r2/phone-diag.ps1 -Apk <apk> -OutTag diag1 -Segment B -Uncapped -Runs "ab_forest=rq_ab=forestfast;ab_veg=rq_ab=vegfast;ab_1pass=rq_ab=hlod1pass;ab_canopy=rq_ab=canopyfast;ab_aniso=rq_ab=veganiso"`

## 16:20 — krok 2: build diag1 + pomiar w toku
- EditMode 247/248 → poprawione (PsoWarmup: ViewCameraResolver zamiast Camera.main); APK diag `kamion-0.1.0-c0a20185ec.apk` (SHA256 b5062b2d…6af3, 191,3 MB).
- Uruchomione `artifacts/perf-low-r2/run-diag1.ps1` (A/B lasu G3-B bez limitu; trace PSO G3-B/G3-A; spike probe G3-A; adb pull *.graphicsstate → artifacts/perf-low-r2/pso/).
- NASTĘPNY KROK: po `artifacts/perf-low-r2/diag1.done`: `python artifacts/perf-low-r2/summarize.py "artifacts/perf-low-r2/diag1/*"`; grep `[PSO]`/`[SPIKE]` w diag1/*/logcat.txt; skopiować *.graphicsstate do game/Assets/_Project/Rendering/Resources/Pso/.

## 16:55 — krok 3: A/B lasu (diag1/diag2), trace PSO, sonda skoków
- G3-B Low bez limitu, rq_ab (12+12 okien 4 s), Δ GPU p50 (wysyłka − bez): **forestfast −0,68 ms** (canopyfast −0,30, hlod1pass −0,28,
  vegfast +0,04 ≈ 0, veganiso −0,03 ≈ 0 → aniso nie wysyłane). cellsort (komórki od najbliższych) +0,12 B / +0,56 A → usunięte.
- Trace PSO działa tylko w buildzie Development (release: BeginTrace ok, 0 stanów): G3-A 78 wariantów / 140 stanów, G3-B 67 / 134
  → `game/Assets/_Project/Rendering/Resources/Pso/pso_Vulkan_Low_g3{a,b}.graphicsstate`.
- Sonda [SPIKE] (dev): piki 50 ms = GPU ~30–34 ms + Gfx.WaitForPresent; skupisko G3-A t≈57–60 s, pos (552,-695) = rondo Bieżeństwa:
  DrawOpaqueObjects kamery głównej 38–70 ms na wątku głównym + `Loading:GfxResource.Register` (pierwsze użycie zasobów/stanów) → hipoteza: PSO/rejestracja przy nowym widoku.
- NASTĘPNY KROK: visual-qa przed/po (`pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Rq rq_forestfast=0 -OutputDir artifacts/perf-low-r2/vqa/before-ov` + after), build czysty, `artifacts/perf-low-r2/gate-final.ps1 -Apk <apk>` + G3-A z pso_warm=0.

## 17:10 — krok 4: finał (czysty APK 6b6c1d8003), testy, dokumenty
- APK `artifacts/apk/kamion-0.1.0-6b6c1d8003.apk` (SHA256 02ce1654a3d14c23073b259863f0c8b6bb95258bed933affcb6ce0d368b12fc3, 191,4 MB).
- Testy: EditMode 248/248, PlayMode 110 pass / 0 fail / 7 skip. visual-qa Low overcast/clear przed/po: `vqa/`, `vqa/960/`.
- docs/adr/0113-perf-low-a16-r2.md, docs/PERFORMANCE_BUDGETS.md (sekcja r2).
- Wideo migotania lasu z telefonu NIE nagrane: lider trzymał PHONE_RUN 17:15–18:05+ (gate3 run5); skrypt gotowy, zatrzymany.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/perf-low-r2/shimmer.ps1` (po/przed, ten sam APK 6b6c1d8003 już na A16), potem
  `ffmpeg -i artifacts/perf-low-r2/shimmer/after.mp4 -vf fps=10,scale=960:-1 artifacts/perf-low-r2/shimmer/after-%03d.jpg` (+ before) i porównać pas lasu.

## RAPORT KOŃCOWY (ADR 0113, gałąź perf-low-r2)
- SHA kodu pomiaru: `6b6c1d80` (APK powyżej); ostatni commit gałęzi: patrz `git log -1` (docs/artefakty po pomiarze).
- Zrobione: szybka ścieżka lasu na Low (`QualityProfile.forestFast`, rev 113): korony HLOD `Kamion/Forest Canopy` (−0,30 ms),
  ściany HLOD jednoprzebiegowo (−0,28), `_KAMION_VEG_FAST` (≈0 ms, ale usuwa artefakty cienia za dystansem cieni); razem −0,68 ms GPU p50.
  Prewarm PSO `GraphicsStateCollection` (Resources/Pso, nagrane na A16 dev buildem; 3,5–5,3 s w ładowaniu): >40 ms w 1. 5 s G3-A 17 → 3.
  Sonda `[SPIKE]` (`spike_probe 1`), trace PSO (`pso_trace`), A/B `rq_ab forestfast|vegfast|hlod1pass|canopyfast|veganiso`, `rq_forestfast`, `pso_warm`.

| A16 Low 30 FPS | FPS | p50/p95/p99 | p99x | >40 (x) | GPU p50/p95 | CPU p50/p95 | PSS | T bat |
|---|---|---|---|---|---|---|---|---|
| G3-A przed (ten APK, forest off, PSO off) | 29,77 | 33,3/33,5/49,9 | 49,9 | 27 (22) | 30,1/32,1 | 22,5/28,9 | 842 | 28,2 |
| G3-A po | 29,81 | 33,3/33,5/49,9 | 33,6 | 24 (12) | 30,0/31,7 | 22,4/29,5 | 869 | 28,2 |
| G3-B przed | 29,89 | 33,3/33,5/33,7 | 33,7 | 16 (15) | 29,7/33,6 | 20,4/27,9 | 858 | 28,4 |
| G3-B po | 29,96 | 33,3/33,5/33,6 | 33,6 | 5 (5) | 29,0/32,2 | 21,8/28,3 | 839 | 28,1 |
  p99x / (x) = bez ostatnich 1,5 s CSV (screencap + dumpsys meminfo skryptu pomiaru w trakcie renderu). Termika: status 0 wszędzie.
  Przejazdy ~1,5 min, nie 30 min (termika po 30 min — nie mierzona w tej rundzie).
- Cel: p99 ≤ 40 — G3-B tak, G3-A tak bez okna zrzutu (oficjalnie 49,9 przez artefakt pomiaru); GPU p95 ≤ 28 — NIE (31,7/32,2).
- Koszt jakości: overcast PSNR ≥ 60 dB, clear ≥ 47 dB; jedyne widoczne różnice = usunięte czarne bloki cienia na dalekich koronach
  (`vqa/960/clear-*-crop-before-after.jpg`).
- Otwarte: (1) device-metrics: zrzut/meminfo po zatrzymaniu zapisu klatek (build-qa); (2) GPU p95 ≤ 28 tylko przez mniej pikseli (D50);
  (3) nagrać PSO ponownie po scaleniu 0107/0108/0110 i dla Medium/High na S24+; (4) korony HLOD bez toe/KamionMixFog (jak URP Lit) — do oceny;
  (5) lusterka bez zmian (Low = 1 render/klatkę już; rzadziej = szarpanie); (6) wideo migotania lasu z telefonu nienagrane
  (telefon zajęty przez lidera) — skrypt `shimmer.ps1`; ryzyko niskie: ściany jednoprzebiegowe mają to samo A2C i ten sam clip.
- Konflikty: QualityProfile(.cs/.asset)/ProjectSetup (rev 113, migracje 98/106 zachowane), Vegetation.shader (GPT 0109),
  WorldInstances.cs (3 haki), RenderOverrides/ExtraViewCostMonitor/QualityProfileApplier (dopisane).

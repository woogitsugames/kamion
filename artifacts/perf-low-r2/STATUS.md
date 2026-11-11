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

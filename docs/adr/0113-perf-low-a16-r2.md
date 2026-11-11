# ADR 0113: Wydajność Low na A16 r2 — szybka ścieżka lasu, prewarm PSO (GraphicsStateCollection)

Status: propozycja (rendering-perf, gałąź `perf-low-r2`, z main `1791a0ed` po 0106), 2026-11-11.
Powiązane: ADR 0106 (rozkład GPU A16, przełączniki rq_ab), 0015/0023 (HLOD lasu, impostory), 0088 (korony), D49 (A16 = Low),
D50 (bez obniżania skali renderu przed tą rundą).

## Kontekst
Po 0106 (A16 SM-A165F, Mali-G57 MC2, Vulkan, Low 30 FPS): G3-A p99 50,0 ms (27 klatek > 40 ms, z tego 14 w pierwszych 5 s okna
i pakiet 7 klatek przy rondzie Bieżeństwa), G3-B p99 33,7; GPU p95 31,1 / 33,7 ms. Las (ADR 0106 A/B): ściany HLOD 1,8 ms,
korony HLOD (URP Lit) 0,9 ms, impostory 1,6 ms. Cel zadania: GPU p95 ≤ 28 ms i p99 ≤ 40 ms na G3-A i G3-B bez widocznej utraty jakości.

## Diagnoza (telefon; `artifacts/perf-low-r2/diag1`, `diag2`, `final`)
**Las — A/B przeplatane (G3-B, bez limitu, 12+12 okien 4 s, Δ GPU p50 wysyłka − bez):**

| zmiana | Δ GPU p50 (ms) | uwagi |
|---|---|---|
| całość szybkiej ścieżki lasu (`forestfast`) | **−0,68** | wysłane (Low) |
| — korony HLOD na `Kamion/Forest Canopy` (`canopyfast`) | −0,30 | |
| — ściany HLOD jednoprzebiegowo (`hlod1pass`) | −0,28 | ZWrite + A2C w kolorze, bez depth pre-pass |
| — `_KAMION_VEG_FAST` (`vegfast`) | +0,04 (≈ 0) | L2 SH per wierzchołek na ścianach, cień za zanikiem; wysłane dla jakości (niżej) |
| aniso 1 zamiast 2 na teksturach roślinności (`veganiso`) | −0,03 (≈ 0) | nie wysłane |
| komórki instancji od najbliższej (front-to-back) (`cellsort`) | +0,12 (B) / +0,56 (A) | gorzej (CPU sortowania, brak zysku early-Z) — usunięte |

Wniosek: koszt lasu na G57 nie siedzi w ALU fragmentu ani w filtrowaniu tekstur, tylko w rasteryzacji/pokryciu (A2C przy MSAA 2×)
dużych, przezroczystych powierzchni; tańsze shadery dają ~0,7 ms z 4,3. Dalszy zysk tylko przez mniej pikseli lasu (geometria
HLOD/impostorów, dystanse) — to zmiana obrazu, poza tą rundą.

**Piki p99.** Sonda `[SPIKE]` (build Development, wszystkie markery profilera): pakiet przy rondzie Bieżeństwa (pos 552,−695) to
`DrawOpaqueObjects` kamery głównej 38–70 ms na wątku głównym z `Loading:GfxResource.Register` — pierwsze użycie stanów/zasobów
w nowym widoku; piki na początku okna to to samo przy ruszeniu. Pozostałe pojedyncze 50 ms to GPU 30–34 ms + `Gfx.WaitForPresent`
(granica 33,3 ms). Trace `GraphicsStateCollection` działa tylko w buildzie Development (release: `BeginTrace()` = true, 0 stanów).
**Artefakt pomiaru:** `device-metrics.ps1` robi `screencap` i `dumpsys meminfo` gdy gra jeszcze renderuje — ostatnie ~1,5 s CSV
ma serię 10–14 klatek 40–54 ms CPU (G3-A: t≈89 s), co samo w sobie przekracza 1 % klatek. Tabele poniżej podają p99 oficjalne
i „p99x” (bez ostatnich 1,5 s CSV), liczone tak samo dla przed/po.

## Decyzja
1. **`QualityProfile.forestFast`** (Low = 1, reszta 0; `revision` 113, migracja `< 113` w `ProjectSetup`, 98 i 106 zachowane;
   `rq_forestfast 0|1`; A/B `rq_ab forestfast|vegfast|hlod1pass|canopyfast|veganiso`), `Game.Rendering.ForestFastPath`:
   - **`Kamion/Forest Canopy`** (`M_ForestCanopy`, `QualityProfile.canopyMaterial`): BRDF URP Lit dla dielektryka (Lambert + GGX słońca,
     środowisko z Fresnelem), SH, odbicie środowiska (mip ~6) i mgła Unity per wierzchołek, bez cieni (HLOD > 70 m > dystans cieni)
     i bez świateł dodatkowych. Kopia materiału Lit w czasie gry (`ForestFastPath.Canopy`), assety generowane bez zmian.
   - **Ściany HLOD jednoprzebiegowo**: na kopiach materiałów `_HLOD_EDGE` wyłączony przebieg `SRPDefaultUnlit`, `_VegZWrite 1`,
     `_VegOffset 0` (nowe właściwości `Kamion/Vegetation`, domyślnie stary tryb dwuprzebiegowy).
   - **`_KAMION_VEG_FAST`** (global multi_compile w przebiegu kolorów `Kamion/Vegetation`): ściany — pasmo L2 SH per wierzchołek
     (L0+L1 per piksel, tryb „mixed” URP); wszystkie rośliny — cień słońca z zanikiem odległości URP i bez próbkowania mapy cieni
     za zanikiem. Stara ścieżka próbkowała mapę cieni bez zaniku i dawała **twarde czarne prostokąty na dalekich koronach
     i pas „płotu” u podstawy ściany lasu** (kamery `clear`: `driver-andersa-to-putry`, `truck-at-gate`) — szybka ścieżka je usuwa.
2. **Prewarm PSO** `Game.Rendering.PsoWarmup` (z `RenderOverrides.Parse`, tylko player): `GraphicsStateCollection` z
   `Rendering/Resources/Pso/pso_Vulkan_Low_g3{a,b}.graphicsstate` (nagrane na A16 w buildzie Development: 78/140 i 67/134
   wariantów/stanów) rozgrzewane w tle przy starcie (A16: 3,5–5,3 s, w czasie ładowania WorldC). `pso_warm 0` wyłącza (A/B),
   `pso_trace <s> pso_tag <t>` nagrywa nową kolekcję (persistentDataPath, `adb pull`), `spike_probe 1` loguje `[SPIKE]`.
   Kolekcja pasuje tylko do Vulkan + Low; inne tiery/API: nagrać tak samo (`artifacts/perf-low-r2/run-diag2.ps1`).
3. **Nie zmieniono**: aniso roślinności, kolejność komórek, lusterka (Low ma już 1 render lusterka/klatkę we wspólnym round-robin;
   rzadsze odświeżanie = widoczne szarpanie w lusterkach, wbrew „lusterka zawsze użyteczne”), skala renderu (D50).

## Wynik (A16, czysty APK `kamion-0.1.0-6b6c1d8003.apk`, SHA256 02ce1654…2fc3, 191,4 MB; limit 30 FPS, okno po 25 s)
„przed” = ten sam APK z `rq_forestfast=0,pso_warm=0`; „bez PSO” = `pso_warm=0` (las szybki). Termika 0, bateria 28,1–28,4 °C.
`artifacts/perf-low-r2/final/summary.txt` (`summarize.py`).

| przejazd | FPS | p50 / p95 / p99 (ms) | p99x | >40 (x) | >40 w 1. 5 s | GPU p50 / p95 | CPU main p50 / p95 | PSS MB |
|---|---|---|---|---|---|---|---|---|
| G3-A r1 (0106, APK fd126bf3a9) | 29,78 | 33,3 / 33,5 / 50,0 | 50,0 | 27 (27) | 14 | 29,5 / 31,1 | 22,5 / 28,3 | 811 |
| G3-A przed (ten APK) | 29,77 | 33,3 / 33,5 / 49,9 | 49,9 | 27 (22) | 7 | 30,1 / 32,1 | 22,5 / 28,9 | 842 |
| G3-A bez PSO | 29,63 | 33,3 / 33,5 / 50,0 | 50,0 | 41 (32) | 17 | 30,1 / 32,2 | 22,5 / 29,4 | 824 |
| **G3-A po (gate3)** | 29,81 | 33,3 / 33,5 / 49,9 | **33,6** | 24 (**12**) | **3** | 30,0 / 31,7 | 22,4 / 29,5 | 869 |
| G3-B r1 (0106) | 29,85 | 33,3 / 33,5 / 33,7 | 33,7 | 21 (20) | 9 | 29,1 / 33,7 | 20,9 / 28,1 | 839 |
| G3-B przed (ten APK) | 29,89 | 33,3 / 33,5 / 33,7 | 33,7 | 16 (15) | 7 | 29,7 / 33,6 | 20,4 / 27,9 | 858 |
| G3-B bez PSO | 29,92 | 33,3 / 33,5 / 33,6 | 33,6 | 11 (11) | 3 | 29,3 / 33,0 | 21,2 / 28,3 | 838 |
| **G3-B po (gate3)** | 29,96 | 33,3 / 33,5 / **33,6** | 33,6 | **5** (5) | 1 | **29,0 / 32,2** | 21,8 / 28,3 | 839 |

Ocena wobec celu: **p99 ≤ 40 ms na G3-B (33,6) — tak; na G3-A — tak po wyłączeniu okna zrzutu (p99x 33,6, 12 klatek > 40 ms
= 0,6 %), nie w oficjalnej liczbie gate3 (49,9), bo 12 klatek > 40 ms to zrzut ekranu/meminfo skryptu pomiaru.** Klatki > 40 ms
w pierwszych 5 s: 17 → 3 (G3-A), pakiet przy rondzie Bieżeństwa zniknął. **GPU p95 ≤ 28 ms — nie** (31,7 / 32,2): przy limicie
30 FPS governor Mali rozciąga GPU do ~30 ms (bez limitu ~26,7), las daje 0,7 ms, a pozostałe składniki (szyba ~2,4, skala
renderu ~13 ms zależne od pikseli) są poza zakresem bez zmiany obrazu (D50). Jedno powtórzenie na wariant — rozrzut między
przejazdami ±5–10 klatek > 40 ms; kierunek spójny w obu odcinkach.

Jakość (kamery kontrolne Low, `artifacts/perf-low-r2/vqa/`): overcast PSNR ≥ 60 dB (różnice < 0,02 % pikseli), clear ≥ 47 dB —
jedyne widoczne różnice to usunięte artefakty cienia (`vqa/960/*-crop-before-after.jpg`). Migotanie lasu w ruchu: **wideo z telefonu nie nagrane w tej rundzie** (telefon zajęty
pomiarami lidera); skrypt `artifacts/perf-low-r2/shimmer.ps1` (ten sam APK, po/przed). Ryzyko niskie: ściany jednoprzebiegowe
mają to samo pokrycie A2C i ten sam próg co ścieżka dwuprzebiegowa, impostory i karty bez zmian geometrii.

## Otwarte
1. `scripts/device-metrics.ps1` (build-qa): zatrzymać zapis klatek przed `screencap`/`dumpsys meminfo` albo liczyć p99 do
   `DurationSeconds` — dziś zrzut dokłada ~1 % klatek > 40 ms do każdego przejazdu (G3-A przekracza przez to p99).
2. GPU p95 ≤ 28 ms przy limicie 30: wymaga mniej pikseli (skala/HLOD/impostory — decyzja właściciela, D50) albo szyby r2.
3. PSO: kolekcje nagrane dla Low/Vulkan i dwóch odcinków; nowe treści (zabudowa 0107, drogi 0110, światło 0108) dodadzą stany —
   po scaleniu nagrać ponownie (`pso_trace`, build Development) i podmienić pliki. Medium/High: nagrać na S24+.
5. Wideo migotania lasu na A16 (po/przed) — `shimmer.ps1`, do obejrzenia przed scaleniem.
4. Korony HLOD nadal bez tonu „toe” Low i z mgłą Unity (jak URP Lit) — niespójność z resztą świata (KamionMixFog) zostawiona,
   bo zmiana obrazu; do oceny wizualnej.

## Konflikty przewidywane
- `QualityProfile.cs/.asset`, `ProjectSetup.cs`: pola `forestFast`, `canopyMaterial`, `CurrentRevision` 113, blok `< 113` (106 → 106
  explicite). Addytywne; przy scaleniu z GPT (0108/0109) zachować wszystkie migracje w kolejności rewizji.
- `Vegetation.shader` (GPT roślinność r3, ADR 0109): nowe właściwości `_VegZWrite/_VegOffset`, `ZWrite/Offset` z właściwości,
  multi_compile `_KAMION_VEG_FAST`, funkcje `LeafAmbientL2`, `VegShadow`; zmiany modelu oświetlenia liści muszą trafić do obu ścieżek.
- `WorldInstances.cs` (world-builder): 3 linie haków (`ForestFastPath.Register/Unregister/Canopy`).
- `RenderOverrides.cs`, `ExtraViewCostMonitor.cs`, `QualityProfileApplier.cs`: dopisane pola/klucze.

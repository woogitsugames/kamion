# R8 — GPU telefonów testowych (Galaxy A16 / Mali-G57 MC2, Galaxy S24+ / Xclipse 940) i plan oszczędności dla A16 Low

- Data: 2026-11-14 · gałąź `research/cloud2-mobile-gpu-a16` (z `origin/main` 81c9bae) · pakiet R8 (cloud2)
- Manifest: **134 wiersze** (SOURCED 117, UNVERIFIED 13, ESTIMATED 4) — `manifest.csv`, generator `make_manifest.py`
- Obejrzane: **25 dokumentów zewnętrznych** (2 PDF Arm: datasheet s.1–2 obejrzane jako obrazy dwukrotnie, Best Practices — 18 stron przeczytanych;
  3 raporty gpuinfo + 2 listy API; 4 zgłoszenia Unity przez API; strony Unity/Qualcomm/Arm/Khronos) + 13 plików repo. Kadrów zdjęciowych brak (pakiet dokumentowy) — kolumny lat/lon/kierunek/opis puste.
- Samokontrola: `audit_20_percent.json` — seed 20261114, 27/134 wierszy, źródła **ponownie pobrane z sieci**: **26 PASS / 1 FAIL** (R8-029 — cytat z dwóch raportów pod jednym URL; poprawiony w manifeście razem z bliźniaczym wierszem). Dodatkowo kontrola wszystkich 134 cytatów względem plików lokalnych.
- Pliki do pobrania przez `fetch.py`: 27 plików, **9,4 MB**.

## Cel
Ustalić, co naprawdę ogranicza GPU A16 na tierze Low (bramka 3: GPU p95 **34,3–34,5 ms** przy budżecie 33,3 ms, `REVIEW-2026-11-14-s20-gate3-phone.md`),
zebrać specyfikacje i limity obu telefonów, koszty technik na Mali/Valhall (i Adreno dla Folda), znane problemy Unity/sterownika,
i dać ranking zmian z uczciwymi przedziałami zysku.

## Metoda
1. Stan repo: `PERFORMANCE_BUDGETS.md`, `DEVICE_MATRIX.md`, ADR 0013/0106/0113/0136/0153/0177, raport bramki 1–2 A16, ustawienia `URP_Low`, `Mobile_Renderer`, `QualityProfile` (Low), `ProjectSettings`.
2. Źródła producentów (MediaTek, Arm, Samsung), gpuinfo (raporty CC BY 4.0), dokumentacja Unity 6.3, Qualcomm, Khronos Vulkan-Samples, Unity Issue Tracker (publiczne API JSON).
3. Każda liczba: cytat + URL (SOURCED), obliczenie z jawną metodą (ESTIMATED) albo UNVERIFIED. Zyski „ms” bez pomiaru na A16 są **UNVERIFIED** z uzasadnieniem.

## Wyniki

### 1. Sprzęt (do gry: „GPU klasy Valhall 2-rdzeniowy” vs „GPU klasy RDNA3 6-rdzeniowy”)
| | Galaxy A16 (SM-A165F) | Galaxy S24+ (SM-S926B) |
|---|---|---|
| SoC / GPU | MT6789 Helio G99 / **Mali-G57 MC2** (Valhall) | **Exynos 2400 / Xclipse 940** (RDNA 3, „hexa-core GPU”) |
| Wariant PL | — | Exynos — **pomiar w repo** (getprop `s5e9945`, `ro.hardware.egl=samsung`); gpuinfo: 7/8 raportów SM-S926B = Xclipse 940; prasa PL: „w Polsce … SM-S926B otrzyma procesor Samsung Exynos 2400”. Snapdragon 8 Gen 3/Adreno 750 nie dotyczy naszego telefonu |
| Na rdzeń (Arm datasheet) | 2 jednostki ALU, warp 16, **FP32 64 / FP16 128 ops/cykl, 2 px/cykl, 4 teksele/cykl**, tile 256 bit/px, cache tekstur 32K | (brak danych producenta na rdzeń) |
| Razem (ESTIMATED) | 4 px/cykl, 128 FP32 ops/cykl, 8 tekseli/cykl × zegar GPU (**zegar UNVERIFIED** — brak u MediaTek) | — |
| Pamięć | LPDDR4X 4266 Mbps; pasmo ≈17 GB/s tylko przy założonej szynie 32-bit (UNVERIFIED) | nie badano (poza zakresem) |
| Vulkan (gpuinfo) | 1.3.303 / sterownik 54.1.0 (Android 17); stary 1.1.177 / 32.1.0 (Android 14). **Repo widzi „Vulkan 1.1” na Androidzie 16** — sprawdzić sterownik naszego telefonu | 1.3.304 / 25.3.3 (Android 17) |
| Limity | maxImageDimension2D 16384; deskryptory per stage 8 388 608 (stary: 500 000); zestawy 7 (stary: 4); subgroup 16; FP16/Int16 tak; ASTC LDR+HDR, ETC2; aniso 16; **multiDrawIndirect false** | 16384; 4 294 967 295; zestawy 32; subgroup 32–64; ASTC LDR (HDR nie); multiDrawIndirect, rayQuery, VRS — tak |
| Cechy G57 ważne dla nas | **MSAA 2× sprzętowo promowane do 4×**; FP16/R11G11B10 blend przyspieszony; brak Fragment Prepass (dopiero G725) → działa tylko early ZS + FPK; shadow map sampling ×2; ASTC bez decode_mode ×2; >32 rejestry = 512 wątków zamiast 1024 | |

Pikseli na Low: 2340×1080 × 0,75² = **1 755 × 810 = 1,42 Mpx**; natywnie 2,53 Mpx. Teoretyczne minimum na jedną pełnoekranową warstwę = px / (4 px/cykl × f) → przy f = 1 GHz ≈ 0,36 ms (0,75) / 0,63 ms (natywnie) — tylko rząd wielkości, bo f GPU nieznane.

### 2. Koszt technik na Mali/Valhall (mechanizm → stan w projekcie → co robić)
| Technika | Mechanizm (źródło) | Stan Low w repo | Wniosek |
|---|---|---|---|
| alpha-test (`discard`) | „forces a late ZS test” (Arm BPG s.22); Adreno: może wyłączyć LRZ/Early-Z (Qualcomm) | karty liści, impostory, HLOD | zmniejszać **powierzchnię** discard (przycinanie geometrii do alfy — ImpostorTrim zmierzony: 1,37→0,51 ms) |
| alpha-to-coverage | też late ZS (BPG s.22) | `leafAlphaToCoverage: 1` | ADR 0013: A2C off −2,6 ms (Medium, las, MSAA 4×); koszt to raster/pokrycie (ADR 0113) |
| alpha-blend | wyłącza early ZS i FPK (BPG s.67); mieszać na unorm | szyba kabiny (3,6–4,3 ms przed szybką ścieżką) | ograniczyć powierzchnię mieszaną szyby (plan P6) |
| depth prepass / Depth Priming | „Do not use depth prepass” (BPG s.23); Unity: Disabled dla mobile | `m_DepthPrimingMode: 0` ✓ | nie ruszać |
| MSAA | 4× „not expensive” przy resolve w tile (BPG s.61); zły resolve 3,9 vs 0,5 GB/s; Mali-G76: +3 % pasma vs +5 GB/s (Vulkan-Samples) | MSAA 2 (= 4× w sprzęcie G57); 2×→1× = 0 ms (ADR 0106) | zostawić; **nie** zamieniać na FXAA (dodatkowy przebieg pełnoekranowy) |
| cienie | porównanie głębi ×2 przy próbkowaniu (datasheet, BPG s.76); soft shadows „High impact” na tiled (Unity) | 1024 / 1 kaskada / 35 m / twarde ✓ | wyczerpane: 25 m / 512 px = szum (ADR 0136 r2c) |
| overdraw / kolejność | test głębi, backface culling, front-to-back, mało przezroczystości (BPG s.56) | las: kolejność komórek bliżej→dalej +0,1..+0,6 ms (gorzej, ADR 0113) | sortowanie per komórka nie pomaga; tylko mniejsza powierzchnia alfy |
| post-processing / HDR | full-screen pass ∝ piksele; HDR → 32 bit (R11G11B10) (Unity); blending FP16/R11G11B10 przyspieszony od G57 | post off, HDR off ✓ | nie dotyczy Low |
| render scale / upscale | URP: skaluje tylko grę, UI natywnie → upscale = przebieg pełnoekranowy; Android: SurfaceFlinger skaluje wydajnie (Qualcomm) | 0,75; D50 zakazuje < 0,75 | P2: ta sama skala przez rozdzielczość okna |
| **Blit Type** | „Always: renders to an offscreen buffer and then uses a blit … usually slower” (Unity) | **`androidBlitType: 0` = Always** (enum z UnityCsReference) — nieopisane w żadnym ADR | **P1** |
| depth / opaque texture | kopie i pasmo (Unity); MSAA + zapis głębi: +6,3 GB/s w najgorszym przypadku (Mali-G76) | off ✓ | nie włączać na Low |
| SRP Batcher / instancing / GRD | SRP Batcher zalecany (Unity); multiDrawIndirect=false na G57 | SRP Batcher on, GRD off ✓ | GRD na A16 bez sensu (brak MDI) |
| LOD / impostory | discard + pusta alfa = koszt rastra (ADR 0136) | impostory przycięte; karty liści 23–48 % pokrycia — otwarte | P3 |
| ASTC / mipmapy | ASTC + mipmapy zawsze w 3D; trilinear ×2 (BPG s.76) | ASTC 5×5/6×6/8×8 ✓; aniso roślin 2→1 ~0 ms (ADR 0113) | brak dźwigni |
| precyzja half | FP16 = 2× ALU (datasheet); mediump samplery (highp do 2× wolniej); nie dla pozycji świata (BPG s.94–95) | nieznane per shader | P5 (Mali Offline Compiler, bez telefonu) |
| światła dodatkowe | Unity: Disabled / Per Vertex | per pixel, limit 2; streetLights 0 | P10 (najpierw sprawdzić, czy w ogóle są) |
| sondy odbić | Unity (słaby mobile): Probe Blending i Box Projection off | oba on | P9 (głównie CPU) |
| LOD Cross Fade | Unity: off na słabym mobile (alpha test) | on w asset, ale wszystkie LODGroup `fadeMode None` | ≈0 GPU, tylko warianty |

**Sprzeczność do wyjaśnienia (MSAA):** datasheet Arm: 2× na G57 jest promowane do 4×; repo: 4× w lesie +10,9 ms vs 2× (ADR 0013), a 2×→1× = 0 ms (ADR 0013, 0106).
Jeśli 2× = 4× w sprzęcie, koszt 2× i 4× powinien być równy. Hipotezy (UNVERIFIED): Unity/sterownik nie używa 2× (spada do 1×), albo A2C liczy pokrycie zależnie od żądanej liczby próbek.
Rozstrzygnięcie: RenderDoc for Arm GPUs / Frame Advisor na A16 — liczba próbek załącznika koloru przy `msaa: 2`. Jeśli wychodzi 1×, Low nie ma dziś MSAA (wpływ na ocenę wizualną, nie na wydajność).

### 3. Znane problemy Unity / sterownik (tylko wpisy z linkiem)
| Klucz | Co | Dotyczy nas? |
|---|---|---|
| UUM-147578 | korupcja (białe kwadraty) na Mali/Vulkan, shader z FrameBuffer + DepthTexture | naprawione w **6000.3.28f1 = wersja projektu**; G57 MC2 nie reprodukował |
| UUM-137912 | crash DoF „Bokeh” na Vulkan (Mali, sterownik GLES_mali) | A15 5G / G57 MC2 nie reprodukował; 6000.3 otwarte; DoF w projekcie `mode 0` (off) — nie włączać Bokeh |
| UUM-28518 | crash `libGLES_mali.so` w `FrameTimingManagerGLES::GetGPUFrameEvents` (G57 MC2 wśród urządzeń klienta) | projekt mierzy GPU przez FrameTimingManager; na A16 działa Vulkan, ale ProjectSettings ma fallback GLES3 → ryzyko w telemetrii przy fallbacku |
| UUM-107530 | spadek FPS po przejściu na Vulkan (2022.3/6000.0) | Adreno 618 itd.; Mali G76–G710 nie reprodukowały; G57 niebadany |
Nie znaleziono wpisu z linkiem o problemach Mali-G57/MT6789 z depth texture, MSAA resolve ani kompilacją shaderów (dwa trafienia wyszukiwarki zniknęły po migracji trackera — „Page not found”). Repo: skoki PSO rozwiązuje prewarm `GraphicsStateCollection` (ADR 0113/0177).

### 4. Plan oszczędności dla A16 Low (ranking; cel: −1,0…−1,2 ms GPU p95)
Weryfikacja każdej pozycji: `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90` na G3-A i G3-B, A/B przeplatane w jednym APK (`rq_*`) albo para APK z tym samym versionCode (ADR 0136: niższego versionCode nie da się zainstalować).
| # | Zmiana | Zysk GPU (ms) | Status liczby | Ryzyko wizualne | Uwagi |
|---|---|---|---|---|---|
| P1 | **Blit Type Always → Auto** (ProjectSettings) | 0,3–1,5 | UNVERIFIED: ≥1 kopia 2,53 Mpx (≈0,63 ms przy 1 GHz, 4 px/cykl) + ~20 MB/klatkę pasma | brak | ustawienie gracza → para APK; `Never` może nie działać na części urządzeń (Unity) — `Auto` bezpieczniejsze. Sprawdzić RenderDoc: liczba przebiegów |
| P8 | Mierzyć pracę w cyklach (GPU active cycles lub ms × f) | 0 (metoda) | — | — | governor dodaje 1,5–2 ms przy limicie 30 FPS (ADR 0136) — część „nadwyżki” może być DVFS; zrobić przed oceną reszty |
| P3 | Przycięcie kart liści LOD0/LOD1 (jak ImpostorTrim) | 0,2–1,0 (G3-B/las) | UNVERIFIED: analogia do zmierzonego −0,86 ms impostorów przy 6–13 % pokrycia; karty mają 23–48 %, więc mniej | brak przy dylatacji | G3-A ≈ 0 (brak lasu) |
| P2 | Skala 0,75 przez rozdzielczość okna (Fixed DPI / `Screen.SetResolution`) zamiast URP renderScale | 0,3–1,5 | UNVERIFIED: znika upscale URP + RT pośredni; skaluje SurfaceFlinger | HUD/tekst w 1755×810 | decyzja właściciela (D50 zachowane — skala ta sama) |
| P4 | LOD1/LOD2 aut 1–2 submeshe (ADR 0153 — zaimplementowane, niezmierzone na A16) | 0,1–0,6 | UNVERIFIED: auta +1,29 ms GPU bez limitu (ADR 0136), przy limicie governor zjada większość | brak | pozwala też wrócić do cull 300 m |
| P6 | Szyba kabiny: mieszać tylko obszar refleksu/brudu | 0,3–1,5 | UNVERIFIED: szyba 3,6–4,3 ms (0106), raster+blend ~1,2 ms | utrata części przyciemnienia | widok z kabiny = główny widok |
| P5 | Mali Offline Compiler (G57) na shaderach świata + half w ALU-bound | 0–1,0 | UNVERIFIED (las nie jest ALU-bound — ADR 0113) | artefakty przy half pozycji | do zrobienia bez telefonu (CI) |
| P12 | LOD bias Low ×0,6 | 0–1,4 | UNVERIFIED (ADR 0106: Δ GPU p50 1,4 ms bez limitu FPS, treść sprzed s11; przy limicie 30 FPS zysk może prawie zniknąć — por. ADR 0136 r2c 1,29→0,17 ms) | popping LOD bliżej | decyzja właściciela; powtórzyć pomiar |
| P11 | Far clip 900 → 720 m | 0–0,7 | UNVERIFIED (ADR 0106: Δ GPU p50 0,7 ms bez limitu FPS, treść sprzed s11; przy limicie 30 FPS zysk niepewny — por. ADR 0136 r2c) | bliższy horyzont | decyzja właściciela |
| P7 | Ściany HLOD: przyciąć puste ~12 % atlasu | 0–0,2 | UNVERIFIED (12 % z ~1,8 ms) | brak | mały |
| P9 | Probe Blending + Box Projection off na Low | 0–0,3 | UNVERIFIED (głównie CPU) | odbicia mniej dopasowane | |
| P10 | Additional Lights Disabled na Low (jeśli brak świateł w G3) | 0–0,3 | UNVERIFIED | ewentualne światła znikną | najpierw Frame Debugger |
| — | **Nie robić:** depth prepass; MSAA→1× (0 ms); FXAA; cienie 25 m/512 px (szum); cull aut 100 m (−0,17 ms) | | SOURCED (repo/Arm) | | |

Zalecana kolejność: **P8 → P1 (+P2 jako wariant) → P3 → P4 → P6**, potem decyzje właściciela (P12/P11).
P1 i P2 nie zmieniają treści ani profilu jakości — zgodne z wnioskiem ADR 0136 („wymaga zmiany treści, nie cięcia profilu”) w tym sensie, że usuwają pracę, której nie widać.

### 5. Narzędzia pomiaru
- **Arm Performance Studio** — bezpłatne („available free of charge”): Streamline + Performance Advisor (liczniki G57, w tym late ZS, cykle), Frame Advisor, Mali Offline Compiler, RenderDoc for Arm GPUs. Unity: wymaga **Development Build** (debuggable).
- **AGI**: A16/G57 nie ma na liście; „new devices with Android 12 … are expected to pass” — sprawdzić walidacją (UNVERIFIED).
- **libGPUCounters** (MIT): liczniki Mali (od G71) wewnątrz aplikacji — kandydat do `DiagnosticsSampler` (cykle GPU niezależne od DVFS); działa tylko ze sterownikiem komercyjnym Arm; dostęp bez roota UNVERIFIED.
- Unity Frame Debugger / RenderDoc — liczba przebiegów (P1/P2), próbki MSAA.

## Co już było w repo / co nowe
| Temat | W repo przed R8 | Nowe w R8 |
|---|---|---|
| Rozkład GPU A16 Low | ADR 0106/0136 (A/B na telefonie) — cytowane, nie dublowane | — |
| Specyfikacja G57 | „2-core Mali-G57” bez liczb | liczby Arm na rdzeń, tile 256 bit, koszty filtrowania, brak Fragment Prepass |
| MSAA | 2×=1× (0106), 4× drogie w lesie (0013) | datasheet: 2× → 4× w sprzęcie → sprzeczność do zbadania |
| Wariant S24+ | getprop: Exynos 2400 | potwierdzenie gpuinfo (7/8) + prasa PL; limity Vulkan Xclipse 940 |
| Blit Type | brak wzmianki | `androidBlitType: 0` = Always → P1 |
| Skalowanie przez okno | brak | P2 (Fixed DPI / SurfaceFlinger) |
| Narzędzia | „no vendor GPU profiler yet” (ADR 0013) | Performance Studio darmowe, wymóg Development Build, libGPUCounters, AGI bez A16 na liście |
| Problemy Unity | PSO (0113/0177) | 4 wpisy trackera z wersjami poprawek; projekt na 6000.3.28f1 ma poprawkę UUM-147578 |

## Luki
- Zegar GPU Helio G99 i szerokość szyny DRAM — UNVERIFIED (brak u producenta). Odczyt na telefonie.
- Wersja sterownika Vulkan na NASZYM A16 (Android 16) — repo mówi „Vulkan 1.1”, gpuinfo ma 1.1 (Android 14) i 1.3 (Android 17).
- Xclipse 940: brak publicznego przewodnika optymalizacji producenta; nie wiadomo, czy zachowuje się jak TBDR (UNVERIFIED) — porady Arm/Qualcomm nie przenoszą się 1:1 na S24+.
- Adreno 750 / wariant Snapdragon S24+ — nie dotyczy naszego telefonu, nie badano. Fold (Adreno 8xx) — tylko porady Qualcomm.
- Wszystkie zyski P1–P10 to szacunki — wymagają `device-metrics.ps1` na A16.

## Jak używać w grze
1. Najpierw P8 (metryka) i P1 (para APK `androidBlitType` 0 vs 2, ten sam versionCode) — najtańszy test bez zmiany obrazu.
2. Zmiany profilu tylko w `QualityProfile`/`ProjectSetup` (generator), z override `rq_*` do A/B — jak w ADR 0106/0136.
3. Przy nowej treści roślinności: przycinać geometrię do alfy (ImpostorTrim jako wzór), nie dokładać discard/A2C na duże powierzchnie.
4. Nie włączać na Low: depth/opaque texture, soft shadows, FXAA, HDR, DoF Bokeh.

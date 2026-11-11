# ADR 0106: Wydajność Low/Medium na A16 r1 — rozkład GPU klatki, szybka ścieżka szyby kabiny

Status: propozycja (rendering-perf, gałąź `perf-low-r1`, z main `7c094c3f` po 0097), 2026-11-11.
Powiązane: ADR 0010 (tiery), 0013 (A16, MSAA), 0042/0046/0068 (lusterka, A/B przebiegów), 0045/0048/0059 (szyba),
0015/0023 (HLOD lasu, impostory), 0062 (skala renderu).

## Kontekst
Bramka 3, A16 (SM-A165F, Mali-G57 MC2, Vulkan), Low 30 FPS, APK `43bc53a769-dirty` (11:25): G3-A/G3-B mean
29,7/29,8 FPS, p95 33,5 ms, **p99 50,0/49,9 ms (budżet 40)**, GPU p50 30,7/30,0, p95 32,9/34,5 ms, CPU main p50 22,5/21,6,
PSS 826/829 MB, termika 0. Cel zadania: GPU p95 ≤ 26 ms (zapas 20 %) i p99 ≤ 40 ms bez widocznej utraty jakości.

## Diagnoza (pomiar na telefonie, nie edytor)
**Skąd p99.** 39 (G3-A) / 32 (G3-B) klatek > 40 ms po rozgrzewce; prawie wszystkie to dokładnie 50 ms (3 vsynci
przy 60 Hz) z GPU 30–48 ms i CPU main 17–24 ms. Świat jest załadowany w całości (bez streamingu chunków), logcat bez
zdarzeń (GC, kompilacja shaderów, ładowanie) w chwilach pików. Piki to **GPU na granicy 33,3 ms** w cięższych widokach
(początek G3-B s≈1232–1300: GPU 34–36 ms; G3-A wiadukt Bieżeństwa). Jeden krótki pakiet CPU 30–50 ms w G3-A (t≈51 s).

**DVFS.** Bez limitu klatek (fps 240) GPU p50 = 27,9 ms (z limitem 30: 30,0) — governor rozciąga GPU tylko o ~2 ms;
koszt ~28 ms jest realny.

**Rozkład GPU klatki** (G3-B Low, bez limitu, ten sam APK, `rq_ab` = przeplatane okna 4 s A/B w jednym przejeździe,
mediana z 12+12 okien; `artifacts/perf-low-r1/diag0..6/summary.txt`). Δ = o ile mniej GPU p50 bez elementu:

| element | Δ GPU p50 (ms) | uwagi |
|---|---|---|
| własna ciężarówka w kamerze głównej (warstwa Vehicle) | 4,7–5,4 | z czego: |
| — **szyba kabiny (Kamion/Truck Glass)** | **3,6–4,3** | 1 warstwa (Windscreen_LOD0 + DoorL_LOD0), ~80 % ekranu w widoku kabiny |
| — — stała barwa zamiast modelu szyby | 3,1 | raster + blend przezroczystej szyby ≈ 1,2 ms |
| — — bez filmu wycieraczek / fog+toe / env / GGX | 0,85 / 0,21 / ~0,15 / 0,06 | reszta rozłożona (Fresnel, absorpcja, faza, SH) |
| — zewnętrze ciągnika | 0,65 | |
| — wnętrze kabiny | −1,2 | bez wnętrza widać świat (drożej) |
| drzewa instancjonowane + HLOD | 2,4–3,0 | p99 50 → 33,5 ms bez drzew |
| — ściany HLOD lasu (Kamion/Vegetation `_HLOD_EDGE`) | 1,8 | depth prepass + A2C |
| — korony HLOD (URP Lit) | 0,9 | |
| — impostory | 1,6 | |
| — cienie drzew / przerzedzanie ×0,5 / karty ×0,5 | 0 / 0,3 / 0 | |
| skala renderu 0,75 → 0,65 / 0,70 / 0,6 (osobny przejazd) | 3,3 / 2,0 / 4,8 | ≈ 13 ms zależne od pikseli przy 0,75 |
| far clip 900 → 720 / 450 m | 0,7 / 1,4 | |
| LOD bias ×0,6 | 1,4 | |
| lusterka (1 render/klatkę) / LOD lusterek 0,5 jak High | 0,75–1,25 / 0,1 | |
| cienie (dystans 0) | 0,9 | |
| propsy i auta instancjonowane | 0,3 | liczba draw calli nie jest wąskim gardłem |
| HUD | 0,3 | |
| MSAA 2× → 1×, niebo/chmury/mgiełka, A8 | 0 | |

## Decyzja
1. **Szybka ścieżka szyby kabiny** `_KAMION_GLASS_FAST` (global multi_compile, `QualityProfile.glassFast`, Low i Medium
   włączone, High/Ultra pełna ścieżka; `QualityProfile.revision` 106 z migracją w `ProjectSetup`). Ten sam model co
   `frag()`, ale wyrazy zależne od kierunku patrzenia, które zmieniają się gładko na płaskiej tafli (Fresnel F1/F,
   absorpcja w szkle, faza Henyeya-Greensteina filmu), ambient SH (na zewnątrz/do góry) i transmitancja mgły liczone per
   wierzchołek (szyba LOD0 518 wierzchołków), sektory wycieraczek w half z wielomianowym atan2. Zmierzone −0,9 ms GPU p50
   (A16 Low, G3-B); kamery kontrolne Low overcast/clear i Medium clear: PSNR 62–82 dB, różnica ×10 czarna
   (`artifacts/perf-low-r1/r1/960/`). `rq_glassfast 0` przywraca pełną ścieżkę (A/B, visual-qa `-Rq`).
2. **Przełączniki diagnostyczne** (bez kosztu, gdy nieużyte): `rq_lod`, `rq_far`, `rq_mask`, `rq_props`, `rq_hud`,
   `rq_glassfast`, `rq_glassdbg`; `rq_ab` klucze `lod scale scale5 far far80 props trees truck hud glass cabint truckext
   cabdisp glassfast glassdbg hlod hlodcanopy hlodedge impostor treeshadow treethin treecard mirrorlow`
   (`ExtraViewCostMonitor`, log `[PASSAB] renderer …` z widocznością i udziałem ekranu wyłączanych rendererów).
   Haki w `WorldInstances` (statyczne flagi A/B w `RenderOverrides`; stan wysyłkowy = bez zmian).
3. **Nie zmieniono** (zmierzone, brak zysku albo widoczna utrata): MSAA, cienie drzew, karty/przerzedzanie drzew,
   LOD lusterek na Low (0,1 ms), niebo. Skala 0,70 (−2,0 ms), far 720 m (−0,7), LOD bias ×0,6 (−1,4) — widoczne
   (skala: miększe napisy bramownicy, `r1/960/low-overcast-*-scale075-vs-070-crop.jpg`) → decyzja lidera/właściciela.

## Wynik (A16, czysty APK `fd126bf3a9`, limit 30 FPS)
WYNIK_TABELA

## Otwarte (kolejne rundy, kolejność wg zysku/jakości)
1. Ściany HLOD lasu 1,8 ms: jeden przebieg z ZWrite + clip zamiast prepass + A2C dla ścian za 70 m (mało nakładek),
   albo A2C tylko na ściankach < 150 m; do pomiaru A/B i oceny migotania w ruchu (wideo z telefonu).
2. Impostory 1,6 ms: tańszy fragment (Low = najbliższy widok już jest), mniejsza tekstura; korony HLOD 0,9 ms: Lambert
   zamiast URP Lit (gładkość 0,05) — wymaga zgodności z obecną mgłą Unity (URP Lit nie używa KamionMixFog).
3. Szyba: pozostałe ~2,4 ms (z tego ~1,2 raster+blend) — rozważyć szybę tylko na ramce/pasie filmu i stałą warstwę
   pod spodem albo połączenie z wnętrzem; wymaga recenzji wizualnej (docs/06).
4. Piki p99 z widoków z dużą głębią (Andersa s 1232–1300): adaptacyjna skala Low tylko w ciężkich oknach (podłoga 0,70)
   — wymaga zgody (jakość) i odporności na DVFS przy limicie 30 FPS.
5. CPU main p95 ~29 ms przy 30 FPS (renderowanie kamery głównej ~10 ms main thread) — osobna runda.

## Konflikty przewidywane
- `QualityProfile.cs` / `QualityProfile.asset` / `ProjectSetup.cs` (GPT ADR 0098 światło): nowe pole `glassFast`,
  `CurrentRevision` 80 → 106 i blok migracji `< 106` — addytywne; przy scaleniu zachować obie migracje (0098 ma
  numer < 106, więc kolejność rewizji jest poprawna).
- `RenderOverrides.cs`, `ExtraViewCostMonitor.cs`, `QualityProfileApplier.cs` (GPT 0098): tylko dopisane pola/klucze.
- `TruckGlass.shader` (GPT 0104 kabina/lusterka, światło 0098): pełna ścieżka bez zmian merytorycznych (dopisane
  `_KamionGlassDebug == 1` na początku `frag`); każda zmiana modelu szyby musi trafić też do `FragFast`/`vert`.
- `WorldInstances.cs` (world-builder): 6 linii haków A/B.

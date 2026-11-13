# 0181 — Struktura soczewek lamp (ciągnik + naczepa) i podświetlenie tablicy rejestracyjnej

Status: kandydat (gałąź `lamplens-0181`), nie scalone. Data: 2026-11-13.

## Problem
Recenzje s18 (0178 P2, 0175 P2): każda lampa sygnałowa to jednolity prostokąt koloru z twardą krawędzią — bez komór,
optyki, punktów LED; „naklejka / prostokąt UI”. Tablica rejestracyjna naczepy o zmierzchu nieoświetlona (świeciła tylko
listwa lampki), tylna tablica ciągnika nie miała lampki wcale (R48 6.8: obowiązkowa). Tablica na Low nieczytelna
(atlas Trim 33 px/m).

## Decyzja
1. **Ramka soczewki w uv1** (kanał `Decal`, poza slotem Paint nieużywany). Eksportery (`a6_export.lens_frame`,
   `trailer_export`) zapisują dla ścian soczewek w slocie Lights:
   `uv1.x = W_mm + u'`, `uv1.y = styl·256 + H_mm + v'`, `u', v' = 0,02 + 0,96·(0..1 w poprzek soczewki)`.
   W, H — wymiar soczewki w całych milimetrach (stałe na soczewce → przeżywają interpolację i decymację LOD);
   `floor(uv1.x) = 0` (dotychczasowe 0,002) = brak soczewki. TexCoord1 nie jest w masce kompresji wierzchołków
   (`VertexChannelCompressionMask` 4054) → float32 na telefonie. Zero nowych kanałów, tekstur, materiałów i draw calli.
   Style (`shader_contract.lens_styles` w obu manifestach): 1 PILLOW (kierunkowskaz / pozycyjne / stop: siatka LED ~30 mm
   w okrągłych odbłyśnikach pod optyką poduszkową 3,5 mm), 2 FLUTE (obrysowe: rząd LED pod ryflami 2,2 mm),
   3 FRESNEL (cofania, przeciwmgłowe tylne: pierścienie 3 mm), 4 REFLEX (odblask: pryzmaty 3 mm, nigdy nie emituje),
   5 PLATE (tablica oświetlana lampką). Ściany boczne pudełka soczewki: w komorach lamp zespolonych leżą na krawędzi
   ramki (uszczelka — bez jasnej obwódki), w cienkich listwach FLUTE zostają zwykłą emisją (`lens_face`).
2. **Shader** — `KamionLampLens.hlsl` (nowy plik) + dwa bloki w `TruckExterior.shader` pod `_KAMION_TRUCK_LAMPS`
   (tylko materiał Lights). Wzór liczony w milimetrach: uszczelka / przegroda komory (3 mm), emitery, relief optyki
   (albedo + normalna → połysk nieba na poduszkach), kubki odbłyśników widoczne przy zgaszonej lampie.
   Emisja w dwóch domenach: `hdr` skaluje radiancję **przed** limiterem barwy 0178 (tło między diodami ≈ 5 % diody —
   w dzień zapalona lampa to punkty), `disp` **po** limiterze (o zmierzchu cała komora jest ponad zakresem ekranu;
   zostaje kontrast 2:1 dioda / tło). Żaden czynnik > 1 → sufit 0178 (max kanał ≤ 0,8) i barwy ECE bez zmian.
   Każdy element wzoru gaśnie do swojej średniej, gdy jest mniejszy od piksela (`fwidth` współrzędnej w mm) —
   lampa z daleka to stabilna plama, nie migotanie. Wszystkie wymiary WORKING_VALUE (generyczna lampa LED, bez
   wzoru konkretnego producenta).
3. **Tablica**: płyta tablicy tylnej (naczepa `plate_rear`, ciągnik `rear_plate`) przechodzi ze slotu Trim do Lights,
   grupa PLATE (13), styl PLATE. Emisja = albedo (z brudem) × stan lampki PLATE × `_PlateIllum` × zanik od listwy nad
   górną krawędzią (góra-środek : dolny róg ≈ 4,7 : 1). `_PlateIllum` = 0,005 (`TruckAssetBuilder.PlateIllum`): lampka
   2 000 cd/m² → ~8 cd/m² na białym polu (R4: ≥ 2,5 cd/m² — z pamięci, UNVERIFIED). Lampka naczepy poszerzona
   90 → 230 mm (listwa LED; 90 mm nie oświetli równo 520 mm). Ciągnik: nowa lampka `numlamp_body/lens` nad tablicą.
   Skutek uboczny: tablica trafia do gęstszego atlasu Lights (naczepa 662 / 331 / 166 px/m High / Medium / Low
   zamiast 132 / 66 / 33) — czytelna także na Low.
4. Materiały: `TruckAssetBuilder.ApplyLensSettings` ustawia `_LensDetail` / `_PlateIllum` przy każdej przebudowie
   (istniejący asset materiału nie przejmuje zmiany wartości domyślnej shadera).

## Koszt
Tylko piksele materiału Lights. Soczewka: 1–2 `exp`, kilka `frac` / `smoothstep`, 2× `fwidth`; brak tekstur.
Trójkąty (`check_export` PASS dla obu): ciągnik LOD0 105 356 / 140 000, LOD1 42 999 / 45 000, LOD2 17 838 / 17 900
(było 17 812; +26 = lampka tablicy); naczepa LOD0 89 000 / 90 000, LOD1 24 499 / 25 000, LOD2 7 850 / 8 000 (było 7 847;
lampka tablicy zostaje na LOD2 — `REGS_KEEP`). Gęstość atlasu Lights ciągnika 1 353 → 1 295 px/m (High; doszła tablica). Draw calle bez zmian (te same sloty). Czas GPU na telefonie: UNVERIFIED (pomiar — lider).

## Weryfikacja
- EditMode `TruckLampLensTests` (nowe, 18 przypadków): ramka soczewki poprawna na LOD0–2 obu pojazdów (styl 1–5,
  W 1–1023, H 1–255, u'/v' w 0,015–0,985; REFLEX tylko na nieemitujących odblaskach), tablice = PLATE 520 × 114 mm z
  lampką nad górną krawędzią (LOD0 i LOD2), odczyt GPU `KamionLensEval`: brak ramki = tożsamość, `hdr`/`disp` ≤ 1,
  uszczelka ciemniejsza od emitera, REFLEX nie emituje, zanik tablicy ograniczony. Razem z `TruckLampEncodingTests`
  i `TruckRegulationLampTests`: 45/45. Pełny EditMode: 552 — 549 passed, 1 skipped, 2 failed (`CarPaintMaterialTests.DepositionChannel_*`, znane z bazy: padają w świeżych worktree, HANDOVER).
- Visual QA WorldC (edytor RTX 5070, nie telefon), High i Low, `dusk` / `dusk + stop + awaryjne` / `overcast` /
  `overcast + mijania + stop + awaryjne`, kamery `lamp-trailer`, `lamp-truck` (2 m), `trailer-34`, `truck-rear34`,
  `chase`: `artifacts/lamplens-0181/{before,after}/<Tier>-<wariant>/`, zestawienia `sheet-trailer-lamps.jpg`,
  `sheet-tractor-lamps.jpg`, wycinki `view/`. Regresja przodu / boków: `after/High-dusk-regress/`.
- Obejrzane: komory rozdzielone uszczelką, widoczne odbłyśniki i punkty LED (zgaszone w dzień i zapalone), pierścienie
  Fresnela na cofania / przeciwmgłowym, pryzmaty na odblasku i trójkącie; pozycyjne vs stop różnią się poziomem tła
  między diodami *(nieprawda — patrz r2: zmierzone nierozróżnialne)*; tablica oświetlona z zanikiem od góry, czytelna także na Low (LOD2); z kamery `chase` lampy są
  stabilnymi plamami barwy (bez mory). Piksel tablicy (góra, High dusk, sRGB): 85 → 208.

## r2 — poprawki po recenzji visual-critic s20 (`docs/reports/REVIEW-2026-11-13-s20-0181.md`)
- **P1-1 aliasing:** `KamionLensFade = saturate(p/(2·fw) − 1)` (0 przy ≤ 2 px/okres, pełny wzór od 4 px), `fw = length(fwidth)`;
  krawędzie kubków i uszczelki poszerzone o `fw`; kropki LED (1,5–1,6 mm) gasną własnym fade (okres 6 mm), środek Fresnela
  gaśnie z pierścieniami; pierścienie = fala trójkątna (piłokształtna dawała morę mimo rozdzielonego okresu). Test
  `Shader_LensFade_IsZeroAtNyquist_AndFullFromFourPixelsPerPeriod`. Dowód: `after3/High-*/lamp-trailer.png` — szachownica
  i mora pierścieni znikły (High 2 m: poduszki 3,5 mm i pierścienie 3 mm wygaszone, zostają kubki i punkty LED).
- **P1-2 Low:** diagnoza — Low = LOD2 (manifest `tiers`), a decymacja collapse przesuwa wierzchołki soczewki w płaszczyźnie
  i interpoluje uv1 i uv0 (atlas rozwijany na LOD0 przed kopiami LOD) → nieafiniczna ramka (jajowate kubki) i trójkąty
  sięgające sąsiedniej komory atlasu (czerwony klin). Poprawka: `a6_export.store_lens_frame` / `fit_lens_atlas`
  (afiniczne uv0 = A·(u,v,1) na soczewce, tylko gdy residuum < 4e-4) / `refit_lens_uv1` po decymacji (oba eksportery) —
  uv1 i uv0 soczewek LOD1–2 liczone od nowa z pozycji. Dodatkowo shader: lookup atlasu przycięty do komory
  (`KamionLensInsetUV`, Jakobian uv0/q z pochodnych ekranowych, wcięcie 1,5 texela mipa). Re-eksport w toku przy STOP s20 —
  **render Low po re-eksporcie (after4) jeszcze niezrobiony**; after3 Low pokazuje stan bez refitu (artefakty zostały).
- **P1-3:** kamery `plate-trailer` (4,2 m) i `plate-truck-bobtail` (3,5 m; `VisualQaRunner` chowa naczepę dla id `*-bobtail`).
  `after3/{High,Low}-dusk/plate-*.png`: obie tablice oświetlone i czytelne, lampka ciągnika nad tablicą widoczna.
- **P2-4 klosz:** dla stylów 1–4 normalna płaska i `rough ≤ 0,08` (relief tylko w albedo), soczewka wyłączona z członu
  gloss-trim (jego przesłonięcie 0,3 czerniło cofania/przeciwmgłowe o zmierzchu), brud na kloszu = mgiełka (rough 0,4,
  nie 0,88 — twarde plamy). Ostatnie dwie zmiany nie mają jeszcze renderu (after4).
- **P2-5 pomiar** (`after3`, komora czerwona x 735–795, y 510–610, średnie R): High dusk 200 vs stop 202, Low 192 vs 193 —
  pozycyjne i stop **nierozróżnialne** o zmierzchu (limiter 0178). Zgłoszone do 0178.

## Otwarte
- **after4** (po re-eksporcie): `pwsh -NoProfile -File art-source/truck/exterior/qa/run_lamplens_0181.ps1 -Tag after4 -Tests
  -Cams 'lamp-trailer,lamp-truck,plate-trailer,plate-truck-bobtail'` + obejrzenie Low-overcast lamp-trailer i klosza High;
  ponowna recenzja visual-critic.
- Stop vs pozycyjne (P2-5) — limiter ADR 0178 spłaszcza oba do sufitu; do 0178.
- P2-6 rozlew światła tablicy na ramkę, P2-7 pomarańczowe kreski krawędzi obudowy (sprzed 0181) — nie ruszane.
- Brak profilu oświetlenia „noc” w `visual-qa` (jest clear / overcast / lowsun / dusk) — noc nieoceniona.
- Zdjęć referencyjnych lamp w `research/` nie ma; wzór oceniany z opisu typowej lampy LED — do oceny `visual-critic`.
- Lampy przednie (DRL, projektory, kierunkowskazy `led_amber`) bez zmian — osobne zadanie, jeśli recenzja uzna je za płaskie.
- Lampy nie oświetlają otoczenia (rama, błotnik) — poza zakresem (brak świateł punktowych na Low).
- Odblask REFLEX: wzór powierzchni jest, człon retroodbicia (światła pojazdu z tyłu) — nie.

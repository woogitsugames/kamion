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
Trójkąty: WYNIK_TRIS. Draw calle bez zmian (te same sloty). Czas GPU na telefonie: UNVERIFIED (pomiar — lider).

## Weryfikacja
WYNIK_WERYFIKACJA

## Otwarte
- Brak profilu oświetlenia „noc” w `visual-qa` (jest clear / overcast / lowsun / dusk) — noc nieoceniona.
- Zdjęć referencyjnych lamp w `research/` nie ma; wzór oceniany z opisu typowej lampy LED — do oceny `visual-critic`.
- Lampy przednie (DRL, projektory, kierunkowskazy `led_amber`) bez zmian — osobne zadanie, jeśli recenzja uzna je za płaskie.
- Lampy nie oświetlają otoczenia (rama, błotnik) — poza zakresem (brak świateł punktowych na Low).
- Odblask REFLEX: wzór powierzchni jest, człon retroodbicia (światła pojazdu z tyłu) — nie.

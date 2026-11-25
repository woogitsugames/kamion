# ADR 0332 — Horyzont: perspektywa powietrzna chmur i dali zamiast białego pasa mgły

Status: Proposed (agent haze-s24, gałąź `haze-s24`), 2026-11-24. Do scalenia przez lidera.
Powiązane: krytyk `artifacts/critic-s24-build5/CRITIC.md` (TOP 10 pkt 2, klatki t0950–t1020), ADR 0080 (mgła
przyziemna, KamionAtmosphere), ADR 0108 (fotograficzne chmury Clear), ADR 0113 (ForestCanopy), D68 (lato wszędzie).

## Kontekst
Krytyk build #5: „poziomy jasny pas nad polem, ostra granica pole/mgła — sztuczny gradient nieba przy ziemi”.
Pomiar na zrzutach (build #4 t1000 oraz visual-qa knyszyn-w, `artifacts/haze-s24/before/`) wskazuje dwie przyczyny:

1. **Niebo (główna).** W `Kamion/Sky` chmury fotograficzne (Clear, `clearCloudCover` 1) w dolnych ~10° były liniowo
   wygaszane do płaskiego `_SkyFogColor` (`smoothstep(0, 0.18, d.y)`), a ich krycie dodatkowo w dolnych 3,4°
   (`smoothstep(0, 0.06, d.y)`). Chmury nad pasem mają jasność z display-cap (~200–220 sRGB), kolor horyzontu jest
   fizyczny (~130–180). Wynik: bezstrukturalny gradient od bieli do szarości przez ~6–10° — „ściana mgły”, a nie
   chmury za zamgleniem. Profil pionowy (dk65-fields-nw, przed): 217 → 206 → 195 → 182 → pole.
2. **Teren (drugorzędna).** Teren kończy się na far clip kamery (PC 1500/2000/3000/4000 m, telefon 900–3500 m), gdzie
   przy V = 20 km zamglenie wynosi tylko 26–55 %. Tuż nad nim niebo poniżej horyzontu ma pełny kolor mgły (teren
   w nieskończoności) — ostra linia. Przy wysokości oka ~3 m dotyczy to tylko ostatnich pikseli, ale na Low (1500 m)
   daleka linia drzew urywała się wyraźnie.

Shader lasu HLOD na szybkiej ścieżce (`Kamion/Forest Canopy`, PC Low / telefon Low) używał unityowego `MixFog`
(bez warstwy przyziemnej ADR 0080 i bez tonu Low), więc przy Overcast las w dali był ciemniejszy niż pole za nim.

## Decyzja
1. **Chmury: perspektywa powietrzna zamiast rampy.** `cloud = lerp(_SkyFogColor, cloudY, T)`,
   `T = exp(-beta * h / sin(el))` — beta to ten sam Koschmieder z `visibilityKm`, którego używa teren
   (`_KamionHaze.x`), h = 300 m to grubość resztkowego welonu przyziemnego (`WORKING_VALUE`). Zdjęcie HDRI zawiera już
   zamglenie dnia, w którym je zrobiono, więc dodawany jest tylko resztkowy welon; 150 m dawało płaski biały bank
   przy horyzoncie (A/B `after150` vs `after300`). Krycie chmur gaśnie tylko w ostatnich ~0,7° (`smoothstep(0, 0.012)`)
   — ukrywa przedłużony wiersz źródła (`clearCloudSourceMinElevationDeg`). Clear V 20 km: T(2°) ≈ 0,19, T(5°) ≈ 0,51,
   T(10°) ≈ 0,71, T(90°) ≈ 0,94. Ten sam kolor docelowy co mgła terenu: jeden system dla ziemi i nieba.
2. **Teren przy far clip.** `KamionFogTau` dodaje do głębokości optycznej `4 · smoothstep` w ostatnich 25 % far clip
   kamery głównej (`_KamionFarFade` z `WorldAtmosphere.FarFade(tier.cameraFarClip)`; 0 = wyłączone). To zastępuje
   3–20 km lądu za płaszczyzną odcięcia: teren na far clip ma 98 % koloru horyzontu. Udział 25 % — `WORKING_VALUE`.
3. **ForestCanopy:** `KamionFogTau` + `KamionMixFog` zamiast `ComputeFogFactor` / `MixFog` (ta sama mgła wysokościowa
   i ton co teren, nadal per wierzchołek, `multi_compile_fog` usunięte — mniej wariantów).

Overcast (deck z szumu, `_KamionCloud.w`) bez zmian — jego zanik przy horyzoncie (`1 - exp(-5 el)`) był spójny;
różnica pikseli przed/po = 0 poza ostatnimi wierszami terenu.

## Koszt
Sky: `exp` + dzielenie zamiast `smoothstep` na piksel nieba (ta sama liczba odczytów tekstur, 0 nowych przebiegów).
Teren: `saturate` + 3 mnożenia na wierzchołek. ForestCanopy: `KamionFogTau` (2× `exp`) zamiast `ComputeFogFactor`
na wierzchołek. Pomiar GPU: **UNMEASURED** (edytor nie jest dowodem; do sprawdzenia w pomiarze buildu `pc-metrics`).

## Konsekwencje i otwarte
- URP Lit (las HLOD na PC Medium+, gdzie `forestFast = false`) nadal używa mgły Unity: bez warstwy przyziemnej
  (Overcast) i bez dociągnięcia przy far clip. Propozycja dla lidera: ForestCanopy także na PC Medium+ (ten sam BRDF
  co Lit wg ADR 0113, tańszy) albo `KamionFogTau` w kopii Lit — wymaga A/B cieni (shadowDistance PC > forestHlodM).
- `kCloudVeilM` 300 m i `FarFadeShare` 0,25 to wartości robocze dobrane na kamerach knyszyn-w; do potwierdzenia
  zdjęciem referencyjnym horyzontu Podlasia latem (brak `art-source/**/refs/` horyzontu).
- Dowody: `artifacts/haze-s24/` (before / after150 / after300 / after2, arkusze `sheet-*-before-after.jpg`).

## Dopisek glass-sky-s24 (2026-11-25): aureola i „dziura” przy słońcu, biały pas t0720/t0830 (krytyk build #8 P1#4, P2)
**1. Aureola, dziura w chmurze (t2370–t3140).** Nie shader, tylko mapa `T_ClearClouds.png` (ADR 0108): generator wyzerował
krycie w 1,5° od fotografowanego słońca („dziura”), a jasne, prawie neutralne niebo okołosłoneczne nie ma nadwyżki
niebieskiego, więc matowanie zostawiło je jako półprzezroczystą „chmurę” z nasyconą luminancją G = 1 („aureola”, 28 %
pikseli w 9° półprzezroczystych). `WorldAtmosphere` obraca mapę tak, że fotografowane słońce leży na słońcu gry — defekt
jest więc zawsze przy słońcu, a widać go jadąc pod słońce (DW671 na SSW, słońce Clear 200°). Naprawa danych, bez kosztu
GPU: `tools/rendering/clear_clouds_sun_repair.py` (na oryginale z hashem ADR 0108) — wypełnienie Laplace krycia w 3° (2594
teksele, gdzie R < 0,9) i luminancji tarczy do mediany pierścienia, ostry re-matte (smoothstep 0,30–0,60 + szum kłębów
0,4–3°) otoczki w 9°, przejście do 11,5°; poza tym mapa bajt w bajt bez zmian. Półprzezroczyste w 9°: 31 % → 5 %.
Skutek uboczny: tarcza słońca Clear chowa się za krawędzią tej chmury (cienie zostają ostre — jak słońce za cienką krawędzią
cumulusa). Test: `ClearCloudsSunTests` (brak dziury w 2°, < 10 % półprzezroczystych w 9°). Nowy hash w
`ClearCloudsSource.json` (`texture_sha256`; stary w `texture_sha256_adr0108`).

**2. Skośne smugi na niebie** — to szyba (grzbiet końca pióra), patrz dopisek glass-sky-s24 w ADR 0341.

**3. Biały pas (t0720 bialystok-knyszynska, t0830 dk65-02; Szosa Knyszyńska, kurs ~W–NW).** Welon chmur blendował do
`_SkyFogColor` = **średniej po azymucie** jasności horyzontu (`SkyModel.HorizonColorExposed`). Pod słońce lokalny horyzont
jest jaśniejszy od średniej (DW671: działa), z dala od słońca ciemniejszy i bardziej niebieski — dolne części chmur kończyły
się płaskim, neutralnym pasem jaśniejszym od nieba obok. Pomiar (knyszyn-w, Clear, kurs 20° = słońce za plecami, profil
pionowy x 1000–1100, `tools/profile.py`): przed 5 wierszy po 20 px 187/189/189 → 180/182/181 sRGB, B−R 1–2 (płaski szary
pas ~5°); po: 179/185/191 → 171/176/179, B−R 9–11 (gradient nieba). Zmiana: `cloud = lerp(sky, cloudY, T)` — światło
rozproszone welonu przed chmurą to światło czystego nieba w tym samym kierunku (kopuła = in-scatter całej drogi), więc
chmura gaśnie w niebo za nią. Koszt: 0 (ten sam `lerp`, inna wartość). Sprawdzone i odrzucone: `kCloudVeilM` 150 m z nowym
celem (pas znów jaśniejszy i płaski: 188/191/193, B−R 5) — zostaje 300 m. Overcast bez zmian (różnica 0,04–0,10 poziomu).
Teren przy far clip nadal blenduje do średniej (`_KamionHazeColor`) — na ten kurs nie widać tego jako pasa nad polem w
kadrach knyszyn-w; otwarte do sprawdzenia w buildzie na Szosie Knyszyńskiej (kafel bialystok-knyszynska, `UNVERIFIED`).
Dowody: `artifacts/glass-sky-s24/` (`cmp_away_3.jpg`: przed / po / welon 150 m, `cloudtex/repair_preview.jpg`,
`crop_t02_sky_after2.jpg`).

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

# ADR 0297 — noc ciężarówki: pozycyjne jaśniej + poświata, tablica ciemniej, światło zegarów w kabinie, miękkie cienie kabiny (PC)

Status: Proposed (agent night-truck-s24, 2026-11-18). Kontekst: `docs/reports/REVIEW-2026-11-18-s24-cabin-lights-knyszyn.md`
(FAIL L1–L3, K1, K2), **decyzja właściciela 18.11 (klik): „Rozjaśnij + poświata”**, ADR 0197 (R148 / R48, limiter z odniesieniem),
ADR 0178 (limiter barwy), ADR 0192 (glare latarni), ADR 0296 (kabina D84), ADR 0108 (noc), ADR 0269 (tiery PC).
Wszystkie nowe wartości wyglądu: `WORKING_VALUE` (oceniane na renderach, brak fotometrii). Liczby z renderów: DrivingLab, 1920×1080,
High `-Pc` i Low, sRGB 0–255 (skrypty `artifacts/night-truck-s24/measure_lamps.py`, `measure_cab.py`, `measure_edge.py`).

## 1. Światła tylne (L1–L3)
Przyczyny: (a) `TailNits` 1 300 cd/m² przy wspólnym wzmocnieniu limitera (ADR 0197) = 0,052 liniowo → ~55/255;
(b) tablica (3–12 cd/m², R148 5.11.3) nie przechodzi przez żadne ograniczenie wyświetlania, więc przy ekspozycji nocnej
dochodziła do bieli (205/255), a lampy siedzą ≤ 0,8 × 1/15; (c) zero poświaty: bloom wyłączony (docs/06), emisja lamp jest
ograniczona do zakresu ekranu, więc żaden próg HDR jej nie wyłowi; Low renderuje bez post.

Decyzja:
1. `LampPhotometry.TailNits` 1 300 → **3 800 cd/m²** (zapas ADR 0197 to 4 000 = `BrakeNits / 5`); 20 000 / 3 800 = **5,26 : 1**
   (R148 4.8.11 ≥ 5 : 1, 5 % marginesu na RGBAHalf i GPU). Testy: `LampRegulationTests` (≥ 5 : 1 po limiterze, CPU + GPU),
   `tools/lamp-check` `TailNits_Adr0297_BrighterButStopStaysFiveToOne`.
2. **Tablica: ramię wyświetlania** w `TruckExterior` tylko dla pikseli tablicy (`lens.style > 4.5`), po limiterze:
   y / (1 + y / M), M = `_PlateDisplayMax` = `LampPhotometry.PlateDisplayMax` = **0,55** (ta sama funkcja co ramię DRL ADR 0115).
   Fotometria tablicy bez zmian (`_PlateIllum` 0,006, min. okręgu 2,91 cd/m² ≥ 2,5 — test ADR 0197). To mapowanie wyświetlania,
   jak limiter lamp, nie zmiana luminancji. Gradient od lampki zostaje (góra jaśniej), czytelność bez zmian.
3. **Poświata = glare optyczny wokół lamp** (`Kamion/Truck Lamp Halo`, `TruckLampHaloBuilder`): model ADR 0192 (Stiles-Holladay,
   L = K·E/φ², E = L_lampy · A_emitera · cos θ / d² luksów na kamerze, × ekspozycja), rdzeń spłaszczony w promieniu kątowym emitera
   (φ² + φ_c²), zanik do 0 przy 2°, sufit 0,5 na kanał. Jeden quad na klaster emiterów grup czerwonych tylnych (6 TAIL_BRAKE,
   10 MARKER_REAR, 14 FOG_REAR, 16 TAIL, 17 STOP) z LOD0 (uv2 'Data'), budowany w `TruckAssetBuilder` / `TrailerAssetBuilder`
   (ciągnik 5 quadów, naczepa 10), stan z globalnej tekstury `TruckLights` — **zero komponentów runtime, 1 draw na część pojazdu**.
   Strona świecenia = na zewnątrz od środka siatki (eksport ma niespójny nawój soczewek: 9/10 klastrów naczepy sumowało się do +Z,
   w after2 halo było tylko po lewej). K = 0,25 (latarnie 0,4). Wyłączone w kostce odbić (`_KamionSkyCapOff`) i od przodu (cos θ ≤ 0).
   Pierwsza wersja z wyciętym rdzeniem dawała ciemny pierścień między kloszem a poświatą („tarcza”) — odrzucona po renderze.

Wyniki (High noc; Low w nawiasie), przed → po:
| element | przed | po |
|---|---|---|
| pozycyjne ciągnika (maska komory) | 54,7 R (51,3) | AFTER3_TAIL |
| stop ciągnika | 192,9 R | AFTER3_STOP |
| stop : pozycyjne (liniowo, ekran) | 14,1 | AFTER3_RATIO |
| tablica naczepy (średnia / max) | 205 / 254 (182 / 236) | AFTER3_PLATE |
| obudowa 4–24 px wokół stopu, z bliska (lamp-truck) | 9,2 R (bez zmiany przy stopie) | AFTER3_RING |
Przepalenia (> 250): bez zmian (≤ 0,02 % kadru).

## 2. Kabina nocą (K1)
Przyczyny (zmierzone A/B): (a) **lokalne podbicie cieni** kabiny (`_CabShadowLift`, k = 8 z tieru, ADR 0044 r4 „telefon”) działało
także nocą i wyciągało całą czarną kabinę do ~12/255 — poziomu nieba; (b) **jednolity `panelGlow` 0,07** × albedo: jasna szara
tapicerka słupka A (albedo ~0,4) wychodziła ponad czarną deskę bez żadnego źródła w pobliżu (17,7 vs 12,4).

Decyzja:
1. Podbicie cieni wygasa ze zmierzchem jak wzmocnienie widoku (D84): × `NightLiftScale(night, nightShadowLift)`, **0,3** nocą.
2. `panelGlow` 0,07 → **0,015** (tylko podłoga światła kabiny).
3. **Światło zegarów i nawigacji**: `CabInteriorLighting.spillSources` (2 emitery Lambertowskie z quadów `DISPLAY_Cluster` /
   `DISPLAY_Infotainment` LOD0: środek, normalna ku oczom, pole 328 / 304 cm², średnia luminancja liniowa tekstury 0,023 / 0,596),
   w shaderze `CabInstrumentSpill`: E = L·A·cos_s·cos_r / (d² + A/π), po podbiciu cieni, × albedo/π × AO. L = wyświetlana wartość
   ekranu min(500 cd/m² × ekspozycja, 0,9) — bez podłogi czytelności, więc w dzień ~0, nocą = poziom ekranu (przyciemniony
   wyświetlacz). Fizycznie (skala 1) A/B dał najwyżej +7/255 (czarne tworzywa ~0,05, powierzchnie deski współpłaszczyznowe
   z ekranami nie dostają światła z definicji) → `spillScale` **4** (WORKING_VALUE: brakujące źródła — pierścienie zegarów,
   legendy, wielokrotne odbicia w osłonie zegarów, odbicie w szybie). Bez cieni od ekranów (koszt), dwa globalne wektory.
   Przełączniki: `instrumentSpill`, `rq_cabspill=0`.

Wyniki `cab-driver` High noc (Low), przed → po: AFTER3_CABTABLE

## 3. Schodkowe cienie słońca w kabinie (K2, znane od s23 P1-1)
Przyczyna: `CabInterior.shader` **nie miał wariantów `_SHADOWS_SOFT`** (decyzja A7: na S24+ miękkie cienie kabiny kosztowały
~3 ms GPU) — kabina brała twardą 1-próbkową mapę cieni niezależnie od tieru, więc ani 1. kaskada 3 m (ADR 0269), ani Soft High
PC nie miały wpływu. Kaskady, rozdzielczość (4096/8192), bias 0,6/0,6 — bez zmian (nie były przyczyną).

Decyzja: warianty `_SHADOWS_SOFT*` w przebiegu forward kabiny (zestaw jak `TruckExterior`) + gałąź jednorodna
`_KamionCabSoftShadow` (CabInteriorLighting: `pcSoftShadows && PcGraphicsTiers.Enabled`, A/B `rq_cabsoft`): na PC filtr URP z assetu
tieru (High/Ultra: Soft High, Medium: Soft Low, Low: brak — twarde), na telefonach twarda próbka A7 (`CabHardShadow`) — koszt
mobilny bez zmian. Wynik: krawędź cienia słupka na desce `cab-hub` clear: szerokość przejścia 10–90 % (mediana) AFTER3_EDGE;
schodki niewidoczne (`artifacts/night-truck-s24/view/hub-*`).

## Koszt
- Draws: halo +1 na ciągnik, +1 na naczepę (addytywny quad, bez cieni, bez sond). AFTER3_DRAWS
- GPU (edytor, GTX 1070, `-TimeFrames 120`, A/B naprzemiennie ×2): AFTER3_TIME. **Czas w buildzie: UNVERIFIED** (lider: `pc-metrics.ps1`).
- Shader kabiny: +2 źródła × ~15 ALU (spill) dla pikseli kabiny; warianty kabiny ×4 (miękkie cienie) — rozmiar buildu UNVERIFIED.
- Pamięć: 2 siatki halo (40 + 20 wierzchołków), 1 materiał.

## Odrzucone
- URP Bloom: wyłączony z założenia (docs/06), lampy ograniczone do zakresu ekranu, Low bez post.
- Obniżenie `_PlateIllum` poniżej 0,00515: łamie R148 5.11.3 (min 2,5 cd/m²) — test.
- Podniesienie sufitu limitera dla czerwieni: stop w clipie 1,0 przy pozycyjnych ≤ 0,2 — niepotrzebne po halo nad kloszem.
- Lokalne światła Unity (point) dla lamp / zegarów: limit świateł na obiekt (4/8), koszt forward, brak cieni i tak.
- Zmiana kaskad / rozdzielczości cieni: przyczyną był brak wariantów miękkich w shaderze kabiny.

## Otwarte
- Zrzuty z playera Windows w tych kadrach (docs/06 §5 pkt 2) i czas GPU w buildzie — lider.
- Halo kierunkowskazów / cofania / przednich lamp (te same mechanizmy, poza zakresem decyzji właściciela).
- Pasma (banding) nieba nocą w kabinie (pierścienie w 8 bitach) — zauważone, poza zakresem.
- Referencje nocne (Commons, CC BY / BY-SA, poza gitem): `Data/raw/refs/night-truck-s24/` + `LICENSES.txt`; najbliższa: tył
  furgonu nocą (ref5) — lampy najjaśniejsze i nasycone z małą poświatą, tablica ciemniejsza od lamp.

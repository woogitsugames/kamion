# 0197 — Światła tylne ciągnika i naczepy wobec R148 / R48: stop : pozycyjne po limiterze, komory naczepy, bursztyn, tablica

Status: PROPOSED (gałąź `lights-0197`, nie scalone). Data: 2026-11-15. Autor: agent lights-0197 (chmura, bez Unity, bez Blendera).

## Źródła
- R148 (Dz.U. UE L 347 z 30.9.2021, s. 123) i R48 seria 07 (tamże, s. 1); cytaty w paczce
  `origin/research/mistral-p16-truck-lamps:research/mistral/p16-truck-lamps/manifest.csv`, wiersze P16-035 (pkt 4.8.11),
  P16-090/092/094 (pkt 5.11.2–5.11.3), P16-111 (R48 §2.11.1.3), P16-112 (§2.11.1.4). Weryfikacja cytatów z Dz.U.:
  `docs/reports/REVIEW-2026-11-14-s20-mistral-m59.md` §3 („zgodne z tekstem”), wnioski dla gry §5 G1–G4.
- Stan gry: ADR 0178 (limiter barwy), ADR 0181 (soczewki, tablica; pomiar r2 P2-5: pozycyjne 201 vs stop 202 sRGB).

## Problem
1. **Stop : pozycyjne ≈ 1 : 1 o zmierzchu.** R148 pkt 4.8.11: przy sprzężeniu (stop + pozycyjne) : pozycyjne „co najmniej
   5: 1” w polu ±5° V / ±10° H (P16-035, SOURCED). Nity gry 20 000 / 1 300 = 15,4 : 1, ale limiter 0178 liczy skalę
   z własnego max kanału piksela, więc oba stany dochodzą do sufitu 0,8 (CPU: 1,015 : 1 przy E = 1e-2; render 201 vs 202).
2. **Naczepa: grupa TAIL_BRAKE na obu komorach** (`trailer_export.light_group`: `_tail_` i `_stop_`). Przy pozycyjnych
   świeciła także komora stop, przy hamowaniu obie skakały do stopu.
3. **Bursztyn (1; 0,28; 0) poza R48** — x 0,524, y 0,422 przekracza granicę zieleni y ≤ x − 0,120 (0,404). Pasmo
   0,398 ≤ y ≤ 0,429 z ADR 0178 pochodzi z ADR 49/00 (Australia), nie z R48.
4. **Tablica:** „≥ 2,5 cd/m² — z pamięci, UNVERIFIED” (ADR 0181). Teraz SOURCED: R148 pkt 5.11.3 lit. a, 2,5 cd/m² dla
   kat. 1a/1b/1c/2a/2b w każdym punkcie pomiarowym (P16-090); punkt = okrąg 25 mm, luminancja korygowana do
   współczynnika odbicia 1,0 (pkt 5.11.2, P16-094); gradient ≤ 2 × B₀/cm (P16-092).

## Decyzja
1. **Limiter z poziomem odniesienia.** `TruckLampHueLimitRef(radiance, refMax, knee, ceiling)`: wspólna skala RGB liczona
   w r = max(refMax, m) zamiast m. refMax = naświetlony max kanał najjaśniejszego stanu grupy (alfa teksela stanu;
   `TruckLampHueLimit` = przypadek refMax = 0, ADR 0178 bez zmian). Wszystkie stany grupy dzielą jedno wzmocnienie, więc
   zachowują liniowy stosunek; max kanał nadal ≤ sufit (m ≤ r). Odniesienie = `BrakeNits` (20 000 cd/m²) dla czerwonych
   tylnych sygnałów: TAIL_BRAKE (6), MARKER_REAR (10), TAIL (16), STOP (17). Pozostałe grupy: 0 (bez zmian).
   MARKER_REAR w tej samej skali, bo R148 tab. 4 daje obrysowym tylnym te same granice co pozycyjnym (R1/RM1 4 / 17 cd;
   recenzja M59 §3) — inaczej obrysówki zostałyby przy 0,8, a pozycyjne przy 0,05.
2. **Naczepa: osobne grupy komór.** `a6_export.LIGHT_GROUPS` += `TAIL` (16), `STOP` (17); `trailer_export.light_group`:
   `_tail_` → TAIL, `_stop_` → STOP. `TruckLights`: TAIL = pozycyjne (z mijania), STOP = 0 / `BrakeNits`, TAIL_BRAKE ciągnika
   bez zmian. Tekstura stanu 16 → **32 × 1** (`LampPhotometry.StateTexels`, `#define KAMION_LAMP_TEXELS 32.0`);
   +16 × 8 B RGBAHalf, nadal jedno `SetPixels` przy zmianie stanu.
3. **Barwy.** Oba obszary R48 (czerwony i bursztynowy) leżą **poza gamutem sRGB** (sprawdzone siatką 41³ i krawędzią
   (1, g, 0), test). Recenzja M59 G3 („czworokąt A1–A4 zawiera (1, g, 0) dla g ≈ 0,16–0,245”) pominęła granicę bieli
   y ≥ 0,790 − 0,670 x: dla x = 0,542 wymaga y ≥ 0,427, a krawędź R–G sRGB ma tam y 0,408. Wybór najbliższego punktu:
   - **Bursztyn (1; 0,22; 0)**: x 0,5417, y 0,4081; spełnia granicę zieleni (zapas 0,0136 w y) i czerwieni (0,0181);
     odległość od obszaru 0,0159 xy. Najbliższy punkt krawędzi to g = 0,240 (0,0153), ale ma tylko 0,0025 zapasu (w y) do
     granicy zieleni — 0,22 kosztuje +0,0006 xy i daje 5× większy zapas. Test: odległość ≤ minimum + 0,001.
   - **Czerwień (1; 0; 0)** bez zmian: x 0,640, y 0,330 (granica żółci y ≤ 0,335 spełniona); x + y = 0,970, granica
     purpury x + y ≥ 0,980 nieosiągalna (maksimum x + y w sRGB = 0,970 w prymarnej czerwonej).
   - Podgląd i manifest eksportu (`a6_export.LIGHT_COLOUR`) = te same wartości (było (1; 0,42; 0,02) i (1; 0,03; 0,01)).
4. **Tablica:** `_PlateIllum` 0,005 → **0,006** (WORKING_VALUE; `TruckAssetBuilder.PlateIllum` = `LampPhotometry.PlateIllum`,
   domyślna w shaderze). Rozkład z `KamionLampLens.hlsl` bez zmian (listwa 0,22 W od środka, 15 mm nad krawędzią,
   1 / (1 + d²/100²)). Położenia punktów z rys. A3-X nie są odczytane (UNVERIFIED), więc test jest **nadzbiorem**: minimum
   średniej po każdym możliwym okręgu 25 mm (środki ≥ 12,5 mm od krawędzi). Wynik przy ρ = 1:
   | tablica | min okręgu (0,005 → 0,006) | góra-środek | max gradient | 2·B₀ |
   |---|---|---|---|---|
   | 520 × 114 (PL, gra) | 2,42 → **2,91** cd/m² | 11,74 cd/m² | 0,78 cd/m²/cm | 5,82 |
   | 520 × 120 (kat. 1b) | 2,34 → **2,81** cd/m² | 11,74 cd/m² | 0,78 cd/m²/cm | 5,62 |
5. **Liczby jako czysty C#.** `game/Assets/_Project/Vehicle/Runtime/LampPhotometry.cs` (asmdef `Game.Vehicle.Runtime`,
   tylko `System`, bez typów Unity): nity, id grup, limiter + odniesienie, sRGB → XYZ (IEC 61966-2-1) → xy, obszary R48,
   luminancja tablicy. `TruckLights` i `TruckAssetBuilder` biorą stałe stąd; testy porównują wartości domyślne shadera
   i stałe rozkładu tablicy z tekstem `.shader` / `.hlsl` (wykrycie rozjazdu HLSL ↔ C#). asmdef bez zmian.

## Skutki dla obrazu (CPU, `LampPhotometry`; ekspozycja zmierzchu E ≈ 1e-3–1e-2 ESTIMATED z ADR 0178 „10–100× ponad zakres”)
| E | pozycyjne (lin. / sRGB 8 bit) | stop | obrysowe tylne | stosunek | pozycyjne przed 0197 |
|---|---|---|---|---|---|
| 1e-4 | 0,047 / 61 | 0,720 / 221 | 0,072 / 76 | 15,4 | 0,130 |
| 1e-3 | 0,052 / 64 | 0,792 / 230 | 0,079 / 80 | 15,4 | 0,677 |
| 1e-2 | 0,052 / 64 | 0,799 / 231 | 0,080 / 80 | 15,4 | 0,788 |
- Pozycyjne o zmierzchu ~64/255 (wcześniej ~201): ciemniejsze, ale wyraźnie czerwone; stop 230/255. Jeśli wizualnie za
  ciemne: podnieść `TailNits` maks. do `BrakeNits / 5` = 4 000 cd/m² (test pilnuje ≥ 5 : 1) — decyzja po renderze.
- Dzień: skala zmienia się tylko, gdy `BrakeNits · E` > kolano 0,4 (E > 2e-5); poniżej tożsamość jak w 0178. Wartość E w
  słońcu nie jest tu zmierzona — sprawdzić render overcast/dzień (pozycyjne mogą lekko ściemnieć, stosunek do stopu fizyczny).
- Koszt shadera: +1 `max`, +1 próbka kanału alfa z tej samej tekstury (to samo `SAMPLE`), +1 mnożenie. Bez nowych tekstur,
  wariantów, przebiegów, draw calli. Czas GPU na telefonie: UNVERIFIED (lider).

## Weryfikacja
- `dotnet test tools/lamp-check` (xunit, net8.0, linkuje ten sam `LampPhotometry.cs`): **185/185 passed** (chmura, 2026-11-15):
  stosunek ≥ 5 dla 57 ekspozycji 1e-7…1 × hdr {1; 0,05}, komory naczepy, sufit i tożsamość pod kolanem dla wszystkich
  grup, narożniki R48 leżą na swoich granicach, obszary poza sRGB, bursztyn/czerwień, tablica 520 × 114/120, zgodność
  z shaderem/hlsl, podział grup w eksporterach.
- EditMode (NIE uruchomione — brak Unity w chmurze): `LampRegulationTests` (CPU + odczyt GPU `TruckLampHueLimitRef`
  i pełnej ścieżki dekodowania tekstury stanu z alfą), `TruckRegulationLampTests.Trailer_TailAndStopChambers_HaveSeparateLightGroups`
  (LOD0, LOD2; **przejdzie dopiero po ponownym eksporcie FBX naczepy z Blendera**), poprawione `TruckLampEncodingTests`
  (szerokość 32, `SignalColoursMeetTheReachableR48Limits` zamiast pasma ADR 49/00).
- Visual QA (lider): kamery `lamp-trailer`, `lamp-truck`, `plate-trailer`, `plate-truck-bobtail`, `truck-rear34`,
  `trailer-34`; dusk / dusk + stop / overcast; Low i High; pomiar ROI z 0181 r2 P2-5 (oczekiwane: pozycyjne ~64, stop ~230).

## Otwarte
- Eksport FBX naczepy (Blender, `trailer_export.py`) i manifestów — bez tego naczepa ma nadal TAIL_BRAKE na obu komorach
  (sam limiter już daje 15 : 1, ale komora stop świeci przy pozycyjnych). Ciągnik nie wymaga eksportu dla działania gry;
  manifest ciągnika dostanie nazwy 16/17 i nowe kolory podglądu przy najbliższym eksporcie.
- Punkty pomiarowe rys. A3-X (R148 zał. 3) nieodczytane — test konserwatywny; emisja listwy lampki do tyłu (pkt 5.11.5,
  recenzja G4) nie sprawdzona.
- Wymiary lampy zespolonej naczepy 520 × 170 mm vs karty 390–450 × 138–153 mm (G5) — poza zakresem.

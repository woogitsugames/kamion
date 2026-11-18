# ADR 0299 — noc: banding nieba, tryb nocny ekranów kabiny, poświata kierunkowskazów i cofania, zrzuty z playera

Status: Proposed (agent night-polish-s24, 2026-11-19). Kontynuacja ADR 0297 (sekcja „Otwarte”), ADR 0108 (dither High),
ADR 0199 (noc), ADR 0284 (noc PC), ADR 0283 (ekrany/HUD). Nowe wartości wyglądu: `WORKING_VALUE` (oceniane na renderach).
Liczby z renderów DrivingLab 1920×1080 (sRGB 0–255, PNG, nie JPEG); skrypty `artifacts/night-polish-s24/measure_band.py`,
`np_probe.py`, `prof.py`.

## 1. Banding nieba nocą

Pomiar (`measure_band.py`, okno nieba `cab-driver` 600–1400 × 0–300): `runlen` = średnia długość serii jednego poziomu
8-bit (gradient z ditherem 1–3 px, pasma ≫ 10 px), kroki po wygładzeniu 16 × 9 px (`steps.py`).
Trzy przyczyny, rozdzielone A/B (`-qaRq`, `-qaLdrTarget`):
1. **Kamery QA renderowały tiery HDR przez 8-bitowy bufor sceny.** URP bierze format bufora pośredniego kamery z jej
   `targetTexture`, a `VisualQaRunner` dawał ARGB32 — kwantyzacja sRGB przed post i ditherem, której player (ekran,
   R11G11B10) nie ma. Dowód: z ditherem kroki po wygładzeniu nadal 0,9 LSB (plateau 8,73 na 100 px). Poprawka: dla
   `allowHDR` cel ARGBHalf (linear) + blit do sRGB przy odczycie; `-qaLdrTarget 1` = stare zachowanie. Dzień bez zmian
   (High clear średnia 91,6/97,5/101,2 → 91,4/97,6/101,4).
2. **PC High bez żadnego ditheru.** ADR 0108 wyłączył końcowy dither URP dla High przez FSR/RCAS telefonu, a nakładka PC
   (ADR 0269) też nazywa się „High”, ale nie ma FSR (upscaler Auto, skala 1). Teraz `QualityProfileApplier.FinalDither`:
   wyjątek tylko dla High z FSR (telefon bez zmian).
3. **Dither URP z szybką konwersją sRGB zgniatał cienie.** `ApplyDithering` robi
   `GetSRGBToLinear(GetLinearToSRGB(c) + n)`; przy `useFastSRGBLinearConversion` aproksymacje nie są wzajemnie odwrotne:
   liniowe 0,0037 → 0,0021 (sRGB 12 → 7). Dlatego Medium/Ultra/PcLow (z ditherem) miały noc ~5 poziomów ciemniejszą od
   High (ADR 0297: niebo High 12,0 vs Low 7,1 — część tej różnicy) i to samo spotkałoby High po włączeniu ditheru.
   Poprawka: `m_UseFastSRGBLinearConversion: 0` we **wszystkich 9** assetach URP (5 telefonowych + 4 PC; tylko lista
   telefonowa jest w QualitySettings, więc mieszane ustawienie wycięłoby wariant bez słowa kluczowego ze strippingu
   playera), `PcTierAssetsSetup` ustawia i sprawdza (`Diff`), test `UrpAssets_NoFastSrgbConversion_…`.
Odrzucone po pomiarze: dither kroku R11G11B10 w `Sky.shader` (A/B `rq_skyqdither`: runlen 1,9 vs 1,9, hpRMS 0,50 vs 0,50 —
bez efektu, usunięty).

Wyniki noc, `cab-driver` (przed = `base`, po = `qa3`, ten sam kadr):
| tier | runlen przed → po | średnia nieba przed → po | hpRMS po |
|---|---|---|---|
| High -Pc | **115,3 → 2,0 px** | 12,0 → 11,7 | 0,50 LSB |
| Ultra -Pc | 4,6 → 3,5 px (pasma widoczne mimo ditheru, przyczyna 1) | 7,0 → **11,7** | 0,35 |
| Medium -Pc / Low -Pc | — → 2,0 px | (zgniecione ~6,9, `after1`) → 11,7 | 0,50 |
| Low telefon (bez post) | 8,8 → 8,8 px | 7,1 → 7,1 (bez zmian: dither w shaderze nieba, inna krzywa tonu) | 0,29 |
Dzień High clear: p5 kadru 24,7 (bez ditheru) / 21,7 (dither + szybka konwersja) / **24,7** (po); niebo dzienne
hpRMS 2,75 → 2,77 (tekstura chmur, nie szum). Kabina nocą bez zmian względem ADR 0297 (deska 6,1, słupek 7,3, wieniec
7,2, droga 8,2). Widok: `view/band-sky-x8-High-Ultra-before-after.jpg` (×8 kontrastu; góra High przed/po, dół Ultra).
Telefony: Medium/Ultra telefonu też dostają dokładną konwersję (koszt: 2 × pow na piksel w post — **UNVERIFIED** na Mali/Adreno, telefon odroczony D73).

## 2. Ekran nawigacji nocą

Przyczyna: ekran „Brak mapy” miał tło `NavNight.Bg` (26,28,32) i biały tekst przy suficie wyświetlania 0,9 także nocą —
w nocnej kabinie (deska 6/255) był najjaśniejszą płaszczyzną: tło 31, tekst 197. Prawdziwe ekrany przechodzą w tryb
nocny czujnikiem światła i ściemniają podświetlenie.
Decyzja:
1. `CabDisplayNight` (Game.Rendering): globalny `_KamionCabDisplayNight` 0..1 z czujnika (`CabDisplayState.Night`, ten sam
   próg co automatyczne mijania), przejście 3 s (`FadeSeconds`, WORKING_VALUE), w kadrze QA bez przejścia.
2. `Kamion/Cab Display`: sufit `lerp(_MaxDisplay, min(_MaxDisplay, _NightMaxDisplay), noc)`, podłoga czytelności nigdy
   ponad sufit. `_NightMaxDisplay`: nawigacja **0,3**, radio/tachograf/panel koi 0,45, zegary 0,9 (już ściemniane paletą
   `ClusterNight`) — `TruckAssetBuilder.NightMaxDisplay`, WORKING_VALUE.
3. Brak mapy: tło = kolor paska (14,15,17), tekst `BarText`.
4. Światło ekranów (ADR 0297 spill) idzie za trybem nocnym: sufit nocny + **średnia żywego obrazu** nawigacji
   (`NavLayout.MapMean` / `Lum(Bar)`) zamiast średniej dziennej tekstury A6 (0,596), której ADR 0297 używał także nocą.
Wyniki High noc (`cab-dash`, okno 1400–1600 × 800–880): tło 31 → **11**, tekst max 197 → **117**; zmierzch 31 → 10; dzień
(brak mapy) 16 / tekst 137. Kadr kabiny: średnia 9,7 → 9,5. Widok `view/nav-night-before-after.jpg`. Bez marek.

## 3. Poświata kierunkowskazów i świateł cofania; poświata stopu z 4 m

Decyzja: ten sam model `Kamion/Truck Lamp Halo` (ADR 0297, bez nowego shadera i bez komponentów), `TruckLampHaloBuilder.HaloGroups`
+ IndL / IndR (4 / 5) i Reverse (7). Kolor = texel stanu lampy z `TruckLights` (Amber (1, 0,22, 0) R48 2.11.1.3 jak ADR 0197,
White, Red), więc poświata ma kolor regulaminowy swojej lampy i miga razem z przerywaczem. Strona świecenia z regulaminu,
nie z nawoju eksportu (`EmittingSide`): czerwone i cofania — do tyłu; kierunkowskazy — boczny powtarzacz (oś soczewki
głównie w X) na zewnątrz od osi pojazdu, przedni / tylny wg połowy rozpiętości kierunkowskazów części (R48 6.5.3).
Quady: ciągnik 5 → **13** (przednie i boczne na `CAB_Body`, tylne + cofania na ramie), naczepa 10 → **14** (2 kierunkowskazy,
2 cofania) — log `[LAMP_HALO]`; nadal 1 draw na część pojazdu.
Stop / kierunkowskaz z 4 m (`plate-trailer`): przy K 0,25 pierścień poświaty miał szerokość lampy po każdej stronie, a
pomarańczowy klosz wybielał do (255,170,107) — „rozmyta plama”; referencje nocne (`Data/raw/refs/night-truck-s24/` ref4, ref5:
nasycone lampy, ciasna poświata przy przepalonym kloszu) → **`_HaloK` 0,25 → 0,15** (WORKING_VALUE). Profil poziomy przez
prawe lampy naczepy (High noc, pozycyjne + stop + awaryjne), K 0,25 → 0,15: 24 px przed kloszem stopu R 122 → 98, 12 px
63 → 51; klosz kierunkowskazu (255,170,107) → **(255,146,66)** (bursztyn zamiast bieli), 24 px za nim 145 → 117; tło 8.
Z dystansu (`plate-truck-bobtail`) i o zmierzchu poświata prawie znika (E ∝ 1/d², ekspozycja). Cofanie: biała poświata
do sufitu 0,5 z 4 m — silna, jak oślepienie światłem cofania nocą; bez zmiany sufitu. QA: `-qaTruckLamps reverse`
(`TruckLights.forceReverse`, tylko QA). Widok: `view/halo-plate-trailer-K025-K015-reverse-lamptruck.jpg`
(K 0,25 | K 0,15 | cofanie | ciągnik z bliska), `view/halo-bobtail-night-dusk.jpg`.

## 4. Zrzuty z playera i koszt (pc-metrics)

__PLAYER__

## Weryfikacja

__VERIFY__

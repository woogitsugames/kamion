# ADR 0280 — Pierścień skrętu 12,50/5,30 m (96/53/WE): metryka obwiedni w runnerze, propozycja rozstawu sworzeń–tridem 7,60 m

Status: **Proposed** (agent P10, gałąź `turning-circle-s23`, 2026-11-16). Zmiana danych gry = decyzja lidera/właściciela (§5).
Dotyczy: ADR 0004 (rdzeń fizyki kompilowany z `game/` przez `tools/physics-runner/Sim`), 0019 (siodło 0,68 m, długość 16,47 m),
0158/0165 (kontakt nadwozia), 0201/0201b (naciski osi), raport `docs/reports/PHYSICS-VALIDATION-2026-11-16.md` §3 i §6 pkt 5,
`docs/04` §6.5/§6.7, `docs/VEHICLE_REFERENCE_DATA.md` (VRD), R3-004 (`research/cloud2/truck-parameters/manifest.csv`).

## 1. Kontekst

Walidacja s23 (P7) pokazała jedyny niezielony wynik: zestaw w pierścieniu 12,50/5,30 m potrzebuje 7,235 m szerokości przy 7,20 m.
Pomiar był ad hoc (numpy na CSV, scenariusz poza repo), bo runner nie miał metryki obwiedni.

**Przepis (sprawdzony u źródła 2026-11-16).** Dyrektywa Rady 96/53/WE, tekst skonsolidowany **CELEX 01996L0053-20190814**,
**załącznik I pkt 1.5** (oznaczenie ►B, czyli tekst pierwotny):
> „Każdy pojazd silnikowy lub zestaw pojazdów, które są w dopuszczone do ruchu, muszą być zdolne do wykonania zakrętu w okręgu
> o promieniu zewnętrznym 12,50 m oraz promieniu wewnętrznym 5,30 m” (PL)
> „Any motor vehicle or vehicle combination which is in motion must be able to turn within a swept circle having an outer radius
> of 12,50 m and an inner radius of 5,30 m” (EN)

Źródło: `https://publications.europa.eu/resource/celex/01996L0053-20190814` (strona EUR-Lex zwraca 202 bez treści dla klienta
bez przeglądarki; ten sam dokument z repozytorium Urzędu Publikacji, cellar `1c5d9587-e9b8-11e9-9c4e-01aa75ed71a1`).
SHA256 pobranych plików XHTML: PL `3dae6422…f46e69c`, EN `437dc827…5f31063`. Pkt **1.5a** (►M1, dyrektywa 2002/7/WE) z
wychyleniem ≤ 0,60 m przy wjeździe stycznym jest zatytułowany „Wymagania dodatkowe dla autobusów” — **nie dotyczy** zestawu
ciągnik + naczepa. Pkt 1.6: sworzeń → tył naczepy ≤ 12,00 m, pkt 4.4: sworzeń → dowolny punkt przodu ≤ 2,04 m.

Przepisy homologacyjne (tylko kontekst, nie kryterium tego ADR):
- Rozporządzenie wykonawcze Komisji (UE) **2021/535**, CELEX 32021R0535, zał. XIII cz. 2 sekcja D pkt 7.1–7.3 (N2/N3:
  „the outermost front point of the motor vehicle shall be guided along the contour of the outer circle”) i sekcja E pkt 3.1–3.3
  (kategoria O: zestaw w pierścieniu 12,50/5,30 m; naczepę „uznaje się za spełniającą” pkt 3.1, gdy jej rozstaw odniesienia
  RWB, czyli odległość od osi sworznia do linii środkowej osi nieskrętnych, spełnia wzór). Ten sam tekst jest w rozporządzeniu
  (UE) 1230/2012 zał. I część D pkt 3.2.
- **Wzór RWB jest w obu dziennikach obrazem.** Odczytany z obrazu brzmi: `RWB ≤ [(12,50 − 2,04)² − (5,30 + W)²]`, bez
  widocznego pierwiastka i z pełnym W („W is the semi-trailer's width”). Wymiarowo to musi być pierwiastek. Odczyt geometryczny
  (√, ½W) daje RWB ≤ 8,135 m, a z pełnym W 6,913 m. Status: **UNVERIFIED**, nie używam tego wzoru jako kryterium. Naczepa gry
  (RWB 7,70 m) spełnia odczyt geometryczny. Ten odczyt zakłada jednak, że sworzeń jedzie po promieniu 10,46 m, a ciągnik gry
  przy zderzaku na 12,50 m prowadzi sworzeń po ok. 10,21 m (§3). Dlatego zestaw nie mieści się, choć oba pojazdy osobno tak.

## 2. Decyzja (część narzędziowa, wykonana)

1. **Metryki obwiedni w runnerze** (`tools/physics-runner/Sim/Metrics.cs`). Plik nie jest kodem gry: `Sim.csproj` kompiluje
   z `game/` tylko `Vehicle/Physics/**` i 4 pliki `Input/`, a `Sim/*.cs` to narzędzia. Dodane metryki: `swept_outer_radius_m`
   (najdalszy narożnik), `swept_inner_radius_m` (najbliższy punkt prostokąta, dokładna odległość punkt–prostokąt),
   `swept_ring_width_m`, `swept_fit_rms_m`. Środek to okrąg dopasowany metodą Kasy do śladu osi tylnej ciągnika w oknie `from..to`.
   Obrys to `Scenario.envelope` (prostokąty ciągnika i naczepy, generator bierze je z `art-source/truck/dims.json`, bez lusterek).
   Do `Sample` doszły osie naczepy (`TrailerFwd/Right`).
2. **Nadpisania geometrii w scenariuszu** (`Scenario.overrides`): `trailerAxlePositionsZ` (wartości bezwzględne; element masy
   `tridem_axles_wheels_brakes` przesuwa się o średnie przesunięcie osi) i `fifthWheelZ`. Działają na świeżej kopii definicji
   w pamięci (`ScenarioRunner.ApplyGeometry`), więc buforowany `Defs` i pliki zostają bez zmian (test
   `GeometryOverrides_ApplyToARunCopyOnly`). Wartości są bezwzględne, więc scenariusz zostaje poprawny po przyjęciu ich w danych.
3. **Scenariusze z generatora** (`tests/physics/generate_stage2_scenarios.py`, drugi argument = katalog znanych porażek):
   - `tests/physics/scenarios_expected_fail/ring_96_53_comb.json`: obecna geometria, `expectedFailMetrics`
     `[swept_inner_radius_m, swept_ring_width_m]`. `ExpectedFailureTests` pilnuje, że padają dokładnie te metryki.
   - `tests/physics/scenarios/ring_96_53_comb_rwb760.json`: propozycja z §4 przez `overrides`. Przechodzi, sprawdza ją
     `ScenarioTests` i pełny runner.
   - Oba: kierowca `circle` 5 km/h, R osi tylnej 10,12 m (narożnik zderzaka tuż wewnątrz 12,50 m), 240 s, ocena od 120 s.
     Kontrole: zewn. ≤ 12,50 i wewn. ≥ 5,30 (**SOURCED**), szerokość ≤ 7,20 (DERIVED) albo ≤ 7,15 (cel zapasu 5 cm, WORKING),
     rms dopasowania ≤ 1 cm, prędkość 4–6 km/h, `max_dv_step`.
   - `tests/physics/test_scenario_strictness.py`: generator ma odtwarzać też katalog znanych porażek. Promienie 12,50/5,30
     i szerokość 7,20 są przypięte niezależnie od generatora (`test_ring_limits_pinned`).
4. Testy xUnit `Tests/SweptPathTests.cs`: dokładność metryk na sztywnej kinematyce z wzoru zamkniętego i z gęstego próbkowania
   (różnica < 1e-6 m), izolacja nadpisań, kierunek i wielkość wrażliwości.

## 3. Wynik PRZED / PO (runner, ta gałąź)

Artefakty (poza gitem): `artifacts/tc-s23/ring-before/` (`--scenarios tests/physics/scenarios_expected_fail --only ring_96_53_comb`),
`artifacts/tc-s23/ring-after/` (`--only ring_96_53_comb_rwb760`), przemiatania w `artifacts/tc-s23/sweep/<nazwa>/`.

| R osi tylnej 10,12 m, 5 km/h | zewn. [m] | wewn. [m] | szerokość [m] | wynik |
|---|---|---|---|---|
| **PRZED** (sworzeń–środek tridemu 7,70 m), pusty | 12,486 | **5,228** | 7,258 | FAIL (wewn. −7,2 cm) |
| PRZED, 40 t | 12,483 | 5,230 | 7,253 | FAIL (wewn. −7,0 cm) |
| **PO** (7,60 m, osie −6,29 / −7,60 / −8,91), pusty | 12,486 | **5,343** | **7,143** | PASS, zapas 1,4 cm na zewn., 4,3 cm wewn., 5,7 cm szerokości |
| PO, 40 t | 12,482 | 5,347 | 7,135 | PASS, 1,8 / 4,7 / 6,5 cm |

Ślad osi tylnej jest okręgiem (rms 1e-8–2e-4 m), przegub 46–47°. Wynik s23 z numpy odtwarza się co do milimetra
(R 10,15: 12,510 / 5,2765 / 7,234 m przy 40 t).

**Promień kierowcy zmienia szerokość.** Wynik s23 („nie zależy od wyboru promienia”) jest błędny: dW/dR = −0,64 m/m
(R 10,10 → 10,20: 7,266 → 7,202 m, 40 t), dR_zewn/dR = 0,91, dR_wewn/dR = 1,55. Rozstrzyga więc wewnętrzny promień przy
zewnętrznym równym 12,50 m. Dla obecnej geometrii wynosi on ≈ 5,252 m (pusty), czyli 4,8 cm za mało.
Przyczyna: efektywny rozstaw tridemu policzony z CSV jako √(R_sworznia² − R_stopy²) wynosi **7,87 m (40 t) / 7,84 m (pusty)**
przy geometrycznym 7,70 m. To zgodne z prostym modelem równych sztywności znoszenia L + Σd²/(nL) = 7,70 + 3,43/23,1 =
7,849 m (DERIVED, model bez źródła). Osie 1 i 3 pracują przeciwnymi siłami bocznymi (scrub).

## 4. Który wymiar decyduje — wrażliwość

Przemiatanie przy stałym R kierowcy 10,15 m, 40 t (`artifacts/tc-s23/sweep/sens/`, `base/`). Wrażliwość = zmiana
szerokości pasa na 1 cm zmiany wymiaru. Wymiary obrysu (zwis, szerokości) działają tylko na metrykę, a osie i siodło
działają na fizykę.

| Wymiar (obecnie) | zmiana | szerokość [m] | wrażliwość [cm/cm] | uwagi |
|---|---|---|---|---|
| — (bazowo) | — | 7,2340 | — | zewn. 12,510, wewn. 5,2765 |
| **sworzeń → środek tridemu 7,70** | −5 / −10 / −20 cm | 7,1748 / 7,1165 / 7,0024 | **1,18 / 1,18 / 1,16** | decyduje; nacisk sworznia −2,6 kN na −10 cm |
| zwis przedni ciągnika 1,45 | −5 cm | 7,2141 | 0,40 | tylko obrys, ale to model 3D ciągnika (1,443 m) |
| szerokość naczepy 2,55 | −5 cm | 7,2090 | 0,50 | 2,55 m to standard UE (zał. I 1.2), nie zmieniać |
| szerokość kabiny 2,49 | −4 cm | 7,2156 | 0,46 | tylko obrys |
| rozstaw osi tridemu 1,31 | −10 cm | 7,2097 | 0,24 | **niedopuszczalne**: przy d ≤ 1,3 m granica tridemu spada z 24 t do 21 t (96/53/WE zał. I 3.3.1–3.3.2, sprawdzone w tym samym tekście), a 40 t ma 22,55 t na tridemie |
| wysunięcie siodła 0,68 | +10 cm | 7,2214 | 0,13 | mały efekt, zmienia naciski ciągnika |
| promień kierowcy | +10 cm | — | −0,64 m/m | to nie wymiar pojazdu (patrz §3) |

**Wymiary naczep 13,6 m z publicznych źródeł** (bez marek w repo, URL jako źródło):
- karta producenta A, katalog firanek 3-osiowych 13,6 m (PDF z 2026-04): „wheelbase” **7 700 mm** we wszystkich 3-osiowych
  wariantach standard / mega / maxima / coil, opony 385/65 R22.5; 8 130 mm w wariancie heavy duty 45 t; 7 200 mm w 4-osiowym.
  Ta sama karta oferuje oś samoskrętną jako opcję.
  `https://kaessbohrer.com/uploads/2026/4/curtainsider-series-en-v5-1-2026-04-27-145956.pdf`
- karta producenta B, trzy karty naczep skrzyniowych 3-osiowych (długość wewn. 13 620 mm, wydanie 01/2024): wymiar rysunkowy pod
  podwoziem **7 630 mm** (odczyt: sworzeń → środek tridemu, UNVERIFIED co do punktu odniesienia), **rozstaw osi 1 310 / 1 310 mm**,
  siodło 1 150 mm, nacisk sworznia 12 000 kg.
  `https://www.krone-trailer.com/fileadmin/media/downloads/EN/Trockenfracht-Sattelauflieger/Datenblaetter/Dry_Liner/Dry_Liner41-STP_EN.pdf`
  (oraz `…-STG_EN.pdf`, `…-STLI_EN.pdf`)
- wynik wyszukiwania (niezweryfikowany, nie użyty): karta naczepy kurtynowej z rynku UK, 8,1 m sworzeń → środek wózka.

Wniosek: 7,70 m (gra) i 1,31 m to wartości typowe. Rzeczywisty zakres 3-osiowych 13,6 m w otwartych kartach wynosi
7,63–7,70 m (2 producentów). W samej fizyce gry zestaw z 7,70 m nie mieści się w 96/53/WE o 4–5 cm. W rzeczywistości
pomagają tu oś samoskrętna i ciągniki o mniejszym obrysie. Gra nie ma osi samoskrętnej: `TrailerDefinition.Validate` odrzuca
`steered`.

## 5. Propozycja (decyzja lidera/właściciela, dane gry NIEZMIENIONE na tej gałęzi)

Porównanie przy R 10,12–10,13 m (pusty = gorszy przypadek, `artifacts/tc-s23/sweep/prop/`):

| Wariant | zewn. | wewn. | szerokość | zapas szerokości | w realnych wymiarach? |
|---|---|---|---|---|---|
| obecny 7,70 m | 12,495 | 5,244 | 7,252 | −5,2 cm | tak (karta A) |
| **A: 7,60 m** (rekomendacja) | 12,495 | 5,358 | 7,137 | **+6,3 cm** | 3 cm poniżej najmniejszej znalezionej wartości 7,63 m; WORKING_VALUE |
| B: 7,63 m | 12,495 | 5,324 | 7,171 | +2,9 cm | tak (karta B) — PASS, ale zapas < 5 cm |
| C: 7,63 m + zwis przedni 1,40 m | 12,475 | 5,324 | 7,151 | +4,9 cm | tak (karta B; zwis w zakresie 1,40–1,50 z dims.json), ale trzeba przerobić model 3D ciągnika |

**Rekomendacja: wariant A.** Zmienia się tylko naczepa, ciągnik bez zmian. Zapas wynosi ≥ 5 cm w obu wariantach masy, a od
najmniejszej znalezionej wartości katalogowej to −3 cm. Jeśli właściciel woli wartość wprost z karty, B przechodzi z
zapasem 2,9 cm. Wariant C daje prawie ten sam zapas co A, ale wymaga zmiany modelu 3D.

Skutki A (runner, postój płasko, `artifacts/tc-s23/kingpin/`): statyczny nacisk sworznia 40 t **97,49 → 94,89 kN** (−265 kg),
pusty 15,68 → 15,27 kN. Tridem ≈ 22,55 → 22,82 t (DERIVED, ≤ 24 t z zał. I 3.3.2 przy d = 1,31 m). Oś napędowa ≈ −0,22 t,
przednia ≈ −0,05 t (DERIVED, dźwignia 0,68/3,70). Zwis naczepy za ostatnią osią 2,99 → 3,09 m. Wymiary z 96/53 (1.1, 1.6,
4.4) bez zmian. **Trzeba powtórzyć pełny runner**: postój 12 % pusty (pełzanie naczepy 4,97/5 mm) i 0–80 pusty to cienkie zapasy.

**Pliki do zmiany przez lidera przy przyjęciu A** (wszystkie poza tą gałęzią):

| Plik | Klucz | Stara → nowa |
|---|---|---|
| `game/Assets/_Project/Vehicle/Physics/Definitions/Data/curtainsider_tridem_13_6.trailer.json` | `axles[0].positionZ` / `axles[1].positionZ` / `axles[2].positionZ` | −6.39 → **−6.29** / −7.7 → **−7.6** / −9.01 → **−8.91** |
| to samo | `massElements[name=tridem_axles_wheels_brakes].center.z` | −7.7 → **−7.6** |
| `art-source/truck/dims.json` | `values.trailer_axle_z_m.value` | [−6.39, −7.7, −9.01] → **[−6.29, −7.6, −8.91]** (pilnuje tego `tests/physics/test_dims_sync.py`) |
| `game/Assets/_Project/Editor/Setup/TrailerAssetBuilder.cs:215` | `_CurtainAxles` | `(-6.39f, -7.70f, -9.01f)` → `(-6.29f, -7.60f, -8.91f)` |
| `tools/blender/truck/trailer/trailer_build.py` (`AXLES` z dims.json) → reeksport `art-source/truck/trailer/export/trailer_manifest.json` | położenie kół / błotników | regeneracja (blender-hero-asset, visual-qa) |
| `art-source/truck/regs/trailer.json` (l. 2654–2656) | osie | regeneracja wraz z modelem |
| `tools/worldgen/roads/swept_path.py:43` | `trailer_axles` | (6.39, 7.70, 9.01) → (6.29, 7.60, 8.91) (`tests/gis/test_swept_path_0218.py` porównuje z dims) |
| `tests/physics/swept_path_gate3.py:55-57, 118, 320` | osie, 7.70 | → 7.60 (analiza bramki 3) |
| `docs/VEHICLE_REFERENCE_DATA.md` (Semi-trailer, „Tridem axle positions”) | wartość | → −6.29 / −7.60 / −8.91 |
| `tests/physics/scenarios_expected_fail/ring_96_53_comb.json` | — | test zgłosi „naprawione? zdejmij expectedFail”: przenieść do `scenarios/` (w generatorze `out=OUT`), wtedy `ring_96_53_comb_rwb760` jest zbędny |

`ladenAxleLoadN` (78 500 N, odniesienie korektora siły hamowania) można zostawić. 22,82 t / 3 = 74,6 kN, więc różnica to
WORKING strojenie, nie wymóg.

## 6. Konsekwencje i ryzyka

- Scenariusz `ring_96_53_comb_rwb760` testuje geometrię, której gra jeszcze nie ma: to dowód propozycji, nie właściwość gry.
  Obecny stan gry dokumentuje znana porażka `ring_96_53_comb`.
- Ograniczenia metryki: stan ustalony po okręgu (nie wjazd styczny), obrys prostokątny bez lusterek (lusterka są poza szerokością
  2,55 m z 96/53 zał. I 1.2), obwiednia płaska. Opony mieszczą się w obrysie (ciągnik 1,24 ≤ 1,245, naczepa 1,21 ≤ 1,275).
  Sprawdzone tylko w solverze .NET, bez Unity/PhysX.
- Kontrola szerokości ≤ 7,15 m w wariancie A ma 0,7 mm zapasu przy pustym zestawie (7,1427). Każda zmiana opon, zawieszenia
  albo siodła, która zmniejszy zapas poniżej 5 cm, ją przewróci. Tak ma być: to strażnik zapasu, nie limit przepisu.
- Wzór RWB z 2021/535 (§1) jest nieczytelny w obrazie DzU. Nie opierać na nim decyzji, dopóki ktoś nie potwierdzi wersji
  tekstowej (np. wersja PDF albo inny język).

# ADR 0280 — Pierścień skrętu 12,50/5,30 m (96/53/WE): metryka obwiedni w runnerze, rozstaw sworzeń–tridem 7,63 m (D79, korekta)

Status: **Accepted (D79, korekta 7,63 m)** — 2026-11-16. Rozstaw sworzeń → środek tridemu **7,63 m** (wartość z 7 kart
producentów, §7; rozstaw osi 1,31 m), dane gry zmienione, wszystkie kontrole zielone (agent P16, gałąź `trailer-763-d79`, §10).
Historia decyzji:
1. Proposed (agent P10, gałąź `turning-circle-s23`): 7,70 m w danych gry **nie mieści się** w pierścieniu (wewn. 5,228 m, FAIL);
   propozycja 7,60 m przez `overrides`.
2. **D79** (właściciel): wariant A 7,60 m, WORKING_VALUE. Wdrożenie P13 (gałąź `trailer-760-d79`, §7–§9): pierścień PASS,
   ale `park_12pct_up_comb@empty` pełzanie naczepy 5,04 > 5 mm (§8.3) → scalenie wstrzymane.
3. **D79 korekta** (właściciel): 7,63 m = wartość z kart (§7), status SOURCED. Pełzanie miało przyczynę w modelu postoju, nie
   w geometrii; poprawione w fizyce (§10.3). Kontrola zapasu szerokości pierścienia 7,15 → 7,18 m (WORKING, §10.2).
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

## 7. Research: rozstaw sworzeń → środek tridemu w kartach naczep 13,6 m (P13, dostęp 2026-11-16)

Cel: czy 7,60 m (± kilka mm) albo mniej występuje w publicznej karcie lub rysunku 3-osiowej naczepy drogowej 13,6 m.
Nazwy producentów występują **tylko tutaj, jako źródło** (zasada 8: nigdzie w danych ani zasobach gry). Pliki PDF pobrane
do `scratchpad` sesji (poza repo), SHA256 skrócone.

| Źródło (URL, dostęp 2026-11-16) | Typ naczepy | Wartość | Uwagi |
|---|---|---|---|
| Krone, karta „Profi Liner 4 in sliding roof design”, typ SDP 27 eLB4-CS, wyd. 03/2020: `https://www.krone-trailer.com/fileadmin/media/downloads/EN/Pritschensattelauflieger/Datenblaetter/Profi_Liner/Profi_Liner_4-CS_GB.pdf` (SHA256 `9cfd25f0…7e99`) | firanka 3-osiowa, 13 620 mm wewn., 385/65 R22.5 | **7 630 mm** (rysunek: 1 668 mm od czoła do sworznia, 7 630 mm od sworznia do osi środkowej) | rozstaw osi 1 310 / 1 310 mm, sworzeń 12 000 kg, promień przedni 2 040 mm |
| Krone, ta sama seria: `…/Profi_Liner/Profi_Liner_4-BS_GB.pdf` (burtowa) i `…/Profi_Liner/Profi_Liner_4-DS_GB.pdf` (firanka dwupoziomowa), wyd. 03/2020 | skrzyniowa / firanka 13 620 mm | **7 630 mm** | 1 310 / 1 310 mm |
| Krone, `…/Mega_Liner/Mega_Liner_4-CS_GB.pdf` (SHA256 `e9c643d4…98d2`), `…/Mega_Liner_50-CS_GB.pdf`, `…/Mega_Liner_Comfort_GB.pdf`, wyd. 03/2020 | firanka mega (szyja 80 / 50 mm), 435/50 R19.5 | **7 630 mm** | 1 310 / 1 310 mm |
| Krone, `…/Mega_Liner/Mega_Liner_Coil_GB.pdf` (SHA256 `2d1efbeb…7e8902`) | firanka mega z kolebką na kręgi | **7 650 mm** | rozstaw 1 410 / 1 310 mm |
| Krone, `…/Mega_Liner/Mega_Liner_Plus_GB.pdf` | firanka mega z łamaną podłogą | 7 900 mm (wymiar na rysunku, punkt odniesienia nieopisany, UNVERIFIED) | nie jest typową naczepą 13,6 m |
| Schmitz Cargobull, „Kurzinformation S.CS Universal KP+”: `https://www.cargobull.com/de/-/media/project/scb-sites/scb-global-site/media-center-de/kurzinformation-scs-universal--kp.pdf` (SHA256 `ed5ca7b5…1112`) | firanka 3-osiowa, wariant ciężki | 8 130 mm („Radstand”) | 1 310 / 1 310 mm; wariant ze zwiększonym naciskiem siodła |
| Kässbohrer, katalog firanek (z §4): `https://kaessbohrer.com/uploads/2026/4/curtainsider-series-en-v5-1-2026-04-27-145956.pdf` | firanka 3-osiowa standard / mega / maxima / coil | 7 700 mm; 8 130 mm (HD 45 t) | nie pobierałem ponownie (wartość z §4) |
| Test drogowy w czasopiśmie branżowym (plik PDF na kfz-anzeiger.com): `https://kfz-anzeiger.com/wp-content/uploads/2023/03/schwarzmueller_curtainsider_1316.pdf` (SHA256 `ad01a983…fdbb`) | firanka Schwarzmüller 3-osiowa, 13 620 mm wewn., **trzecia oś samoskrętna (nachlaufgelenkt)**, pierwsza podnoszona | „Technischer Radstand” **7 620 mm** | to nie karta producenta; przy osi skrętnej „rozstaw techniczny” liczy się inaczej, więc nie jest to porównywalny sworzeń → środek tridemu |
| Ogłoszenia dealerskie / wyniki wyszukiwania (niezweryfikowane, nieużyte) | — | 7 700 mm (S.CS 24/L, karta dealera), 8,1 m (rynek UK, karta z serwisu prezentacji) | odczyt tylko ze streszczeń wyszukiwarki |

Szukałem też kart: Kögel, Wielton, Fliegl, Schwarzmüller (karty `?pdf=1` platform: 2 × 1 310 mm, sworzeń 2" „EG-Einbaumaß,
Eckmaß 2 040 mm”, ale bez wymiaru sworzeń–oś). Nie znalazłem żadnej publicznej karty ani rysunku z wartością ≤ 7 600 mm dla
3-osiowej naczepy drogowej 13,6 m z osiami sztywnymi.

**Wniosek:** najbliższe wartości to **7 630 mm** (Krone, 7 kart: standard, mega, burtowa, dwupoziomowa), 7 650 mm (mega coil),
7 700 mm (Kässbohrer, karta dealera S.CS) i 7 620 mm (test czasopisma, naczepa z osią samoskrętną, czyli inna kinematyka).
Wartość 7,60 m leży 3 cm poniżej najmniejszej wartości z karty producenta, więc **WORKING_VALUE zostaje** (dims.json,
VRD). Do zdjęcia statusu potrzebny jest rysunek lub karta z ≤ 7 600 mm (właściciel, D79).

## 8. Wdrożenie D79 (P13, gałąź `trailer-760-d79` z `origin/main` @ `65eab5bd5`, 2026-11-16)

### 8.1 Zmienione pliki

| Plik | Klucz | Stara → nowa |
|---|---|---|
| `game/Assets/_Project/Vehicle/Physics/Definitions/Data/curtainsider_tridem_13_6.trailer.json` | `axles[0..2].positionZ` | −6.39 / −7.7 / −9.01 → **−6.29 / −7.6 / −8.91** |
| to samo | `massElements[tridem_axles_wheels_brakes].center.z` | −7.7 → **−7.6** (pusty CoG naczepy z −5,939 → −5,907 m) |
| `art-source/truck/dims.json` | `trailer_axle_z_m` | [−6.39, −7.70, −9.01] → **[−6.29, −7.60, −8.91]**, WORKING_VALUE, źródło: D79 + §7 |
| `game/Assets/_Project/Editor/Setup/TrailerAssetBuilder.cs:216` | `_CurtainAxles` (zabrudzenie firanki za osiami w shaderze) | (−6.39f, −7.70f, −9.01f) → **(−6.29f, −7.60f, −8.91f)**; wartości były wpisane na sztywno (kopia dims.json), materiały i geometria bez zmian |
| `tests/physics/swept_path_gate3.py` | `TYRES trl_1..3`, `offtracking()`, kierunek osi | stała `KP_TRIDEM = 7.60` zamiast 7.70 (analiza bramki 3, tylko stała wymiaru; nieprzeliczona — wymaga zbudowanego świata) |
| `tests/physics/generate_stage2_scenarios.py` | `ring_96_53_comb` | z `out=OUT_XFAIL` na wyjście domyślne, bez `expectedFail*`, szerokość ≤ **7,15 m** (WORKING: 7,20 z promieni SOURCED − zapas 5 cm); `ring_96_53_comb_rwb760` **usunięty** |
| `tests/physics/scenarios/ring_96_53_comb.json` (nowy), `scenarios_expected_fail/ring_96_53_comb.json` i `scenarios/ring_96_53_comb_rwb760.json` (usunięte) | — | regeneracja generatorem |
| `tests/physics/scenarios/circle_r50_10kmh_comb.json` | opis źródła offtrackingu | „L = 7.7 m → 0.59 m” → „L = 7.6 m (D79) → 0.58 m” (limity 0,4–0,8 m bez zmian) |
| `tests/physics/test_scenario_strictness.py` | `test_generator_reproduces_committed_scenarios`, `test_ring_limits_pinned` | pierścień ma być zwykłym scenariuszem bez `overrides` i `expectedFail*`; szerokość przypięta ≤ 7,15 (było ≤ 7,20 dla obu plików) |
| `tools/physics-runner/Tests/SweptPathTests.cs` | `GeometryOverrides_ApplyToARunCopyOnly`, `ShorterKingpinToTridem_WidensTheInnerRadius` | czytają `ring_96_53_comb.json`; „przed” = dawne osie 7,70 m przez `overrides` (mechanizm nadpisań zostaje przetestowany) |
| `tests/physics/scenarios_expected_fail/README.md` | opis | pierścień nie jest już znaną porażką |

**Dlaczego `ring_96_53_comb_rwb760` usunięty, a nie zostawiony:** po zmianie danych jego `overrides` są równe danym gry, więc
byłby bitowym duplikatem `ring_96_53_comb` (te same liczby, 2 przebiegi runnera więcej) i wprowadzałby w błąd nazwą
„propozycja”. Strażnik zapasu 5 cm (≤ 7,15 m) przeszedł do `ring_96_53_comb`, a mechanizm `overrides` dalej testują
`SweptPathTests` (z osiami 7,70 m jako nadpisaniem).

Syntetyczne testy kinematyki w `SweptPathTests` (`Synthetic(..., 7.70, ...)`, l. 84 i 102) zostały: to wzór zamknięty dla
dowolnego L, niezależny od danych gry.

### 8.2 Wyniki PRZED / PO

Runner: `dotnet run -c Release --project tools/physics-runner/Runner -- --out artifacts/t760/{main,run}` (Linux, .NET SDK
8.0.428, dt 0,01 s, 4 podkroki). PRZED = `origin/main` @ `65eab5bd5` (pierścień PRZED: `--scenarios
tests/physics/scenarios_expected_fail --only ring_96_53_comb`). PO = gałąź `trailer-760-d79`. Pary liczb: pusty / 40 t.

| Pozycja | PRZED (7,70 m) | PO (7,60 m) | Limit / status |
|---|---|---|---|
| Pierścień: zewn. [m] | 12,486 / 12,483 | 12,486 / 12,482 | ≤ 12,50 (S) ✅ |
| Pierścień: wewn. [m] | **5,228 / 5,230 FAIL** | **5,343 / 5,347** | ≥ 5,30 (S) ✅ |
| Pierścień: szerokość [m] | 7,258 / 7,253 FAIL | 7,143 / 7,135 | ≤ 7,15 (W, zapas 5 cm; 7,20 D) ✅, zapas 0,7 mm przy pustym |
| Promień skrętu (obrys zewn., narożnik zderzaka ciągnika) | 12,486 m | 12,486 m | ciągnik bez zmian |
| Nacisk statyczny przód [t] (postój płasko, t ≥ 60 s) | 5,648 / 7,216 | 5,641 / 7,167 | 7,5 t (karta S9) ✅, zapas 0,33 t |
| Napęd [t] | 3,453 / 10,225 | 3,419 / 10,008 | 11,5 t (96/53 zał. I 3.4.1) ✅ |
| Sworzeń [kN] | 15,68 / 97,46 | 15,27 / 94,86 | −2,6 kN przy 40 t |
| Tridem [t] (osie 1/2/3) | 5,404 / 22,573 (7,51/7,52/7,54) | 5,445 / 22,838 (7,59/7,61/7,63) | 24 t przy 1,3 < d ≤ 1,4 m (zał. I 3.3.2) ✅, d = 1,31 m bez zmian |
| Rozkład ciągnika solo 73/27 % (ADR 0201b) | — | bez zmian (naczepa nie wpływa na solo) | ✅ |
| Jackknife bez ABS (pusty) / z retarderem | 87,45° / 92,63° | 87,44° / 92,66° | ≥ 30° ✅ |
| Jackknife ABS 50 / 100 | 7,77 / 4,59° (pusty), 5,14 / 5,14° (40 t) | 7,64 / 4,54°, 5,17 / 5,17° | ≤ 10° ✅ |
| 0–80 km/h (solo / pusty / 40 t) | 14,06 / 21,14 / 47,58 s | 14,06 / 21,19 / 47,59 s | pusty ≥ 20 s; 40 t 40–95 s ✅ |
| Hamowanie 60–0 ABS (R13, S) | 23,19 / 24,10 m | 23,16 / 24,14 m | ≤ 36,7 m ✅ |
| Hamowanie 80–0 ABS sucho / mokro | 39,19 / 41,31; 55,20 / 56,84 m | 39,16 / 41,29; 55,18 / 56,84 m | ≤ 61,2; 45–95 ✅ |
| Offtracking R 50 m, 10 km/h | 0,609 / 0,603 m | 0,593 / 0,588 m | 0,4–0,8 (D 0,58) ✅ |
| Rollover 40 t (CoG 1,9 / 2,6 m) | 0,458 / 0,337 g | 0,460 / 0,340 g | 0,25–0,55 g ✅ |
| Lane change 80: RA | 0,991 / 0,996 | 0,992 / 0,998 | 0,8–1,6 ✅ |
| Postój 12 % w dół: pełzanie naczepy | 4,69 / 4,55 mm | 4,76 / 4,47 mm | ≤ 5 mm ✅ |
| **Postój 12 % w górę: pełzanie naczepy** | 4,97 / 3,26 mm | **5,04 / 3,13 mm** | **≤ 5 mm — FAIL (pusty)** |
| Runner razem | 141 scen. / 833 kontroli PASS | **140 / 141 scen., 832 / 833 kontroli** | — |
| `dotnet test tools/physics-runner -c Release` | 287 / 287 | **284 / 287** (3 FAIL, §8.3) | — |
| `pytest tests/physics` | — | 18 passed, 14 skipped (bramka 3: świat niezbudowany) | ✅ |
| `pytest tests/gis/test_swept_path_0218.py` | 6 / 6 | **5 / 6** (`test_combination_matches_dims_json`, §9.3) | czeka na zmianę lidera |

### 8.3 Co pada i dlaczego (stop — limity nie były ruszane; rozwiązane w §10)

1. **`park_12pct_up_comb@empty`, `trailer_creep_m` = 5,043 mm > 5 mm** (WORKING „bez pełzania”, 12 % z R13 zał. 4 pkt 2.3.2).
   Przed zmianą 4,972 mm (zapas 0,6 %, opisany w ADR 0201b jako cienki). To osiadanie w pierwszych ~60 s (podatność zawieszenia
   i siodła przy hamulcu sprężynowym tylko na ciągniku), nie stałe pełzanie: od 60 s do 300 s przesunięcie stoi, a
   `creep_m` od 60 s i `max_speed_after_ms` przechodzą. Oś tridemu 10 cm do przodu przenosi 0,4 kN pustej naczepy ze
   sworznia na tridem, a naczepa trzymana tylko przez sworzeń osiada o 0,07 mm więcej.
   Przemiatanie (`artifacts/t760/sweep/`, nadpisania osi na kopii danych): pełzanie pusty w górę 7,60 → 5,043; 7,61 → 5,036;
   7,62 → 5,028; 7,63 → 5,021; 7,65 → 5,007; 7,70 → 4,972 mm. Pierścień (szerokość ≤ 7,15 przy pustym): 7,60 → 7,143 PASS;
   7,61 → 7,154 FAIL; 7,63 → 7,177; 7,65 → 7,200 (wewn. 5,286 FAIL). **Przy obecnej fizyce żaden rozstaw nie spełnia obu
   warunków jednocześnie**: pełzanie wymaga ≥ ~7,69 m, pierścień ≤ ~7,645 m (≤ 7,60 m z zapasem 5 cm).
2. Golden telemetry (`Stage2Tests.GoldenTelemetry_Matches`): `brake_80_0_wet_noabs_comb@empty` (`rear_L_fz`, 5,0 % odchyleń)
   i `launch_6pct_uphill_comb@laden40` (`kingpin_fz`, maks. 8,0 kN, 3,3 %). To oczekiwany skutek zmiany geometrii (statyczny
   nacisk sworznia −2,6 kN przy 40 t, inny rozkład na napęd), nie regres solvera. **Nie aktualizowałem goldenów**
   (`--update-golden`), bo pkt 1 blokuje całość; zrobić to razem z rozwiązaniem pkt 1 i przejrzeć diff.

Opcje dla lidera / właściciela (żadna nie jest wdrożona):
- (a) strojenie fizyki postoju (źródło osiadania: poziomowanie miechów / podatność siodła przy hamulcu sprężynowym, ADR 0201b
  pkt o 4,97 mm) — osobne zadanie fizyki z pełnym runnerem;
- (b) decyzja właściciela o limicie „bez pełzania” 5 mm (WORKING, nie przepis; R13 wymaga tylko utrzymania na 12 %) —
  zmiana limitu = decyzja właściciela, nie agenta;
- (c) zostać przy 7,70 m (pierścień znowu znaną porażką) do czasu (a).

### 8.4 Dokumenty

`docs/04_FIZYKA.md` §6a, `docs/PHYSICS_VALIDATION.md` §3 i `docs/VEHICLE_REFERENCE_DATA.md` (wiersz „Tridem axle
positions”, „Empty CoG / static kingpin load” → z −5,907 m / 1559 kg, tabela przypadków obciążenia: pusty 5,64 / 3,42 /
5,45 t, sworzeń 1,56 t; 40 t 7,17 / 10,01 / 22,84 t, sworzeń 9,67 t) **nie zostały odświeżone** na tej gałęzi, bo wynik nie
jest zielony. Liczby do wpisania są w §8.2 i w `artifacts/t760/run/summary.md`.

## 9. Kroki dla agenta lokalnego (Windows, Blender + Unity) — pod 7,63 m

Stan po §10: dane fizyki, `dims.json`, `TrailerAssetBuilder` i testy mają osie **−6.32 / −7.63 / −8.94** (rozstaw 1,31 m).
Model 3D, prefab i shader mają jeszcze −6.39 / −7.70 / −9.01. Przesunięcie względem modelu: **+0,07 m w stronę sworznia**
(oś środkowa 7,70 → 7,63 m). Agent P16 nie uruchamiał Unity ani Blendera.

### 9.1 Blender (model naczepy)

Wszystko czyta osie z `art-source/truck/dims.json` → `trailer_axle_z_m` (`tools/blender/truck/trailer/trailer_build.py:37`
`AXLES = D("trailer_axle_z_m")`; komentarz `# [-6.39, -7.70, -9.01]` w tej linii poprawić na `# [-6.32, -7.63, -8.94]`).
Od pozycji osi zależą (przesuną się same, z kodu, o +0,07 m):
- `axles_and_suspension()` (belki osi, wsporniki, wahacze, miechy), `wheels()` (`WHEEL_1x..3x`, piwoty kół);
- `mudguards()` (błotniki `mudguard_*`, kołnierze, wsporniki) i chlapacze `MUDFLAP_L/R` (`AXLES[-1] − 0,66` = −9,60 m, także w
  `trailer_export.py:636` — pozycja piwotu chlapacza);
- `side_guards()` (osłony boczne UN R73: koniec `AXLES[0] + TYRE_R + 0,22` — osłona wydłuży się o 0,07 m do tyłu,
  przerwa do opony bez zmian 0,22 m ≤ 0,30 m);
- wysięgniki ramy nad kołami (`over_wheels`, l. ~682), materiał zabrudzenia firanki (węzły `AXLES[0] + 0,9 … AXLES[-1] − 1,2`
  i pętla po `AXLES`, l. ~105 i ~352);
- światła obrysowe boczne: lampa `side_marker_*_3` w `(AXLES[0] + AXLES[1]) / 2` przesunie się z −7,045 na −6,975 m;
  odstępy do sąsiadów −4,05 / −9,58 m: 2,925 / 2,605 m (≤ 3 m, R48 6.18.4.3 — sprawdzi `regs_check.py`);
- **bez zmian** (stałe z obrysem, nie z osi): zderzak / belka RUPD, tylne lampy i odboje (od `Y_REAR` = −12,00), podpory
  (`trailer_landing_gear_m` z −2,2), skrzynka paletowa (−3,98 … −5,50), koło zapasowe (−3,32), skrzynka narzędziowa,
  kliny. Zwis za ostatnią osią rośnie 2,99 → 3,06 m (obrys niezmieniony).

Komendy (wzorce z nagłówków skryptów, ADR 0175):
```
blender -b --factory-startup --python tools/blender/truck/trailer/trailer_export.py -- [--out ABS_DIR] [--renders ABS_DIR]
blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/trailer/check_export.py -- --manifest art-source/truck/trailer/export/trailer_manifest.json
blender -b --factory-startup --python tools/blender/truck/regs_audit.py -- --out <ABS>/art-source/truck/regs/trailer.json --what trailer
python tools/blender/truck/regs_check.py --tractor art-source/truck/regs/tractor.json --trailer art-source/truck/regs/trailer.json
```
`trailer_export.py` sam porównuje osie modelu z fizyką (l. 861–863, tolerancja 1 mm) — po zmianie dims.json musi przejść.
Regenerowane: `art-source/truck/trailer/export/trailer_manifest.json` (pola `axle`/`art`/`physics` z −6.39 / −7.7 / −9.01),
`art-source/truck/regs/trailer.json` (`axles`, l. 2654–2656), rendery kontrolne (skill `blender-hero-asset`, `visual-qa`:
koła w nadkolach, błotniki, osłony boczne).

### 9.2 Unity

- `-executeMethod Game.Editor.Setup.TrailerAssetBuilder.BuildBatch` (przebudowa `Assets/_Generated/Trailer`, materiały z nowym
  `_CurtainAxles` = (−6.32, −7.63, −8.94)), potem `Game.World.Import.WorldTruckInstaller.InstallBatch` (WorldC).
- Prefab `game/Assets/_Project/Vehicle/Runtime/Prefabs/Trailer_Curtainsider_Graybox.prefab` ma osie −6.39 / −7.7 / −9.01
  (8 transformów przy osiach, np. l. 241). Generuje go `GrayboxTrailerBuilder` z `TrailerDefinition` — przebudować w Unity
  (wspólny prefab = lider), nie edytować ręcznie.
- `game/Assets/_Project/Rendering/Shaders/TruckExterior.shader:63` — domyślna wartość `_CurtainAxles` (−6.39, −7.7, −9.01)
  → (−6.32, −7.63, −8.94); builder ją nadpisuje, ale dla spójności poprawić razem z modelem.
- Fizyka (§10.3) jest wspólna dla Unity i runnera (ADR 0004): `CombinationModel` przekazuje koła ciągnika naczepie sam, adapter
  Unity nie wymaga zmian. Sprawdzić w Play Mode postój 12 % (pusty) — naczepa nie powinna osiadać po zatrzymaniu.
- Visual QA naczepy (`pwsh scripts/visual-qa.ps1 …`) i build Windows (DoD).

### 9.3 Lider: `tools/worldgen/roads/swept_path.py:43` (zakazane dla P13/P16)

`trailer_axles: tuple = (6.39, 7.70, 9.01)` → **`(6.32, 7.63, 8.94)`** — w tym samym commicie co ta gałąź albo zaraz po
scaleniu. `tests/gis/test_swept_path_0218.py::test_combination_matches_dims_json` (l. 23) porównuje tę krotkę z
`dims.json` `trailer_axle_z_m` (z odwróconym znakiem) **dokładnie**, więc oba pliki muszą się zmienić razem — inaczej test pada
(na tej gałęzi pada, bo dims.json już ma 7,63). `L2` (domyślnie `trailer_axles[1]`) zmieni się na 7,63 → przeliczyć testy
`tests/gis` obwiedni (ADR 0218) i analizę bramki 3 (`tests/physics/swept_path_gate3.py` ma już `KP_TRIDEM = 7.63`).
`tests/gis/test_swept_path_0218.py::test_knyszyn_ring_sectors_clear_the_u_turn` pada też na `origin/main` (niezależnie od
osi; nie badane).

### 9.4 Wykonanie §9.1–9.2 (agent trailer-763-s23, gałąź `trailer-763-s23`, 2026-11-16)

Blender 4.2.9 (Windows): generator już czytał osie z `dims.json`, więc zmiana kodu to tylko komentarz w
`trailer_build.py:37`, kamera `zbl_kolo` liczona z `T.AXLES[1]` i nowa kamera kontrolna `gora` (ortho z góry, przekrój na
1,20 m przez bliską płaszczyznę odcięcia, przód w prawo). Pełny eksport (`trailer_export.py`, ok. 6 min; pierwsza próba padła
na braku pamięci w bake'u AO przy obciążonej maszynie, kolejne OK):
- manifest: piwoty `WHEEL_1x..3x` i puste `AXLE_1..3` na **−6,32 / −7,63 / −8,94**, chlapacze −9,692 → **−9,622**,
  `physics_crosscheck` osi 3/3 zgodne; `check_export.py` **PASS** (LOD 89 000 / 24 499 / 7 847 tr., budżety 90k/25k/8k);
- `regs_audit.py` + `regs_check.py`: **158/158 OK**; lampa obrysowa boczna 3: środek −7,045 → **−6,975 m** (odstępy
  2,925 / 2,605 m ≤ 3 m, R48 6.18.4.3); `pytest tests/physics/test_dims_sync.py` 9/9, `test_truck_regs.py` 5/5;
- atlasy przebake'owane (AO przy przesuniętych częściach), układ UV atlasów lekko inny (pakowanie zależy od geometrii).
- Znalezisko **sprzed tej zmiany** (nie naprawiane tu): obręcze kół próbkują w atlasie Metal czerwone / tekstowe fragmenty
  (czerwone plamy na beczce obręczy w `zbl_kolo`). Pomiar: 639 z 10 651 tekseli UV kół ma R − G > 0,2 — **identycznie** w FBX
  i atlasie z `origin/main` i z tej gałęzi; UV kół nakładają się na 7 506 tekseli `CHASSIS` (koło zapasowe dzieli UV koła 1L).
  Do osobnego zadania (truck-artist).

Unity: `TruckExterior.shader` domyślne `_CurtainAxles` → (−6,32, −7,63, −8,94); nowe wejście
`DrivingLabSceneBuilder.RebuildTrailerPrefabBatch` (sam prefab graybox z definicji, bez przebudowy sceny DrivingLab);
test `Tests/EditMode/TrailerAxleSyncTests.cs` (osie fizyki vs `dims.json`, piwoty manifestu we wszystkich LOD, `AXLE_n` i
środki kół w FBX z art-source i w kopii `_Generated` użytej przez prefab, spinnery prefabu graybox i art, domyślna wartość
shadera; tolerancja 1 cm).

## 10. Korekta D79: 7,63 m i przyczyna pełzania (P16, gałąź `trailer-763-d79`, 2026-11-16)

Gałąź z `origin/trailer-760-d79` @ `5fe05662c` + `git merge origin/main` (@ `8133dfd7f`). Runner: `dotnet run -c Release
--project tools/physics-runner/Runner -- --out <dir>` (Linux, .NET SDK 8, dt 0,01 s, 4 podkroki). Bez Unity i Blendera.

### 10.1 Dane (commit `feat(physics): trailer kingpin to tridem centre 7.63 m`)

| Plik | Klucz | 7,60 (r5) → 7,63 |
|---|---|---|
| `curtainsider_tridem_13_6.trailer.json` | `axles[0..2].positionZ` | −6.29 / −7.6 / −8.91 → **−6.32 / −7.63 / −8.94** (7,63 ± 1,31) |
| to samo | `massElements[tridem_axles_wheels_brakes].center.z` | −7.6 → **−7.63**; pusty CoG naczepy z = −5,917 m, nacisk statyczny sworznia (dźwignia na środek tridemu) 1 572 kg (7,70: −5,89 / 1 645 kg w VRD) |
| `art-source/truck/dims.json` | `trailer_axle_z_m` | → [−6.32, −7.63, −8.94], **WORKING_VALUE → SOURCED**: 7 630 mm sworzeń → oś środkowa i 1 310/1 310 mm w 7 kartach (§7); nazwy producentów tylko tu, w ADR |
| `TrailerAssetBuilder.cs:216` | `_CurtainAxles` | → (−6.32f, −7.63f, −8.94f) |
| `tests/physics/swept_path_gate3.py:51` | `KP_TRIDEM` | 7.60 → 7.63 |
| `generate_stage2_scenarios.py`, `circle_r50_10kmh_comb.json` | opis offtrackingu | „L = 7.63 m (D79) → 0.59 m” (wzór daje 0,586 m; limity 0,4–0,8 bez zmian) |
| to samo, `ring_96_53_comb.json` | opis, kontrola zapasu szerokości | §10.2 |
| `test_scenario_strictness.py` | `test_ring_limits_pinned` | szerokość przypięta ≤ 7,18 (było ≤ 7,15); 12,50 / 5,30 bez zmian |
| `SweptPathTests.cs` | `GeometryOverrides_*`, `ShorterKingpinToTridem_*` | produkcyjna oś −7,63; masa tridemu −0,07 m względem 7,70; wrażliwość dzielona przez 0,07 m |

### 10.2 Pierścień 96/53/WE przy 7,63 m

Zmierzone (`ring_96_53_comb`, od t = 120 s): zewn. **12,486 / 12,482 m**, wewn. **5,309 / 5,312 m**, szerokość
**7,177 / 7,170 m** (pusty / 40 t). Przepis (zał. I pkt 1.5, SOURCED): zewn. ≤ 12,50 ✅ (zapas 14 / 18 mm), wewn. ≥ 5,30 ✅
(zapas 9 / 12 mm), szerokość ≤ 7,20 ✅ (warunek konieczny, DERIVED).

Kontrola **zapasu** szerokości (WORKING_VALUE, nie przepis) była ≤ 7,15 m (5 cm) przy 7,60 m. 7,63 m daje 7,177 m, więc 7,15
nie da się utrzymać bez łamania decyzji właściciela. Nowa wartość **≤ 7,18 m = 2 cm zapasu do 7,20 m** (zapas względem pomiaru
3,2 mm przy pustym). Uzasadnienie: zapas ma łapać pogorszenie geometrii (opony, siodło, zawieszenie), a 2 cm to ~2 cm na
promieniu wewnętrznym przy wrażliwości ~1,15 cm/cm rozstawu (§4). Historia w polu `source` scenariusza: „7.15 (5 cm) with the
7.60 m axles (D79); 7.18 (2 cm) since the owner's D79 correction to the datasheet value 7.63 m”. Limity przepisu bez zmian.
Ryzyko: każda zmiana, która zmniejszy promień wewnętrzny o > 9 mm, przewróci kontrolę przepisu (5,30) — to właściwość wybranej
geometrii, nie testu.

### 10.3 Pełzanie 12 %: przyczyna w modelu i poprawka (commit `fix(physics): trailer standstill relaxation …`)

Pomiar przy 7,63 m przed poprawką: `park_12pct_up_comb@empty` `trailer_creep_m` (od 5 s) = **5,021 mm** > 5 mm. Rozkład
(sonda na `ScenarioRunner.Setup` + pętla kroków, osie świata):
- koła naczepy są zahamowane (hamulec roboczy przez zawór ręczny ciągnika w pozycji „park”, 1,92 bar po korekcji obciążenia,
  3 370 N m ≫ potrzebne; ω = 0) — nie ślizgają się; oś 3 bez siłownika sprężynowego (`parkingBrakeTorque` 0, osie 1–2
  12 000 N m) nie ma znaczenia, bo w zestawie sprzężonym siłowniki naczepy są zwolnione (przewód zasilający pod ciśnieniem);
- po puszczeniu zestawu na 12 % siła spadku rozkłada się **sprężyście**: wszystkie zahamowane koła przesuwają się razem (sworzeń
  sztywny), więc każde niesie k_x·u. Sześć sztywnych opon 385/65 pustej naczepy niesie po 1,6–1,9 kN (razem ~11 kN, więcej niż
  8,2 kN spadku samej naczepy; sworzeń pcha ciągnik w górę +2,9 kN);
- relaksacja postoju R6 (`TrailerModel.RelaxStickAtStandstill`, τ 2 s) ciągnęła każde zahamowane koło naczepy do „własnego
  udziału” F_z·tanθ = 1,07 kN. Różnica (~3–5 kN) przechodziła przez ~60 s na sworzeń (kpFx +1,40 → −1,85 kN od 5 s);
- ciągnik przyjmował ją podatnością: ugięcie opon napędu +1,9 mm (ux tylnych 4,3 → 6,2 mm) i osiadanie miecha tyłu 3,1 → 8,0 mm
  wewnątrz strefy martwej zaworu poziomującego 8 mm (pochylenie 2,1 mrad → 2,4 mm na wysokości siodła); do tego pochylenie
  naczepy 0,64 mrad × 1,15 m = 0,7 mm. Razem 1,9 + 2,4 + 0,7 ≈ 5,0 mm. Od 60 s stoi (`creep_m` od 60 s ≈ 0).
- Kontrola: z wyłączoną relaksacją (τ = 0) naczepa po 5 s **nie rusza się wcale** (0,000 mm); zmiana strefy martwej 8 → 4 / 2 mm
  zmniejsza tylko składową ciągnika (3,26 / 2,39 mm), przyczyny nie usuwa. Wstępne ustawienie ux kół naczepy na „własny udział”
  przed pierwszym krokiem pogarsza (6,3 mm), bo puszczenie i tak rozkłada siłę sprężyście.

Mechanizmy wykluczone: tarcie statyczne / poślizg (ω = 0, siła ≪ μF_z i ≪ momentu hamulca), sztywność wzdłużna opony
(nie zmieniana; daje tylko rozkład sprężysty, który bez relaksacji stoi), rozkład nacisków pustej naczepy przy krótszym
rozstawie (sworzeń −0,3 kN; wpływ 5,04 vs 4,97 mm to skutek, nie przyczyna), podatność siodła (błąd sworznia ≤ 0,0003 mm).

**Co jest niefizyczne:** relaksacja R6 ma zdejmować **wewnętrzne napięcie między bryłami** (niedopasowanie geometrii przy
zmianie pochylenia: nacisk przechodzi z podpór na siodło, poziomowanie miechów; ADR 0009 R6, `PHYSICS_VALIDATION.md` §2a),
nie obciążenie od spadku. Cel „własny udział” zdejmował też sprężysty udział naczepy w sile spadku i przenosił go na ciągnik
— zestaw osiadał po zatrzymaniu, choć w realnym zestawie guma wszystkich opon relaksuje tak samo, więc podział sprężysty
zostaje. Zestaw bez napięcia wewnętrznego ma na każdym zahamowanym kole to samo ugięcie u.

**Poprawka** (`game/Assets/_Project/Vehicle/Physics/TrailerModel.cs:218–272`, `CombinationModel.cs:59, 109`):
- zahamowane koła naczepy relaksują do **ugięcia wspólnego zahamowanych kół ciągnika** u_ref = Σk_i·u_i / Σk_i (siła netto
  zahamowanych kół ciągnika / ich sztywność), z ograniczeniem do momentu hamulca; niezahamowane do 0 (bez zmian);
- średnia ważona sztywnością: napięcie między osiami samego ciągnika (przód pcha, tył ciągnie po cofaniu i hamowaniu,
  `couple_standstill_locked`: ux przodu +7,0 mm, tyłu −17,4 mm) znosi się w niej — zwykła średnia dawała tam
  `kingpin_load_vs_static` 1,03–1,04 (FAIL);
- „własny udział” F_z·tanθ zostaje jako wyjście awaryjne, gdy ciągnik nie ma zahamowanego koła w kontakcie;
- `CombinationModel` ustawia `TrailerModel.TowingWheels = Tractor.Wheels` przy sprzęgnięciu (null po rozprzęgnięciu / zmianie
  naczepy). Bez alokacji w pętli, C# 9.
- Status: **WORKING_VALUE (wybór modelu z uzasadnieniem fizycznym)**, τ = 2 s bez zmian. Brak źródła liczbowego — to definicja,
  co relaksuje, nie nowy parametr. Limit 5 mm i test bez zmian.

Wynik: `park_12pct_up_comb` naczepa **0,69 / 0,29 mm** (pusty / 40 t; zapas 86 % / 94 % do 5 mm), w dół 0,69 / 0,65 mm.

### 10.4 Golden telemetry (commit `test(physics): regenerate golden …`)

Przegenerowany **tylko** `tests/golden/brake_80_0_wet_noabs_comb_empty.csv` (`--update-golden --only brake_80_0_wet_noabs_comb`).
Pada już przy samych danych 7,63 (bez poprawki fizyki): `rear_L_fz` 4,0 % odchyleń > 3 %. Przyczyna: golden sprzed ADR 0201b
(przy t = 0,1 s `front_L_fz` 25,10 → 27,70 kN, `rear_L_fz` 19,59 → 16,83 kN, `rear_L_p_bar` na końcu 2,72 → 2,31 bar — te same
wartości co `origin/main`), więc main był blisko progu; 7,63 m dokłada `rear_L_fz` −0,12 kN i sworzeń −0,29 kN (15,74 → 15,45 kN
przy 0,1 s) i przekracza 3 %. Poprawka §10.3 zmienia tylko ogon po zatrzymaniu (t ≳ 14 s): przy 20 s `rear_L_fz` 15,92 →
16,49 kN, `kingpin_fz` 14,74 → 15,10 kN (sworzeń nie przejmuje już udziału naczepy). Maks. |różnica| nowy − stary golden:
prędkość 0,42 km/h, `kingpin_fz` 1,97 kN, `front_L_fz` 3,86 kN, `rear_L_fz` 3,21 kN. `launch_6pct_uphill_comb@laden40`, który
padał przy 7,60, przy 7,63 przechodzi bez regeneracji; pozostałe 7 goldenów bez zmian.

### 10.5 PRZED (main, 7,70) / r5 (7,60) / PO (7,63 + poprawka)

Pary: pusty / 40 t. Naciski: średnia z `park_flat_5min_comb` dla t ≥ 60 s. Pełzanie: `trailer_creep_m` od 5 s (300 s).
Kolumna „7,63 bez poprawki” = commit danych (`bec798465`).

| Pozycja | PRZED 7,70 (main) | r5 7,60 | 7,63 bez poprawki | **PO 7,63 + poprawka** | Limit / status |
|---|---|---|---|---|---|
| Pierścień zewn. [m] | 12,486 / 12,483 | 12,486 / 12,482 | 12,486 / 12,482 | **12,486 / 12,482** | ≤ 12,50 (S) ✅ |
| Pierścień wewn. [m] | 5,228 / 5,230 FAIL | 5,343 / 5,347 | 5,309 / 5,312 | **5,309 / 5,312** | ≥ 5,30 (S) ✅ |
| Pierścień szerokość [m] | 7,258 / 7,253 | 7,143 / 7,135 | 7,177 / 7,170 | **7,177 / 7,170** | ≤ 7,20 (D) ✅; zapas ≤ 7,18 (W, było 7,15) ✅ |
| Naciski pusty: przód / napęd / tridem [t], sworzeń [kN] | 5,646 / 3,452 / 5,402; 15,68 | 5,639 / 3,418 / 5,443; 15,27 | 5,641 / 3,428 / 5,431; 15,40 | **5,642 / 3,427 / 5,431; 15,39** | — |
| Naciski 40 t: przód / napęd / tridem [t] (osie 1/2/3), sworzeń [kN] | 7,214 / 10,221 / 22,565 (7,51/7,52/7,53); 97,46 | 7,165 / 10,005 / 22,831 (7,59/7,61/7,63); 94,86 | 7,179 / 10,071 / 22,750; 95,64 | **7,178 / 10,073 / 22,749 (7,56/7,58/7,60); 95,65** | 7,5 t (S9); 11,5 t; 24 t (zał. I 3.4.1, 3.3.2) ✅ |
| Pełzanie naczepy 12 % w górę [mm] | 4,97 / 3,26 | 5,04 FAIL / 3,13 | 5,02 FAIL / 3,17 | **0,69 / 0,29** | ≤ 5 (W) ✅ |
| Pełzanie naczepy 12 % w dół [mm] | 4,69 / 4,55 | 4,76 / 4,47 | 4,74 / 4,50 | **0,69 / 0,65** | ≤ 5 (W) ✅ |
| Pełzanie ciągnika 12 % w górę / w dół [mm] | 1,90 / 0,97; 2,71 / 1,48 | — | 1,91 / –; – | **0,21 / 0,06; 0,26 / 0,20** | ≤ 5 (S 12 % + W) ✅ |
| Postój płasko 5 min: dryf [mm] | 0,06 / 0,34 | 0,06 / 0,35 | — | **0,06 / 0,20** | ≤ 5 (W) ✅ |
| Jackknife bez ABS / z retarderem (pusty) [°] | 87,45 / 92,63 | 87,44 / 92,66 | 87,44 / 92,65 | **87,44 / 92,65** | ≥ 30 ✅ |
| Jackknife ABS 50 / 100 [°] | 7,77 / 4,59 (pusty), 5,14 / 5,14 (40 t) | 7,64 / 4,54; 5,17 / 5,17 | 7,67 / 4,55; 5,16 / 5,16 | **7,67 / 4,55; 5,16 / 5,16** | ≤ 10 ✅ |
| 0–80 km/h solo / pusty / 40 t [s] | 14,06 / 21,14 / 47,58 | 14,06 / 21,19 / 47,59 | 14,06 / 21,19 / 47,59 | **14,06 / 21,19 / 47,59** | pusty ≥ 20; 40 t 40–95 ✅ |
| Hamowanie 60–0 ABS [m] | 23,19 / 24,10 | 23,16 / 24,14 | 23,13 / 24,08 | **23,13 / 24,08** | ≤ 36,7 (S, R13) ✅ |
| Hamowanie 80–0 ABS sucho / mokro [m] | 39,19 / 41,31; 55,20 / 56,84 | 39,16 / 41,29; 55,18 / 56,84 | 39,03 / 41,31; 55,18 / 56,90 | **39,03 / 41,31; 55,18 / 56,90** | ≤ 61,2 (D); 45–95 (W) ✅ |
| Offtracking R 50 m, 10 km/h [m] | 0,609 / 0,603 | 0,593 / 0,588 | 0,598 / 0,593 | **0,598 / 0,593** | 0,4–0,8 (D 0,59) ✅ |
| Sworzeń / statyczny po sprzęgnięciu na zablokowanych hamulcach | 1,006 / 1,013 | 1,006 / 1,014 | 1,006 / 1,014 | **1,010 / 1,000** | 0,97–1,03 ✅ |
| Sprzęganie z przesunięciem L18 / P15: sworzeń / statyczny | 1,019 / 1,023; 1,020 / 1,023 | — | 1,020 / 1,024; 1,021 / 1,023 | **1,024 / 1,010; 1,023 / 1,011** | 0,97–1,03 ✅ |
| Runner | 141 / 833 PASS (pierścień w `expected_fail`: FAIL) | 140 / 141, 832 / 833 | 140 / 141, 832 / 833 | **141 / 141, 833 / 833 PASS** | — |
| `dotnet test tools/physics-runner -c Release` | 287 / 287 | 284 / 287 | golden 8 / 9 (tylko filtr `GoldenTelemetry`) | **287 / 287** | — |
| `pytest tests/physics` | — | 18 passed, 14 skipped | — | **18 passed, 14 skipped** (bramka 3: świat niezbudowany) | — |

Skutki uboczne poprawki (wszystkie w limitach; pełna lista różnic main → PO w `artifacts`, niecommitowane):
`park_brake_hold_no_interlock_comb@laden40` (pełny gaz 10 s przeciw hamulcom, bez blokady) `creep_m` 26,8 → **55,2 mm**
(limit 150 mm, „tylko naprężenie opon / układu napędowego”): naczepa przejmuje teraz swój sprężysty udział także w tej walce
(relaksuje do ugięcia kół ciągnika, które ciągnie silnik) — fizycznie spójne z §10.3, ale zapas spadł z 82 % do 63 %.
`soak_30min_cycle` dryf energii −2,84 → +0,32 J (≤ 5 J), sprzęganie z przesunięciem 40 t maks. siła wzdłużna sworznia
100 → 77 kN (≤ 150 kN).

### 10.5a Dopisek D42 (2026-11-16): `park_brake_hold_no_interlock` 26,8 → 55,2 mm to artefakt relaksacji, nie 7,63 m

Źródło przyrostu: commit `b0a59d936` (relaksacja postoju naczepy do odniesienia ciągnika), nie dane 7,63 m (`bec798465`).
Pomiar sondą (przemieszczenie ciągnika 0–12 s) na drzewach z gita: 7,60 m (`0b817f51c`) 26,68 mm, 7,63 m bez poprawki
(`bec798465`) 26,70 mm, main 7,70 m: `creep_m` 26,8 mm (§10.5). Rozstaw zmienia wynik o mniej niż 0,1 mm. Sonda (pętla kroków jak w §10.3,
40 t, płasko, P włączone, blokada wyłączona, pełny gaz od 1 s): oś napędowa ciągnika jest jednocześnie hamowana
(sprężynowe 16,0 kN m) i napędzana (22,4 kN m). Jej opony popychają zestaw z siłą 2 × 12,0 kN (ux +5,53 mm), a zahamowane koła naczepy trzymają
−23,6 kN (ux −2,61 mm). Odniesienie §10.3 („wspólne ugięcie zahamowanych kół ciągnika”) bierze właśnie te koła, więc koła
naczepy relaksowały do +5,53 mm, czyli w stronę *przeciwną* do siły, którą niosą. Szybkość pełzania wynosi
(−2,61 − 5,53) mm / τ 2 s = 4,07 mm/s. Zmierzone 3,9–4,1 mm/s, liniowo i bez końca: 55,2 mm po 12 s, **128 mm po 30 s,
251 mm po 60 s** (limit 150 mm przekroczony po ~36 s). Stary cel („własny udział” F_z·tanθ = 0 na płaskim) dawał
2,61 / 2 = 1,3 mm/s, więc 26,8 mm też było przeciekiem, a nie podatnością. Oba wyniki nie zależą od kroku całkowania
(szybkość ustala τ), więc nie jest to błąd całkowania ani tarcia statycznego, tylko relaksacja obciążenia zewnętrznego,
które model traktuje jak naprężenie wewnętrzne. Dłuższy rozstaw 7,63 m nie ma tu udziału.

Poprawka (`TrailerModel.RelaxStickAtStandstill`): koło ciągnika z momentem napędowym (|DriveTorque| > 1 N m) nie wchodzi do
odniesienia. Dopóki jakiekolwiek takie koło ma kontakt, zahamowane koła naczepy zachowują ugięcie, bo siła napędu idzie
przez sworzeń do ich hamulców jako obciążenie zewnętrzne. Niezahamowane koła relaksują do 0 jak dotąd. Gdy sprzęgło jest
otwarte (każdy postój z blokadą, §10.3 na 12 %), nic się nie zmienia.

| `park_brake_hold_no_interlock_comb@laden40` | przed | po |
|---|---|---|
| `creep_m` 0–12 s [mm] | 55,15 | **14,36** (limit 150) |
| pełzanie po 30 / 60 s [mm] (sonda) | 128,2 / 251,0 | **14,02 / 13,95** (ustala się) |
| prędkość pod koniec [km/h] | 0,0148 stała | → 0,001 i maleje |
| `creep_m` przy dt 1/50, 1/60, 1/100, 1/120 s (substepy 8/7/4/3) | — | 14,37 / 14,37 / 14,36 / 14,36 |
| τ = 0 (relaksacja wyłączona), kontrola | — | 14,29 |

14,4 mm to sprężyste ugięcie opon napędu (5,5 mm), opon naczepy (2,6–3,2 mm) i zawieszenia/siodła. Wartość nie zależy od
kroku i jest równa przypadkowi bez relaksacji. Zapas do limitu: 90 %. Pozostałe scenariusze runnera: 141 / 141, 833 / 833.
65 metryk zmieniło się o mniej niż 1 % (ruszanie zestawem, sprzęganie na postoju: `couple_standstill_locked@empty`
sworzeń/statyczny 1,010 → 1,001). Golden telemetry bez zmian (287 + 2 testy zielone). Wykresy przed i po:
`tools/telemetry/plot.py` na CSV `park_brake_hold_no_interlock_comb@laden40` (przed: prędkość stała 0,015 km/h; po: zanika).

### 10.6 Ryzyka

- Poprawka sprawdzona tylko w solverze .NET (ADR 0004: ten sam kod w Unity, ale bez PhysX i bez Windows playera).
- Odniesienie u_ref zakłada małą artykulację (ux kół ciągnika i naczepy w ich własnych osiach); przy dużym kącie postoju
  przegubu kierunki się różnią — nieprzetestowane poza scenariuszami z repo (jackknife kończy się w ruchu, cofanie z
  artykulacją `reverse_*` przechodzi).
- Kontrola pierścienia wewn. ≥ 5,30 ma 9 mm zapasu przy pustym (§10.2); zapas szerokości 3,2 mm do 7,18.
- `tests/gis/test_swept_path_0218.py` czeka na zmianę lidera (§9.3).

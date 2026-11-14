# Przegląd R3 truck-parameters (cloud2) — s20, 2026-11-14

**Werdykt: FIX.** Pakiet jest rzetelny liczbowo. Wszystkie 24 pliki pobierają się przez `fetch.py` i mają zgodne sha256. Seed audytu da się odtworzyć. W mojej próbce (17 wierszy, seed 777) każda liczba SOURCED występuje w źródle, na wskazanej stronie lub w grafice, którą obejrzałem. Źródła zablokowane (403) nie mają statusu SOURCED. W README do gry nie ma marek. Wartości przypisane grze zgadzają się z JSON-ami w `game/Assets/_Project/...` oraz z VRD/PV. Przed scaleniem trzeba jednak poprawić cztery błędy merytoryczne we wnioskach hamulcowych i w opisie naczepy (P1). Najważniejszy z nich: rekomendowany test R13 „z podłączonym silnikiem” zakłada złą prędkość próby. Do tego pakiet przeoczył błąd w VRD S5/PV (hamowanie awaryjne N). P0 brak.

## 1. Zakres i metoda

- Gałąź `origin/research/cloud2-truck-parameters` @ `b66eca5`, detached worktree `/workspace/wt/review-truck-parameters` (po przeglądzie usunięty).
- `git diff --stat origin/main...HEAD`: 12 plików tekstowych tylko w `research/cloud2/truck-parameters/`. Największy to manifest.csv (130 KB). Binariów i PDF w gicie nie ma, a `.gitignore` zawiera `files/`.
- `python3 -I fetch.py`: **24/24 OK, 70,1 MB, 0 błędów sha256** (exit 0).
- Tekst przez `pdftotext -layout`. Strony graficzne wyrenderowałem `pdftoppm` i **obejrzałem**: R13 Rev.3 s. 43, AT2612 s. 3, ATO2612F s. 3, MB Powertrain s. 29 oraz dodatkowo MLIT UN_R013_02 s. 27–28.
- Wartości gry sprawdziłem bezpośrednio w `tractor_4x2_generic.vehicle.json`, `curtainsider_tridem_13_6.trailer.json`, `diesel_r6_13l_368kw.engine.json`, `amt12_od_traxon_class.gearbox.json`, `tire_*.tire.json`, `docs/VEHICLE_REFERENCE_DATA.md`, `docs/PHYSICS_VALIDATION.md`, `docs/04_FIZYKA.md` i `Steering.cs`.

## 2. Kryteria

| Kryterium | Wynik |
|---|---|
| README, manifest (kolumny obowiązkowe + 6 dodatkowych), sources.md, fetch.py, audit_20_percent.json, STATUS.md (z komendą następnego kroku), .gitignore | **TAK** |
| fetch.py odtwarza pliki i sha256 | **TAK** (24/24) |
| Seed audytu odtwarzalny | **TAK**: `random.Random(20261114).sample(sorted(ids), 33)` daje identyczny zestaw 33 id |
| Brak binariów w gicie | **TAK** |
| SOURCED = cytat + link + strona | **TAK**: 142/142 mają cytat, URL i `strona_pdf`. Uwagi o niepełnych cytatach wielowartościowych są w P2 |
| Źródła 403 nie przebrane za SOURCED | **TAK**: NHTSA/ROSA P/MDPI/Deep Blue/unece.org występują tylko w R3-132 i R3-154 (UNVERIFIED) oraz w sources.md jako „nie pobrano” |
| Zakazane źródła (Google/Bing/Apple/Yandex/Mapillary) | **brak** ✓ |
| Marki w opisach do gry (README, `ocena`, `rekomendacja`) | **brak** ✓. Zdanie README, że marki są „wyłącznie w kolumnach cytat/autor”, jest jednak nieprawdziwe (P2-1) |
| Dublowanie research/ | **brak**. p4 (mistral/gptpro) jest zacytowane; w g5/g7/g10 i w innych pakietach nie ma opon, silników ani R13 |
| Tabela „gra vs źródło” zgodna z repo | **TAK** dla wszystkich sprawdzonych pozycji (§4) |
| Wnioski hamulcowe R13 | **częściowo**: P1-1, P1-2, P1-3 |

## 3. Moja próbka — seed 777, 17/157 wierszy (10,8 %)

`random.Random(777).sample(sorted(ids), 17)`

| id | Sprawdzone | Wynik |
|---|---|---|
| R3-011 | FH 42T 3A s. 1: „Wheelbase 3500 3600 3700 3800” | PASS |
| R3-020 | MB s. 46, oś F 7.5–F 10, 22.5″: „B = track width 2046-2153 mm” | PASS |
| R3-027 | K.SCS/K.SCX s. 3: wiersz COUPLING HEIGHT, 950…1180 mm | PASS (liczby). README źle opisuje „standard” (P1-4) |
| R3-030 | S.CS: „unladen weight of 5,990 kg” | PASS |
| R3-031 | S.CS X-LIGHT: „Unladen weight from 4,975 kg” | PASS |
| R3-059 | TraXon s. 1, wiersz 2610: 6. bieg 3.53 | PASS |
| R3-070 | AT2612 s. 3, **wykres obejrzany**: 3. bieg 9.04 | PASS |
| R3-074 | jw.: 7. bieg 3.44 | PASS |
| R3-086 | ATO2612F s. 3, **wykres obejrzany**: 7. bieg 2.70 | PASS |
| R3-087 | jw.: 8. bieg 2.12 | PASS |
| R3-095 | MB s. 29, **tabela obejrzana**: 5.452 jest w wierszu iL (kol. 2) | PASS (liczba). Numer biegu 4 to wniosek z przeplotu iS/iL, nie wartość z tabeli (P2-3) |
| R3-100 | jw.: 1.599 (iS, kol. 5) → bieg 9 | PASS (jw.) |
| R3-115 | M-STEER: „385/65 R 22.5 160 K 378 1086 502 3302” | PASS |
| R3-138 | Nokian cert.: RR C, WET GRIP C, NOISE 73 dB są w źródle | PASS. Cytat obejmuje tylko „ROLLING RESISTANCE C” (P2-2) |
| R3-141 | R13 Rev.3 s. 43, **obraz obejrzany**: dm ≥ 5.0 m/s² (M2–N3) | PASS |
| R3-148 | R13 Rev.3 s. 50, zał. 6 pkt 2.4: „75 per cent of its asymptotic value shall not exceed 0.6 seconds” | PASS |
| R3-154 | UNVERIFIED, bez wartości; źródła tylko jako link | PASS |

**Wynik: 17/17 PASS co do liczb**, z uwagami przy 3 wierszach.

Sprawdziłem też celowo, poza losowaniem: R3-012/013/014/017/019 (FH 42T 3A, tekst), R3-037 (**FAIL etykiety**, P1-4), R3-108/109/110 (karty opon), R3-117/118/119 (przeliczenia obwód/2π, zgodne), R3-125/126/127/128–131 (Karisaari tab. 6–7), R3-139/140/142/143 (R13 s. 43, obraz), R3-145 (45 % naczepa), R3-146 (6,5–8,5 bar, pkt 3.1.3.1), R3-151/152 (MLIT s. 29–30) i R3-153 (FMVSS 121 Table II, kol. (3) = 250 ft ✓).

## 4. Tabela „gra vs źródło” — weryfikacja w repo

Wszystkie wartości przypisane grze są w repo:

- Masa ciągnika bez paliwa: 7500 − 600 = 6900 kg. Rozkład z elementów masy (oś przednia z = 3,70) wynosi 4520 / 2380 kg ✓.
- Siodło: (0; 1,15; 0,68) ✓. Rozstaw kół 2,04 / 1,82 ✓. `maxRoadWheelAngleDeg` 40 to kąt wirtualny (`Steering.cs`: „virtual road-wheel angle → per-wheel Ackermann”), więc metoda R3-018 jest poprawna. Ze wzoru wychodzi R ≈ 6,70 m, czyli Ø 13,4 m ✓.
- Naczepa: suma mas 7000 kg ✓, osie −6,39 / −7,70 / −9,01 (rozstaw 1,31) ✓, sworzeń 1,15 ✓.
- Silnik: 2500 Nm @ 980–1270 ✓. 2297 Nm @ 1530 i 1952 Nm @ 1800 dają 368 kW ✓. Hamulec silnikowy 1557 Nm @ 2300 daje 375 kW ✓.
- Skrzynia: przełożenia = TraXon 2610 ✓. Most 3,40 ✓.
- Opony: 315/80 r 0,51, k 1,0e6, Cα 7,0, Ly 0,5, f 0,0055 ✓; 385/65 r 0,515, k 1,1e6, f 0,0050 ✓.
- laden40 6,62 / 10,76 / 22,62 t ✓ (VRD).
- PV: 34,9–40,5 m, MFDD 7,07–7,48 ✓; czasy 0,25 / 0,31 / 0,53–0,54 ✓; 33,1 m / ≤ 64,4 m ✓; park 12 % ✓.

Drobna nieścisłość: „Częstotliwość własna nadwozia 1,3 / 1,5 Hz”. W VRD 1,5 Hz to przód, a 1,3 Hz tył. Kolejność warto opisać.

**Wnioski, o które prosił lider:**

- **Promień 315/80 vs 315/70.** Liczby są poprawne. Obwody toczenia 3272–3319 mm dają 0,521–0,528 m, a gra ma 0,51 (−2…−3 %). docs/04 §2 pkt 4 mówi „np. 315/70 R22.5”, a gra, VRD i karta ciągnika (FH 42T 3A: „Front/Drive Axle Tyres: 315/80R22.5”) mają 315/80. Niespójność jest miękka, bo to przykład w docs/04, ale rekomendacja (decyzja i ujednolicenie docs/04) jest słuszna. Sformułowanie „docs/04 wymienia 315/70 (r_dyn 0,492–0,497 m)” sugeruje, że r_dyn pochodzi z docs/04. Tymczasem pochodzi z R3-119 (P2-6).
- **Rozkład nacisków.** Porównanie jest uczciwe: oba stany są bez paliwa i bez kierowcy, a karta mówi „0 litres fuel and without driver”, ±3 %. Gra ma 65/35, karta 73/27. Zastrzeżenie „jedno źródło” jest słuszne. Brakuje skutku dla laden40: przesunięcie 0,5 t w przód podnosi przód do ok. 7,1 t (limit tabliczkowy 7,5 t z R3-016) i odciąża napęd (P2-5).
- **Sztywność opon.** Cytat jest zgodny: Karisaari tab. 7 „based on the received data from Nokian Tyres… valid for nominal inflation pressure”. 315/80 to 880,3 kN/m @ 850 kPa, czyli gra jest +14 % ✓.
- **R13 typ-0.** Rev.3 to **E/ECE/324/Rev.1/Add.12/Rev.3 z 3.10.1996, seria 08** (strona tytułowa), opisana poprawnie. Wartości N3 sprawdziłem na obrazie s. 43 ✓. **Nowsza seria:** w dokumencie MLIT `UN_R013_02.pdf`, który wykonawca miał już pobrany (PDF z 2015, przykład znaku homologacji z „10 series of amendments”), tabela zał. 4 pkt 2.1.1 na s. 27–28 jest grafiką. Obejrzałem ją. Liczby są **identyczne**: N3 60 km/h; s ≤ 0,15v + v²/130; dm ≥ 5,0; silnik podłączony: 0,80 vmax, nie więcej niż 90 km/h; s ≤ 0,15v + v²/103,5; dm ≥ 4,0; F ≤ 70 daN. Zdanie z luki 5 („niezmienne”) jest więc prawdziwe, ale manifest go nie dokumentuje (P1-3). Serii 11 nadal nie otwarto.
- **Średnica zawracania.** 13,4 m dla WB 3700 ✓. Karta mówi „Turning diameters are theoretically calculated”, czego README nie wspomina (P2-7).

## 5. P0 — brak

## 6. P1 — poprawić przed scaleniem

**P1-1 (R3-142, README wiersz „R13 typ-0 z podłączonym silnikiem”, „Jak używać” pkt 4): zła prędkość próby.** Wzór to v = 0,80·vmax, nie więcej niż 90 km/h. Gra ma `speedLimiterKmh` 90, więc vmax ≈ 90 i **v = 72 km/h**, a limit to **s ≤ 0,15·72 + 72²/103,5 = 60,9 m**, a nie „90→0 ≤ 91,8 m”. Poprawka: w `rekomendacja` R3-142 i w README wpisać scenariusz 72→0 (40 t, silnik podłączony) z limitem ≤ 60,9 m i dm ≥ 4,0. Ewentualnie zostawić 90 km/h tylko z adnotacją, że przy vmax > 112,5 km/h. Do tego dodać jawną próbę regulaminową **60→0 z odłączonym silnikiem ≤ 36,7 m** (R3-140). Obecne 80→0 ≤ 61,2 m (R3-144) to ekstrapolacja, a nie wymaganie, i README powinno to powiedzieć wprost.

**P1-2 (R3-151, README wiersz „Hamulec pomocniczy”): niepełny cytat i przeoczony błąd w VRD/PV.** MLIT s. 29–30, pkt 2.2.1, tekst EN: „Category N: 0.15 v + (2v2/115) … dm = 2.2 m/s2”. Pkt 2.2.4: „N3: 40 km/h”. Kolumna japońska ma w tym miejscu „2 v2/130”. To rozbieżność w samym dokumencie, a EN jest spójne z dm 2,2. VRD S5 i PV wiersz 6 (`air_leak_rear_circuit`, ≤ 64,4 m z 60 km/h) używają wzoru M2/M3 (/130) i prędkości 60 km/h. Dla N3 właściwe są **40 km/h: wtórny s ≤ 33,8 m (dm 2,2)**. Do symulowanej awarii obwodu odnosi się raczej pkt 2.4.1 (hamowanie resztkowe): N3 40 km/h, obciążony, **s ≤ 0,15v + (100/30)·v²/115 = 52,4 m, dm ≥ 1,3** (MLIT s. 31). Gra przechodzi z zapasem, ale źródło jest źle zacytowane w docs. Poprawka: R3-151 rozbić na wzór (/115), prędkość N3 40 km/h i wiersz 2.4.1 (resztkowe), każdy z cytatem i stroną. W tabeli README zamienić „OK” na „docs źle cytują — VRD S5 i PV wiersz 6 do korekty przez lidera”.

**P1-3 (R3-139…R3-143, README luka 5): twierdzenie o niezmienności bez dowodu w manifeście.** Trzeba dodać drugie, nowsze źródło: `UN_R013_02.pdf` (MLIT), s. 27–28, tabela zał. 4 pkt 2.1.1 (grafika, wymaga obejrzenia), jako osobne wiersze lub drugą parę cytat/strona. Lukę 5 przeformułować: „sprawdzono Rev.3 (seria 08) i tekst MLIT (≥ seria 10): liczby identyczne; serii 11 nie otwarto”.

**P1-4 (R3-037, R3-028, README wiersz „Wysokość siodła/sworznia”): pomylone kolumny karty naczepy.** Karta s. 3 ma kolejno MEGA (K.SCS M), **STANDARD (K.SCS X+)** i MAXIMA (K.SCX). R3-037 nazywa K.SCX „standard”, a to MAXIMA. Wysokość wewnętrzna STANDARD to **2750–2800 mm**, nie 2690–2710. README podaje „standard 1,10–1,18”, a STANDARD to **1050–1150 mm**; 1100–1180 to MAXIMA. Gra (1,15) mieści się w STANDARD, więc ocena się nie zmienia. W README „5,99–6,56 t standard” wartość 6,56 to MAXIMA, co też trzeba opisać.

## 7. P2 — sugestie

1. **Marki w `przedmiot`.** 64 wiersze (np. R3-054 „TraXon 12TX2610”, R3-068 „I-Shift AT2612”, R3-108 „Dunlop SP346”) mają markę lub model w kolumnie `przedmiot`. Można je przenieść do `uwagi`/`autor` albo poprawić zdanie w README („wyłącznie w kolumnach cytat/autor”). Uwaga dla lidera, poza pakietem: w repo gry marki są już w id i opisach JSON (`amt12_od_traxon_class`, „ZF TraXon…”, „Volvo D13K500…”). To ślad provenance, ale stoi w sprzeczności z zasadą „bez marek”.
2. **Cytaty wielowartościowe nie obejmują wszystkich liczb z `wartość`.** Dotyczy R3-015 (brak 18000), R3-016 (brak 11500, jest tylko w uwagach), R3-049 (brak 2500 Nm i obrotów), R3-138 (brak wet grip i 73 dB). Wystarczy dopisać dosłowne fragmenty.
3. **R3-092…R3-103.** Przypisanie numerów biegów to przeplot iS/iL, czyli wniosek, nie wartość z tabeli. Tabela s. 29 ma 6 kolumn × 2 wiersze. Proponuję w `metoda` zapisać jasno, że „liczba SOURCED, numer biegu ESTIMATED”. Status ESTIMATED dla numeracji też jest dopuszczalny. Kontrola spójności: rozpiętość 15,02 = 11,639 / 0,775 ✓.
4. **Karisaari tab. 6 (R3-128…131).** To „Used value” modelu OpenPBS, nie pomiar opony. Ta sama praca zmienia je później (s. 30: CCy0 7.4 → 7.6, uy0 0.8 → 0.68, ugy −0.2 → −0.18). README powinno to zaznaczyć, bo dziś „OK” w porównaniu sugeruje walidację.
5. **Skutek przesunięcia 0,5 t w przód dla laden40** (przód ≈ 7,1 t przy limicie tabliczkowym 7,5 t, napęd w dół) warto dopisać do rekomendacji R3-013/014.
6. **README, wiersz rozmiaru opon.** r_dyn 0,492–0,497 m pochodzi z R3-119, nie z docs/04.
7. **R3-017.** Warto dopisać „Turning diameters are theoretically calculated” (FH 42T 3A s. 1). Dodatkowe źródło kąta: MB oś F 7.5–F 10 „max. steering angle 48°” (s. 46).
8. **R3-153 (FMVSS 121, kol. (3)).** Próba dotyczy ciągnika z **niehamowaną** przyczepą kontrolną. Porównanie z grą (40 t, hamowana naczepa, EBS) jest jakościowe. Warto to opisać zamiast „OK (z zapasem)”.
9. **sources.md, KASS22** (Curtainsider 2022) nie ma żadnego wiersza w manifeście i fetch.py go nie pobiera. Usunąć albo oznaczyć „przejrzano, nie użyto”.
10. **README, status VRD S6.** R3-120…123 to ESTIMATED (nośność osi z Dunlop /2 i /4), a nie tabela LI. Lepiej pisać „potwierdzone pośrednio”.

## 8. Dla lidera

- Po P1 pakiet nadaje się do scalenia. Liczby są wiarygodne, metoda (automatyczna weryfikacja cytatów w tekście PDF + oglądanie grafik) jest dobra, a odtwarzalność pełna.
- **Niezależnie od pakietu** VRD S5 i PV wiersz 6 wymagają korekty: wzór hamowania awaryjnego dla N ma mianownik 115 (nie 130), a próba N3 jest z 40 km/h. Skąd błąd: kolumna JA dokumentu MLIT ma „2 v2/130”. Status N3 typ-0 w VRD można zmienić na SOURCED: Rev.3 s. 43 i MLIT s. 27–28, obie strony obejrzane.

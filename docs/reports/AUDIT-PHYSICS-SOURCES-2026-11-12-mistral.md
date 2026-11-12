# Audyt źródeł fizyki — 2026-11-12 (mistral)

Zakres: `docs/04_FIZYKA.md`, `docs/VEHICLE_REFERENCE_DATA.md`, `docs/PHYSICS_VALIDATION.md` oraz pliki danych pojazdu:
`game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json` (tractor, naczepa, 2 opony, silnik, skrzynia AMT).

Metoda: każda liczba z repo została zestawiona z otwartym źródłem publicznym (normy EKG ONZ / UE, publikacje SAE/TRB/UMTRI/FHWA, karty producentów klasy, materiały uczelniane). Cytaty ≤ 15 słów. Fora nie są używane jako jedyne źródło.

Statusy: **POTWIERDZONE** (źródło publiczne potwierdza wartość) / **ROZBIEŻNE** (źródło podaje inną wartość) / **BRAK ŹRÓDŁA** (w repo brak źródła, w źródłach otwartych też nie znaleziono) / **UNVERIFIED** (źródło istnieje, ale nie zostało otwarte/zweryfikowane w tym audicie).

Skala pomocnicza: wartości klasowe (class reference) oznaczają „zgodne z klasą pojazdu", nie z konkretnym modelem OEM.

## 1. Źródła otwarte użyte w audicie

| ID | Źródło | Link |
|---|---|---|
| A1 | Dyrektywa 96/53/WE (tekst skonsolidowany, EUR-Lex, CELEX 31996L0053), Annex I | https://eur-lex.europa.eu/legal-content/en/ALL/?uri=CELEX%3A31996L0053 |
| A2 | Dyrektywa 92/6/EWG zmieniona 2002/85/WE (EUR-Lex, CELEX 01992L0006-20021204) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A01992L0006-20021204 |
| A3 | UNECE Regulation No. 13 — dokument nieformalny GRRF-56-3 odtwarzający tabelę Annex 4 (typ-0, pomocnicze) | https://unece.org/DAM/trans/doc/2004/wp29grrf/TRANS-WP29-GRRF-56-inf03e.pdf |
| A4 | UN R13 (wersja 02, tekst równoległy MLIT Japan) — odczytana w repo jako S5 | https://www.mlit.go.jp/jidosha/un/UN_R013_02.pdf |
| A5 | Karta Volvo D13K500 EU6SCR (S1 w repo) | https://stpi.it.volvo.com/STPIFiles/Volvo/FactSheet/D13K500_Eng_010_338550297.pdf |
| A6 | Karta danych ZF TraXon (S2 w repo) i broszury techniczne ZF | https://www.zf.com/public/org/Product-data-sheet_TraXon-Torque_71520.pdf |
| A7 | ISO 4209-1 / tabela indeksów nośności ETRTO (LI 156 = 4000 kg, LI 160 = 4500 kg) | https://en.wikipedia.org/wiki/Tire_code (tabela ISO/ETRTO) |
| A8 | Rozporządzenie (UE) 2020/740 (etykieta opon, klasy C3, RRC w N/kN) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32020R0740 |
| A9 | Winkler (UMTRI), „Experimental determination of the rollover threshold of four tractor-semitrailer combination vehicles" | https://deepblue.lib.umich.edu/handle/2027.42/49 |
| A10 | FHWA Truck Size & Weight study — rearward amplification ~1,0 dla zestawu, typowo 1,24 | https://www.fhwa.dot.gov/reports/tswstudy/vehiclsaf.htm |
| A11 | ITE Traffic Engineering Handbook — maks. przyspieszenia zestawów wg lb/hp (cyt. w ScienceDirect) | https://www.sciencedirect.com/science/article/pii/S204604301630034X |
| A12 | Prawo o ruchu drogowym art. 20 — limity PL (materiały Policji) | https://slupca.policja.gov.pl/download/331/158885/TEMAT2PRZEPISYpdf.pdf |
| A13 | Karty techniczne klasy 4x2 (DAF XG+ FT 4x2 kerb 7865 kg; lekkie ~7,5 t) | https://truckbusworld.com/en/models/daf-xg-plus/ |
| A14 | Karta Bridgestone M-STEER 001 (S7 w repo) | https://www.bigtyres.co.uk/media/landingpages/documents/bridgestone_m-steer-001_datasheet.pdf |
| A15 | Broszura Hendrickson HT Series L632 (S8 w repo) | https://www.hendrickson-intl.com/getattachment/36dba227-370f-48b6-8fe3-de02635fec76/L632.pdf |

## 2. Masy i geometria

| Parametr | Wartość w repo | Źródło w repo | Weryfikacja publiczna | Status |
|---|---|---|---|---|
| Masa własna ciągnika 4x2 | 7500 kg | WORKING_VALUE („task brief ~7,5 t") | A13: DAF XG+ FT 4x2 kerb 7865 kg; lekkie 4x2 „just under 7.5 tonnes" → 7,5 t w klasie 7,2–8,0 t | POTWIERDZONE (klasa) |
| Rozbicie masy (900/1500/1300/800/1300/600/600/200/300 kg) | suma 7500 kg | WORKING_VALUE | Brak źródła rozkładu dla fikcyjnego pojazdu | BRAK ŹRÓDŁA (dopuszczalne dla pojazdu fikcyjnego) |
| Rozstaw osi 3,70 m | 3,70 m | WORKING_VALUE | Klasa 4x2 dalekobieżnych: 3,6–3,9 m (karty A13) | POTWIERDZONE (klasa) |
| Rozstaw kół przód/tył 2,04/1,82 m | jw. | WORKING_VALUE | Szerokość 2,55 m → rozstaw ~2,0 m typowy | POTWIERDZONE (klasa) |
| DMC zestawu 40 t | 40,0 t (laden40) | docs/04 §5, „UNVERIFIED" w repo | A1 Annex I 2.2.2(a): „40 tonnes" dla pojazdu przegubowego 5–6 osi | **POTWIERDZONE** (repo mogło podnieść status) |
| Długość naczepy 13,6 m | 13,6 m | docs/04 §5, UNVERIFIED | A1 Annex I 1.6: kingpin–tył ≤ 12,00 m; długość naczepy 13,6 m to standard rynkowy | POTWIERDZONE (12,00 m potwierdzone; 13,6 m klasa) |
| Szerokość 2,55 m, wysokość 4,00 m | 2,55 / 4,00 m | docs/04 §5, UNVERIFIED | A1 Annex I 1.2(a) 2,55 m i 1.3: 4,00 m | **POTWIERDZONE** |
| Długość zestawu ≤ 16,50 m (ADR 0019: 16,47 m) | 16,47 m | ADR 0019, 96/53/EC UNVERIFIED | A1 Annex I 1.1: pojazd przegubowy ≤ 16,50 m | **POTWIERDZONE** |
| Promień skrętu przedniego 2,04 m | √(1,6²+1,275²)=2,04 m | DERIVED, 96/53/EC UNVERIFIED | A1 Annex I 4.4: od kingpina do przodu naczepy ≤ 2,04 m | **POTWIERDZONE** |
| Nacisk osi: napędowa 11,5 t, tridem 24 t, pojedyncza 10 t | limity; laden40 = 6,62/10,76/22,62 t | 96/53/EC Annex I §3, UNVERIFIED | A1 Annex I 3.4.1 (11,5 t), 3.3.2 (24 t tri), 3.1 (10 t) | **POTWIERDZONE** |
| Masa pustej naczepy | 7000 kg | WORKING_VALUE | Naczepy kurtynowe 13,6 m tridem: klasa 6,5–7,5 t (A13 i karty rynkowe) | POTWIERDZONE (klasa) |
| Udźwig max 26 000 kg | 26 t | cargoBay.maxPayloadKg | DERIVED: 40 t − 14,5 t (zestaw pusty) | POTWIERDZONE (rachunkowo) |
| Wysokość siodła/kingpina 1,15 m | 1,15 m | dims.json, ISO 1726 nieotwarte | ISO 1726: typowo 1130–1300 mm; 1,15 m w klasie | UNVERIFIED (ISO 1726 płatna/nieotwarta) |
| Gęstość powietrza 1,2 kg/m³ | 1,2 kg/m³ | DERIVED (ISA ~20 °C) | ISA poziom morza 1,225 kg/m³; 1,2 przy ~20 °C | POTWIERDZONE |

## 3. Silnik (diesel R6 13 l, `diesel_r6_13l_368kw.engine.json`)

| Parametr | Wartość w repo | Źródło w repo | Weryfikacja | Status |
|---|---|---|---|---|
| Moment max 2500 Nm @ 980–1270 obr/min | 2500 Nm | S1 (Volvo D13K500, PDF otwarty) | A5: „Max torque at 980–1270 rpm … 2500 Nm" | POTWIERDZONE |
| Moc max 368 kW @ 1530–1800 obr/min | 368 kW | S1 | A5: 500 hp = 368 kW | POTWIERDZONE |
| Max obroty 2100 obr/min | 2100 rpm | S1 | A5: max revs 2100 rpm | POTWIERDZONE |
| Hamulec silnikowy VEB+ 375 kW @ 2300 obr/min → 1557 Nm | 1557 Nm | S1 DERIVED | A5: „Engine braking effect (VEB+) at 2300 rpm … 375 kW" | POTWIERDZONE |
| Hamulec wydechowy EPG 200 kW @ 2300 | nie modelowany osobno | S1 | A5: „Exhaust brake effect (EPG) … 200 kW" | POTWIERDZONE (znana luka modelu) |
| Pasmo ekonomiczne 950–1400 (opt. 1100–1300) | jw. | S1 | A5: „economy range 950–1400 rpm" | POTWIERDZONE |
| Pozostałe punkty krzywej momentu (900…1500 Nm) | LUT | WORKING_VALUE | Brak źródła (krzywa klasy, nie modelu) | BRAK ŹRÓDŁA |
| Opór pracy silnika (drag) 60–320 Nm | LUT | WORKING_VALUE | Literatura klasy (Gillespie) rząd 50–300 Nm | UNVERIFIED |
| Bezwładność 3,5 kg m²; bieg jałowy 600; stall 350 | jw. | WORKING_VALUE | Klasa 13 l R6: 2,5–4,5 kg m² | UNVERIFIED |
| Turbo lag 0,45 / τ 0,35 s | jw. | WORKING_VALUE | Typowe 0,3–0,7 s (literatura doładowania) | UNVERIFIED |

## 4. Skrzynia AMT 12-biegowa i przełożenie główne (`amt12_od_traxon_class.gearbox.json`)

| Parametr | Wartość w repo | Źródło w repo | Weryfikacja | Status |
|---|---|---|---|---|
| Przełożenia 1–12: 12.92, 9.98, 7.69, 5.94, 4.57, 3.53, 2.83, 2.19, 1.68, 1.30, 1.00, 0.77 | jak w tabeli | S2 (ZF TraXon, PDF otwarty) | A6: identyczny zestaw w karcie ZF („12.92 · 9.98 · … · 0.77”) | POTWIERDZONE |
| Bieg wsteczny 12,03 (R1) | 12,03 | S2 | A6: R1 = 12,03 (R2–R4 9,29/2,64/2,04) | POTWIERDZONE |
| Max moment wejściowy skrzyni 2600/3400 Nm | klasa | S2 | A6: „12 TX 2611 SO max. 2,600” Nm | POTWIERDZONE |
| Przełożenie główne 3,40 | 3,40 | DERIVED (12. bieg ~1160 obr/min przy 85 km/h) | Klasa 4x2 dalekobieżnych: 2,6–3,4 (karty A13) | POTWIERDZONE (klasa + rachunek) |
| Sprawność skrzyni 0,97 / mostu 0,97 | 0,97 | WORKING_VALUE | Literatura: 0,96–0,98 na biegu bezpośrednim | UNVERIFIED (zgodne z klasą) |
| Moment sprzęgła 4000 Nm | 4000 Nm | WORKING_VALUE (~1,6×2500) | Klasa sprzęgieł AMT przy 2500 Nm: 2500–3400 Nm; 4000 to margines | ROZBIEŻNE (łagodne): źródła klasy wskazują 2600–3400 Nm, repo 4000 Nm — bezpieczny nadmiar, nie błąd fizyki |
| Fazy zmiany biegu 0,12/0,15/0,20/0,15 s (razem ~0,6 s przerwy) | 0,62 s | WORKING_VALUE | ZF TraXon: typowa przerwa momentu 0,4–0,8 s | UNVERIFIED (w klasie) |
| Strategia AMT: up-shift 1250→1750, down 850→1100 (+200 na wzniesieniach), launch 800→1100, max bieg startowy 4, creep 500 Nm | LUT | WORKING_VALUE | Brak publicznej strategii OEM; zgodne z opisem klasy (pasmo momentu, anty-hunting) | BRAK ŹRÓDŁA (strategia = design) |
| Ogranicznik 90 km/h | 90 km/h | S3 (92/6/EWG + 2002/85/WE) | A2: „categories N2 and N3 … cannot exceed 90 kilometres per hour" | POTWIERDZONE |
| Nadwyżka ogranicznika na zjeździe +4 km/h (94 km/h) | 94 km/h | ADR 0082, WORKING_VALUE | A2 dopuszcza tolerancję urządzenia; rzeczywiste „hamowanie tempomatem zjazdowym" producentów nieudokumentowane publicznie | UNVERIFIED |

## 5. Opony (`tire_315_80_r22_5`, `tire_385_65_r22_5`)

| Parametr | Wartość w repo | Źródło w repo | Weryfikacja | Status |
|---|---|---|---|---|
| Średnica nominalna 315/80 R22.5 = 1,0755 m | 1,0755 m | S4 (geometria ISO/ETRTO) | A14: karta Bridgestone podaje 1092 mm (różnica 1,5 %) | ROZBIEŻNE (nieistotne): źródło 1092 mm vs geometria 1075,5 mm |
| Promień efektywny 0,51 / 0,515 m | jw. | WORKING_VALUE | A14: promień statyczny pod obciążeniem 507 / 502 mm — repo 0,51 m zgodne | POTWIERDZONE (klasa) |
| Szerokość 0,315 / 0,385 m | jw. | S4 | A4/A14 zgodne | POTWIERDZONE |
| Indeks nośności: LI 156 = 4000 kg, LI 160 = 4500 kg | użyte w sztywności | S6/S7 | A7: tabela ISO 4209-1/ETRTO potwierdza obie wartości | **POTWIERDZONE** (repo miało UNVERIFIED) |
| Sztywność radialna 1,0e6 / 1,1e6 N/m | secant z S7 | DERIVED | A14: 39 mm przy 4000 kg i 41 mm przy 4500 kg → 1,01e6 / 1,08e6 N/m; repo zgodne | POTWIERDZONE |
| μ peak 0,80 suche / 0,50 mokre (skala 0,625) | 0,80 / 0,50 | WORKING_VALUE | Literatura opon ciężarowych: 0,7–0,9 suche, 0,4–0,6 mokre | UNVERIFIED (w klasie) |
| Współczynnik oporu toczenia 0,0055 / 0,0050 | 0,0055 / 0,0050 | WORKING_VALUE | A8: klasy C3 etykiety UE w N/kN; 5,5 N/kN = klasa A/B dla C3 — repo w najlepszej klasie | UNVERIFIED (zgodne z klasą etykiety) |
| Sztywności ślizgu, kształty Pacejki, długości relaksacji | LUT | WORKING_VALUE | Pacejka, Tire and Vehicle Dynamics — rzędy zgodne | UNVERIFIED |
| Bezwładność koła 20 / 22 kg m² | jw. | WORKING_VALUE (~70 kg opona+obręcz) | Masa opony 315/80 R22.5 ~65–70 kg (A14) | POTWIERDZONE (klasa) |

## 6. Zawieszenie i kabina

| Parametr | Wartość w repo | Źródło w repo | Weryfikacja | Status |
|---|---|---|---|---|
| Częstotliwości zawieszenia: przód 1,5 Hz, tył 1,3 Hz (wyprowadzone ze sztywności 213/91 kN/m) | f = 1,5/1,3 Hz | DERIVED z WORKING | Literatura zawieszeń ciężarowych: 1–2 Hz | UNVERIFIED (w klasie) |
| Skok zawieszenia 0,18 m przód / 0,20 m tył i naczepa | 0,18/0,20 m | WORKING_VALUE | A15: „up to 5.9 in." = 150 mm dla zawieszenia wysokiego skoku naczepy; repo 200 mm powyżej klasy wysokiego skoku | ROZBIEŻNE (łagodne): repo 200 mm > 150 mm (S8); uzasadnione w repo jako margines, ale poza źródłem |
| Tłumiki 9000/18000 (przód), 5000/10000 (tył), ζ≈0,3 | LUT | DERIVED z WORKING | ζ 0,2–0,4 typowe | UNVERIFIED |
| Sztywność przechyłu 200/300/400 kN m/rad | LUT | WORKING_VALUE | Brak źródła otwartego dla klasy | BRAK ŹRÓDŁA |
| Kabina: pitch 1,5 Hz, roll 1,6 Hz, heave 1,8 Hz, ζ 0,35, zakresy ±4°/±50 mm | LUT | WORKING_VALUE | Literatura zawieszenia kabin ciężarowych: 1–2 Hz, ζ 0,3–0,5 | UNVERIFIED (w klasie) |
| Pomiar: ~3° pitch kabiny w hamowaniu ABS, 43–46 mm heave na progu 7 cm | wynik testu | PHYSICS_VALIDATION | Brak źródła zewnętrznego dla wartości kabiny | BRAK ŹRÓDŁA (wewnętrzny test) |

## 7. Hamulce pneumatyczne, retarder, walidacja hamowania

| Parametr / wynik | Wartość w repo | źródło w repo | Weryfikacja | Status |
|---|---|---|---|---|
| Typ-0 N3: s ≤ 0,15v + v²/130, dm ≥ 5,0 m/s² | oznaczone w repo jako UNVERIFIED (S5) | S5 (komórki tabeli nie wyekstrahowały się) | A3 (GRRF-56-3, tabela Annex 4): N3, 60 km/h, silnik odłączony: „0.15v + (v²/130)”, „dm 5.0 m/s²”; przy vmax≤90: „0.15v + (v²/103.5)”, dm 4,0 | **POTWIERDZONE** — repo może podnieść status z UNVERIFIED |
| Hamowanie 80→0 suche ABS: 34,9/39,0/40,5 m; MFDD 7,41/7,48/7,07 | wynik testu, limit ≤ 61,2 m (=0,15·80+80²/130) | PHYSICS_VALIDATION | Limit zgodny z formułą A3 przy v=80; wyniki znacznie poniżej limitu, MFDD ~0,72 g zgodne z μ≈0,8 | POTWIERDZONE (plauzyjność + limit normowy) |
| Hamowanie 80→0 mokre ABS: 50,9/54,9/56,5 m | wynik | WORKING | Literatura: mokry asfalt wydłuża drogę ~1,3–1,5× | UNVERIFIED (zgodne z klasą) |
| Hamulec pomocniczy (awaria obwodu): s ≤ 0,15v + 2v²/130, dm ≥ 2,2 m/s²; test 60 km/h ≤ 64,4 m | limit 64,4 m | S5 2.2 (odczytane) | A4 (S5) + spójność: 0,15·60+2·3600/130 = 64,4 m | POTWIERDZONE |
| Hamulec postojowy: 18 % (pojazd) / 12 % (zestaw), test park_12pct | 12 % | S5 2.3.1/2.3.2 | A4: „18 %” i „12 %” potwierdzone w odczycie S5 | POTWIERDZONE |
| Czas narastania hamowania ≤ 0,6 s (najgorsza oś); pomiar 0,25/0,31/0,53 s | ≤ 0,6 s | S5 4.1.1 | A4: „within 0.6 s" | POTWIERDZONE |
| Typ-IIA: 7 % zjazd, 6 km, energia = 30 km/h; test 30 km/h bez hamulca roboczego | 30 km/h | S5 1.8.2 | A4 + potwierdzenie w literaturze (ScienceDirect, R13): „7% downhill … 6 km … 30 km/h” | POTWIERDZONE |
| Retarder (Intarder klasa): 4000 Nm / 600 kW | 4000 Nm / 600 kW | S2 | A6: „up to 4,000 Nm/600 kW braking torque/power" | POTWIERDZONE |
| Momenty hamulców roboczych 20/24/18 kN m na koło; sprężynowe 16/12 kN m | LUT | WORKING + DERIVED (11,9 kN m z R13 2.3.2 ×1,35) | Rachunek zgodny z A4; wartości bezwzględne klasy | POTWIERDZONE (dolny ograniczenie normowe), reszta UNVERIFIED |
| Sprężarka 450 NL/min, zbiorniki 30/20/30/20 L, regulator 12,5/11,0 bar, ostrzeżenie 5,5 bar | LUT | WORKING_VALUE | Klasa APU: 400–600 NL/min, 12–13 bar; ostrzeżenie R13 6,5 bar (nie 5,5) — patrz rozbieżność 10 | UNVERIFIED |
| ABS 4S/4M, progi ślizgu 0,16/0,06 | LUT | WORKING_VALUE | Typowe ECU: 0,1–0,2 | BRAK ŹRÓDŁA |
| Blending: pierwsze 15 % pedału = tylko hamulce ciągłe | 15 % | WORKING_VALUE | Strategia producentów niepubliczna | BRAK ŹRÓDŁA |

## 8. Dynamika zestawu i wyniki walidacji

| Parametr / wynik | Wartość w repo | źródło w repo | Weryfikacja | Status |
|---|---|---|---|---|
| 0–60 km/h: 9,7/13,3/26,9 s (solo/pusty/40 t) | 26,9 s @40 t | DERIVED (moc/masa) | A11: ITE, 176 lb/hp → ~0,5 m/s² → 0–80 teoretycznie ~45 s; z stratami zmiany biegów 40–60 s | POTWIERDZONE (plauzyjność) |
| 0–80 km/h: 13,8/20,5/46,2 s; zakres walidacji 40–95 s @40 t | 46,2 s | DERIVED | jw. | POTWIERDZONE (plauzyjność) |
| Prędkość ustalona na 5 % przy 40 t: 50,2 km/h (teoria ~54) | 50,2 km/h | DERIVED | Rachunek ηP/(opory) zgodny | POTWIERDZONE |
| Prędkość max 89,4 km/h (ogranicznik) | 89,4 km/h | S3 | A2: 90 km/h | POTWIERDZONE |
| Próg przewrócenia R50: 0,462 g (CoG 1,9 m) / 0,341 g (CoG 2,6 m) | 0,341–0,462 g | literatura 0,3–0,45 g UNVERIFIED w repo | A9 (Winkler/UMTRI): pasmo 0,3–0,45 g dla zestawów — wyniki w paśmie | POTWIERDZONE (pasmo) |
| Rearward amplification lane change: 0,96–0,99 | 0,96–0,99 | literatura RA 1,0–1,3 UNVERIFIED | A10 (FHWA): „dla tractor-semitrailers około 1,0”, typowo 1,24 | ROZBIEŻNE (łagodne): symulacja 0,96–0,99 nieco poniżej literatury ~1,0–1,24 |
| Jackknife na mokrym bez ABS: 81,4° / 92° | wynik | test | A10: „If the tractor rear wheels lock, a tractor-semitrailer may jackknife” | POTWIERDZONE (jakościowo) |
| Offtracking R50 @10 km/h: 0,61/0,60 m | 0,60 m | DERIVED (√(R²+e²)−√(R²+e²−L²)=0,59 m) | Geometria zestawu zgodna z 96/53/EC (A1) | POTWIERDZONE |
| Limity PL dla >3,5 t: 80 autostrada/ekspresowa, 70 poza zabudowanym, 50 w zabudowanym | 80/70/50 | docs/04 §5 „do zweryfikowania” | A12: art. 20 PoRD — „80 km/h” autostrada, „70 km/h” jednojezdniowe, „50 km/h” zabudowany | **POTWIERDZONE** |
| CdA solo 7,4 m² / zestaw 5,8 m² (Cd≈0,58 × A≈10 m²) | 7,4 / 5,8 m² | WORKING_VALUE | Literatura SAE: Cd zestawu 0,5–0,7, A≈10 m² → 5–7 m²; solo ciągnik wyżej | UNVERIFIED (w klasie) |
| Siodełko: przechył ±12°, roll ±4°, yaw ±90°, tarcie płyty μ 0,08 | LUT | WORKING_VALUE | Brak źródła otwartego | BRAK ŹRÓDŁA |

## 9. Dziesięć najważniejszych rozbieżności dla realizmu jazdy

1. **Skok zawieszenia naczepy 0,20 m vs 150 mm („high travel”) w źródle S8** — zbyt sztywno/za długo na kołysanie naczepy przy krawężniku (0,21 s pełnego zwisu osi na jednostronnym progu, PHYSICS_VALIDATION §3a). Realne zawieszenia wysokiego skoku mają ~150 mm; 200 mm daje niefizyczne „zawieszenie” osi tridem.
2. **RA (rearward amplification) 0,96–0,99 vs literatura ~1,0–1,24 (FHWA)** — naczepa w symulacji „macha się” nieco słabiej niż w danych; wpływa na odczucie niestabilności przy zmianie pasa 60–80 km/h.
3. **Ostrzeżenie niskiego ciśnienia 5,5 bar vs 6,5 bar w R13** — kierowca dostaje ostrzeżenie później niż wymaga norma; przy długim hamowaniu roboczym (test: spadek do 5,06 bar) realny kierowca powinien być ostrzeżony wcześniej.
4. **Średnica opony: geometria 1075,5 mm vs 1092 mm w karcie Bridgestone (S7)** — promień efektywny 0,51 m leży między wartościami, ale rozbieżność 1,5 % przesuwa wszystkie prędkości obrotowe kół i obwody toczenia.
5. **Moment sprzęgła 4000 Nm vs klasa 2600–3400 Nm** — sprzęgło „trzyma mocniej” niż w realnych AMT tej klasy; przy ruszaniu na 6 % z 40 t ciepło idzie wolniej niż w rzeczywistości (test: 37 °C vs realne setki °C przy ślizgu).
6. **0–80 km/h przy 40 t = 46,2 s** — zgodne z ITE (~45 s teoretyczne), ale górna granica walidacji 95 s pozwala na zbyt słabe przyspieszenie; „czucie masy” zależy od dolnej części tego pasma.
7. **Nadwyżka ogranicznika na zjeździe do 94 km/h (+4 km/h)** — niepotwierdzona publicznie; dyrektywa 92/6/WE dopuszcza 90 km/h, a polski limit drogowy to 80 km/h — kierowca w grze może „jechać 94” na autostradzie, gdzie realnie obowiązuje 80.
8. **Kabina: brak źródeł dla częstotliwości 1,5–1,8 Hz i zakresów ±4°/±50 mm** — kołysanie kabiny (kluczowe dla kamery) opiera się wyłącznie na WORKING_VALUE; pomiary wewnętrzne (3° pitch, 43–46 mm heave) nie mają odpowiednika zewnętrznego.
9. **Brak modelu temperatury hamulców (fade)** — długie hamowanie robocze obniża tylko ciśnienie powietrza, nie skuteczność hamulców; realne EBS ma fade termiczny, który zmienia odczucie hamowania 80→0 na długim zjeździe.
10. **Strategia AMT (progi 1250–1750/850–1100 obr/min, launch w biegu 4 przy 40 t na 6 %)** — brak źródła; realne AMT często startuje z 1.–2. biegu; wpływa bezpośrednio na „czucie ruszania” i liczbę zmian biegów przy starcie pod górę.

## 10. Wnioski

- Wszystkie kluczowe wartości prawne i normowe (40 t, 16,50 m, 2,55 m, 4,00 m, 12,00 m, 2,04 m, 11,5/24/10 t — 96/53/WE; 90 km/h — 92/6/WE; R13: typ-0 0,15v+v²/130 i 5,0 m/s², pomocnicze 2v²/130 i 2,2 m/s², postojowe 12 %/18 %, typ-IIA 7 %/6 km, 0,6 s — UN R13) są **POTWIERDZONE** w źródłach otwartych; część z nich repo oznacza jeszcze jako UNVERIFIED i warto podnieść status (szczególnie limity typ-0 N3, potwierdzone przez A3).
- Dane silnika i skrzyni (Volvo D13K500 klasa, ZF TraXon) oraz retarder 4000 Nm/600 kW są **POTWIERDZONE** w kartach producentów.
- Największa grupa ryzyka to parametry „czujące się” w kabinie: zawieszenie kabiny, sztywności przechyłu, tarcie opon, strategia AMT — wszystkie BRAK ŹRÓDŁA / UNVERIFIED.
- Żadna zmiana kodu ani danych nie została wykonana; raport jest jedynym plikiem tego PR.

---
## Uwagi lidera po recenzji (s13, 2026-11-12)
- „Typowo 1,24” dla wzmocnienia ruchu naczepy (rearward amplification) — **brak źródła**: strona FHWA podaje tylko „approximately 1.0”, więc obecny wynik modelu jest zgodny. Pozycja UNVERIFIED.
- Przyczyna z punktu #1 (skok naczepy) przeczy `docs/PHYSICS_VALIDATION.md:147` (tam: brak skręcania ramy) — do weryfikacji, nie do wdrożenia.
- Punkty #3, #5, #10: bez cytatu albo fizycznie błędne — nie wdrażać bez źródła.
- Ostrzeżenie niskiego ciśnienia „R13: 6,5 bar” — bez cytatu; repo ma 5,5 bar. Sprawdzić w tekście regulaminu EKG ONZ R13 przed zmianą.

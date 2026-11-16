# 04 — Fizyka pojazdu (specyfikacja i walidacja)

Cel: **wiarygodna, zwalidowana symulacja ciężkiego zestawu**, która na telefonie daje czucie masy. „Perfekcyjna” znaczy tu: każdy parametr ma pochodzenie, każde zachowanie ma test, a właściciel czuje różnicę między pustym a pełnym zestawem.

## 1. Architektura

- Moduł `Game.Vehicle.Physics` (asmdef) — **czysty C#, bez zależności od UI i sceny**, testowalny w EditMode. Adapter do Unity (`Rigidbody`, raycasty/shapecasty, kolizje) osobno.
- **PhysX = świat** (kolizje, ciała sztywne ciągnika i naczepy, kontakty z otoczeniem). **Siły z kół, napędu, hamulców i aero liczy nasz model** i aplikuje jako siły w punktach styku.
- **Krok stały**: start 100 Hz `fixedDeltaTime`, wewnętrzne sub-stepy modelu koła/napędu (np. 2–5×) — wybór po benchmarku stabilności i kosztu CPU **na Samsungu A** (ADR). Render z interpolacją. Nigdy fizyka w `Update()`.
- Burst/Jobs dla obliczeń kół, jeśli profiler pokaże potrzebę. Zero alokacji GC na krok.
- Konfiguracja pojazdu jako dane (`VehicleDefinition`, `TrailerDefinition`, `TireDefinition`, `EngineDefinition`, `GearboxDefinition` — ScriptableObject + JSON), wersjonowane.
- **Nie zakładaj deterministyczności PhysX między urządzeniami** — testy porównują z tolerancją.

## 2. Warstwy modelu (budowane w tej kolejności)

1. **Ciała sztywne**: ciągnik (masa własna z dokumentacji klasy pojazdu, środek masy nisko i realistycznie, tensor bezwładności liczony, nie domyślny z collidera), naczepa osobno, ładunek przesuwa środek masy naczepy.
2. **Kontakt koła**: wieloraycast / shapecast po obwodzie (nie jeden promień przez środek) — krawężniki, koleiny, progi. Podwójne koła na osi napędowej. Kolizja z **osobnym gładkim mesh kolizyjnym drogi**.
3. **Zawieszenie**: oś przednia (resory paraboliczne lub pneumatyka — wg wybranej specyfikacji), tylna pneumatyczna z regulacją wysokości; nieliniowe sprężyny i tłumiki, stabilizatory, limity skoku, odbój. **Zawieszenie kabiny** jako osobny układ sprężysto-tłumiący (nurkowanie przy hamowaniu, przechył w łukach, bujanie) — kluczowe dla kamery w kabinie.
4. **Opony**: model z poślizgiem łączonym (combined slip) — start: stabilny model szczotkowy/eliptyczny z telemetrią; cel: **Pacejka Magic Formula** (uproszczona) z wrażliwością na obciążenie, długością relaksacji (stabilność przy ~0 km/h i na postoju), współczynnikami nawierzchni (asfalt suchy/mokry, beton, kostka, szuter, trawa, błoto). Parametry dla opon ciężarowych (315/80 R22.5 prowadzące/napędowe, 385/65 R22.5 naczepa — rozmiary danych gry, `docs/VEHICLE_REFERENCE_DATA.md`; ADR 0201).
5. **Układ kierowniczy**: geometria Ackermanna (w zakresie stosowalności), przełożenie przekładni, maks. kąt skrętu kół, prędkość obracania, moment powrotny → używany do **feedbacku kierownicy dotykowej**.
6. **Silnik**: diesel R6 ~13 l, mapa momentu z LUT (płaski moment w niskim zakresie obrotów), bezwładność, opóźnienie doładowania (turbo lag), ogranicznik obrotów, hamulec silnikowy, mapa zużycia paliwa (BSFC). Wartości z publicznych danych technicznych klasy pojazdu, ze źródłem.
7. **Przeniesienie napędu**: sprzęgło suche z modelem tarcia, AMT 12-biegowa (logika doboru biegu do masy/nachylenia/prędkości, przerwa w momencie przy zmianie), tryb manualny, wał, most z przełożeniem głównym, mechanizm różnicowy z blokadą, straty.
8. **Hamulce pneumatyczne jako system**: kompresor, zbiorniki, ciśnienie robocze, opóźnienie narastania (dłuższe dla osi naczepy), zużycie powietrza, hamulec postojowy sprężynowy, ABS/EBS, ostrzeżenie o niskim ciśnieniu, utrata powietrza = realne skutki. **Retarder** (stopniowany) i hamulec silnikowy przed hamulcem roboczym.
9. **Naczepa**: siodło jako **własny stabilny constraint** (yaw szeroki do jackknife, pitch ograniczony na rampach, roll sztywny w granicach), obciążenie siodła, osie naczepy z własnym zawieszeniem (tandem/tridem), sprzęganie/odpinanie, nogi podporowe, scyzorykowanie możliwe przy błędach.
10. **Aero i opory**: opór czołowy zależny od naczepy, opór toczenia, nachylenie; boczny wiatr (później).
11. **Uszkodzenia** (proste, później): karoseria, nie symulacja belek.

## 3. Sterowanie mobilne jako część fizyki

- **Kierownica dotykowa**: obrót do realnego zakresu (np. ±900° w trybie sim, mniejszy w trybie komfort), krzywa czułości, martwa strefa, **samopowrót zależny od prędkości i momentu powrotnego z modelu**, wygładzanie bez opóźnienia odczuwalnego przez gracza. Pozycja i rozmiar konfigurowalne, wsparcie dla dwóch kciuków.
- **Pedały**: analogowe (przeciąganie palcem), progresywne krzywe; hamulec z modulacją (nie zero-jedynkowy).
- **Gyro**: kalibracja neutralnej pozycji, filtr (komplementarny/1€), limit kąta, krzywa; wyłączanie przy pauzie i zmianie orientacji.
- **Asysty** (opcjonalne, domyślnie minimalne w trybie „Symulacja”): stabilizacja przy niskich prędkościach, auto-sprzęgło, tempomat, asystent cofania z naczepą. Tryb „Komfort” dla graczy dotykowych — ale fizyka pod spodem ta sama.
- Kierunek sterowania (ruch kierownicy → kąt kół → skręt pojazdu) testowany automatycznie we wszystkich trybach wejścia.
- Haptyka (wibracje) na krawężnikach, ABS, kontakcie — przez abstrakcję platformową.

## 4. Telemetria (obowiązkowa od pierwszego koła)

CSV/JSON + overlay: czas symulacji, prędkość, przyspieszenia, yaw rate, RPM, bieg, moment silnika, pozycja pedałów/kierownicy, dla każdego koła Fz/Fx/Fy, slip ratio, slip angle, skok zawieszenia, ciśnienia (zbiorniki, siłowniki), stan retardera, kąt przegubu, obciążenia osi, czas kroku fizyki, FPS, ID konfiguracji, commit SHA. Narzędzie `tools/telemetry/plot.py` generuje wykresy PNG do raportów (i do obejrzenia przez Ciebie).

## 5. Parametry i źródła

`docs/VEHICLE_REFERENCE_DATA.md`: każdy parametr z wartością, jednostką, źródłem (dokumentacja techniczna klasy pojazdu, testy prasowe, normy, literatura: Gillespie *Fundamentals of Vehicle Dynamics*, Pacejka *Tire and Vehicle Dynamics*, Bosch *Automotive Handbook*), statusem (`SOURCED` / `DERIVED` / `WORKING_VALUE`). Nie wpisuj „realnych danych” bez źródła.

Fakty prawne do uwzględnienia (zweryfikuj aktualność): ogranicznik prędkości pojazdów ciężarowych w UE (90 km/h), w Polsce limity dla ciężarowych > 3,5 t: 80 km/h autostrady/ekspresowe, 70 km/h poza obszarem zabudowanym, 50 km/h w obszarze zabudowanym; DMC zestawu 40 t; długość naczepy 13,6 m, szerokość 2,55 m.

## 6. Pakiet walidacyjny (`tests/physics/`, uruchamiany po każdej zmianie fizyki)

Każdy test: warunki (masa, nawierzchnia, nachylenie, prędkość), oczekiwana wartość **ze źródłem**, tolerancja dobrana do jakości danych, wynik, wykres.

1. Postój na płaskim i na nachyleniu 12% z hamulcem postojowym — brak dryfu i oscylacji przez 5 min.
2. Ruszanie z miejsca: pusty zestaw i 40 t, płasko i pod górę 6% — bez cofania się, realne obroty/sprzęgło.
3. 0–60 i 0–80 km/h: pusty i 40 t — porównanie z danymi referencyjnymi.
4. Prędkość maksymalna na płaskim (ogranicznik) i ustalona prędkość na podjeździe 5% z 40 t.
5. Droga hamowania 80→0 (oraz 60→0 = punkt próby UN R13 typ-0 N3, i 50→0): sucho/mokro, pusty/40 t, z ABS i bez.
6. Zjazd 6–8% z retarderem i hamulcem silnikowym — stabilizacja prędkości; długie hamowanie roboczym → spadek ciśnienia.
7. Łuk o stałym promieniu przy kilku prędkościach — przechył, poślizg, granica przyczepności; wrażliwość na środek masy ładunku; pierścień skrętu 12,50/5,30 m (96/53/WE zał. I pkt 1.5, ADR 0280).
8. Zmiana pasa / manewr ISO-like przy 60–80 km/h — stabilność naczepy.
9. Jackknife: gwałtowne hamowanie w łuku na mokrym.
10. Cofanie z naczepą pod rampę, ciasne manewry w strefie przemysłowej.
11. Krawężnik 8/15 cm, koleiny, próg zwalniający — ciągłość kontaktu, brak teleportacji.
12. Różne `fixedDeltaTime`, FPS 30/60, obciążenie CPU — brak jakościowych różnic.
13. Floating origin i streaming w trakcie jazdy — brak skoków sił i prędkości.
14. Soak 30 min — brak dryfu energii, drgań, wzrostu błędu.
15. Spójność kierunku sterowania we wszystkich trybach wejścia.

### 6a. Liczby walidacji (runner .NET, gałąź `turning-circle-s23` @ `31c1383ca`, 2026-11-16)

Wyniki z `dotnet run -c Release --project tools/physics-runner/Runner -- --out artifacts/tc-s23/run`: **141 przebiegów, 833 kontrole,
wszystkie PASS**. Do tego `dotnet test` 287/287. Solver to rdzeń gry w czystym .NET (dt 0,01 s, 4 podkroki), **bez Unity/PhysX i
bez Windows playera**. Wartości oczekiwane i źródła są w JSON-ach `tests/physics/scenarios/*.json`; tu jest skrót.
Status: S = SOURCED (punkt przepisu sprawdzony w tekście), D = DERIVED (wzór/ekstrapolacja), W = WORKING_VALUE.
Masy: pusty zestaw 14,5 t / 40 t. Tam, gdzie są dwie liczby, pierwsza dotyczy pustego zestawu, druga 40 t.

| §6 | Scenariusz | Wynik | Limit | Źródło / status |
|---|---|---|---|---|
| 1 | `park_12pct_down/up_comb` (300 s, hamulec postojowy ciągnika) | pełzanie 2,71 / 1,48 mm w dół, 1,90 / 0,97 mm w górę; naczepa do **4,97 mm** (pusty, w górę) | ≤ 5 mm; ≤ 1 mm/s | S: UN R13 zał. 4 pkt 2.3.2 (12 %); „bez pełzania” W |
| 1 | `park_flat_5min_comb`, `soak_30min_parked` | dryf 0,34 mm; KE ≤ 1,0e-5 J przez 30 min; dryf energii 1,07 J | ≤ 5 mm; ≤ 1e-3 J; ≤ 5 J | W |
| 2 | `launch_6pct_uphill_comb` | cofnięcie 2,2 / 2,4 mm; 0–15 km/h 3,11 / 4,94 s; sprzęgło 29 / 37 °C | ≤ 5 cm; ≤ 250 °C | W |
| 3 | `launch_0_80_flat` (solo), `launch_flat_comb` | 0–60: 9,69 / 13,71 / 28,04 s; 0–80: **14,06** / 21,14 / 47,58 s | 40 t: 25–60 / 40–95 s; pusty 0–80 ≥ 20 s | D (moc/masa + zmiany biegów); solo W |
| 4 | `top_speed_flat_comb` | 89,38 / 89,17 km/h | ≤ 90,5; ustala 88–90 | S: ogranicznik 90 km/h (S3) |
| 4 | `grade_5pct_steady` (40 t) | 49,77 km/h, zakres 0,05 km/h, ≥ 1464 rpm | 44–60 km/h | D ≈ 54 km/h |
| 5 | **`brake_60_0_dry_abs_comb`** (silnik odłączony, N) | **23,19 / 24,10 m**; MFDD 7,20 / 6,85 m/s² | **s ≤ 36,7 m; dm ≥ 5,0 m/s²** | **S: UN R13 zał. 4 pkt 2.1.1, N3 typ-0 z odłączonym silnikiem: v = 60 km/h, s ≤ 0,15 v + v²/130, dm ≥ 5,0** (ADR 0280) |
| 5 | `brake_80_0_dry_abs_comb` | 39,19 / 41,31 m; MFDD 7,42 / 6,88 | ≤ 61,2 m; 5,0–8,0 | D: ten sam wzór przy 80 km/h = **ekstrapolacja** |
| 5 | `brake_50_0_dry_abs_comb` | 16,59 / 17,37 m; MFDD 6,76 / 6,69 | ≤ 26,7 m; 5,0–8,0 | D: ekstrapolacja przy 50 km/h |
| 5 | `brake_80_0_dry` (solo) | 34,26 m; MFDD 7,72 | 32–55 m; MFDD ≥ 5,0 (D) | W |
| 5 | `brake_80_0_wet_abs_comb` / bez ABS sucho i mokro (40 t) | 55,20 / 56,84 m; bez ABS 49,18 / 81,99 m | 45–95 m; 33–150 m | W (μ mokre ≈ 0,5) |
| 5 | `brake_response_static` | przód 0,25 s, tył 0,31 s, naczepa 0,54 / 0,53 s | ≤ 0,6 s | S: R13 zał. 4 pkt 4.1.1 (metoda zał. 6 nieczytana) |
| 6 | `downhill_7pct_typeIIA` (40 t, 6 km) | średnio 30,0 km/h, hamulec roboczy 0 | 25–35 km/h, bez roboczego | S: R13 zał. 4 pkt 1.8.2 |
| 6 | `downhill_8pct_retarder_comb` (40 t) | 40,0 km/h, retarder 2193 N m | 35–45 km/h; ≤ 4000 N m | W / S2 |
| 6 | `air_leak_rear_circuit` (pęknięcie przy 60 km/h, 40 t) | zatrzymanie 32,50 m | ≤ 52,4 m (z 40 km/h) | S: R13 zał. 4 pkt 2.4.1 (test gry trudniejszy) |
| 7 | **`ring_96_53_comb`** (znana porażka, obecna naczepa 7,70 m) | zewn. 12,486 / 12,483 m, **wewn. 5,228 / 5,230 m**, szerokość 7,258 / 7,253 m | zewn. ≤ 12,50; wewn. ≥ 5,30 | **S: dyr. 96/53/WE zał. I pkt 1.5** (CELEX 01996L0053-20190814) — **FAIL**, `scenarios_expected_fail/` |
| 7 | `ring_96_53_comb_rwb760` (propozycja ADR 0280: osie przez `overrides`) | zewn. 12,486 / 12,482, wewn. 5,343 / 5,347, szerokość 7,143 / 7,135 m | jw. + szerokość ≤ 7,15 (zapas 5 cm, W) | S + W — PASS; dane gry bez zmian |
| 7 | `circle_r50_10kmh_comb` | offtracking 0,609 / 0,603 m | 0,4–0,8 m | D: √(R²+e²) − √(R²+e²−L²) = 0,59 m |
| 7 | `rollover_r50_cog_low/high` (40 t) | pierwsze oderwanie koła przy 0,458 g / 0,337 g | 0,25–0,55 g | W (literatura 0,3–0,45 g UNVERIFIED) |
| 8 | `lane_change_80` | przegub 0,85 / 0,83°, RA 0,991 / 0,996, bez oderwania kół | RA 0,8–1,6; ≤ 6° | W |
| 9 | `jackknife_wet_curve_noabs` / `_retarder_noabs` (pusty) | przegub **87,45°** / 92,63° | ≥ 30° (musi być możliwy) | W; stan przed ADR 0228 / PR #113 |
| 9 | `jackknife_wet_curve_abs_50/_100` | 7,77 / 4,59° (pusty), 5,14 / 5,14° (40 t) | ≤ 10° | W |
| 11 | `curb_15cm_left_comb` | Fz maks. 3,24 / 2,95 × statyczne, przechył naczepy 2,79 / 3,39° | ≤ 4×; ≤ 8° | W (kontakt analityczny) |
| 11 | `kerb_step_27cm_42kmh_comb` (40 t, z koliderami, D58) | Fz 6,02×, oderwanie osi 0,38 s, zgniot zderzaka 0,036 m | 5,2–7,5×; ≤ 0,5 s; ≤ 0,05 m | W (ADR 0165) |
| 12 | dt 50/60/100/120 Hz; podkroki 2/4/8 | maks. odchyłka 0,63 % (0–60 40 t); podkroki 0,56 % | ≤ 5 % | W |
| 3/14 | powtarzalność (3 przebiegi, kurs 0/37/113°) | 0–60 9,688 s ×3, 0–80 14,055 s ×3 — 0,00 % | ≤ 3 % | §6.3 |
| 14 | `soak_30min_cycle` (40 t, 20 cykli) | prędkość przelotowa 73,02 → 72,46 km/h; dryf energii −2,84 J; powietrze ≥ 11,34 bar | 60–82 km/h; ≤ 5 J | W |
| 15 | `steer_sign_*` | np. 40 t w prawo +17,16 °/s, cofanie −3,16 °/s | znak | D |

Niesprawdzone bez Unity: integracja PhysX, kolizje ze światem, §6.10 na prawdziwej rampie, §6.12 FPS/CPU w buildzie, §6.13,
feel test właściciela (`docs/reports/PHYSICS-VALIDATION-2026-11-16.md` §5).

**Odbiór fizyki**: testy zielone **i** feel test właściciela na telefonie z listą uwag.

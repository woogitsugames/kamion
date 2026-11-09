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
4. **Opony**: model z poślizgiem łączonym (combined slip) — start: stabilny model szczotkowy/eliptyczny z telemetrią; cel: **Pacejka Magic Formula** (uproszczona) z wrażliwością na obciążenie, długością relaksacji (stabilność przy ~0 km/h i na postoju), współczynnikami nawierzchni (asfalt suchy/mokry, beton, kostka, szuter, trawa, błoto). Parametry dla opon ciężarowych (np. 315/70 R22.5 prowadzące/napędowe, 385/65 R22.5 naczepa).
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
5. Droga hamowania 80→0: sucho/mokro, pusty/40 t, z ABS i bez.
6. Zjazd 6–8% z retarderem i hamulcem silnikowym — stabilizacja prędkości; długie hamowanie roboczym → spadek ciśnienia.
7. Łuk o stałym promieniu przy kilku prędkościach — przechył, poślizg, granica przyczepności; wrażliwość na środek masy ładunku.
8. Zmiana pasa / manewr ISO-like przy 60–80 km/h — stabilność naczepy.
9. Jackknife: gwałtowne hamowanie w łuku na mokrym.
10. Cofanie z naczepą pod rampę, ciasne manewry w strefie przemysłowej.
11. Krawężnik 8/15 cm, koleiny, próg zwalniający — ciągłość kontaktu, brak teleportacji.
12. Różne `fixedDeltaTime`, FPS 30/60, obciążenie CPU — brak jakościowych różnic.
13. Floating origin i streaming w trakcie jazdy — brak skoków sił i prędkości.
14. Soak 30 min — brak dryfu energii, drgań, wzrostu błędu.
15. Spójność kierunku sterowania we wszystkich trybach wejścia.

**Odbiór fizyki**: testy zielone **i** feel test właściciela na telefonie z listą uwag.

# ADR 0149: czułość przesuwu kciukiem 24–60 km/h — stałe przyspieszenie poprzeczne na milimetr (Fold r2)

Status: proponowany (2026-11-12, gałąź `steer-r2`). Źródło: nagranie właściciela z Samsunga Fold, ekran wewnętrzny,
12.11 ok. 20:03 (`artifacts/owner-feedback/2026-11-12-fold-video/Screen_Recording_20261112_200336_Kamion.mp4`,
1080×1200, 120 fps, 27,0 s): „dalej ciężko się kieruje, nieprzyjemnie, szybko się traci kontrolę”. „Dalej” = po
ADR 0135 (gest „przesuw”, 10,8°/mm, 5°/mm od 60 km/h) i ADR 0058 (kolumna, limit rąk).

## 1. APK nagrania
`artifacts/orientation/kamion-0.1.0-387a492d24.apk` (19:53, 10 min przed nagraniem). `387a492d2` zawiera scalony
`steer-fold` (ADR 0135); na `origin/main` po nim nie ma zmian w `Input/`, `Gameplay/`, `Vehicle/` — nagranie pokazuje
dokładnie kod z ADR 0135. Gest = przesuw (domyślny po migracji v4): potwierdza to też ruch znacznika (niżej).

## 2. Diagnoza z klatek (liczby)
Klatki: ffmpeg 10 fps (pełne) i 30 fps (wycinek kierownicy 330×340 px). Pomiar automatyczny
(`artifacts/steer-r2/video/track.py` → `track30.csv`): kąt pomarańczowego znacznika (= kąt kierownicy ekranowej,
polecenie palca), kąt białej kreski (= kierownica w kabinie, `ColumnScreenDeg`), położenie białej kropki dotyku
(systemowe „pokaż dotknięcia”), prędkość z HUD. Środek koła (155, 1048) px nagrania, obręcz r ≈ 122 px. Zestawienia:
`artifacts/steer-r2/video/wheel_20.0-23.4s.png`, `wheel_23.6-26.6s.png`, `road_19-25s.png`.

| czas [s] | km/h | co się dzieje (palec → znacznik → kreska) |
|---|---|---|
| 17,57–18,23 | 35 | kciuk na górze obręczy, 35 px (≈ 4,4 mm) w lewo → znacznik −44° ekranu, kreska −49° (≈ −110° w kabinie ≈ **5° kół**); puszczony → samopowrót do −4° w 0,8 s |
| 18,4–21,0 | 35→34 | bez dotyku (znacznik −3°); po skręcie z 18 s zestaw zjeżdża w lewo na wyspę z kreskowaniem (klatki 19,0–20,6) |
| 20,10–20,93 | 35 | **chybiony chwyt**: dotyk zaczyna się w (154, 906) — w pasku „← AWAR. →” nad obręczą (szczyt obręczy y ≈ 926) — i jedzie 100 px (≈ 12,6 mm) w prawo po obręczy; znacznik stoi (−3°), korekta przepada na ~0,9 s |
| 21,10–21,90 | 34 | ponowny chwyt, ≈ 8 mm w prawo → +89° ekranu (≈ +10° kół); kreska dochodzi do +92° w 0,7 s |
| 22,97–23,10 | 33 | szarpnięcie ≈ 12 mm w lewo → −138° ekranu w 0,13 s; kreska idzie ≈ 116° ekranu/s (≈ 260°/s w kabinie = limit rąk 285°/s przy 33 km/h) i dochodzi do −117° po 0,9 s |
| 24,03–25,43 | 32→30 | kciuk **zatacza pełne koło po obręczy** zgodnie z zegarem w ~1,4 s; przesuw bierze tylko składową poziomą → znacznik +133° → −156° → +164° (±12 mm): kołysanie ~0,7 Hz, na dolnej połowie obręczy polecenie odwrotne do zamiaru |
| 25,5–26,6 | 30→0 | puszczone, hamowanie do zera |

Hipotezy z zadania:
- **Skala dpi na Foldzie — odrzucona.** Regresja znacznika na poziome położenie kropki (z opóźnieniem): 1,36° ekranu na
  px nagrania (24,0–25,4 s, r² 0,97, opóźnienie obrazu za kropką 67 ms) i 1,29°/px (23,0–23,7 s, r² 0,94, 100 ms).
  Oczekiwane 10,8°/mm × 0,126 mm/px = 1,36°/px przy panelu 1968 px ≈ 135,8 mm szerokości (Fold7, ~368 ppi — dane
  z pamięci, UNVERIFIED; 1080 px nagrania = przeskalowane 1968 px panelu). Implikowana szerokość 133–136 mm: mm są
  liczone dobrze (±5 %). Linii `[SCREEN]/[CONTROLS] dpi` z Folda nie ma (brak logcat z tej sesji).
- **Czułość przy 30–40 km/h — przyczyna główna.** Krzywa ADR 0135 (smoothstep 20→60 km/h między 32° a 5° w kabinie
  na mm) zostawia przy 35 km/h **23,5° w kabinie/mm = 1,17° kół/mm**. W przyspieszeniu poprzecznym (kinematycznie
  v²·δ/L, L = 3,70 m) to 0,52 m/s² na mm — **1,6× więcej niż przy 60 km/h (0,33)** i 2,2× więcej niż przy 20 km/h
  (0,23); szczyt 0,54 m/s²/mm przy 40 km/h. Kciuk drga o milimetry, więc dokładnie w paśmie z nagrania (30–41 km/h)
  każdy ruch był za duży: 4,4 mm = 5° kół, 8 mm = 10°, 12 mm = 14°.
- **Opóźnienie kolumny / rąk — skutek, nie przyczyna.** Śledzenie małych ruchów 50 ms (ADR 0058); duże polecenia
  (12 mm) ogranicza limit rąk ~280°/s → 0,9 s opóźnienia. Mniejsze polecenia po zmianie = krótsze dojścia; limitu nie
  ruszano.
- **Samocentrowanie — działa** (−49° → −4° ekranu w 0,8 s przy 35 km/h, puszczone koło idzie z kreską).
- **Dynamika (naczepa, tłumienie odchylenia) — odrzucona** jako przyczyna: walidacja 112/112 scenariuszy (589
  sprawdzeń) zielona, bez palca zestaw nie kołysze; kołysanie pojawia się dopiero w pętli z kciukiem (pkt 4).
- **Chybiony chwyt** (20,1 s) i **kręcenie po obręczy** (24,0 s) — realne, ale wtórne (po utracie toru); poza zakresem
  tej zmiany (pkt 5).

## 3. Decyzja
`SteeringFeel.dragLatAccelMatchKmh = 60` (nowe, JSON + C#, WORKING_VALUE). Dla gestu przesuw między ~24 a 60 km/h
stopnie kierownicy w kabinie na mm są ograniczone do `dragHighSpeedHandwheelDegPerMm × (60 / v)²` — milimetr kciuka
nigdy nie żąda większego kinematycznego przyspieszenia poprzecznego niż przy 60 km/h (`SteeringFeel.DragGain`,
`TouchSteeringWheel.Sample`). Ciągłe w 60 km/h, bez zmian od 60 km/h w górę, poniżej ~24 km/h (pełny skręt w 25 mm
zostaje), dla gestu „obrót”, gyro i klawiatury. `0` = krzywa ADR 0135. Ustawienia: istniejąca „Czułość” dalej mnoży
całość; nowej opcji nie dodano (właściciel ocenia domyślną). Zero alokacji, krok stały (Sample/kolumna bez zmian
w strukturze).

| km/h | 25 | 30 | 35 | 40 | 45 | 50 | 60 | 80 |
|---|---|---|---|---|---|---|---|---|
| ° w kabinie / mm, przed | 30,8 | 27,8 | 23,5 | 18,5 | 13,5 | 9,2 | 5,0 | 5,0 |
| ° w kabinie / mm, po | 28,8 | 20,0 | 14,7 | 11,3 | 8,9 | 7,2 | 5,0 | 5,0 |
| a_y na mm [m/s²], przed | 0,35 | 0,46 | 0,52 | 0,54 | 0,50 | 0,42 | 0,33 | 0,58 |
| a_y na mm [m/s²], po | 0,33 | 0,33 | 0,33 | 0,33 | 0,33 | 0,33 | 0,33 | 0,58 |

## 4. Dowód (physics-runner, ten sam kod co Unity)
Runner kompiluje teraz także `Input/TouchSteeringWheel.cs`, `SteeringColumn.cs`, `SteeringMath.cs`, `DriverIntent.cs`
(shim `tools/physics-runner/Sim/UnityShim.cs`: `Mathf`/`Vector2`/`JsonUtility` o semantyce Unity), więc łańcuch
palec → koło ekranowe → kolumna → `Steering` → opony jest kodem gry. `TouchDriver` (typ kierowcy `touch`):
odtworzenie palca z klatek albo model człowieka (podgląd 1,5 s z kursem i jego zmianą, opóźnienie percepcji 0,25 s,
mięśniowe 0,1 s, stałe wzmocnienie kciuka w mm na metr błędu — człowiek nie przestraja kciuka z każdym km/h).
Zestaw 40 t (`laden40`), zmiana pasa 3,5 m na 4 s jazdy. Komenda:
`dotnet run -c Release --project tools/physics-runner/Runner -- --touch-evidence artifacts/steer-r2/evidence` +
`uv run tests/physics/plot_touch_feel.py artifacts/steer-r2/evidence` (wykresy `gain_curve.png`, `replay35.png`,
`lc35.png`, `lc45.png`, `sweep35.png`, `sweep45.png`; CSV `summary.csv`, `gain_margin.csv`).

- **Odtworzenie 17,57–18,23 s** (4,4 mm w lewo w 0,66 s, puszczenie, 35 km/h): kąt kół 4,76° → **2,97°**, kurs po 5 s
  8,9° → **5,7°**, zjazd w bok po 5 s 4,0 m → **2,5 m**, a_y 1,93 → 1,17 m/s².
- **Zmiana pasa 35 km/h, kciuk 4 mm/m:** przed — trwałe kołysanie ±10 mm kciuka, ±5,5° kół, ±2,3 m/s², ~0,6 Hz
  (nagranie: ±12 mm, ~0,7 Hz); wskaźnik PIO (RMS odchylenia prędkości kątowej > 0,3 Hz, ostatnie 8 s) **10,2 → 0,06°/s**.
  45 km/h: 10,4 → 0,05°/s.
- **Margines wzmocnienia kciuka** (najmniejsze wzmocnienie, przy którym pętla kołysze; wyżej = łatwiej):
  30/35/40/45/50 km/h **4/3/3/4/4 → 5/5/5/5/6 mm/m**; 20 i 60 km/h bez zmian (6 i 8). Przed zmianą minimum całej
  skali leżało dokładnie w paśmie z nagrania.
- **Koszt (uczciwie):** przy bardzo delikatnym kciuku auto reaguje wolniej — 35 km/h, 1/2/3 mm/m: przestrzał po zmianie
  pasa 1,42/0,83/0,52 m → 1,82/1,12/0,82 m (`sweep35.png`). Ten sam ruch kciuka skręca o 37 % mniej, więc przy
  30–45 km/h trzeba przesunąć kciuk ~1,6× dalej niż dotąd (tyle co przy 60 km/h w przeliczeniu na a_y).
- Testy: `tools/physics-runner` **226/226** (w tym nowe `TouchSteeringTests` ×5), walidacja **112/112 scenariuszy,
  589 sprawdzeń**; EditMode `SteerFoldR2Tests` ×4 (krzywa 1/v², bez zmian < 24 i ≥ 60 km/h, obrót bez zmian, JSON).

## 5. Poza zakresem — dla lidera / gameplay-ui
1. **Chwyt nad obręczą trafia w pasek kierunkowskazów** (20,1 s: dotyk w „AWAR.” 2,5 mm nad obręczą, 12,6 mm ruchu
   bez skrętu). Pasek „← AWAR. →” leży tuż nad kołem, a obszar chwytu (ADR 0135 r3) jest do niego przycięty.
   Propozycja: odsunąć pasek albo oddać kierownicy pas ~5 mm nad obręczą.
2. **Kręcenie po obręczy w trybie przesuw** daje polecenie odwrotne na dolnej połowie koła (24,0–25,4 s). Właściciel
   kręci kołem, bo rysunek wygląda jak koło. Do decyzji: gest „po obwodzie” (składowa styczna ruchu w mm) albo
   test „Chwyt: obrót” (już w Ustawieniach). Nie zmieniono bez testu właściciela.
3. Od 60 km/h stałe 5°/mm daje a_y/mm rosnące z v² (80 km/h: 0,58 — więcej niż „przed” przy 35 km/h). Na nagraniu nie
   było tej prędkości; jeśli właściciel zgłosi nerwowość na drodze szybkiego ruchu, ta sama zasada (stałe a_y/mm)
   rozciągnięta powyżej 60 km/h to jedna liczba w `steering_feel.json`.

4. **Fizyka (UNVERIFIED, nie zmieniano):** po odtworzonym szarpnięciu i puszczeniu koła (koła proste, 0,0000°) zestaw
   nie wraca do jazdy prosto: przegub zostaje na −0,41° (40 t) / −0,11° (pusty), odchylanie trwa 0,43 / 0,10°/s przez
   20 s (łuk R ≈ 1,3 km przy 35 km/h); ciągnik solo wraca do 0. Prawdopodobnie tarcie Coulomba płyty siodła
   (`plateFrictionCoeff` 0,08 × nacisk × 0,35 m ≈ 3 kN m przy 40 t, WORKING_VALUE bez źródła) trzyma mały kąt
   przegubu. Dodaje „ucieczkę” po każdej korekcie. Do zadania fizyki: źródło dla tarcia płyty i scenariusz „jazda
   prosto po impulsie” (`TouchSteeringTests.Replay35_ResidualYawAfterRelease_Diagnostic`).

## Do sprawdzenia przez właściciela na Foldzie (UNVERIFIED do tego czasu)
- Prosta 30–45 km/h: drobna korekta kciukiem (2–4 mm) przesuwa ciężarówkę spokojnie, bez „ucieczki” i bez kołysania.
- Zmiana pasa przy 40 km/h jednym ruchem ~5–8 mm; plac (≤ 20 km/h) — pełny skręt jak dotąd w 25 mm.
- Jeśli teraz za mało przy 30–40 km/h: „Czułość” w Ustawieniach (np. 1,2) — i podać wartość.

## Konsekwencje
- Jedna nowa liczba (`dragLatAccelMatchKmh` = 60, WORKING_VALUE: zrównanie z punktem ADR 0135, który nie był
  przedmiotem skargi). Parametry pojazdu bez zmian.
- Model człowieka w runnerze (podgląd 1,5 s, 0,25 s, 0,1 s, próg PIO 0,75°/s) = WORKING_VALUE; służy porównaniu
  przed/po, nie przewidywaniu bezwzględnemu.

# ADR 0058: kierownica w kabinie jako ciężkie koło obracane rękami (limit prędkości rąk, przełożenie zależne od prędkości)

Status: przyjęty (2026-11-10). Źródło: test właściciela na S24+ (f6abb8b): „kierownica powinna płynnie, delikatnie
skręcać jak prawdziwa, bo tu nierealistycznie za szybko się kręci”.

## Kontekst (liczby z logu właściciela)
`artifacts/owner/feel-test/20261110-s24/logcat-unity.txt`, 94 linie `[CONTROLS] in`, tryb koło 270° (domyślny):
- Ścieżka v2: kąt kierownicy ekranowej / 270° → wygładzenie 20 ms → `Steering` (pełny skręt 40° kół, limit
  **30°/s kół** = 600°/s kierownicy w kabinie, przy każdej prędkości). Kierownica w kabinie = kąt kół × 20.
- t=174,6–175,1 s przy **90 km/h**: steer 0 → −0,70 → −1,00 w 0,5 s (palec ~700°/s). Polecenie = pełny skręt kół 40°
  (800° w kabinie); fizyka dała 30°/s kół, czyli kierownica w kabinie kręciła się 600°/s przy autostradowej prędkości.
- t=181,2 przy 41 km/h: −0,07 → −0,51 w 0,27 s (1,6/s znormalizowane = 65°/s kół polecone, 1300°/s w kabinie),
  limit fizyki ciął do 30°/s. Wszystkie 11 próbek |steer|>0,3 były powyżej 30 km/h.
- Przyczyny: (1) tryb 270° to przełożenie palec→kabina ~3:1 przy każdej prędkości (90° palcem = 300° w kabinie);
  (2) jedyny limit prędkości był limitem pompy wspomagania (30°/s kół), niezależny od prędkości; (3) brak bezwładności
  (skok prędkości kierownicy w jednym kroku).

## Decyzja
- **Geometria (bez zmian, dane pojazdu):** przełożenie całkowite 20:1, wirtualny kąt kół 40° → ±800° kierownicy
  (4,4 obrotu od oporu do oporu); przy Ackermannie 1,0, rozstawie osi 3,70 m i rozstawie kół 2,04 m koło wewnętrzne
  ma 47,5°, zewnętrzne 34,3° (wyliczone z `tractor_4x2_generic.vehicle.json`). Typowe ciężarówki 18–22:1 i ~4,5–5
  obrotu: WORKING_VALUE, nie cytowane z karty producenta. Fizyki (`Steering`, dane JSON) nie ruszano.
- **`Game.Controls.SteeringColumn`** (czysty C#, bez alokacji, krok stały 100 Hz w `DrivingLabBootstrap.FixedUpdate`,
  kolejność −200 przed `VehicleBody`): stan = kąt i prędkość kierownicy w kabinie. Z rękami na kole śledzi cel
  z limitem prędkości rąk zależnym od prędkości jazdy, limitem przyspieszenia (rozpęd w 0,1 s, hamowanie 2×),
  krzywą hamowania bez przeregulowania i stałą śledzenia 50 ms dla małych ruchów (10° → 63 % po 60–70 ms).
  Bez rąk: samopowrót do zera z prędkością od prędkości jazdy (kaster) i momentu powrotnego z modelu opon, zero
  poniżej 2 km/h; mnożnik „Samocentrowanie” z ustawień. Kąt / blokada → `DriverInput.Steer`; limit `Steering`
  (600°/s) jest powyżej limitu rąk, więc kierownica w kabinie (`Steering.HandwheelDeg`) = kąt kolumny co krok (test).
- **Parametry** w `Input/Resources/Controls/steering_feel.json` (= domyślne w `SteeringFeel`, test pilnuje), wszystkie
  WORKING_VALUE do testu właściciela:
  - limit rąk [°/s kierownicy] przy 0/10/30/50/80/100 km/h: 540/480/300/200/130/110 (przy 80 km/h = 6,5°/s kół
    zamiast 30°/s). Rząd wielkości: kierowcy przy manewrach obracają kołem chwytem „ręka za ręką” ~1–1,5 obr./s,
    przy autostradowych korektach rzadko ponad ~100–150°/s (bez cytowanego pomiaru dla ciężarówek: UNVERIFIED);
  - samopowrót: maks. 300°/s, nasycenie członu prędkości 30 km/h, momentu 800 N m, stała końcowa 0,3 s → 270° przy
    30 km/h wraca w ~1,5 s, przy 10 km/h ~3,2 s, 60° przy 80 km/h ~1,0 s;
  - przełożenie zależne od prędkości (nowe ustawienie „Przełożenie: stałe / od prędkości”, domyślnie od prędkości):
    do 20 km/h zakres ekranowy sięga pełnego skrętu (komfort 270° ≈ 3:1), od 60 km/h 1° palcem = 1° w kabinie
    (smoothstep pomiędzy); zakres 900° (sim) zostaje ~1:1 zawsze. Gyro: przy prędkości pełny przechył = 30 % skrętu.
- **Kierownica ekranowa** dalej idzie 1:1 za palcem; puszczona pokazuje kąt kolumny (odwrotność mapowania), więc
  wraca razem z kabinową i ponowny chwyt nie skacze. Gyro: martwa strefa 1°, filtr 1€, wynik = cel kolumny.
- Autopiloty (koło R25/R50, trasa) omijają model rąk (ich regulatory są strojone na surowe polecenie); kolumna jest
  ustawiana na ich kąt, żeby przejęcie było płynne. Klawiatura (edytor) przechodzi przez kolumnę.
- **Zapis ustawień:** schemat 3 (`speedSensitiveSteering`); migracja v2→v3 włącza nowe mapowanie, reszta wyborów
  właściciela zostaje. Log `[CONTROLS] in` dostał `hw=` (kąt kierownicy w kabinie), linia ustawień `speedSteer=`.
- Logi `[CONTROLS]` z `ControlInputLogger` i `ControlSettings.Log` idą bez stack trace (`LogOption.NoStacktrace`):
  w logu S24+ każda linia miała dopisaną linię `DebugLogHandler` (Player: stack trace Log = ScriptOnly).

## Dowód
`artifacts/gameplay/steering-feel/`: CSV i wykresy przed/po (palec, kierownica w kabinie, kąt kół) dla 4 scenariuszy
(manewry 5 km/h, odtworzenie logu właściciela 41 km/h, pełny obrót przy 80 km/h, zmiana pasa 80 km/h), generowane
z kodu gry przez `SteeringFeelTests.Evidence_BeforeAfter_Csv` (prędkość stała, moment powrotny 0 — wersja
zachowawcza). Testy: `SteeringFeelTests` (EditMode), zaktualizowane `ControlSettingsTests`, `Stage1LogicTests`.

## Konsekwencje / otwarte
- Do oceny przez właściciela na telefonie (feel): limit rąk przy 30–80 km/h, czas samopowrotu, przełożenie przy
  prędkości, gyro 30 %. Wszystko w JSON, bez przebudowy kodu.
- Fizycznie wspomaganie hydrauliczne ma też limit pompy (dziś 30°/s kół w danych pojazdu) — zostaje jako górna
  granica; parametry kierownicy pojazdu (przełożenie zmienne, 45–50° koła wewnętrznego) należą do agenta fizyki.
- Domyślne ustawienie stack trace dla Log=None w Player Settings to decyzja lidera (ProjectSettings) — tu obeszliśmy
  je w naszych logach.

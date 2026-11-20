# ADR 0312 — Sterowanie PC: limit przyspieszenia bocznego, progresywny klawisz, lusterko klasy II za naczepą

Data: 2026-11-20. Status: przyjęta w gałęzi `drive-feel-s24` (D93 pkt 3). Ocena odczucia przez właściciela otwarta.
Dotyczy: ADR 0264 (pad i klawiatura), ADR 0058 (kolumna kierownicy), ADR 0042/0243/0283 (lusterka).

## Kontekst

Pakiet walidacyjny fizyki (runner .NET) przechodzi w całości: 159 przebiegów, 987 kontroli. Sama fizyka nie wymagała
zmian. Brakowało jednak sprawdzenia, jak łańcuch wejścia PC (klawiatura i pad → `KeyboardAxisRamp` / `PadSteerFilter` →
`SteeringColumn` → `Steering`) zachowuje się razem z modelem pojazdu. Dodano tryb `physics-runner --input-feel`, który
uruchamia te same pliki źródłowe co Unity, i z niego wyszły dwa błędy:

1. **Trzymany klawisz albo pełne wychylenie gałki przewracały zestaw 40 t ze środkiem masy ładunku na wysokości 2,6 m**
   przy każdej prędkości od 30 do 90 km/h. Koła odrywały się od jezdni, a przy 80 i 90 km/h zestaw się przewracał.
   Statyczny próg przewrócenia tej konfiguracji w runnerze wynosi 0,339 g (3,3 m/s², `rollover_r50_cog_high`), a limit
   amplitudy zakładał 4,0 m/s². Od ok. 70 km/h działała do tego podłoga `minAmplitude 0,05`: 2° na kołach
   unieważniały limit boczny.
2. **Jedno stuknięcie klawisza (0,1 s) przy 50 km/h przesuwało zestaw o 0,70 m w ciągu 4 s.** Pas ma 3,5 m, a naczepa
   2,55 m, więc zapas z każdej strony to ok. 0,475 m (WORKING_VALUE). Najmniejsza możliwa korekta była więc większa
   niż ten zapas.

Lusterka: geometria R46 z `MirrorFieldOfVisionTests` (szkło, MirrorAim, MirrorOptics), siodło i tridem z definicji
fizyki. Wewnętrzne koło ostatniej osi naczepy wychodzi z pola klasy II przy przegubie ≥ 30° (lewe lusterko) i ≥ 25°
(prawe), czyli na rondach. Widać je wtedy tylko w lusterku szerokokątnym klasy IV, a okienka HUD na PC pokazują
wyłącznie klasę II (D70).

## Decyzja (wszystkie wartości WORKING_VALUE do testu odczucia)

- `pad_keyboard_feel.json` / `PadKeyboardFeel`: `maxLatAccelMs2` 4,0 → **2,5** (szczyty ciągnika i naczepy poniżej
  0,8 × progu 3,3 m/s²), `minAmplitude` 0,05 → **0,02** (podłoga zaczyna działać dopiero powyżej ok. 95 km/h). Gracz może
  podnieść limit 2× suwakiem `SpeedLimitScale`, tak jak dotąd.
- Progresywny start klawisza skrętu: `keyOnsetFraction` **0,35**, `keyOnsetS` **0,4 s**. Świeżo wciśnięty klawisz
  skręca z szybkością 35 % `keyRatePerS`, która rośnie liniowo do 100 % w ciągu 0,4 s. Puszczenie klawisza i powrót do
  środka bez zmian. `keyOnsetFraction = 1` przywraca zachowanie z ADR 0264.
- `RenderTextureMirror`: lusterko klasy II **po wewnętrznej stronie łuku** obraca się na zewnątrz o
  `0,7 × (przegub − 20°)`, maksymalnie o 25°. Lusterko po zewnętrznej stronie zostaje na miejscu. Na prostej (przegub
  < 20°) ustawienie R46 pozostaje bez zmian. Prawo dobrano jako najmniejszy obrót, przy którym widać koło, plus 3,5–5°
  zapasu (tabela w `artifacts/drive-feel-s24/mirror_trailer_pan.csv`). Przegub ustawia `DrivingLabBootstrap` co klatkę.
  Ten sam obraz trafia do szkła 3D i do okienka HUD, więc nie ma dodatkowych renderów: koszt GPU się nie zmienia,
  a transform aktualizuje się tylko przy zmianie > 0,05°. Wyłącznik: `RenderTextureMirror.TrailerPanEnabled`.
  Zwykłe lusterka się nie obracają. Obracanie obrazu za naczepą występuje w systemach kamera-monitor (UNVERIFIED), więc
  to decyzja grywalności, a nie wymóg R46.

## Liczby (runner, zestaw 40 t, środek masy ładunku 2,6 m, przed → po)

| przypadek | przed | po |
|---|---|---|
| trzymany klawisz 30 / 50 / 70 / 80 km/h, maks. ay ciągnika [m/s²] | 3,92 / 3,75 / 3,54 / 9,65 (przewrócenie) | 2,49 / 2,32 / 2,27 / 2,21 |
| ten sam przypadek, oderwanie koła [próbki] | 383 / 459 / 200 / 1147 | 0 / 0 / 0 / 0 |
| stuknięcie 0,1 s, przesunięcie po 4 s, 30 / 50 / 80 km/h [m] | 0,44 / 0,70 / 0,65 | 0,22 / 0,26 / 0,26 |
| zmiana pasa klawiaturą (model ludzki, 80 km/h): indeks PIO [°/s] / ustalenie [s] | 7,31 / 21,3 | 2,95 / 9,6 |
| zmiana pasa padem (wzmocnienie 1,0/m, 80 km/h): indeks PIO [°/s] | 6,70 | 0,008 |
| ostatnia oś naczepy w klasie II, przegub 25–45° | NIE (tylko klasa IV) | TAK (do 55°) |

Pełne tabele: `artifacts/drive-feel-s24/input-before|input-after/summary.csv`, wykresy `input-after/png/` (szare = przed).

## Konsekwencje

- Pusty zestaw przy 80 km/h dostaje z pełnego klawisza ok. 1,7 m/s² (wcześniej 3,0). Do zmiany pasa to wystarcza, ale
  limit nie zależy od ładunku. Czy uzależnić go od masy, ma rozstrzygnąć właściciel.
- Na rondzie R ≈ 15 m z ładunkiem trzeba zwolnić do ok. 22 km/h, żeby klawiszem wejść w promień. Zestaw 40 t realnie
  jedzie tam podobnie (wartość nieźródłowana).
- Fizyka, autopilot i kierownica PC (`DirectSteer`) bez zmian. Limit dotyczy wyłącznie pada i klawiatury.
- Testy: `PadKeyboardInputTests` (+2), `MirrorTrailerVisibilityTests` (2, nowe). Runner `--input-feel` zostaje jako
  dowód przy każdej zmianie `pad_keyboard_feel.json` / `steering_feel.json`.

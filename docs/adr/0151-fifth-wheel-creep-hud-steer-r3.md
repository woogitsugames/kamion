# ADR 0151: pełzanie płyty siodła, pasek kierunkowskazów oddaje przesuw kierownicy, a_lat/mm stałe także powyżej 60 km/h (steer r3)

Status: proponowany (2026-11-12, gałąź `steer-r3`). Kontynuacja ADR 0149 (Fold, „szybko się traci kontrolę”),
otwarte punkty 4, 1 i 3 z §5 tamtego ADR. Gest obwodowy (punkt 2) czeka na test r2 przez właściciela.

## 1. Zestaw po puszczonym impulsie skrętu nie jechał prosto (fizyka)
**Objaw (physics-runner, odtworzony kciuk z nagrania, 35 km/h):** po powrocie kół do 0,0000° zestaw 40 t zostawał na
przegubie −0,41° i skręcał stale 0,43°/s przez 20 s (łuk R ≈ 1,3 km); pusty −0,11° / 0,10°/s; ciągnik solo wracał do
zera. Po każdej korekcie ciężarówka „uciekała” dalej w tę samą stronę.

**Przyczyna (zmierzona):** tarcie płyty siodła w `FifthWheel` było idealnym Coulombem z przyleganiem: dopóki moment
potrzebny do wyprostowania przegubu był mniejszy niż μ·N·r (0,08 × ~98 kN × 0,35 m ≈ 2,7 kN m przy 40 t), przegub stał
sztywno w dowolnym małym kącie, a zestaw jechał jak sztywne auto z „załamaniem”. Przegląd μ przy pozostałych
parametrach bez zmian: μ 0,08 / 0,04 / 0,02 / 0 → przegub po 20 s −0,41 / −0,21 / −0,10 / 0,00°, odchylenie
0,43 / 0,22 / 0,11 / 0,00°/s. Czyli resztka jest proporcjonalna do μ: przyleganie, a nie asymetria ani brak momentu
prostującego (ten działa, gdy tarcia nie ma).

**Źródło μ:** nie znalazłem zmierzonego μ dla smarowanej płyty. Rząd wielkości daje patent US 6045148 (sprzęg siodłowy):
okładziny cierne o μ 0,1–0,2 dla „komfortowego poślizgu” — to cel projektowy dla okładziny niesmarowanej, nie pomiar.
Patent US 5746438 opisuje smar jako zwykły sposób zmniejszenia tarcia płyty i wiąże duże tarcie zrywające z bujaniem
naczepy. μ 0,08 dla smarowanej płyty zostaje jako WORKING_VALUE (poniżej zakresu okładzin, zgodnie z kierunkiem
smarowania); `docs/VEHICLE_REFERENCE_DATA.md` ma oba odnośniki.

**Decyzja:** `FifthWheelDefinition.plateFrictionCreepRateDegS = 1,0` (C# + `tractor_4x2_generic.vehicle.json`,
WORKING_VALUE). Poniżej momentu zrywającego tarcie jest lepkie (moment ∝ prędkości względnej, pełny cap przy 1°/s),
zrealizowane jako miękkie ograniczenie Catto (tłumik c = cap / 1°/s, bez sprężyny) z tym samym obcięciem do μ·N·r.
Przy szybkich ruchach przegubu (manewry, > ~1°/s) tarcie jest takie jak dotąd. Uzasadnienie: prawdziwa płyta pod
drganiami drogi i z luzem sworznia nie trzyma stałego kąta wbrew momentowi prostującemu osi naczepy. Idealne
przyleganie to artefakt modelu bez szumu. `0` przywraca stare zachowanie. Przegląd wartości pełzania: 0,25 / 0,5 /
1 / 2 / 4°/s → przegub po 10 s −0,051 / −0,013 / −0,003 / −0,001 / 0,000°, wszystkie wracają do 0 przed 20 s.
Wybrane 1°/s: powrót w ~8 s, a przy ruchach szybszych niż 1°/s tarcie się nie zmienia.

**Walidacja:** nowy scenariusz `tests/physics/scenarios/straight_after_steer_pulse.json` (solo / pusty / 40 t, ten sam
kciuk przez łańcuch dotykowy gry): od 10 do 14 s max |przegub| ≤ 0,05° i max |odchylenie| ≤ 0,05°/s. Z przyleganiem
(pełzanie 0): **FAIL** (pusty 0,109° / 0,103°/s, 40 t 0,413° / 0,426°/s); po zmianie **PASS** (40 t 0,0027° / 0,0011°/s).
Wykresy `tools/telemetry/plot.py`: `artifacts/steer-r3/pulse/` (po) i `pulse_before_creep0/` (przed). Cała walidacja
po zmianie: **115/115 scenariuszy, 607 sprawdzeń** (z kontrolami wielokrotnymi: powtarzalność, dt, substepy), w tym
lane change / slalom / rearward amplification / articulation_settle bez zmian statusu.

## 2. Pasek „← AWAR. →” nad kierownicą przejmował kciuk (HUD)
Nagranie, 20,1 s: dotyk w „AWAR.” 2,5 mm nad obręczą, 12,6 mm przesuwu w bok bez skrętu. Przeciągnięcie, które
zaczyna się na kierownicy, już przed zmianą zostawało przy niej (EventSystem trzyma `pointerDrag` przy celu
naciśnięcia). Problemem był dotyk, który **zaczyna się** na pasku.
**Decyzja:** `WheelDragRelay` na strefie `TurnSignals` (`UI/Driving/TouchWidgets.cs`, podpięty w
`DrivingHud.BuildLeftControls`). Przyciski nie mają obsługi przeciągania, więc przeciągnięcie trafia do strefy. Jeśli
jest przeważnie poziome (|dx| ≥ |dy|), relay przekazuje gest kierownicy (`SteeringWheelWidget.BeginRelayed`). Gest
liczy się od punktu naciśnięcia, więc droga sprzed progu przeciągania nie ginie. Kierunkowskaz nie zadziała
(`eligibleForClick = false`). Stuknięcie dalej włącza kierunkowskaz, przeciągnięcie pionowe nic nie robi. Kierownica
trzymana już innym palcem nie zostaje przejęta. W trybie gyro (kierownica nieaktywna) relay nic nie robi.
Układ stref HUD (ADR 0079) bez zmian: nic nie przesunięto, prawego górnego obszaru nie ruszano. Test PlayMode
`WheelDragRelayTests` (3).

## 3. Powyżej 60 km/h: stałe a_lat/mm
ADR 0135/0149 trzymały 5° w kabinie/mm od 60 km/h, więc a_lat/mm rosło z v²: 70/80/90 km/h = 0,45/0,58/0,74 m/s²
na mm (1,4/1,8/2,2× wartości przy 60 km/h). Decyzja: `SteeringFeel.dragLatAccelCapAboveMatch = true` (JSON + C#,
WORKING_VALUE). To samo ograniczenie 5 × (60/v)² działa też powyżej 60 km/h: 70/80/90 km/h = 3,67/2,81/2,22° w
kabinie/mm, a_lat/mm stałe 0,33. `false` = r2.

Dowód (runner, model człowieka jak w ADR 0149, 40 t, fazy: ADR 0135 / r2 / r3; `artifacts/steer-r3/evidence/`,
`gain_curve.png`, `sweep80.png`, `lc80.png`, `gain_margin.csv`). Wzmocnienie kciuka przy początku PIO [mm/m]:

| km/h | 30 | 35 | 40 | 45 | 50 | 60 | 70 | 80 | 90 |
|---|---|---|---|---|---|---|---|---|---|
| ADR 0135 | 4 | 3 | 4 | 4 | 5 | 8 | 6 | 6 | 5 |
| r2 (ADR 0149) | 5 | 5 | 5 | 6 | 6 | 8 | 6 | 6 | 5 |
| r3 (ten ADR) | 5 | 5 | 5 | 6 | 6 | 8 | **8** | **10** | **10** |

(Liczby dla 30–50 km/h różnią się o ±1 od ADR 0149, bo pełzanie płyty zmienia dynamikę zestawu. Siatka
wzmocnień: 1, 1,5, 2, 3, 4, 5, 6, 8, 10, 12, 16.) Przy 80 km/h i kciuku 8 mm/m r2 trwale kołysze z przesunięciem 3,5 m
w bok (nasycenie zakresu koła), r3 zbiega (`sweep80.png`). Koszt: przy 80 km/h zmiana pasa wymaga ~1,8× dłuższego
ruchu kciuka niż w r2 (tyle samo a_lat na mm co przy 60 km/h).

## Testy
- physics-runner `dotnet test`: 230/230 (`TouchSteeringTests`: krzywa ≤ a_lat(60) od 20 do 90 km/h, r2 przy
  `CapAbove = 0`, diagnostyka pełzania). Walidacja 115/115 (607).
- EditMode: `SteerFoldTests.Drag_AtSpeed_FiveCabDegreesPerMillimetre` → 5°/mm przy 60 km/h i 5 × 0,5625 przy 80;
  `SteerFoldR2Tests` (+ `Drag_Above60_ConstantLateralAccelPerMm_ADR0151_OrFixed5WhenOff`, pętla 21–99 km/h).
- PlayMode: `WheelDragRelayTests`, `HudLayoutTests`, `ControlSettingsPanelTests`.

## Do sprawdzenia przez właściciela (UNVERIFIED do tego czasu)
- Po korekcie kciukiem i puszczeniu ciężarówka przestaje „ciągnąć” w bok (szczególnie z ładunkiem).
- Kciuk, który zacznie na „← AWAR. →” tuż nad kołem i pojedzie w bok, skręca. Stuknięcie dalej włącza kierunkowskaz.
- 70–90 km/h: zmiana pasa spokojna. Jeśli za mało, „Czułość” w Ustawieniach.

## Konsekwencje
- Nowe liczby: `plateFrictionCreepRateDegS` 1,0°/s, `dragLatAccelCapAboveMatch` true — obie WORKING_VALUE.
- Golden CSV (`tests/golden`) i testy w `tools/physics-runner` przeszły bez przepisywania.

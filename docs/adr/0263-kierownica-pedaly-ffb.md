# ADR 0263 — Kierownica, pedały, skrzynia H i force feedback na PC

Status: przyjęty (scalony do main 2026-11-16, `3e9ef52fc`; status zaktualizowany 2026-11-16); pierwotnie: zaproponowany (gałąź `wheel-0263`, zadanie H1). Kontekst: D56, D73 / ADR 0260 (Windows platformą główną, „sterowanie klawiatura/pad/kierownica”), docs/04 §2.5 i §3.

## Kontekst
- Wejście gry idzie przez `IDriverInput` → `DriverInputMixer` → `DriverIntent` (dotyk, gyro, klawiatura, autopiloty). Kierownica w kabinie to `SteeringColumn` (ADR 0058): model rąk z limitem prędkości/przyspieszenia i samopowrotem z momentu powrotnego z modelu opon.
- Fizyka liczy moment powrotny kół skrętnych: `WheelGroup.AssembleForces` → `w.AligningTorque = -trail * Fy` (ślad pneumatyczny `pneumaticTrail0` malejący do zera przy szczycie kąta znoszenia), suma kół skrętnych w kontakcie = `VehicleModel.AligningTorqueTotal` [N m], znak: dodatni = obraca koła w prawo. Przełożenie `steeringRatio` = 20, `maxRoadWheelAngleDeg` = 40 (dane `tractor_4x2_generic`) → pół zakresu kierownicy w kabinie 800° (1600° od oporu do oporu).
- Kierownice PC (G29/G920/G923, T300/T150, Fanatec CSL) to urządzenia USB HID. Budżet 0 zł, zakaz zamkniętych SDK producentów i ich marek w grze.

## Decyzja
1. **Wejście przez Unity Input System, ogólne HID** (bez SDK producentów). Urządzenia z usage `GenericDesktop/Joystick` dostają automatyczny układ `Joystick` (manual Input System, HID). `HidWheelDriverInput : IDriverInput` dopasowuje urządzenie do **profilu jako danych** (`Input/Resources/Controls/wheel_profiles.json`: VID/PID, fragment nazwy produktu, ścieżki kontrolek osi/przycisków, kalibracja, zakres obrotu urządzenia, H-shifter, łopatki, przyciski → akcje). VID/PID i nazwy tylko w profilu i w `docs/compat/wheels.md`, nigdy w UI (źródło sterowania w HUD: „kierownica”).
2. **Kalibracja** (`WheelAxis.cs`, czysta logika): oś kierownicy kawałkami wokół środka (krzywy środek → 0 na wprost, ±1 na ograniczach), osie malejące, `invert`, martwa strefa środka z przeskalowaniem; pedały min/max (także odwrócone), martwe strefy spoczynku i nasycenia; pedały łączone na jednej osi (`SplitCombined`); kreator: `AxisCalibrator` (min/max/środek, wykrycie odwróconego pedału), `AxisAutoDetect` (która oś się ruszyła). **Bez kalibracji** działa bezpieczny tryb automatyczny: pierwszy odczyt = środek/spoczynek, zakres uczony z ruchu (`AutoSteer`, `AutoPedal`), więc zła zgadywanka w profilu nie daje pełnego gazu.
3. **Zakres 270–900° i odwzorowanie** (`WheelSteeringMap`): gracz ustawia zakres (270–900°, nie więcej niż obraca urządzenie). Tryb domyślny `ScaledToLock` — koniec zakresu = pełny skręt ciężarówki (900° fizycznych nie obróci 1600° kabiny 1:1); tryb `OneToOne` — stopień urządzenia = stopień kierownicy w kabinie, soft-lock na mniejszym z (zakres/2, skręt pojazdu). Poza soft-lockiem komenda stoi na pełnym skręcie, a FFB stawia ścianę.
4. **Kierownica fizyczna omija model rąk.** Nowe pole `DriverIntent.DirectSteer`: `DrivingLabBootstrap.FixedUpdate` ustawia `SteeringColumn` na kąt urządzenia (`SnapTo`) zamiast `Step` — ręce gracza i masa koła są prawdziwe, drugi limit byłby opóźnieniem. Ograniczenie prędkości obrotu kół (`Steering.maxSteerRateDegS`) w fizyce zostaje. Klawiatura (wyżej w kolejności miksera) nadal przejmuje skręt, gdy klawisz jest wciśnięty; dotyk/gyro nie steruje, gdy kierownica jest podłączona.
5. **H-shifter i łopatki** (`HShifterMapper`, `ButtonEdges`): bieg = bramka + (zakres wysoki ? liczba bramek : 0) (12 biegów AMT = 6 bramek × przełącznik zakresu); R → `Selector.Reverse`, bieg po N/R → `Selector.Drive`, bieg po biegu → `ShiftDelta = nowy − stary` i `TargetGear` (nowe pole, absolutne); neutral dopiero po `NeutralHoldS` = 0,6 s (WORKING_VALUE) poza bramką, żeby przejście 3→4 przez luz nie wrzucało N. Łopatki = `ShiftDelta ±1` na zboczu. Przyciski → akcje (`WheelAction`: postojowy, retarder ±, kierunkowskazy, awaryjne, D/N/R, tryb ręczny, tempomat zjazdu, kamera cofania, sprzęganie, nogi, zakres).
6. **Sprzęgło**: nowe pole `DriverIntent.Clutch` (0..1, max po źródłach w mikserze). Fizyka go jeszcze nie czyta (AMT ma sprzęgło automatyczne) — propozycja dla vehicle-physics niżej.
7. **Force feedback po stronie gry = czysty model** (`ForceFeedback.cs`, krok stały 100 Hz, zero alokacji): moment na wieńcu urządzenia
   `T = Mz_osi / przełożenie × (1 − wspomaganie) × przełożenie_wirtualne × zanik(v)` + tłumienie (−c·ω) + tarcie (−F·tanh(ω/ω₀)) + ściana soft-locka (−k·nadmiar, tłumienie tylko przy ruchu w ścianę) + „droga” (górnoprzepustowy filtr różnicy obciążeń Fz prawe−lewe koła skrętnej osi × ramię). Wyjście: `T / pełna_skala × gain`, obcięte do `maxOutput`, ograniczone narastaniem (`maxSlewPerS`), NaN → 0. Nieaktywne (pauza, menu, autopilot, brak urządzenia/backendu, utrata fokusu) → jednorazowe `Stop()` i zero. Na postoju człon powrotny = 0 (zanik od 0,3 do 2,5 m/s), a tłumienie i tarcie działają tylko gdy wieniec się rusza → nieruchomy wieniec na postoju = 0. Efekty nawierzchni wyłącznie z sił kontaktu fizyki (Fz), nie z animacji ani losowego szumu.
8. **Wyjście przez interfejs** `IForceFeedbackSink` (`Available`, `SetConstantForce(-1..1)`, `Stop`) z implementacjami `NullForceFeedbackSink` (domyślna w grze) i `RecordingForceFeedbackSink` (bufor pierścieniowy, testy/strojenie). `PcWheel` spina wejście, model i ujście; `DrivingLabBootstrap` woła go w `FixedUpdate` z liczb modelu i zatrzymuje w `OnApplicationPause`/utracie fokusu/`OnDestroy`. **Natywny backend = propozycja** (niżej), nie w tym ADR.
9. Ustawienia gracza: `WheelSettings` (PlayerPrefs `controls.wheel`, schemat 1 z migracją jak `ControlSettings`): włączenie, wymuszony profil, zakres, odwzorowanie, FFB wł./wył. i parametry, kalibracje per profil.

### Wartości (wszystkie WORKING_VALUE do feel testu na prawdziwej kierownicy)
| parametr | wartość | uzasadnienie |
|---|---|---|
| wspomaganie (`powerAssist`) | 0,85 | hydrauliczne wspomaganie ciężarówki przejmuje większość momentu; brak źródła liczbowego — UNVERIFIED |
| pełna skala na wieńcu | 8 N m | rząd momentu, który da się odczuć bez męczenia ręki; niezależny od urządzenia (maks. moment urządzeń nieweryfikowany) |
| zanik członu powrotnego | 0,3 → 2,5 m/s | ślad pneumatyczny modelu nie ma sensu przy ~0 km/h (długość relaksacji, docs/04 §2.4) |
| tłumienie / tarcie | 0,35 N m·s/rad / 0,4 N m (wygładzenie 8°/s) | stabilność wieńca przy puszczeniu, bez drgań na postoju |
| soft-lock | 1,5 N m/° + 0,8 N m·s/rad | ściana wyczuwalna od pierwszych stopni |
| ramię „drogi” | 0,01 m, τ 0,05 s | brak promienia zataczania w danych pojazdu — mały, wyłączalny |
| narastanie | 20 /s | brak szarpnięć przy skokach siły |
| neutral H-shiftera | 0,6 s | szybka zmiana przez luz nie wrzuca N |
| domyślny zakres w grze | 540° | środek przedziału 270–900 |

## Force feedback — co umożliwia Unity 6 bez płatnych pakietów (badanie)
- **Unity Input System** (projekt: 1.20.1): haptyka tylko jako `IHaptics`/`IDualMotorRumble` (`SetMotorSpeeds`, `PauseHaptics`, `ResetHaptics`) dla gamepadów: Xbox na Windows, DualShock 4 na Windows/Mac, konsole z pakietami konsolowymi. **Brak API force feedback dla kierownic.** Źródło: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/Gamepad.html
- **Wyjście HID**: Input System pozwala wysłać surowy raport wyjściowy HID komendą typu `HIDO` przez `InputDevice.ExecuteCommand`; format raportu jest specyficzny dla urządzenia; `HIDDeviceDescriptor` ma `outputReportSize`. Źródła: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/HID.html, https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/api/UnityEngine.InputSystem.HID.HID.HIDDeviceDescriptor.html. To technicznie droga do FFB bez wtyczki, ale wymaga własnej implementacji protokołu każdego producenta:
  - Logitech klasyczny (G29): komendy w sterowniku Linuksa `hid-lg4ff.c` (np. zakres obrotu `0xf8 0x81`), **GPL-2.0-or-later** — wolno czytać jako dokumentację zachowania, nie kopiować kodu. https://github.com/torvalds/linux/blob/master/drivers/hid/hid-lg4ff.c
  - G920/G923 Xbox: HID++ (strona FFB `0x8123`) w `hid-logitech-hidpp.c` (GPL). https://github.com/torvalds/linux/blob/master/drivers/hid/hid-logitech-hidpp.c
  - Thrustmaster T300: sterownik `hid-tmff2` (GPL-2.0, poza jądrem). https://github.com/Kimplul/hid-tmff2
  - Fanatec: `hid-fanatecff` (GPL-2.0, poza jądrem). https://github.com/gotzl/hid-fanatecff
  - Na Windows wiele baz ma FFB przez sterownik producenta i DirectInput, a surowy dostęp HID do interfejsu FFB może być zajęty przez ten sterownik — UNVERIFIED (do sprawdzenia na sprzęcie). Wniosek: droga `HIDO` = dużo pracy per urządzenie, ryzyko konfliktu ze sterownikiem; odrzucona jako pierwsza.
- **Windows.Gaming.Input.RacingWheel + ForceFeedback** (część Windows 10/11, bez opłat): odczyt koła/pedałów/sprzęgła/H-shiftera (`HasClutch`, `HasPatternShifter`, `MaxWheelAngle`, `MaxPatternShifterGear`) i FFB przez `WheelMotor` z efektami `ConstantForceEffect`, `ConditionForceEffect`, `PeriodicForceEffect`, `RampForceEffect`. Źródło: https://learn.microsoft.com/en-us/windows/uwp/gaming/racing-wheel-and-force-feedback. Dokumentacja opisuje UWP/Xbox; użycie z aplikacji desktop (Unity Standalone) przez C++/WinRT — UNVERIFIED; lista kierownic obsługiwanych przez WGI zależy od sterowników — UNVERIFIED.
- **SDL3 haptic** (licencja zlib — `LICENSE.txt`: https://github.com/libsdl-org/SDL/blob/main/LICENSE.txt): `SDL_OpenHapticFromJoystick`, `SDL_CreateHapticEffect`, `SDL_UpdateHapticEffect`, `SDL_RunHapticEffect`, `SDL_SetHapticGain`, `SDL_SetHapticAutocenter`; efekty CONSTANT, SPRING, DAMPER, FRICTION, INERTIA, okresowe, RAMP. https://wiki.libsdl.org/SDL3/CategoryHaptic. Backend Windows to DirectInput (`src/haptic/windows/SDL_dinputhaptic.c`): https://github.com/libsdl-org/SDL/tree/main/src/haptic/windows. Podsystem haptic nie jest bezpieczny wątkowo (wiki).
- **DirectInput 8 FFB** bezpośrednio (Windows SDK, bez opłat): to samo co SDL3 pod spodem, ale własny kod C++ COM.
- **vJoy** i podobne: wirtualne joysticki (wejście do gry z innych programów) — nie dają FFB do fizycznej kierownicy; nieprzydatne tutaj.
- **SDK producentów** (np. Logitech Steering Wheel SDK): zamknięta licencja → **odrzucone** (zakaz w zadaniu, ryzyko marki).

## Propozycja kolejności natywnego backendu (dla lidera)
1. **SDL3 (zlib) jako mała natywna wtyczka x64** (`Plugins/x86_64/SDL3.dll` + cienka warstwa P/Invoke `Sdl3ForceFeedbackSink : IForceFeedbackSink`): jeden efekt CONSTANT tworzony przy podłączeniu, `SDL_UpdateHapticEffect` co krok stały (lub co 2. krok, jeśli koszt), autocenter 0, gain z ustawień. Dopasowanie urządzenia SDL ↔ Input System po VID/PID. Licencja zlib: wpis w `docs/LICENSES.md` + informacja w atrybucjach. Koszt: build DLL (CMake, MSVC) jako kod w repo (`tools/native/sdl3-ffb/`), test na sprzęcie właściciela.
2. Jeśli SDL3 nie obsłuży danej bazy: **Windows.Gaming.Input** przez C++/WinRT (część systemu) jako drugi sink.
3. Surowe raporty `HIDO` tylko dla konkretnego modelu bez sterownika DirectInput — ostatnia opcja.
Wymaga zgody lidera (nowy katalog `Plugins/`, ewentualnie zmiana `ProjectSettings` dla natywnych bibliotek) i **testu na prawdziwej kierownicy** (właściciel).

## Propozycje dla lidera (poza moją własnością)
- **asmdef**: brak zmian — wszystkie nowe pliki w `Input/` (Game.Controls) i `Tests/EditMode/` (istniejący Game.Tests.EditMode, który już widzi Game.Controls i GcAllocCounter z PlayMode).
- **`.inputactions`**: nie zmieniane (konflikt z 0261 uniknięty) — kierownica czytana bezpośrednio z urządzenia jak `KeyboardDriverInput`. Gdy powstanie remapowanie w UI, można dodać osobny asset `WheelActions.inputactions` (nie ruszać `InputSystem_Actions`).
- **`DrivingLabBootstrap.cs`** (Gameplay) zmieniony w 5 miejscach (pole `PcWheel`, `m_Mixer.Add(PcWheel.Input)` po klawiaturze, `PcWheel.Load()`, `m_SteerDirect` → `Column.SnapTo`, krok FFB w `FixedUpdate`, `Stop` przy pauzie, `Dispose` w `OnDestroy`). Możliwy konflikt tekstowy z 0262 (spawn/route_start) — bez konfliktu logicznego.
- **vehicle-physics**: (a) absolutne żądanie biegu w AMT (`DriverIntent.TargetGear` → `AmtController`), dziś bootstrap zamienia `ShiftDelta` na jedno zbocze `ShiftUp/ShiftDown`, więc przeskok 4→2 zmienia o 1 bieg; (b) sprzęgło nożne (`DriverIntent.Clutch`) w trybie ręcznym; (c) mechaniczny ślad kółka (caster) i promień zataczania w `SteeringDefinition` ze źródłem — dziś FFB zna tylko ślad pneumatyczny, więc przy małym kącie znoszenia moment powrotny jest słaby (to samo dotyczy samopowrotu w ADR 0058).
- **gameplay-ui**: kreator kalibracji (`AxisCalibrator`, `AxisAutoDetect`) i panel ustawień kierownicy (zakres, odwzorowanie, FFB) — teksty w tabelach lokalizacji; wieloczęściowe zestawy (osobne USB pedałów, np. Fanatec) wymagają drugiego `IDriverInput` „pedały” z tym samym profilem.

## Scalenie z main (ADR 0261) i z #133 (ADR 0264) — agent H6, s22
- Konflikt z 0261 w `DrivingLabBootstrap` (obie gałęzie dopisały źródło po `m_Mixer.Add(Keyboard)`): kolejność
  **Keyboard → Pad (0261) → PcWheel.Input → Wheel (dotyk) → Gyro → Touch**. Pad 0261 jest aktywny tylko przy wychylonej
  gałce, więc jak klawisze nadpisuje kierownicę na czas wychylenia; dotykowe koło (`TouchSteeringWheel`, zawsze
  `SteerActive`) musi zostać za kierownicą PC. Kierownica (`Joystick`) i pad (`Gamepad`) to rozłączne klasy urządzeń
  Input System — jedno urządzenie nie trafia do dwóch źródeł.
- Po #133 (ADR 0264) pole `Pad` i `m_Mixer.Add(Pad)` znikają z bootstrapu; `PcInputBridge` wstawia pad i klawiaturę z
  akcjami **przed** `Keyboard`, czyli też przed `PcWheel.Input` — ta sama zasada priorytetu. Gałąź `wheel-0263` ma już
  w sobie scalone `gamepad-0264` (stos), żeby ten fragment i `DriverInputMixer` scaliły się bez konfliktu w kolejności
  #133 → #132; szczegóły w komentarzu PR #132.
- `DriverIntent.DirectSteer/Clutch/TargetGear` nie kolidują z 0261/0264 (pad i klawiatura ich nie ustawiają).

## Alternatywy odrzucone
- Kierownica przez `SteeringColumn.Step` (model rąk) — dodaje opóźnienie i limit prędkości do fizycznego urządzenia.
- Mapowanie wyłącznie 1:1 — 900° urządzenia nie da pełnego skrętu ciężarówki (1600°); zostaje jako opcja.
- FFB jako „sprężyna centrująca” z efektu urządzenia (SPRING) — nie wynika z fizyki; ewentualnie tylko jako awaryjny tryb backendu.
- Efekty nawierzchni z szumu/animacji — zakaz (fizyka w kodzie).

## Walidacja
- Testy EditMode: `PcWheelInputTests` (30 przypadków: kalibracja, odwrócone pedały, martwe strefy, tryby automatyczne, zakres 270–900, soft-lock, kierunek we wszystkich odwzorowaniach, H-shifter, zbocza, mikser, profile), `ForceFeedbackModelTests` (12: wielkość i znak z syntetycznych Fy/Mz, zero na postoju, tłumienie/tarcie, soft-lock, obcięcie i narastanie, stop, NaN, droga z różnicy Fz, przełożenie wirtualne, sanitize), `PcWheelDataTests` (7: JSON przez JsonUtility, migracje, **zero alokacji ścieżki na krok** przez `GcAllocCounter`).
- Uruchomione poza Unity: 42/42 zielone (`dotnet test`, .NET 8, NUnit 3.14, z atrapą `UnityEngine.Vector3/Mathf`) dla `PcWheelInputTests` + `ForceFeedbackModelTests`. **Nieuruchomione**: Unity EditMode (brak Unity w chmurze), kompilacja w Unity plików zależnych od Input System (`HidWheelDriverInput`, `WheelSettings`, `PcWheel`, bootstrap), test na sprzęcie, build Windows.

## Budżet
Zero alokacji na krok (test). Koszt CPU: kilka działań na klatkę i na krok fizyki — pomijalny (nie mierzony; ESTIMATED).

## Uzupełnienie s23 (zgodność z kodem), 2026-11-16
Stan `origin/main` `0d91ee7db`.
- **Force feedback nie ma dziś sterownika wyjścia.** `PcWheel.Sink` = `NullForceFeedbackSink.Instance`
  (`Input/PcWheel.cs:15`), który ma `Available => false` (`Input/ForceFeedback.cs:21-24`); poza nim istnieje tylko
  `RecordingForceFeedbackSink` do testów (`ForceFeedback.cs:32`). Model FFB liczy moment, ale na kierownicę nic nie trafia,
  dopóki nie powstanie natywny sink (propozycja SDL3 / Windows.Gaming.Input wyżej).
- **Brak kreatora kalibracji i panelu kierownicy w grze.** `WheelSettings`, `AxisCalibrator`, `AxisAutoDetect` są
  używane tylko w `Game.Controls` (`Input/WheelAxis.cs`, `PcWheel.cs`, `WheelDeviceProfile.cs`, `HidWheelDriverInput.cs`,
  `WheelSettings.cs`); żaden plik `UI/` ich nie używa. Ustawienia kierownicy USB da się dziś zmienić tylko w PlayerPrefs
  `controls.wheel` (`WheelSettings.cs:14`). Kalibracja: pierwszy odczyt osi = środek (`HidWheelDriverInput.cs:98`).
- **Dwa różne zakresy kierownicy:**
  kierownica USB — 270–900° (`WheelSteeringMap.cs:22`), `rangeDeg = 0` = domyślny z profilu (`WheelSettings.cs:22-23`),
  w profilach 540° (`Resources/Controls/wheel_profiles.json:35`; uwaga: środek przedziału 270–900 to 585°, więc
  „środek przedziału” w tabeli wyżej jest przybliżeniem); kierownica **dotykowa** (D70) — domyślnie 270°
  (`ControlSettings.cs:32`), zakres 180–900° co 90° w „Ustawieniach sterowania” (`ControlSettings.cs:21`,
  `ControlSettingsPanel.cs:188`). D70 mówi o kierownicy dotykowej (270° domyślnie, 900° w ustawieniach) i nie podaje
  minimum — 180° to wartość z kodu.

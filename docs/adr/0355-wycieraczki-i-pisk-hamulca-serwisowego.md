# ADR 0355 — Wycieraczki i pisk hamulca serwisowego

Status: proposed (codex-audio-wipers-s24, 2026-11-27).

## Kontekst

ADR 0142 pozostawił niepodłączone wycieraczki i pisk hamulca serwisowego. ADR 0341
opisuje zaparkowane pióra, a eksport TRAKT-a udostępnia osie `WIPER_L_LOD0` i
`WIPER_R_LOD0` z potomnymi LOD1/2. Pisk hamulca serwisowego jest osobnym
zdarzeniem względem pisku opon w poślizgu (ADR 0145).

## Decyzja

- Domyślny klawisz **U** cyklicznie zmienia tryb wył. → przerywany → 1 → 2 → wył.
  Akcję można przypisać w Ustawieniach sterowania także na padzie. Klikalna etykieta
  w HUD (**Panel → Zestaw…**) pokazuje tryb i wykonuje tę samą zmianę.
- `WiperDrive` na pojeździe prowadzi fazę ruchu i liczniki startu oraz powrotu do
  spoczynku. Pióra poruszają się wokół lokalnych osi +Y po imporcie FBX do
  Unity. Maksymalny kąt od pozycji spoczynkowej to 72° po lewej i 95°
  po prawej (`WORKING_VALUE`). Krótszy lewy łuk omija słupek A. Wspólny zegar
  uruchamia klip silnika i tarcia obu suwów na starcie, a osobny stuk przy końcu.
  Zmiana biegu obowiązuje od następnego cyklu. Wyłączenie pozwala dokończyć
  bieżący cykl. Czasy robocze (`WORKING_VALUE`) wynoszą 1,20 s dla trybu
  przerywanego i 1, 0,80 s dla trybu 2 oraz 2,40 s przerwy po zaparkowaniu
  w trybie przerywanym.
- Presety oświetlenia nie symulują deszczu. Przy rozpoczęciu cyklu silnik audio
  wybiera mokrą wersję, gdy istniejąca globalna wilgotność `_KamionWet.x` wynosi
  co najmniej 0,25 (`WORKING_VALUE`). Obydwa standardowe presety clear
  i overcast są suche. Scenariusz mokry można uruchomić przez `-rq_wet 1`.
- Pisk hamulca serwisowego może wystąpić, gdy przez 0,10 s moduł prędkości
  mieści się w przedziale [1, 15) km/h, maksymalne ciśnienie komory koła
  ciągnika z kontaktem wynosi 22–65% maksimum, a żądanie hamulca serwisowego
  wynosi 12–75%.
  Postojowy i Hill Hold blokują zdarzenie. Jedna próba losowania (28%) na
  aplikację, ponowne uzbrojenie po spadku żądania poniżej 8%, odstęp co najmniej
  3 s pomiędzy zdarzeniami. Progi, czasy i poziomy miksu są `WORKING_VALUE`.
- Oba zestawy audio korzystają z tych samych własnych klipów. Każde zdarzenie
  wybiera perspektywę przy starcie. Hamulec dochodzi z okolic przedniej osi
  i ma filtrowaną wersję kabinową. Źródła powstają przy inicjalizacji.

## Odtworzenie

`tools/audio/render_all.py --no-previews` uwzględnia nowe pary w pełnym banku.
Klipy można wygenerować osobno przy użyciu interpretera z NumPy i SciPy.

```powershell
& $python tools/audio/cab_mechanisms.py game/Assets/_Project/Audio/Generated/Clips/sfx
. ./scripts/env.ps1
Invoke-UnityBatch -LogFile (Join-Path $LogsDir 'import-cab-mechanisms.log') -BuildTarget Win64 -Arguments @('-executeMethod', 'Game.Editor.Audio.VehicleAudioImporter.ImportCabMechanismsBatch')
```

Przed uruchomieniem Unity obowiązuje slot repozytorium. Do porównania statycznego
użyj `scripts/visual-qa.ps1 -Scene DrivingLab -Pc -Tier High -BuildTarget Win64`
z `-Lighting clear|overcast` oraz `-WiperPhase 0.5` dla punktu nawrotu.
Kalibracja brzmienia na słuchawkach i pomiar synchronizacji wyjścia audio
z klatkami playera pozostają `UNVERIFIED`.

## Pomiar

PlayMode Win64, DrivingLab. W końcowym przebiegu przy zadanej prędkości
10 km/h i pedale 0,55 odnotowano 14 zdarzeń na 64 aplikacje w kabinie oraz
20 na 64 z kamery pościgowej. Maksymalne ciśnienie komory koła z kontaktem
w chwili startu pisku wynosiło 0,454–0,460 maksimum. Próba wycieraczek
zapisała 5 startów i 4 powroty (ostatni cykl jeszcze trwał) oraz wybór
suchego klipu w kabinie i mokrego na zewnątrz. Zmierzono 0 B GC w 300
aktualizacjach wycieraczek i w 8320 aktualizacjach audio ze scenariuszy
hamowania. Własny bank obejmuje 8 WAV mono 48 kHz o łącznym rozmiarze
543 712 B. Najwyższy zmierzony szczyt próbki to −3,10 dBFS przed miksem.

Wyniki są w `artifacts/codex-audio-wipers-s24/drivinglab-events.log`
oraz `wav-measurements.txt`.

Pełny PlayMode na tej bazie wymagał lokalnej regeneracji brakującej mapy
`bialystok-krywlany` poleceniem
`& $python tools/ui/build_nav_map.py --region bialystok-krywlany`.

## Dopisek (`agy-horn-rattle-s24`): klakson (HUD PC + synteza pneumatyczna) i grzechot naczepy/sprzęgu (ADR 0142)

Zamknięto kolejne dwa punkty otwarte od ADR 0142 („przycisk klaksonu na HUD; grzechot naczepy”), spójnie ze wzorcami ADR 0355:

1. **Klakson pneumatyczny + przycisk w HUD PC (`DesktopHudLayout` / `DrivingHud.Desktop` / `TruckAudioController`)**
   - Klawisz `K` (`DrivingActionCatalog.Horn`, domyślnie `<Keyboard>/k` i `<Gamepad>/rightStickPress`, zmienialny w menu wiązań `InputBindingsPanel`) naprawiono w `DrivingLabBootstrap` tak, aby respektował `Keyboard.Enabled` zamiast sztywnego odczytu `kb.kKey.isPressed`. Klawisz `H` pozostaje przypisany do świateł awaryjnych (`DrivingActionCatalog.Hazard`).
   - W HUD PC (`DesktopHudLayout`, strefa `DesktopHorn` `136 × 52 u` w stylu matowej tablicy `UiPalette.HudPanel`, podpis `Klakson`) dodano widget `HornButtonWidget` (`IPointerDownHandler`/`IPointerUpHandler`) po lewej stronie dolnego bloku wskaźników (`AudioCues.HornHudHeld` niezależny od `AudioCues.HornHeld`).
   - Synteza proceduralna w `tools/audio/horn_rattle.py` generuje parę pętli mono 48 kHz (`horn_air_loop.wav` `1,000 s`, peak `−3,00 dBFS`, RMS `−16,15 dBFS`; `horn_air_cab_loop.wav` `1,000 s`, peak `−5,79 dBFS`, RMS `−17,80 dBFS`) z dwutonowych trąb pneumatycznych (~`192 Hz` i ~`238 Hz`, parzyste + nieparzyste składowe mosiężne + szum wypływu powietrza `1,2–5,2 kHz`), używaną przez zestaw proceduralny w `VehicleAudioLibrary.hornAir` (zestaw ElevenLabs zachowuje `elHorn`). Podtrzymanie minimalnego impulsu (`HornMinBlastSeconds = 0,22 s`, `WORKING_VALUE`) rozróżnia krótkie naciśnięcie od przytrzymania.

2. **Grzechot naczepy i siodła (`TrailerRattleGate` / `TruckAudioController.CabMechanisms`)**
   - Struktura wartościowa `TrailerRattleGate` (zero alokacji GC) wylicza pobudzenie z fizyki sprzężonej naczepy: `|TrailerModel.LocalAcceleration.y|`, prędkości ugięcia osi `Wheels[i].CompressionRate`, dynamicznego odchylenia nacisku siodła względem wygładzonej bazy (`FifthWheel.KingpinLoadLocal.y`), prędkości jazdy (`MinSpeedKmh = 1,5 km/h`), nawierzchni szorstkich (`Cobbles`/`Gravel`/`Grass`) oraz chwili sprzęgnięcia (`SinceCoupled`).
   - Stochastyczny generator zdarzeń wyzwala 4 pary klipów mono 48 kHz (`trailer_rattle_{chain_a,chain_b,tarp_a,kingpin}(_cab).wav`, czasy `0,220–0,400 s`, peak `−3,50..−4,00 dBFS` na zewnątrz i `−4,95..−13,61 dBFS` w kabinie) z losową modulacją głośności i wysokości; w kabinie poziom jest cichszy (`cabTrailerRattleFactor = 0,35 × trailerRattleVolume = 0,55`).

3. **Weryfikacja (`agy-horn-rattle-s24`, Win64)**
   - `tools/audio/tests/test_horn_rattle.py`: `3 passed`.
   - PlayMode Win64 (filtr `HornRattlePlayModeTests;CabMechanismsPlayModeTests;PcHudGc0244Tests;ElevenLabsFxAudioTests;AudioLayersTests`): `16 total, 16 passed, 0 failed, 0 inconclusive`.
     - `DrivingLab_ProceduralHorn_ShortPressVsHold_HudButton_ZeroGc`: krótkie muśnięcie 30 ms osiąga `short_peak = 0,900`, przytrzymanie w kabinie `hold_cab_vol = 0,630` (< `short_ext_vol = 0,900`), przycisk HUD `hud_hold = 0,900`, `gc_bytes = 0/300`.
     - `DrivingLab_TrailerRattle_BumpsAndCobbles_QuieterInCab_ZeroGc`: gładki asfalt `flat = 0` zdarzeń; pas przeszkód `DrivingLab` (progi 8/15 cm, próg zwalniający, koleiny) daje `ext_events = 27`, `cab_events = 25`, `peak_ay = 7,41 m/s2`, `peak_compRate = 2,00 m/s`, `gc_bytes = 0/1800`.
   - EditMode Win64: `1694 total, 1572 passed, 0 failed, 122 skipped (Skipped:Ignored)`, w tym `HornRattleTests` `6/6` i `HudRedesign0283Tests` `21/21`.
   - Telemetria zdarzeń, pomiary WAV i zrzuty visual-qa (`before`/`after`/`sbs`) zapisano w `artifacts/agy-horn-rattle-s24/`.


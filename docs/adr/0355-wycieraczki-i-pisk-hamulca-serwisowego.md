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

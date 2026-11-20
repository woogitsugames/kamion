# GPS — rondo Dobrzyniewo, przejazd s24 t=1540

- Gałąź: `gps-roundabout-cli`; zakres: logika C#, bez Unity, playera i buildów gry, bez push.
- Przyczyna: `game/Assets/_Project/Core/Navigation/RoutePlanner.cs:418` przypisywał rondo wyłącznie do punktu wjazdu; `RouteTracker.cs:105–108` odrzucał manewr już metr przed tym punktem (`ms > s + 1f`). Na pierścieniu następny manewr pochodził więc z Knyszyna, ponad 10 km dalej.
- Rzeczywisty graf DK65-06 zawiera rondo Dobrzyniewo i generuje poprawnie zjazd **2**. Regresja przed poprawką: oczekiwany indeks manewru 0, otrzymany 1. Nie stwierdzono utraty ronda przez małą liczbę zjazdów, granicę kafla ani łączenie skrętów.
- `RoutePath.cs:33,111,145`: dodano `ManEndPoint`, domyślnie równy punktowi manewru, resetowany przy dodaniu oraz kopiowany przez `CopyFrom`.
- `RoutePlanner.cs:419`: koniec ronda jest początkiem wybranej krawędzi zjazdowej (lub końcem ścieżki, jeśli cel leży na pierścieniu).
- `RouteTracker.cs:106–111`: manewr pozostaje aktywny do zjazdu włącznie. Przed wjazdem odległość wskazuje wjazd; na rondzie — zjazd. Dalsze rondo pojawia się po wyjeździe.
- `UI/Navigation/NavTrip.cs:293–298`: składanie ścieżek przelicza oba punkty manewru do wspólnej geometrii. `Gameplay/NavStreamFollower.cs:168` wywołuje `SwitchRegion`; obsługuje zmianę kafla, nie generuje manewrów i nie wymaga zmiany.
- EditMode `NavRoutingTests.cs:17`: rzeczywisty przejazd południe→zachód DK65-06, drugi zjazd, ostatnie 0,5 m przed wjazdem, wszystkie punkty pierścienia, odległość do zjazdu, postój oraz wyjazd. Test dodany; Unity zgodnie z poleceniem nie uruchamiano.
- Odpowiednik .NET w `tools/nav-runner/Tests/NavRoutingTests.cs`; dodatkowo `NavTripRoundaboutTests.cs:21`: trasa do Tykocina od DK65-05, ponowne złożenie w ramie DK65-06, `CopyFrom`, właściwy koniec ronda, dalsze rondo ze zjazdem 3 dopiero po wyjeździe, zero GC podczas śledzenia ronda.
- Nav-runner kompiluje teraz także oryginalny `NavTrip.cs`; shim JSON służy do odczytu istniejącego pliku podróży w testach .NET.
- `dotnet test tools/nav-runner/Tests/Tests.csproj --verbosity minimal --logger "trx;LogFileName=nav-tests.trx" --results-directory artifacts/gps-roundabout`: **98/98 PASS**, 0 pominiętych.
- `dotnet run --project tools/nav-runner/Runner/Runner.csproj`: **ALL OK**, 36 tras wzorcowych, 0 różnic, 0 B GC (10 planowań + 2000 aktualizacji).
- Dowody w tym worktree: `artifacts/gps-roundabout/nav-tests.trx`, `artifacts/gps-roundabout/runner.log`; `git diff --check` PASS. Weryfikacja obrazu HUD w playerze pozostaje poza zakresem tej sesji.

# DK8: snapping startu do przeciwnej jezdni

Gałąź: `nav-uturn-alt`. Unity nie było uruchamiane.

## Przyczyna odtworzona na danych projektu

`NavStreamFollower.StartTrip` uruchamia `NavTrip`, którego `PlanLeg` przekazuje pozycję i kurs ciężarówki do
`RoutePlanner.Plan`. Planer wybierał jedną krawędź startową przez `RouteGraph.Snap`, wyłącznie według odległości.
Kurs był uwzględniany dopiero podczas inicjalizacji A*: kara `AgainstHeadingS` nie pozwalała już zmienić jezdni.
Jeżeli nieco bliżej była przeciwna jezdnia jednokierunkowa, ścieżka zaczynała się w kierunku przeciwnym do kursu
pojazdu i prowadziła do rzeczywistego połączenia jezdni. Generator manewrów sumował dwa bliskie skręty w U-turn.
Sama klasyfikacja manewru była zgodna z taką błędnie wybraną ścieżką.

Reprodukcja na zatwierdzonym `bialystok-industrial-c_route.bytes`:

- start lokalny E/N `(-537, -270)`, kurs `-16.2°`, cel `(-734.943, 695.352)`;
- najbliższa krawędź: 526, jezdnia na południe, odległość 6.404 m;
- przed poprawką regresja wymagała 530, ale otrzymała 526 (test uruchomiony i czerwony);
- ścieżka oparta wyłącznie na odległości: 1420.222 m, U-turn −181.253° za 196.375 m;
- po poprawce: początek na 530, jezdni na północ, 1022.030 m, bez U-turn;
- dla kursu `163.8°` oraz nieznanego kursu (`NaN`) pozostaje 526 i rzeczywisty U-turn.

To reprodukcja mechanizmu zgłoszonego błędu, a nie odtworzenie konkretnej klatki z napisem „300 m”.
Nie otrzymano logu pozycji/kursu/celu z tego przejazdu.

## Sprawdzony przepływ danych i zmiana

`nav_trips.json` zawiera kolejność kafli, punkty przejścia i cel, bez listy manewrów.
`tools/ui/build_nav_map.py` zapisuje KNAV z trasą kontrolną `route_start.json`; `scripts/export-route.py`
wyznacza tę trasę przez skierowany graf worldgen i `roads.route.lane_route`.
Nawigacja Live w kabinie odczytuje manewry planera C#, a nie wykrywa ich ponownie z KNAV.
Przejrzano również obliczanie kątów i scalanie skrętów w `RoutePlanner.BuildManeuvers` oraz składanie etapów w
`NavTrip.Compose`. Do odtworzenia wystarcza jeden kafel, bez zmiany ramek streamingu lub łączenia etapów.

Planer ponownie rozpatruje start, gdy najbliższa krawędź jednokierunkowa biegnie przeciw kursowi.
Szuka kierunkowo zgodnej krawędzi w promieniu ograniczonym do odległości najbliższej + 15 m i dotychczasowych 60 m.
15 m i próg zgodności 60° to WORKING_VALUE. Drogi dwukierunkowe dopuszczają zgodność w obu kierunkach.
Brak bliskiego zgodnego kandydata zachowuje pierwotny snap. Strzałka i generator manewrów nie zostały zmienione.

## Weryfikacja

- Dodano dwa testy EditMode w istniejącym `NavRoutingTests.cs` i ich odpowiedniki w `tools/nav-runner`:
  rzeczywisty DK8 (w tym zachowanie prawdziwego U-turn) oraz brak przeskoku na odległą / poprzeczną drogę.
- `dotnet test tools/nav-runner/Tests/Tests.csproj --no-restore --logger 'trx;LogFileName=nav-uturn.trx' --results-directory artifacts/nav-uturn/tests`
  — **96/96 PASS**, w tym istniejące testy golden routes, ograniczeń, reroutingu i GC.
- Dowody lokalne: `artifacts/nav-uturn/tests/nav-uturn.trx`, `artifacts/nav-uturn/repro.txt`.
- `git diff --check` — PASS. Python nie został zmieniony, pytest nie dotyczy tej poprawki.
- Nieweryfikowane: Unity EditMode, kompilacja Unity/Windows/Android, przejazd playera i wygląd kabiny;
  dokładne położenie ze zgłoszenia oraz dobór progu 15 m na całej sieci dróg.

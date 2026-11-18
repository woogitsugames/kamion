# REVIEW s23 code — `SpawnSafety` r2: start nie za zamknięciem wyjazdowym (D18, temat 4)

- Commit: `8778bbe5a` „fix(spawn-fix-0262): P2-1 …” (rodzic `ded16aed7`). Pliki kodu:
  `game/Assets/_Project/Gameplay/SpawnSafety.cs` (+12/−2), `DrivingLabBootstrap.cs:416-417` (log `[START]`),
  `Tests/PlayMode/RouteSpawnTests.cs:98-133` (nowy test); ADR `docs/adr/0262-start-poza-zaporami.md` (Wyniki i Otwarte).
- Kontekst: ADR 0262, recenzja s22 punkt P2-1 („start za rzędem wyjazdowym, przodem do krawędzi kafla”).

## Werdykt: OK (poprawka P2-1 poprawna; jedna regresja P2 w przypadku brzegowym)

## Poprawność (`SpawnSafety.cs:36-73`)
- `limit` = min po rzędach wyjazdowych (`!c.entry`) leżących za strefą wjazdu, liczony jako
  `max(entry, c.s − BehindClosureM)`. `entry = SafeStartS(crossings, 0, length)` to najdalszy wjazd + 25 m
  (`StartClearance.cs:93-99`, z obcięciem do długości), więc reguła wjazdu wygrywa na krótkiej trasie, tak jak opisano.
- Start za `limit` cofa się do `limit`, a powody są łączone przez `" + "`. Pętla kolizji (`:60`) nie wychodzi poza
  `limit`, więc start nie „ucieknie” za wyjazd, szukając wolnego miejsca. Przy `limit = 215 m` przód zestawu stoi
  na 215 + 5,15 = 220 m, czyli 20 m przed rzędem. Tablice (`BoardsM` 0,75 m) są poza zestawem.
- Kierunek `entry`/`exit` w `StartClearance.Crossings:76` (`entry = db < da`, czyli trasa idzie od krawędzi do
  środka) jest spójny z testem: `headingDeg = 45°` = kierunek trasy, czyli trasa wychodzi przez rząd → `exit`.
- Log `DrivingLabBootstrap.cs:417`: dla zapieczonego spawnu (`m_RouteS < 0`) bierze `NearestRouteS(route, spawnPoint)`.
  Gdy bezpiecznik przesunął start, `ResolveRouteStart` (`:394`) ustawia `m_RouteS = s`, więc log pokazuje stację
  po przesunięciu. Poprawne.
- Wydajność i GC: `ResolveStartS` działa raz na start lub respawn, nie w pętli jazdy. `s_Crossings` i `s_Hits` są
  statyczne i wielokrotnego użytku. Alokacje są tylko w łańcuchach `reason` przy przesunięciu i w
  `List.Sort(Comparison)` w `Crossings`, czyli jednorazowo. Fizyka: tylko zapytanie `OverlapBoxNonAlloc`, brak
  zapisu transformacji pojazdu poza spawnem (spawn to dozwolone ustawienie pozy początkowej).

## Test (`RouteSpawnTests.RouteS_AtOrPastTheExitClosure_MovesBackInFrontOfIt`)
Trasa 300 m, punkty co 10 m, rząd na `points[24]` (s = 240). Oczekiwane 230 → 215 i 290 → 215 (`LogAssert.Expect`
z regexem powodu) oraz 120 bez zmian. Asercje pozycji < 1,5 m i kursu < 2°. Test jest dobry: sprawdza obie strony
rzędu i przypadek bez ruchu. `TestRoute` nie jest niszczony na końcu, ale następny test ładuje scenę `Single`, więc obiekt znika
(tak samo w sąsiednich testach klasy). Nieuruchomiony w chmurze. Autor raportuje PlayMode `RouteSpawnTests` 5/5 i EditMode 61/61
(`artifacts/spawn-fix-0262/*post-merge.xml`). Pytest `tests/gis/test_start_clear_0262.py` uruchomiłem w chmurze:
zielony (w zestawie 124 passed, raport tematu 1).

## Uwagi

### P2
1. **`SpawnSafety.cs:60` — regresja: przy przeszkodzie tuż przed wyjazdem bezpiecznik nie ma dokąd iść.** Przed r2
   szukanie szło do 200 m naprzód. Teraz kończy się na `limit`, więc gdy start stoi na `limit` (albo kilka metrów
   przed nim) i jest kolizja, od razu jest `LogError` i start **w kolizji** (`:70-72`). Wcześniej zestaw zwykle
   znajdował miejsce dalej (za wyjazdem, co było złe z innego powodu). To jest otwarty punkt P2-2 z ADR 0262
   „Otwarte 7”, ale r2 zawęża okno, więc rośnie jego waga. **Poprawka:** po nieudanym szukaniu naprzód szukać wstecz
   od `from` do `entry` tym samym krokiem (`for d = StepM; from − d >= entry; d += StepM`), a dopiero potem `LogError`.
   Do tego test PlayMode z kolizją (BoxCollider) na 215 m i wyjazdem na 240 m → oczekiwane < 215.
2. **`SpawnSafety.cs:55` — rząd wyjazdowy w strefie wjazdu jest ignorowany.** Warunek `c.s > entry` pomija wyjazd
   leżący między rzędem wjazdowym a `entry` (= wjazd + 25 m), np. trasę przecinającą róg kafla (wjazd 10 m, wyjazd
   30 m). Start ląduje wtedy na 35 m, czyli za wyjazdem, przodem do krawędzi. To przypadek, który r2 miało usunąć.
   Takie trasy są dziś wykluczone przez dane (najkrótsza trasa 262 m po starcie). **Poprawka:** w tym przypadku
   `LogError("[START] route has no valid start window …")` zamiast cichego startu, a docelowo walidacja w
   `export-route.py`/`test_start_clear_0262.py` (odstęp wjazd–wyjazd ≥ 25 + 25 + długość zestawu).
3. Drobne: `NearestRouteS` (`DrivingLabBootstrap.cs:397-410`) bierze najbliższy segment w 2D. Na trasie, która
   przechodzi dwa razy obok tego samego miejsca (pętla, rondo), może wybrać złą stację, ale dotyczy to tylko logu
   i zapieczonego spawnu. Na razie tylko do odnotowania.

## Zgodność z CLAUDE.md
Bez zmian w `ProjectSettings/`, `Packages/` i asmdef. `BehindClosureM`/`MaxSearchM` są oznaczone WORKING_VALUE.
ADR 0262 zaktualizowany (Wyniki, Otwarte). Dowody w `artifacts/spawn-fix-0262/`.

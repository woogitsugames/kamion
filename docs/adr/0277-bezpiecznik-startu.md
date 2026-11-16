# ADR 0277 — bezpiecznik startu: strefy między zamknięciami, szukanie wstecz, brak miejsca = brak startu
Status: Proposed — gałąź `spawn-safety-0277` (chmura H r3, zadanie H13); czeka na weryfikację lidera (Unity, build Windows).
Powiązane: ADR 0262 (start za zamknięciem krawędzi kafla, `SpawnSafety`, recenzja `docs/reports/REVIEW-2026-11-15-s23-code-spawn-fix-0262.md`
P2-2…P2-9), ADR 0169 (zamknięcia krawędzi, 60 m w głąb), ADR 0229 (katalog regionów, menu), ADR 0082 (`WorldSafetyNet`).

## Kontekst
Po ADR 0262 start z menu i ze starej sceny stoi za zamknięciem wjazdowym, ale recenzja zostawiła P2: przy braku wolnego
miejsca w 200 m przed punktem startu zestaw rodził się **w colliderze** (`LogError` + `return from`) — dokładnie scenariusz
zgłoszenia właściciela (naczepa wyrzucona pionowo, `artifacts/owner-a16-s22/3.webp`); szukanie szło tylko do przodu;
`SafeStartS` brał maksimum po wszystkich rzędach wjazdowych (także daleko przed startem); krótkie trasy; pudło proste na łuku;
bufor 128 bez obsługi przepełnienia; brak testów ścieżki starej sceny i zapieczonego spawnu importera.

## Decyzja
1. **Czysta funkcja wyboru miejsca** `Game.Gameplay.StartSearch` (bez fizyki, bez alokacji, testowalna w .NET):
   wejście = przecięcia trasy z rzędami zamknięć (`StartClearance.Crossings`, jak w ADR 0262), długość trasy, żądane `s`,
   sonda `IStartSpaceProbe` (wywołanie generyczne — struktura nie jest pakowana); wyjście `StartSearchResult`
   (`Unchanged` / `Moved` / `NoSpace`, `s`, powody jako flagi, strefa, liczba zapytań).
   - **Strefy.** Rzędy tną trasę na odcinki; odcinek jest „w kaflu”, gdy zaczyna się rzędem, przez który trasa **wjeżdża**
     (albo początkiem trasy, gdy pierwszy rząd jest wyjazdowy lub rzędów nie ma). Użyteczna część odcinka zostawia
     `BehindClosureM` = 25 m od rzędów na obu końcach (ADR 0262, WORKING_VALUE); odcinek za krótki na to — sam obrys
     (tył naczepy + deski + 0,5 m za wjazdem, przód + deski + 0,5 m przed wyjazdem); za krótki i na to — nieużyteczny.
     Żądany start poza strefą → najbliższy punkt strefy (remis: do przodu). Liczą się tylko rzędy wokół startu (P2-3).
   - **Miejsce.** Sonda sprawdza punkt; zajęty → do przodu co `StepM` = 2 m do `MaxForwardM` = 200 m (nie dalej niż koniec
     strefy), potem **wstecz** co 2 m do `MaxBackM` = 200 m (nie przed początkiem strefy = 25 m za zamknięciem wjazdowym).
     Kroki i limity: WORKING_VALUE (2 m i 200 m przeniesione z ADR 0262; 200 m wstecz — symetrycznie, niemierzone).
   - Nic wolnego → `NoSpace`. Nigdy nie zwraca zajętego miejsca do postawienia.
2. **Sonda w grze** (`SpawnSafety.PhysicsProbe`): (a) zgięcie trasy pod prostym zestawem — `StartSearch.MaxLateralOffset`
   (największa odległość osi trasy od prostej zestawu od tyłu naczepy do przodu ciągnika) > `MaxCurveOffsetM` = 1,0 m →
   zajęte (P2-8; WORKING_VALUE: powyżej 0,88 m zmierzonego w punkcie startu katalogu dk65-06, największego z 21 regionów na
   danych `Data/Regions/*/route_start.json` 2026-11-16; rondo dk65-06 w 60 m za startem daje 7,1 m); (b) pudło zestawu
   `Physics.OverlapBoxNonAlloc` jak w ADR 0262; pełny bufor (128) = zajęte (P2-9).
3. **Brak miejsca przy starcie sceny** (`DrivingLabBootstrap.Awake` / `RestartFromSceneStart`): zestaw **nie jest stawiany** —
   ciągnik i naczepa wyłączone (`SetActive(false)`) przed pierwszym krokiem fizyki, bootstrap wyłączony, `LogError`
   `[START] no free place for the combination …`, powrót do menu (`Boot`) i jednorazowy komunikat w menu (bursztynowa linia pod
   tytułem, `BootMenu.ShowNotice`, tekst `StartSafetyTexts.NoSpaceMessage`, PL):
   „Nie udało się ustawić zestawu na starcie: na drodze w tym regionie nie ma wolnego miejsca. Ciężarówka nie została
   postawiona. Wybierz inny region lub inny start.”
   **Dlaczego menu, a nie automatycznie „inny punkt”:** bezpiecznik już przeszukał całą strefę wjazdową w granicach limitów;
   dalszy automatyczny skok (inny koniec trasy, inny region) postawiłby gracza w miejscu, którego nie wybrał, często przodem
   do zamknięcia wyjazdowego, i ukryłby błąd danych, który trzeba naprawić eksportem katalogu / reimportem. Menu jest jedynym
   miejscem, gdzie gracz świadomie wybiera start, region zostaje zapamiętany (`menu.region`), więc wybór innego to jedno
   kliknięcie. Bez sceny `Boot` w buildzie (nie dotyczy gry) scena zostaje z wyłączonym pojazdem.
   **Respawn w trakcie jazdy** (`SetRouteSpawn`, `route_s` z testów/API): przy `NoSpace` zestaw zostaje tam, gdzie jest
   (jedzie, więc nie stoi w colliderze), HUD: „Brak wolnego miejsca na trasie: zestaw zostaje na miejscu.”
4. **Importer** (`WorldSceneBuilder`) piecze spawn tą samą regułą stref (`StartSearch.BakedSpawnS`) zamiast `SafeStartS`;
   brak strefy = `LogError` w imporcie (gra wtedy odmawia startu). Na danych 21 regionów wynik = `startS` katalogu (test).
5. Pozycja startu: bez zmian w ścieżce postawienia (`VehicleBody.ResetPose`/`SetPose`, `TrailerBody.SetPose` ustawiają
   `Rigidbody.position/rotation` i zerują prędkości, potem `Physics.SyncTransforms`), raz w `Awake` przed pierwszym
   `FixedUpdate`; bezpiecznik nie dodaje ruchu w pętli jazdy. Test PlayMode sprawdza, że pierwszy `FixedUpdate` widzi
   finalną pozycję i zerowe prędkości.
6. Zero GC: `StartClearance.Crossings` sortuje wstawianiem (bez komparatora `List.Sort`), `StartSearch` bez alokacji (test
   .NET `GC.GetAllocatedBytesForCurrentThread` = 0 i `Is.Not.AllocatingGCMemory` w Unity), bufor `Collider[128]` statyczny.
   Napisy logu budowane tylko przy przesunięciu / błędzie (raz na start). Nic nie działa w `Update`/`FixedUpdate`.
7. Teksty gracza w `Game.Gameplay.StartSafetyTexts` (tabela PL jak `PcSettingsTexts`; projekt nie ma jeszcze pakietu
   lokalizacji — przy jego wdrożeniu pola stają się kluczami tabeli PL).

## P2 z recenzji 0262
| P2 | Stan | Jak / dlaczego |
|---|---|---|
| P2-2 brak miejsca = start w kolizji; brak szukania wstecz; komunikat „within 200 m” kłamie | **zrobione** | `NoSpace` → zestaw nie jest stawiany, menu z komunikatem PL (p. 3); szukanie wstecz do zamknięcia wjazdowego; log podaje strefę, oba limity i liczbę zapytań. Testy: `StartSearchTests` (wstecz, ograniczenie, NoSpace), PlayMode `StartSafetyTests` (respawn, start sceny → menu) |
| P2-3 `SafeStartS` = maksimum po wszystkich rzędach wjazdowych | **zrobione (runtime + importer)** | strefy liczą tylko rzędy wokół startu. `StartClearance.SafeStartS` zostaje dla testu katalogu ADR 0262 i eksportera (zgodność sprawdza `ZoneRule_KeepsTheCatalogStart_AndRepairsTheOld12mSpawn`) |
| P2-4 krótkie trasy | **zrobione** | odcinek < 50 m → sam obrys; za krótki → brak strefy → `NoSpace` / błąd importu zamiast startu za zamknięciem wyjazdowym. Eksporter katalogu (Python) bez zmian — dziś najkrótsza trasa 352 m, pytest 0262 łapie start przed zamknięciem |
| P2-5 brak testu ścieżki starej sceny (bez menu, bez `-route_s`) | **zrobione** | `RestartFromSceneStart` = ta sama ścieżka co `Awake`; PlayMode: zapieczony spawn 12 m → 85 m, wolny spawn bez zmian; EditMode na danych 21 regionów: reguła stref naprawia stary spawn 12 m tak jak ADR 0262 |
| P2-6 brak testu zapieczonego spawnu importera; `WorldScenes` pomijane bez scen | **zrobione** | EditMode `ImportedScene_BakedSpawnIsTheImportersStart` (`WorldScenes`: `Spawn_DepotGate` = `BakedSpawnS` z danych importu, ciągnik na spawnie, bezpiecznik nic nie rusza) + nigdy niepomijany test danych (`ZoneRule_…`: importer upiekłby `startS` katalogu). Sceny poza gitem nadal → `Assert.Ignore` w `WorldScenes` |
| P2-7 stare binaria nie są naprawione | **pominięte (fakt, nie kod)** | wymaga nowego buildu (komendy w PR); runtime naprawia stare sceny w nowym buildzie |
| P2-8 pudło proste na łuku | **zrobione** | test zgięcia `MaxLateralOffset` > 1,0 m = zajęte (rondo, ciasny łuk); krawężnik/wysepka < 0,5 m nadal nie wchodzi do pudła — zgięcie to łapie pośrednio. Start katalogu każdego regionu ≤ 1,0 m (test EditMode) |
| P2-9 bufor 128 | **zrobione** | pełny bufor = miejsce zajęte (`StartBlock.Overflow`) zamiast „wolne” |

## Budżet
Draws/tris: bez zmian. Runtime: raz na start ≤ 1 + 100 + 100 zapytań `OverlapBoxNonAlloc` (było ≤ 101) + test zgięcia
(przejście po punktach trasy w obrysie) na zapytanie; zero alokacji na ścieżce „wolne”; zero pracy w pętli jazdy.
Telefon/PC: niemierzone (chmura bez Unity).

## Walidacja
- .NET (`tools/spawn-runner`, ten sam plik testów co EditMode, shim UnityEngine): `StartSearchTests` **13/13 PASS**
  (dotnet 8, NUnit 3.14, 2026-11-16). Kompilacja `SpawnSafety`+`StartSearch`+`StartClearance` na shimie fizyki: 0 błędów;
  parser Roslyn (C# 9) 12 zmienionych plików: 0 błędów składni.
- **NIEuruchomione** (brak Unity w chmurze): EditMode `StartSearchTests` (w tym `Is.Not.AllocatingGCMemory`),
  `StartClearanceTests` (nowe: `ZoneRule_…`, `ImportedScene_BakedSpawnIsTheImportersStart`), PlayMode `StartSafetyTests`
  (5) i `RouteSpawnTests` (regresja ADR 0262), build Windows, oględziny linii komunikatu w menu (visual-qa `Boot`).

## Otwarte
1. Oględziny komunikatu w menu (układ: linia między tytułem a nagłówkami kolumn, skalowanie best-fit 14–20) — render `Boot`
   z wymuszonym komunikatem nie istnieje; lider: zrzut po teście `NoFreePlace_SceneStart_…` albo ręcznie.
2. `MaxCurveOffsetM` = 1,0 m, `MaxBackM` = 200 m — WORKING_VALUE; ocena na danych po każdej zmianie tras.
3. Eksporter katalogu (Python) nadal liczy tylko start za zamknięciem wjazdowym; reguła stref sprawdzana testem EditMode.
4. Pakiety testowe `tools/spawn-runner` (NUnit 3.14, MIT; Microsoft.NET.Test.Sdk) — tylko narzędzie dev, nie trafiają do buildu.

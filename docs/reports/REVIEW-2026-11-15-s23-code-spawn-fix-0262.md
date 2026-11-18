# Recenzja kodu — `spawn-fix-0262` (ADR 0262, start poza zaporami) — s23, 2026-11-15

Recenzent: agent recenzji kodu (tylko odczyt). Przedmiot: `git diff main...spawn-fix-0262 -- . ':(exclude)artifacts'`
(15 plików, +772/−28), gałąź @ `221a30be4`, baza scalenia `418ef670c`. Unity nie było uruchamiane; liczby testów
pochodzą z XML-i na gałęzi (`artifacts/spawn-fix-0262/editmode-green.xml`: 61/61, skipped=0;
`editmode-playmode-green.xml`: 4/4; `editmode-red.xml` na starym katalogu: 41/45 failed).

## Werdykt: **SCAL warunkowo**

Brak P0. Poprawka usuwa przyczynę zgłoszenia właściciela we wszystkich 20 regionach korytarza: katalog daje 90 m,
importer piecze spawn za zamknięciem, a runtime naprawia też sceny, których nie reimportowano. Testy działają na
prawdziwych zamknięciach (`WorldEdgeBuilder.PlanRegionClosures` + `ResolveClosures`), nie na mockach. Czerwony dowód
jest prawdziwy: 41 failed na katalogu z main.

Warunki scalenia (P1):
1. Rozwiązać konflikt w `region_catalog.json` przez ponowne uruchomienie `python scripts/export-region-catalog.py`
   na scalonym drzewie, a potem pytest `tests/gis/test_start_clear_0262.py` i EditMode `StartClearanceTests`
   (także kategorię `WorldScenes` po reimporcie dk65-11 i knyszyn-s) oraz `RouteSpawnTests`.
2. Domknąć pętlę wizualną: obejrzane rendery są dla 6 z 20 regionów. Uzupełnić w ADR sekcję „Wyniki”, do której ADR
   odsyła, choć jej nie ma.

## P0
Brak.

## P1

**P1-1 Konflikt z main i nieaktualny dowód testowy.** `game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json:117`
(knyszyn-s). `git merge-tree --write-tree main spawn-fix-0262` pokazuje jeden konflikt treści, właśnie w tym pliku.
Main zmienił `routeLengthM` knyszyn-s z 2420.66 na 2420.72, a gałąź zmieniła `startS` z 12 na 90 w sąsiedniej linii.
Main zmienił też `Data/Regions/dk65-11/route_start.json` i `Data/Regions/knyszyn-s/route_start.json` (dk65-r4-s21).
`DrivingLabBootstrap.cs` i `WorldSceneBuilder.cs` scaliły się automatycznie; zmiany main w nich nie dotykają spawnu.
- Scenariusz: lider rozwiąże konflikt ręcznie, biorąc wersję gałęzi. Wtedy `test_catalog_is_what_the_exporter_derives`
  padnie na `routeLengthM` knyszyn-s, a EditMode dla dk65-11 i knyszyn-s był liczony na starej trasie.

**P1-2 Niedomknięta pętla wizualna i ADR bez wyników.** `docs/adr/0262-start-poza-zaporami.md:62` odsyła do sekcji
„Wyniki”, której w pliku nie ma. W worktree są statusy `import=0 qa=0` tylko dla 6 regionów: dk65-05, dk65-06,
knyszynska, maczka, kleeberga i knyszyn-w. Pozostałe 13 ma `.status.dead-2242`, a dk65-01 nie ma żadnego statusu.
Ponowienie działa w odłączonym procesie i nie jest skończone. Obejrzałem render dk65-05 `truck-at-gate.png`: zestaw
stoi na jezdni, zapory są daleko z tyłu i wygląda to poprawnie.
- Scenariusz: scalenie bez renderów pozostałych 14 regionów łamie żelazną zasadę 4 (visual-qa). Region z nietypową
  geometrią startu, na przykład z wiaduktem lub barierą przy pasie, nie zostanie obejrzany przed wydaniem APK/exe.

## P2

**P2-1 Wyszukiwanie wolnego miejsca idzie tylko do przodu i nie zna zamknięcia wyjazdowego.**
`game/Assets/_Project/Gameplay/SpawnSafety.cs:50` oraz `game/Assets/_Project/World/Runtime/StartClearance.cs:97`
(`SafeStartS` bierze tylko `entry`).
- Scenariusz: `-route_s` albo `SetRouteSpawn` ustawi start blisko końca trasy, na przykład `length − 70` przy rzędzie
  zapór wyjazdowych w `length − 60`. Pudło dotknie zapór, pętla przesunie start o 2 m kroki, aż tył naczepy minie rząd
  (około `length − 47`). Zestaw stanie wtedy za zamknięciem, przodem do krawędzi kafla, czyli w lustrzanym odbiciu
  zgłoszonego błędu.
- Podobnie `-route_s` większe niż stacja rzędu wyjazdowego nie jest korygowane wcale, bo pudło za rzędem jest wolne,
  a `SafeStartS` ignoruje wyjazdy.
- Start z menu jest bezpieczny: katalog plus test `CatalogStart_…AndTheRouteAheadIsOpen` pilnuje 300 m bez rzędu.
  Problem dotyczy tylko argumentu deweloperskiego i API.

**P2-2 Brak wolnego miejsca oznacza start w kolizji.** `game/Assets/_Project/Gameplay/SpawnSafety.cs:60-62`.
- Scenariusz: na 200 m trasy za żądanym punktem każde położenie pudła dotyka collidera, na przykład wąska droga z
  barierą energochłonną przy pasie wyższą niż 0,5 m. Wtedy `LogError` i `return from`, więc zestaw rodzi się w
  colliderze, a naczepa może zostać „wyrzucona” jak na zrzucie 3.webp.
- Pętla jest ograniczona (najwyżej 101 zapytań), więc nie ma pętli bez końca.
- Komunikat „within 200 m” kłamie, gdy pętlę wcześniej przerwie koniec trasy (`from + d <= length`).
- Nie ma też wyszukiwania wstecz.

**P2-3 `SafeStartS` bierze maksimum po wszystkich rzędach wjazdowych, także daleko przed startem.**
`game/Assets/_Project/World/Runtime/StartClearance.cs:96-98`.
- Scenariusz: trasa wyjdzie z kafla i wróci do niego. Możliwe jest też, że poszerzony rząd zamknięcia drogi bocznej
  przy krótkiej krawędzi (80 % długości krawędzi grafu, `±(span/2 + 1,775 m)`) przetnie pas trasy w kierunku „entry”.
  Wtedy start przeskoczy na `entry + 25 m` gdzieś w środku trasy albo na jej koniec, bo `Min(s, routeLength)`.
- Na obecnych danych 21 regionów tak się nie dzieje, co pokazuje zielony test `SafeStartS(catalog) == catalog`.

**P2-4 Krótkie trasy.** `scripts/export-region-catalog.py:56` i `StartClearance.cs:98`.
- Trasa od krawędzi kafla krótsza niż 190 m dostanie `startS = length − 100 < 90`, czyli przed zamknięciem.
  Runtime i importer przesuną start na `entry + 25`.
- Przy trasie krótszej niż około 85 m `SafeStartS` przytnie start do końca trasy, potencjalnie za zamknięciem
  wyjazdowym (patrz P2-1).
- Dziś najkrótsza trasa w katalogu ma 352 m (dk65-09), a pytest `test_start_is_inside_the_edge_closure` złapie taki
  przypadek, więc ryzyko dotyczy tylko przyszłych regionów.

**P2-5 Ścieżka „stara scena, start bez menu i bez route_s” nie ma testu.** `game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:379-381`
(`NearestRouteS(spawnPoint)`).
- To jedyna ścieżka, która naprawia sceny zapieczone ze spawnem 12 m (start `scene=<id>` przez adb). PlayMode
  `RouteSpawnTests` sprawdza tylko `SetRouteSpawn(s)` w scenie labu z syntetycznym zamknięciem.
- Scenariusz: regresja w `NearestRouteS` (na przykład inny układ `Route_start` po zmianie importera) przejdzie
  niezauważona, a stara scena znów wystartuje przed zaporą.

**P2-6 Brak testu zapieczonego spawnu importera.** `game/Assets/_Project/World/Import/WorldSceneBuilder.cs:118-127`.
- Żaden test nie sprawdza, że `Spawn_DepotGate` w zaimportowanej scenie leży na stacji `SafeStartS(catalog)`. Test
  `WorldScenes` czyta `startS` z katalogu, nie spawn ze sceny.
- Ten test robi `Assert.Ignore`, gdy sceny nie ma (`StartClearanceTests.cs:175`), bo sceny są poza gitem. W innym
  worktree lub na CI kategoria może więc być w całości pominięta. Tutaj w XML jest skipped=0.
- Scenariusz: importer zapiecze stary spawn, a gra i tak wystartuje dobrze dzięki runtime. Kamery kontrolne
  `truck-at-gate` / `cab-gate` będą jednak pokazywać zły punkt i nikt tego nie wykryje.

**P2-7 Stare binaria nie są naprawione.** Opis faktu, nie błąd kodu.
- Nowy build (APK/exe) ze starymi scenami jest naprawiany w runtime: menu podaje `startS = 90` z katalogu w
  Resources, a start bez menu przechodzi przez spawnPoint, `NearestRouteS` i `SafeStartS` na `WorldBoundary.closures`.
- Już zbudowany APK d67-full i istniejący exe nie są naprawione. Potrzebny jest nowy build. ADR „Otwarte 2” mówi o
  tym tylko pośrednio.

**P2-8 Pudło zestawu jest proste wzdłuż stycznej w punkcie s.** `SpawnSafety.cs:91-103`.
- Odpowiada to rzeczywistemu postawieniu, bo `CombinationPlacement.Coupled` ustawia przegub 0.
- Na łuku (rondo, ciasny zakręt) naczepa ustawiona prosto może jednak wystawać poza pas. Pudło zaczyna się 0,5 m nad
  jezdnią, więc nie wykryje krawężnika ani wysepki (0,12–0,15 m), tylko obiekty wyższe.
- Scenariusz: `-route_s` na rondzie postawi koła naczepy na wysepce. To zachowanie istniało przed tą gałęzią;
  gałąź go nie pogarsza.

**P2-9 Bufor 128 colliderów** (`SpawnSafety.cs:29`).
- Przy przepełnieniu `OverlapBoxNonAlloc` zwraca tylko część trafień. W pudle zestawu około 17,5 × 3,6 × 3,5 m to
  nierealne, więc pozycja niepotwierdzona i niska.

## Odpowiedzi na pytania zlecenia

### 1. Poprawność

**Start z menu i katalogu (20 regionów korytarza)** jest poprawny.
- `startS` wynosi 90 m. Zmierzone stacje rzędu wjazdowego to od 14,5 do 61,2 m, więc najgorszy przypadek daje
  61,2 + 25 = 86,2 m, czyli mniej niż 90.
- Tył naczepy (90 − 11,30 = 78,7 m) stoi co najmniej 16,7 m za rzędem, a test wymaga ≥ 0,5 m od desek.
- Test EditMode na prawdziwych zamknięciach plus test `WorldScenes` (pudło wolne, 300 m trasy bez collidera) jest
  zielony dla 21 regionów.

**Zamknięcie skośne:** rząd jest poszerzony o połowę szerokości pojazdu plus zapas, a stacja jest mierzona na osi
pasa. Zapas 25 − 12,55 m pokrywa skos tylnego narożnika naczepy do bardzo dużych kątów.

**Region C:** brak zamknięć na trasie, start 12 m. Szlaban bazy na 244 m jest daleko od pudła startu (0,7–17,2 m).
Starty G3-A (12 m) i G3-B (1232 m) w C nie mają zamknięć.

**Skrzyżowanie:** sprawdziłem tablicę `edge` w `route_start.json`, czyli węzły o `degree ≥ 3` w oknie
[startS − 26,3; startS + 20,15].
- Żaden węzeł skrzyżowania nie leży w obrysie zestawu [78,7; 95,15] m.
- Najbliższe: dk65-06 w 70,1 m (8,6 m za tyłem naczepy) i 104,1 m (9 m przed zderzakiem); knyszyn-w w 68,0 m.
- W dk65-05 nie ma węzła w oknie.

**Pod prąd i poza jezdnią:** przesunięcie idzie po punktach trasy (środek prawego pasa) ze styczną trasy jako
kierunkiem, więc nie zmienia pasa ani kierunku. Wyjątki opisują P2-8 (łuk) i P2-1 (wyjście za zamknięcie wyjazdowe).

**Pętla bez końca:** nie występuje (P2-2).

**Brak miejsca:** start w kolizji z `LogError` (P2-2).

**Inne przypadki:** `-route_s` opisuje P2-1, trasy krótkie P2-4, stare sceny, APK i exe P2-5 i P2-7.

**Kolejność wykonania:** `WorldCollisionCooker` ma `[DefaultExecutionOrder(-900)]` i włącza MeshCollidery w `Awake`
przed `DrivingLabBootstrap` (-200). Zapory to `BoxCollider` (`WorldEdgeBuilder.cs:148`). Zapytania w `Awake`
bootstrapa widzą więc świat.

### 2. Teleport a zasada „żadnego `transform.position +=`”

Zasada jest zachowana.
- `ResolveRouteStart` jest wołany w `Awake` (`DrivingLabBootstrap.cs:216`) przed `Spawn` (`:221`), czyli przed
  pierwszym `FixedUpdate`.
- Ścieżka postawienia nie jest zmieniona przez gałąź: `SpawnAt` → `VehicleBody.ResetPose` (zeruje prędkość liniową i
  kątową, robi `Initialize` solvera) → `trailer.Initialize` + `ConnectTrailer(coupled)` → `CombinationPlacement.Coupled`
  (przegub 0) → `TrailerBody.SetPose` (zeruje prędkości) → `Physics.SyncTransforms`.
- `SetRouteSpawn` w trakcie gry to jednorazowy reset tą samą ścieżką co istniejący reset R.
- Gałąź nie dodaje żadnego ruchu pojazdu w pętli jazdy.

### 3. Alokacje GC i koszt

Nic nowego nie działa w `Update` ani `FixedUpdate`.
- `SpawnSafety` jest wołane tylko z `ResolveRouteStart`, czyli w `Awake` i w `SetRouteSpawn` (testy/API).
- `RecoverToSpawn` z `WorldSafetyNet` (`:141`, rzadkie zdarzenie) woła `Spawn` bez `SpawnSafety`.
- Jednorazowe alokacje:
  - `List.Sort(Comparison)` w `StartClearance.cs:79`;
  - sklejanie stringów `reason` i logu tylko przy przesunięciu;
  - `new List` w przeciążeniu `SafeStartS(points, …)` (`:88`), używanym tylko przez importer i testy.
- Bufor `Collider[128]` jest statyczny.
- Koszt: najwyżej 101 zapytań `OverlapBoxNonAlloc` plus jedno przejście polilinii na zamknięcie, raz na start.
  Pomiar na urządzeniu: niemierzone.

### 4. Testy

**Złapałyby regresję.**
- Dla katalogu i geometrii zamknięć: test na prawdziwych zamknięciach z `WorldEdgeBuilder` przez refleksję
  (`Game.World.Import.Editor`). Czerwony dowód: 41/45 na starym katalogu.
- Dla obrysu pojazdu: `Footprint_FollowsTheVehicleDefinitions` czyta JSON-y fizyki i `TractorDimensions` /
  `TrailerDimensions`.
- Dla zgodności katalogu z eksporterem: pytest.

**Luki:**
- ścieżka spawnPoint starej sceny (P2-5);
- zapieczony spawn importera (P2-6);
- `WorldScenes` pomijane bez scen (P2-6);
- zamknięcie wyjazdowe i `-route_s` za nim (P2-1);
- „brak wolnego miejsca” (P2-2).

PlayMode używa syntetycznego zamknięcia w scenie labu, co jest celowe dla bezpiecznika.

### 5. Zmiany poza zakresem

- `ProjectSettings/`, `Packages/`, `*.asmdef`, sceny `.unity`, prefaby, `_Generated`, `route_start.json`: **brak zmian**.
- Plik współdzielony: `game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json`. Ma 20 × `startS` 12 → 90
  i jest w konflikcie (P1-1).
- `RegionStart.DefaultStartS` wskazuje teraz na `StartClearance.DefaultStartS`. Wartość się nie zmieniła (12 m).
- `RegionSelectTests.cs:225`: asercja na `route_s=` z katalogu zamiast stałego `12.0`.
- Testy EditMode sięgają do `Game.World.Import.WorldEdgeBuilder` przez refleksję (`Type.GetType(..., true)`). Zmiana
  nazwy assembly lub metody wywali test w czasie wykonania, nie przy kompilacji. Nie wymagało to zmiany asmdef.
- 33 pliki w `artifacts/spawn-fix-0262/` (logi, XML-e, 6 par renderów jako wskaźniki LFS, skrypty `run-*.ps1`).

### 6. Konflikty z main

`git merge-tree --write-tree main spawn-fix-0262`: **1 konflikt**,
`game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json`.
- Automatycznie scalone: `DrivingLabBootstrap.cs`, `WorldSceneBuilder.cs`. Zmiany main w nich nie dotykają spawnu.
- Rozwiązanie: przyjąć dowolną stronę, uruchomić eksporter na scalonym drzewie, potem testy (P1-1).

## Niepotwierdzone
- Czy w wąskich przekrojach (bariera energochłonna lub skarpa wyższa niż 0,5 m w odległości do 1,775 m od osi pasa)
  pudło startu nie da fałszywego „zajęte” i nie przesunie startu. Na 21 obecnych scenach przy 90 m nie daje
  (test `WorldScenes` zielony). Dla `-route_s` w innych miejscach nie sprawdzałem.
- Wpływ floating origin, jeśli przesuwa korzeń regionu bez `Route_start`. `Route_start` nie jest dzieckiem
  `Region_*`, a `Crossings` porównuje lokalne x/z obu. Dziś korzeń różni się tylko przesunięciem w Y, więc działa.

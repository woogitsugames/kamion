# Recenzja kodu — chmura H, runda 3 (PR #113, #118, #117, #141, #142) — s23, 2026-11-16

Recenzent: agent recenzji kodu, tylko odczyt. Nic nie scalone ani nie wypchnięte.
Podsumowanie autora: `origin/claude/epic-euler-pxcll3:docs/reports/CLOUD-H-R3-SUMMARY-2026-11-16.md`.
Main w chwili recenzji: `origin/main` = `08c2e21f8`. Wszystkie pięć gałęzi ma tę samą bazę scalenia `639da4e54`.

Oznaczenia dowodów: **[uruchomione]** to test lub przebieg wykonany przez recenzenta. **[kod]** to wniosek z czytania kodu,
bez uruchomienia. **[przypuszczenie]** to wniosek niepotwierdzony. Numery linii podaję w plikach na sha PR-a.

## Werdykty

| PR | gałąź @ sha | werdykt | blokuje |
|---|---|---|---|
| #113 | `jackknife-0228` @ `a84ad5e14` | **SCAL warunkowo** | EditMode `BodyBoxGeometryTests` + PlayMode `CombinationLabTests`/`KerbStrikeParityTests` w Unity |
| #118 | `perf-loop-0244` @ `ae052e54b` | **SCAL warunkowo** | kompilacja i zielony `PcInputGc0244Tests` w Unity (decyzja o asmdef — niżej) |
| #117 | `controls-0243` @ `0710168df` | **SCAL** (po EditMode/PlayMode) | — |
| #141 | `spawn-safety-0277` @ `cd03fb181` | **SCAL warunkowo** | P1-1: pętla scen przy `-scene` (poprawka 3–5 linii w `GameBootstrap`) |
| #142 | `pc-polish-0276` @ `746c2fd28` | **SCAL** (konflikt w `BootMenu.cs` rozwiązany jak niżej) | — |

## Testy uruchomione przez recenzenta (łańcuch scalony w scratch, poza Unity)

Łańcuch zbudowałem jako odłączony worktree na `08c2e21f8` i scalałem w kolejności #113 → #118 → #117 → #141 → #142.
Testy szły na niezatwierdzonym scaleniu wszystkich pięciu PR-ów, z `BootMenu.cs` w wersji #142. Żaden z projektów .NET nie
kompiluje `BootMenu.cs`. 54 testy pytest obejmują też nowe testy #142. Worktree jest już usunięty.

- `tools/spawn-runner` **13/13**; `tools/controls-runner` **13/13**; `tools/loop-runner` **30/30**; `tools/physics-runner/Tests` **319/319** (dotnet 10.0.403, cel net8.0).
- Pełny runner fizyki (`--no-multi`): **149 scenariuszy / 915 checków PASS**.
- Sondy H11 (`artifacts/jackknife-0228/h11/probe_scenarios`): 2 z 4 nie spełniają kryterium „0 kontaktu”. To zgodne z „Otwarte 1” ADR 0228 (szczegóły w #113).
- `pytest tests/dist tools/pcperf`: **54 passed**.
- Kąt zgięcia trasy pod zestawem (`StartSearch.MaxLateralOffset`) przeliczyłem skryptem Python na danych **main**. Na danych bazy skrypt odtwarza 0,876 m dla dk65-06.
- **Nieuruchomione:** cała warstwa Unity (kompilacja, EditMode, PlayMode), build Windows, zrzuty. Test .NET „38/38” z #142 nie jest w repo, więc nie da się go odtworzyć (P2-142-1).

---

## #113 — kontakt kabina–naczepa jako ogranicznik przegubu (ADR 0228) — SCAL warunkowo

P0: brak. P1: brak.

**Energia i drgania [uruchomione + kod].** Wiersze kontaktu to jednostronna, miękka sprężyna z tłumieniem (forma Catto).
- Impuls normalny jest ≥ 0. Nie ma odbicia: `dj = Math.Min(dj, _cMN[c] * (recovery - vn))` (`FifthWheel.cs:353`), z `contactRecoverySpeed` = 0,05 m/s.
- Punkt spekulatywny może tylko domknąć szczelinę: `_cRhs = pen / dt` dla `pen < 0` (`FifthWheel.cs:334`).
- Górna granica energii oddanej przez jedno rozsunięcie to ½·m·(0,05 m/s)², czyli pojedyncze dżule.

Przebieg czasowy sond (CSV 100 Hz, łańcuch scalony):

| sonda | epizody kontaktu | szczyt siły | wnikanie | potem |
|---|---|---|---|---|
| `probe_turn55_stop_from20kmh@laden40` | 41,16–41,60 s; 42,59–43,09 s | **78,8 kN**; 25,6 kN | 0,19; 0,06 mm | do 50 s brak kontaktu |
| `probe_turn57_stop_from15kmh@laden40` | 41,11–41,15 s | **71,1 kN** | 0,59 mm | do 50 s brak kontaktu |
| obie sondy `@empty` | brak | — | — | — |

Drugi epizod jest słabszy od pierwszego, trzeciego nie ma, przegub stoi na 48,8–49,0°. **Kontakt rozprasza energię, nie wzbudza
drgań.** W pełnym runnerze kontakt poza scenariuszami jackknife pojawia się tylko w:
- `fuzz_grade8_dry_laden40`: przegub −117°, 47 kN, 1 epizod;
- `fuzz_touch_wet_empty`: stałe oparcie przy −117,2°, siła 15 kN, ustalona, bez szarpania;
- `fuzz_shrink_articulation_stop_fulllock`.

To prawdziwe złożenia, nie fałszywe kontakty przy jeździe.

**FFB z kontaktu.** Siła kontaktu działa na bryły, a nie bezpośrednio na moment kierownicy, i to jest fizycznie poprawne.
`AligningTorqueTotal` liczony z opon zostaje wygładzony filtrem 1. rzędu 0,5 s, podtrzymanym przez 0,5 s. To nie fizyka, tylko
filtr odczucia (WORKING_VALUE, opisany w ADR). Pomiar autora (skok 4,53 → 0,48 N m/krok) pokazuje, że filtr działa. Uwagi niżej (P2).

**Golden** `brake_80_0_dry_abs_comb_laden40.csv`: droga hamowania 50,43 → 50,26 m. Postój (< 0,5 km/h) zaczyna się w 4,0 s
zamiast 4,4 s. Zmienia się tylko kołysanie po zatrzymaniu (histereza odbojnika). Akceptowalne.

**Zakres.** Brak zmian w ProjectSettings, Packages, asmdef, scenach i plikach generowanych.

**Zero GC.** Bufory mają stały rozmiar (`MaxPoints` 64), `Detect` liczy na strukturach. Alokuje tylko `SetGeometry` przy
podpięciu naczepy. Zielony test .NET `CombinationStep_WithBodyContact_DoesNotAllocate` [uruchomione].

**PhysX [kod].** `VehicleBody.SetCollisionIgnored` zostawia ignorowanie par ciągnik–naczepa do czasu podmiany naczepy, także po
rozpięciu, więc nie ma podwójnej siły (solver plus PhysX). Komentarz w `VehicleBody.cs:136` („.NET runner … has no tractor-trailer
contact”) jest już nieaktualny.

**P1 z recenzji s22 (prześwit 7 mm) — zamknięte w zakresie, o który prosiła recenzja.**
- [uruchomione] Ustalony skręt 55–60° przy 5 i 10 km/h (`jackknife_tight_turn_forward*`, pusty i 40 t) daje 0 kontaktu.
- Zostaje kontakt po pełnym hamowaniu z 15–20 km/h przy 40 t (tabela wyżej). Jest krótki, rozpraszający i bez tarcia
  „hamującego” w trakcie jazdy, więc **nie blokuje feel testu**. Właściciel powinien jednak o nim wiedzieć (P2-113-1).

### P2
- **P2-113-1 „Muśnięcie 0,61 mm” to w pierwszym kroku 71–79 kN.** `docs/adr/0228-…:161` podaje tylko wnikanie i prędkość.
  Przy 40 t, ~1 km/h i przegubie ~49° kontakt spekulatywny zatrzymuje zbliżanie w jednym kroku: 78,8 kN przy wnikaniu 0, potem
  10–20 kN przez 0,45 s.
  - Skutek: siła wystarczy, żeby w przyszłości wyzwolić dźwięk „stuku” albo telemetrię uderzenia przy zwykłym zatrzymaniu po ciasnym skręcie.
  - Do zrobienia: dopisać siłę do „Otwarte 1”. Decyzja o wymiarach albo tłumieniu kołysania ciągnika zostaje u lidera/właściciela.
  - Sondy leżą w `artifacts/`, nie w `tests/physics/scenarios`, więc runner w CI nie pilnuje regresji tej pozostałości. Proponuję
    dodać je jako scenariusze z progiem (np. `max_coupling_contact_force_kn ≤ 100`, `coupling_contact_s ≤ 1,5`), a nie „= 0”.
- **P2-113-2 Wygładzanie FFB może się przeciągać po kontakcie [przypuszczenie, z kodu].** Powrót do surowej wartości wymaga
  `|mz − AligningTorqueTotal| < 1,0 N m` (`VehicleModel.cs:337`; moment na kołach, rzędu setek N m).
  - Warunek spełnia się, gdy wartość surowa i wygładzona się przetną, czyli przy każdej zmianie trendu momentu.
  - Przy jednostajnym, szybkim narastaniu (r > 2 N m/s, błąd ustalony r·0,5 s), na przykład przy długim kontrowaniu zaraz po
    kontakcie, opóźnienie trwa do końca narastania. Długości tego okna nie zmierzyłem.
  - [kod] Wartość wygładzona idzie też do `SteeringColumn.Step` (`DrivingLabBootstrap.cs:726`), więc w tym czasie opóźnia
    samocentrowanie kierownicy dotykowej, nie tylko FFB. Do telemetrii (`VehicleTelemetryRecorder.cs:107`, runner `Telemetry.cs`)
    trafia wartość wygładzona.
  - Propozycja: próg względny (np. 2 % |mz|) albo stały czas zaniku. W CSV logować `AligningTorqueRaw`.
- **P2-113-3** `BodyBoxGeometryTests` (ścieżka JsonUtility) jest nieuruchomiony. Pola `ground`/`coupling` mają inicjalizatory `true`,
  a JSON podaje je jawnie, więc ryzyko jest niskie. Test trzeba jednak uruchomić w Unity przed scaleniem.

---

## #118 — testy GC wejścia PC i HUD PC (ADR 0244) — SCAL warunkowo

P0: brak. P1: brak (warunek: kompilacja i zielony test w Unity).

- Runda 3 to jeden commit (`ae052e54b`, `git show --stat`: 5 plików, +275). Dodaje dwa testy i dopisek do ADR 0244, **bez zmian w kodzie gry**:
  - `PcInputGc0244Tests` (EditMode): wirtualny pad, klawiatura i joystick przez refleksję; mikser z bramką menu; FFB z dostępnym sinkiem;
  - `PcHudGc0244Tests` (PlayMode): 500 odświeżeń HUD, 16:9 i 21:9, okienka lusterek.
- Reszta diffu względem bazy pochodzi z wcześniejszych rund, zrecenzowanych w s22.
- Liczenie GC idzie przez `GcAllocCounter` (Recorder „GC.Alloc”) z kontrolą 64 B, czyli tym samym mechanizmem co pozostałe testy zero-GC.
- Test nie przejdzie po cichu: brak API daje `AddVirtual` = null, a wtedy `Assert.IsNotNull(Current("Gamepad"))` pada.

### Ocena propozycji `Unity.InputSystem` w `Game.Tests.EditMode`
- **Czy potrzebne do kompilacji [przypuszczenie].** Test używa `new DrivingActions()`, `.Gamepad`/`.Keyboard` (typ `DrivingActionSet`
  z `Game.Controls`) i konstruktorów `GamepadDriverInput(DrivingActionSet, …)`. Typy z `Unity.InputSystem` są tylko w sygnaturach
  innych składowych (`DrivingActionSet.Map`, `DrivingActions.Asset`, `FindConflict(InputActionMap, …)`).
  - Roslyn zwykle nie wymaga wtedy referencji. Istniejący `PadKeyboardInputTests` nie tworzy `DrivingActions`, więc precedensu nie ma.
  - **Pierwsza kompilacja w Unity rozstrzygnie.** Jeśli wypadnie CS0012, referencja staje się warunkiem scalenia.
- **Rekomendacja: dodać** `"Unity.InputSystem"` do `references` w `game/Assets/_Project/Tests/EditMode/Game.Tests.EditMode.asmdef`.
  Zmiana należy do lidera. Ryzyko jest niskie, bo assembly jest tylko edytorowe i ma `UNITY_INCLUDE_TESTS`. Zysk:
  - zamiast refleksji bezpośrednie `InputSystem.AddDevice<Gamepad>()` / `RemoveDevice`;
  - błąd API wychodzi przy kompilacji, a nie w czasie testu.
- **Lepiej, w osobnym kroku:** `InputTestFixture` (referencja `Unity.InputSystem.TestFramework` plus `"testables": ["com.unity.inputsystem"]`
  w `Packages/manifest.json`, też zmiana lidera).
  - Fixture izoluje stan Input System. Dziś test dodaje urządzenia do żywego Input System edytora.
  - Na PC lidera z podpiętym prawdziwym padem lub kierownicą `Gamepad.current` albo dopasowanie profilu „gc-test” do `Joystick`
    może trafić w prawdziwe urządzenie. Test nadal mierzy zero GC, ale nie dokładnie tę gałąź, którą opisuje [przypuszczenie].
- P2-118-1: `STATUS.md` z gałęzi przy scaleniu pominąć (jak w recenzji s22).

---

## #117 — kierownica 270/900°, lusterka jako okienka (ADR 0243) — SCAL

P0, P1: brak.

- **Jedno źródło kąta [kod].** Dotyk: `ControlSettings.wheelRangeDeg` → `TouchSteeringWheel.HalfRangeDeg`. Kierownica PC (#132/#133):
  `WheelSettings.rangeDeg` → `HidWheelDriverInput.RangeDeg` (`WheelSteeringMap.ClampRange`). Grep po łańcuchu nie znalazł miejsca,
  gdzie jedno czyta drugie. Kąt fizyczny kolumny to `HandwheelLockDeg()` z definicji pojazdu, wspólny dla obu urządzeń.
  Komentarze w `ControlSettings.cs:24-27` i `:42` opisują ten podział.
- **Lusterka.** Jedna logika `MirrorWindowLayout.Solve` / `SolveTouch` dla monitora i dotyku. Okienka chowają się, gdy się nie mieszczą.
  Zachowanie `StepDue` na High jest bez zmian (`FillSpareFor = !standing && !Applies`), a polityka Low z okienkami jest taka jak w s22.
- **Zero GC [kod].** `MirrorInsetBudget` i layout są czyste. Test GC okienek przeszedł na `GcAllocCounter`.
- **Migracja v4→v5** włącza okienka i usuwa `lab.mirrorInsets`. Zakres 900° gracza zostaje: to świadoma decyzja, opisana w recenzji s22.
- P2-117-1 (bez zmian od s22): teksty panelu w kodzie. Ustawienia kierownicy dotykowej i żyroskopu widać na PC (tak jest też w podsumowaniu autora).
- P2-117-2: `artifacts/controls-0243/STATUS.md` przy scaleniu można pominąć.

---

## #141 — bezpiecznik startu: brak miejsca → menu (ADR 0277) — SCAL warunkowo

### P1
- **P1-141-1 Nieskończona pętla scen przy starcie z argumentem `-scene` [kod].**
  - `GameBootstrap.Awake` przy **każdym** wczytaniu sceny `Boot` czyta `Platform.GetLaunchArgument("scene")` (`GameBootstrap.cs:173-174`),
    a `Start()` od razu ładuje tę scenę (`:53-57`).
  - `DefaultPlatformServices.GetLaunchArgument` czyta `Environment.GetCommandLineArgs()` przy każdym wywołaniu.
    `AndroidPlatformServices` czyta `getIntent().getStringExtra`. Nic nie oznacza argumentu jako zużytego.
  - Scenariusz: `Kamion-<region>.cmd` (z #142; `Kamion-knyszyn.cmd` istnieje już na main) albo `adb … -e scene <region>`, a region daje
    `NoSpace`, na przykład przez błąd danych albo kolizję na całym odcinku 200 m:
    1. `FailStart` (`DrivingLabBootstrap.cs:425-434`) ładuje `Boot`.
    2. `Awake` ustawia `m_PendingScene` = ten sam region, a `ConsumeStartFailure` (`:162`) zjada komunikat.
    3. `Start` ładuje region, znowu `NoSpace`, znowu `Boot`… w kółko, co klatkę jedno `LogError`.
    4. Gracz nigdy nie zobaczy menu ani komunikatu. Wyjście tylko przez zabicie procesu.
  - Ta sama przyczyna jest od dawna w `ReturnToMenu`: przycisk „Menu” po starcie przez `Kamion-<region>.cmd` wraca od razu do regionu.
    Do pętli zamienia ją dopiero #141.
  - `StartSafetyTests.NoFreePlace_SceneStart_…` tego nie łapie: nie ma argumentu `-scene` i idzie przez `RestartFromSceneStart`, a nie przez `Awake`.
  - **Poprawka** (w #141 albo w commicie integracyjnym): statyczna flaga w `GameBootstrap`, np.
    `static bool s_LaunchSceneUsed; … if (!s_LaunchSceneUsed && !string.IsNullOrEmpty(scene)) { s_LaunchSceneUsed = true; m_PendingScene = …; }`.
    Reset flagi w `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` (wyłączony domain reload). Do tego test PlayMode:
    `-scene` symulowany przez wstrzykniętą platformę, a po powrocie do `Boot` scena regionu nie jest ładowana ponownie.

### P2
- **P2-141-1 Uzasadnienie `MaxCurveOffsetM` = 1,0 m jest nieaktualne.** `StartSearch.cs:95` i `docs/adr/0277-…:29` mówią o 0,88 m na
  starcie katalogu dk65-06 (`startS` 90). Na main (`c62937283`, rail-dk65-s22) dk65-06 ma `startS` **340**.
  - [uruchomione] `MaxLateralOffset` na danych main dla `startS` z katalogu main: maksimum **0,587 m** (bialystok-kleeberga),
    dk65-06 przy 340 m daje 0,001 m.
  - Próg 1,0 m nadal ma zapas, ale komentarz i ADR trzeba poprawić.
  - Test EditMode `ZoneRule_KeepsTheCatalogStart_…` (zapieczony spawn = `startS`, także dk65-06 = 340 za rondem) jest **warunkiem
    scalenia**. Policzyłem tylko zgięcie: reguła stref wymaga zamknięć z `WorldEdgeBuilder` i bez Unity jej nie sprawdziłem.
- **P2-141-2 Zmiana importera [kod].** `StartSearch.BakedSpawnS` zamiast `SafeStartS`:
  - nowa reguła przesuwa start także **wstecz** przed zamknięcie wyjazdowe (dawniej tylko do przodu za wjazdowe);
  - przy braku strefy daje `LogError` i zostawia `startS` z katalogu.
  - Na 21 regionach wynik ma być równy `startS` z katalogu (test EditMode, nieuruchomiony).
  - Zapieczone sceny poza gitem zmienią się dopiero po reimporcie. Runtime i tak sprawdza każdy start, więc stare sceny są
    bezpieczne. Zgodność z r2 `8778bbe5a` (granica przed zamknięciem wyjazdowym) jest zachowana: `zoneHi = right − BehindClosureM`,
    a szukanie do przodu kończy się na `zoneHi`.
- **P2-141-3** `FailStart` w `Awake` wraca, gdy HUD, audio i kamery są już utworzone (`DrivingLabBootstrap.cs:225`). Do końca klatki
  (`LoadScene` jest odroczone) HUD może raz odświeżyć się z wyłączonym pojazdem [przypuszczenie: możliwy jednorazowy NRE w logu].
  Do sprawdzenia w logu PlayMode `NoFreePlace_…` po poprawce P1, uruchomionej przez `Awake`.
- [uruchomione + kod] Zasięg nowego kontraktu poza katalogiem:
  - starty menu G3-A (`StartRequest.G3AStartS` = 12 m) i G3-B (1232 m) na trasie `bialystok-industrial-c` (dane main) dają
    zgięcie 0,048 i 0,002 m, czyli poniżej progu;
  - `SetRouteSpawn`, `ResolveStartS` i `RestartFromSceneStart` poza testami nie mają wywołań (`WorldSafetyNet` ich nie używa),
    więc nowa wartość `false` nigdzie nie jest ignorowana.
- **P2-141-4** `tools/spawn-runner` nie jest w CI (propozycja autora: job jak `physics-runner`). Kroki i limity (2 m, 200/200 m) mają status WORKING_VALUE.
- Zero GC na ścieżce „wolne” [kod]: sortowanie przez wstawianie zamiast `List.Sort(Comparison)`, sonda jako klasa przez generyk
  (bez boxingu), napisy budowane tylko przy przesunięciu lub błędzie. Pracy w pętli jazdy brak.

---

## #142 — PC polish (ADR 0276) — SCAL

P0, P1: brak. Konflikt z #141 jest w `BootMenu.cs` (sekcja „Jak zintegrować”).

- `BuildInfo.ReadContentHash` czyta plik raz na proces (`Current` jest w pamięci podręcznej), tylko na desktopie i nigdy nie rzuca wyjątku.
  `build-id.json` leży poza `Kamion_Data`, więc hash nie zawiera sam siebie.
- `MenuOverlayBoard`/`ApplyLayout` co klatkę liczą na strukturach i stosują układ tylko przy zmianie. Statyczne pola są resetowane w `SubsystemRegistration`.
- `build-windows.ps1`:
  - symbole Burst są przenoszone, nie kasowane;
  - nieudany postbuild kończy skrypt kodem 5;
  - `-Package` zwraca kod 6;
  - `-Regions` normalizowany jak w `build-android.ps1`.
  - `collect-logs.ps1` dostał BOM. To poprawne dla Windows PowerShell 5.1 i polskich napisów.
- P2-142-1: „dotnet 38/38” (`MenuOverlayLayoutTests` + `BuildInfoTests` na atrapie) nie ma projektu w repo. Dowód jest nieodtwarzalny.
  Dodać `tools/<…>-runner` jak przy innych PR-ach albo polegać tylko na EditMode.
- P2-142-2: `Kamion-<region>.cmd` uruchamia `-scene <region>`, a wtedy przycisk „Menu” w jeździe wraca od razu do regionu
  (przyczyna i poprawka jak w P1-141-1). Do zipu dla testerów trafia tylko `Kamion-okno.cmd`, więc ich to nie dotyczy.
  Właściciela i lidera, którzy używają folderu buildu, dotyczy.
- P2-142-3: przesunięcie menu o 87 px przy 1080p jest wyliczone, nie zmierzone. Potrzebny zrzut `Kamion-okno.cmd`.

---

## Jak zintegrować

### Konflikty
`git merge-tree --write-tree --name-only 08c2e21f8 <sha>` (sprawdzone dla `08c2e21f8`; wcześniej także dla `2103926bc`):
**każdy z pięciu PR-ów scala się z main bez konfliktów.** Od bazy main zmienił w kodzie tylko `region_catalog.json` (dk65-06
`startS` 90 → 340) i zasoby Nav.

Istniejące testy na main, na które mogą wpłynąć zmiany zachowania (grep w `game/Assets/_Project/Tests` na sha PR-ów) [kod]:
- `HudTextAllocTests.DiagnosticsButtonLabels_…` (#142) wyłącza `m_Panel` refleksją. Po #142 `ApplyLayout` nie włącza panelu
  ponownie przy niezmienionym układzie, a treść panelu dalej zależy od `m_Panel.activeSelf`, więc test powinien przejść.
- `StartClearanceTests:270` (#141) używa zachowanego `ResolveStartS` — działa.
- Testy #117 przechodzą na schemat 5 przez `CurrentSchema`.
- Nie znalazłem testów Unity, które zakładają kąt 90° z ogranicznika ani klucz `lab.mirrorInsets`.
- Żadnego testu, o którym wiadomo, że będzie czerwony.

Próbny łańcuch #113 → #118 → #117 → #141 → #142 na `08c2e21f8`:

| krok | wynik |
|---|---|
| #113 | czysto |
| #118 | czysto |
| #117 | czysto (`DrivingLabBootstrap.cs` scalony automatycznie z #118) |
| #141 | czysto (`DrivingLabBootstrap.cs` z #117 w innych blokach, `GameBootstrap.cs`) |
| #142 | **konflikt: `game/Assets/_Project/UI/BootMenu.cs`** (jeden plik, dwa bloki) |

**Rozwiązanie `BootMenu.cs`.** Weź wersję #142 (wszystko pod `m_Block`, `MeasureBlock`, `OnDestroy` z `MenuOverlayBoard`) i dodaj z #141:
1. Zaraz po linii `Label(m_Block, "Title", …)` wstaw blok komunikatu z rodzicem **`m_Block`, nie `m_Safe`**:
   `m_Notice = Label(m_Block, NoticeName, "", 20, …, new Vector2(left, top + 26f), new Vector2(total, 26f));` oraz 3 linie
   ustawień i `SetActive(false)`. Z rodzicem `m_Safe` komunikat nie przesunie się razem z blokiem, gdy nakładka diagnostyczna
   przesuwa menu, i zostanie w starym miejscu. Etykieta mieści się w ramce bloku (między tytułem a nagłówkami), więc
   `MeasureBlock` liczy tę samą ramkę także przy etykiecie wyłączonej.
2. Po `OnDestroy()` i `MeasureBlock(...)` z #142 zostaw składowe z #141: `NoticeName`, `m_Notice`, `NoticeText`, `ShowNotice`.
   Wywołują je `GameBootstrap` (#141) i `StartSafetyTests`.
3. **Nie** rozwiązuj przez „theirs”: to usuwa `ShowNotice` i kompilacja `GameBootstrap` padnie.

To rozwiązanie jest niesprawdzone kompilatorem, bo żaden projekt .NET nie kompiluje `BootMenu.cs`. Trzeba je sprawdzić w Unity.

### Kolejność
1. #113
2. #118
3. #117
4. #141 z poprawką P1-141-1 (flaga `-scene` w `GameBootstrap`); można ją dodać w commicie integracyjnym
5. #142 z rozwiązaniem konfliktu jak wyżej

Po scaleniu #141 i #142 nie trzeba ponownie uruchamiać eksportera katalogu (`startS` się nie zmienia). Trzeba za to zielonego `StartClearanceTests`.

### asmdef / Packages (tylko lider)
- `Game.Tests.EditMode.asmdef`: dodać `"Unity.InputSystem"` (rekomendacja przy #118). Opcjonalnie później `Unity.InputSystem.TestFramework`
  plus `testables` w `Packages/manifest.json` i przepisać `PcInputGc0244Tests` na `InputTestFixture`.
- Żaden z pięciu PR-ów nie zmienia ProjectSettings, Packages, asmdef, scen ani `_Generated`.

### Testy w Unity do uruchomienia (Win64)
```
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64
pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64
```
Kluczowe klasy:
- EditMode:
  - `BodyBoxGeometryTests` (#113);
  - `PcInputGc0244Tests`, `PerfLoop0244Tests`, `HeadlampProjectionTests` (#118);
  - `Controls0243Tests`, `SteerFoldTests` (#117);
  - `StartSearchTests`, `StartClearanceTests` (w tym `ZoneRule_…` na danych main z dk65-06 = 340 oraz `WorldScenes` po reimporcie) (#141);
  - `MenuOverlayLayoutTests`, `BuildInfoTests`, `RegionSelectTests` (#142).
- PlayMode:
  - `CombinationLabTests`, `KerbStrikeParityTests` (#113);
  - `PcHudGc0244Tests`, `CabEnvironmentThrottleTests` (#118);
  - `StartSafetyTests`, `RouteSpawnTests` (#141);
  - `MenuOverlayUiTests` (#142).

Poza Unity, na scalonym main:
- `dotnet test` w `tools/{physics,spawn,controls,loop}-runner/Tests`;
- `dotnet run -c Release --project tools/physics-runner/Runner -- --no-multi`;
- `uv run --no-project --with pytest pytest tests/dist tools/pcperf -q`.

Po buildzie (`pwsh scripts/build-windows.ps1 -Slot -Regions d67-full -Package`):
- `Kamion-<region>.cmd`, a potem „Menu” w jeździe: musi zostać w menu (sprawdzenie P1-141-1);
- zrzut menu z nakładką i z komunikatem (`NoFreePlace_…` albo ręcznie);
- dwa buildy dają różne `contentHash`;
- feel test: cofanie do ogranicznika, zatrzymanie po skręcie 55° z 40 t (P2-113-1), FFB.

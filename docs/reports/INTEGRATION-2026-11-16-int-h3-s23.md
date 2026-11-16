# Integracja int-h3-s23 — chmura H, runda 3 (#113, #118, #117, #141, #142) — 2026-11-16

Integrator: agent int-h3-s23 (worktree `win-build-0261`, Library Win64). Lider jako jedyny scala do main.
Recenzja: `docs/reports/REVIEW-2026-11-16-s23-code-H3.md`.
Podsumowanie autora: `origin/claude/epic-euler-pxcll3:docs/reports/CLOUD-H-R3-SUMMARY-2026-11-16.md`.

- Gałąź `int-h3-s23` (wypchnięta) = `origin/main` `f421fc79e` + #118, #117, #141, #142 + poprawki integracyjne.
- **#113 jest wycofany** zgodnie z decyzją lidera. Gałąź odtworzyłem bez merge'a #113 zamiast robić `git revert -m 1`.
  Dzięki temu poprawiony #113 da się później normalnie scalić; przy revercie git uznałby jego commity za już scalone.
- Poprzedni stan, czyli łańcuch z #113 i wszystkimi poprawkami, zostaje dla porównania jako gałąź `int-h3-s23-with113` @ `13104cf21`.
- Sprawdziłem, że drzewo `int-h3-s23` różni się od `int-h3-s23-with113` dokładnie zbiorem plików z diffu #113.

## Werdykt

| PR | gałąź @ sha | wynik w integracji | decyzja |
|---|---|---|---|
| #113 | `jackknife-0228` @ `a84ad5e14` | PlayMode: 5 faili `KerbStrikeParityTests`; bisekcja jednoznaczna | **WYCOFANY** → FIX dla chmury H (niżej) |
| #118 | `perf-loop-0244` @ `ae052e54b` | kompiluje się (także z referencją `Unity.InputSystem`), testy zielone | **SCAL** |
| #117 | `controls-0243` @ `0710168df` | 1 nieaktualny test z main (`saved v4`), poprawiony | **SCAL** |
| #141 | `spawn-safety-0277` @ `cd03fb181` | CS1061 w teście, P1-141-1 i test ostrzeżeń — wszystko poprawione | **SCAL** (z poprawkami) |
| #142 | `pc-polish-0276` @ `746c2fd28` | konflikty w 4 plikach; nieaktualny test ścieżek; reguła paczki zmieniona decyzją lidera | **SCAL** (z poprawkami) |

**Gotowe do scalenia: TAK** (bez #113), jeśli przebieg 4 (EditMode i PlayMode na gałęzi bez #113) jest zielony.
Wynik przebiegu 4 jest w sekcji „Testy”.

## Kolejność i commity na `int-h3-s23`

| sha | treść |
|---|---|
| `a3cfbcad2` | Merge #118 |
| `53f3f61a1` | Merge #117 |
| `9e4387316` | Merge #141 |
| `27d705249` | Merge #142. Konflikty `BootMenu.cs`, `package-windows.py`, `tests/dist`, `docs/12` (opis niżej) |
| `0831e7556` | P1-141-1: `-scene` tylko przy pierwszym Boot procesu, test `LaunchArgumentOnceTests` |
| `7b003c4bf` | `Unity.InputSystem` w `Game.Tests.EditMode.asmdef` (zmiana lidera wykonana w jego imieniu, opisana w commicie) |
| `162375ecc` | #141 `StartSearchTests`: `Is.Not.AllocatingGCMemory()` → `GcAllocCounter.AssertZero` (CS1061) |
| `3dbdd72a3` | #141 `StartSafetyTests`: licznik linii `[START]` zamiast `LogAssert.NoUnexpectedReceived()` |
| `73ff61790` | #117 `ControlSettingsTests`: wersja logu ze stałej `ControlSettings.CurrentSchema` |
| `f5dfec72c` | #142 `BuildInfoTests`: ścieżki porównywane po normalizacji (`Path.GetFullPath`) |
| `92358c4b5` | Paczka testera według decyzji lidera: `Kamion-<region>.cmd` trafia do zipa, gdy region jest w buildzie, bez `DEV_LAUNCHERS`; ADR 0276 pkt 9, docs/12 |

`STATUS.md` w katalogu głównym jest taki sam jak na main. Pliki statusu PR-ów (`artifacts/controls-0243/STATUS.md`,
`docs/status/spawn-safety-0277-STATUS.md`) weszły razem z gałęziami. Przy scaleniu do main lider może je pominąć (P2-117-2, P2-118-1).

## Rozwiązane konflikty (#142 na łańcuchu)

Recenzja przewidziała konflikt tylko w `BootMenu.cs`. Pozostałe trzy pliki wynikają z `473173a55` (`fix(dist)`), który trafił do main po recenzji.

- **`game/Assets/_Project/UI/BootMenu.cs`**: wziąłem wersję #142 (`m_Block`, `MeasureBlock`, `MenuOverlayBoard`) i dodałem z #141 komunikat
  `m_Notice`.
  - Rodzicem komunikatu jest **`m_Block`**, nie `m_Safe`, więc przesuwa się razem z blokiem menu.
  - Zostały `NoticeName`, `NoticeText` i `ShowNotice`, których używają `GameBootstrap` i `StartSafetyTests`.
  - Kompiluje się w Unity: build i EditMode przechodzą.
- **`scripts/package-windows.py`, `tests/dist/test_package_windows.py`, `docs/12`**: reguła launcherów.
  - Najpierw rozwiązałem według #142 (każdy `Kamion-*.cmd` poza paczką). Lider zdecydował inaczej: zostaje reguła main
    (ADR 0271, uzupełnienie s23). Launcher z `-scene <x>` trafia do zipa, gdy `<x>` jest w buildzie (lista z logu buildu, inaczej
    `build.json` + katalog regionów); `Kamion-okno.cmd` trafia zawsze.
  - Zgodnie z drugą decyzją lidera usunąłem wyjątek `DEV_LAUNCHERS = ("Kamion-knyszyn.cmd",)`. Od int-pc-s23 ten skrót startuje
    region knyszyn, więc testerzy dostają go, gdy knyszyn jest w buildzie.
  - Zmiany w testach:
    - przywrócony test main `test_region_launcher_ships_when_region_in_build`, który oczekuje teraz także `Kamion-knyszyn.cmd`;
    - `test_region_launcher_set_d67_has_no_knyszyn_w`: `Kamion-knyszyn.cmd` jest w paczce;
    - nowy `test_other_scene_launcher_ships_only_when_region_in_build`;
    - fixture `make_build` ma launchery z prawdziwym `-scene`.
  - ADR 0276 pkt 9 i tabela w docs/12 opisują tę regułę.
  - Wynik: `pytest tests/dist tools/pcperf` **61 passed**.

## P1-141-1 — pętla scen przy `-scene` (naprawione)

- Problem: `GameBootstrap.Awake` czytał `-scene` przy każdym wczytaniu `Boot`.
- Poprawka: statyczna flaga `TakeLaunchArguments()`. Zerowanie `ResetLaunchArguments()` ma tylko
  `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]`, czyli start procesu albo wejście w Play przy wyłączonym domain reload.
- Skutki:
  - start bez wolnego miejsca (`FailStart` → `Boot`) pokazuje menu z komunikatem ADR 0277, a nie wraca do regionu w pętli;
  - przycisk „Menu” po starcie z `Kamion-<region>.cmd` zostaje w menu (P2-142-2);
  - powrót do `Boot` z ustawionym `-scene` daje w logu `[BOOT] launch argument scene already used this run: staying in the menu`.
- **Poza zakresem P1, zaakceptowane przez lidera:** ta sama flaga obejmuje `DesktopAutoShot.StartFromArguments`. Obiekt ma
  `DontDestroyOnLoad` i przy każdym powrocie do menu tworzył kolejną kopię, która robiła dodatkowe zrzuty i zamykała grę w `quit_t`.
- Test EditMode `LaunchArgumentOnceTests` (3 przypadki):
  - pierwsze wejście bierze argument, kolejne nie;
  - reset przy starcie procesu;
  - strażnik w źródle: `m_PendingScene` i `DesktopAutoShot` są ustawiane tylko w gałęzi strażnika.
- Sprawdzenie w buildzie: `-scene knyszyn` → `[BOOT] launch argument scene=World_knyszyn_High`, start w Knyszynie.
  Ścieżki „Menu” → Boot w buildzie nie przeklikałem ręcznie. Pokrywa ją test, a ręcznie warto ją sprawdzić przy feel teście.

## Testy

| przebieg | drzewo | wynik |
|---|---|---|
| 1 | łańcuch z #113 @ `9ff1150d9` | dotnet `tools/{physics,spawn,controls,loop}-runner/Tests` exit 0; runner fizyki `--no-multi` exit 0; pytest exit 0; **Unity: CS1061** w `StartSearchTests.cs:260` (#141), przez to EditMode, PlayMode i build exit 1 |
| 2 | z #113 @ `149abab54` | EditMode: 2 faile (#142 `BuildInfoTests`, #117 `ControlSettingsTests`); PlayMode 199: 6 faili (5× `KerbStrikeParityTests`, 1× `StartSafetyTests`); build knyszyn OK; uruchomienia: błąd mojego skryptu (szukał exe `…-dirty`) |
| 3 | z #113 @ `13104cf21` | **EditMode exit 0**; PlayMode: 199 testów, 186 passed, **5 failed (tylko `KerbStrikeParityTests`)**, 8 skipped; build knyszyn exit 0; uruchomienia knyszyn i menu exit 0 (bez wyjątków) |
| bisekcja | `KerbStrikeParityTests` | `f421fc79e` (main) **exit 0**; `65145dac4` (main + sam #113) **exit 1** |
| 4 | **bez #113** @ `92358c4b5` | EditMode **exit 0**; PlayMode: _(w toku — uzupełnię)_ |

- Logi: `artifacts/int-h3-s23/*.log` w repo głównym, plus `run-status-run{1,2,3}.txt` i `run-status.txt`.
- XML testów: `artifacts/tests/{editmode,playmode}-*.xml` w worktree.

## #113 → FIX dla chmury H

Kontekst wartości: `KerbStrikeParityTests` (PlayMode) porównuje Unity z wartościami referencyjnymi runnera. Te wartości są
wpisane na stałe w teście (`KerbStrikeParityTests.cs:270-277`, komentarz „artifacts/physics run 2026-11-09”).

| przypadek | metryka | Unity z #113 | referencja w teście | runner z #113 (przebieg 1, `--no-multi`) |
|---|---|---|---|---|
| `KerbStep27cm42_40t_Mesh` | oderwanie koła ciągnika | **0,31 s** | 0,42 s ±0,084 | `kerb_step_27cm_42kmh_comb@laden40` `max_wheel_airtime_s(1)` = **0,31** |
| `KerbStrike14cm50_Empty_{Box,Mesh}` | oderwanie koła ciągnika | **0,08 s** | 0,11 s ±0,03 | `curb_strike_14cm_50kmh_comb@empty` `max_wheel_airtime_s(1)` = **0,08** |
| `KerbStrike14cm50_40t_{Box,Mesh}` | szczyt pochylenia | **1,38°** | 1,99° ±0,398 | brak w logu runnera (metryki pochylenia testu runner nie wypisuje) |
| — (kontekst) | Fz/static 40 t | — | 3,53 | `curb_strike_14cm_50kmh_comb@laden40` `max_fz_ratio` = **3,297** |

**Hipoteza (z diffu #113, w części potwierdzona danymi):**
- Unity i runner są ze sobą zgodne. Przestarzałe są wartości referencyjne w teście.
- #113 zmienia wspólną fizykę zawieszenia. `WheelGroup.BumpStopUnloading` to histereza odbojnika przy rozprężaniu (forma
  Hunt–Crossley, `bumpStopHysteresis` w definicji pojazdu, WORKING_VALUE). Zmiana zmniejsza energię oddawaną przez odbojnik
  po uderzeniu w krawężnik, więc koło krócej wisi w powietrzu, a szczyt pochylenia kabiny jest niższy.
- Runner ma tę samą zmianę: jego scenariusze dalej przechodzą w swoich tolerancjach, ale z nowymi wartościami
  (0,31 s; 0,08 s; Fz 3,30). Testu parzystości Unity nikt nie przeliczył.
- Ta hipoteza tłumaczy 2 z 3 metryk co do liczby. Pochylenia 1,38° nie da się sprawdzić bez wyliczenia metryki pochylenia
  testu na runnerze z #113.
- Kontakt kabina–naczepa (`FifthWheel` ADR 0228) w jeździe na wprost po krawężniku nie powinien się włączać [przypuszczenie]
  i zgodność 0,31 i 0,08 to wspiera.

**Do zrobienia przez chmurę H (#113 r4):**
1. Przeliczyć runner z #113 dla `curb_strike_14cm_50kmh_comb@{empty,laden40}` i `kerb_step_27cm_42kmh_comb@laden40` z tymi samymi
   metrykami co `KerbStrikeParityTests`: Fz/static, oderwanie koła ciągnika, czas „all”, szczyt pochylenia.
2. Zaktualizować stałe referencyjne w `KerbStrikeParityTests.cs:270-277` i datę przebiegu w komentarzu. Opisać zmianę
   w `docs/PHYSICS_VALIDATION.md` §3a i w ADR 0228, z przyczyną: histereza odbojnika. Tolerancji nie poszerzać.
3. Jeśli szczyt pochylenia w runnerze z #113 nie wyjdzie ≈1,38°, to jest to prawdziwa rozbieżność Unity–runner. Wtedy trzeba
   znaleźć przyczynę (kandydaci: kolejność sił odbojnika w kroku Unity, kontakt nadwozie–grunt z `bodyBoxes`
   kontra BoxCollidery PhysX) i nie dopasowywać stałych.
4. Uruchomić PlayMode Win64 w Unity: `pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64 -Filter KerbStrikeParityTests`,
   potem pełny.
5. P2 z recenzji zostają w r4:
   - **P2-113-1:** w ADR 0228 „Otwarte 1” podać przy „muśnięciu 0,61 mm” siłę w pierwszym kroku, **71–79 kN**. Dodać sondy
     jako scenariusze z progiem, np. `max_coupling_contact_force_kn ≤ 100` i `coupling_contact_s ≤ 1,5`.
   - **P2-113-2:** wygładzanie FFB. Powrót do wartości surowej przy `|mz − AligningTorqueTotal| < 1,0 N m` może się
     przeciągać przy jednostajnym narastaniu momentu; opóźnia to też samocentrowanie kierownicy dotykowej. Proponowany próg
     względny (np. 2 % |mz|) albo stały czas zaniku; w CSV logować `AligningTorqueRaw`.
   - Nieaktualny komentarz `VehicleBody.cs:136`.

## Oględziny buildu i zrzutów (przebieg 3, `kamion-0.1.0-13104cf215-regions`, z #113)

Pętla wizualna: zrzuty obejrzane. `-Regions knyszyn` dało w buildzie Boot, DrivingLab, WorldC (+High) i knyszyn (+High).
Build bez #113 nie powstał; zmiany #113 dotyczą fizyki, nie UI, więc oceny UI to nie zmienia.

- **`-scene knyszyn`** (`artifacts/win/runs/20261116-151704/shot.png` w worktree):
  - start `[START] region=knyszyn route_s=90.0 road='Obozowa'`; High 1600×900, 60 fps, p99 16,7 ms, bez wyjątków;
  - **lusterka #117:** dwa okienka obok prędkościomierza u góry ekranu, czytelne;
  - **HUD PC:** prędkość, bieg, ciśnienie, kontrolki;
  - **widoczne kontrolki dotykowe** (kierownica, R/N/D, HAMULEC/GAZ, kierunkowskazy). To **nie jest błąd tych PR-ów**.
    W PlayerPrefs gracza na tym PC jest `ui.touchControls = 1` („zawsze”, ADR 0265), zapisane wcześniej z menu ustawień.
    Domyślne „auto” na PC bez dotyku je chowa (`TouchControlsPolicy.Resolve`). Nie zmieniałem ustawień właściciela.
    Do sprawdzenia przy feel teście albo osobnym zrzutem po ustawieniu „Kontrolki dotykowe: auto”.
  - Obserwacja: w 35 s ciężarówka jedzie 74 km/h po wąskiej ulicy w Knyszynie, przy `autopilot=off` w logu `[LAB]`.
    Pochodzenia gazu nie badałem (może to być podłączone urządzenie wejścia). P2 do wyjaśnienia.
- **Menu** (`artifacts/win/runs/20261116-151756/shot.png`):
  - nakładka diagnostyczna #142 jest nad blokiem menu i nic nie zachodzi;
  - wersja i `dane 5d78195c9d73` (contentHash) są w nakładce i stopce;
  - region 16/21 „Knyszyn — wlot DK65” to knyszyn-w, którego nie ma w buildzie, więc szare pole „brak w tym APK” jest poprawne.
    Tekst „APK” na PC to drobne P2 z #117/#142.
  - **P2-int-1:** tytuł „TRUCK SIM PL — TEST WRAŻEŃ” i nagłówki kolumn („WYBIERZ START”, „OPCJE”, „REGION…”) są bardzo blade
    na tle placu. Słaby kontrast, może animacja wejścia w 12 s. Do sprawdzenia drugim zrzutem po ok. 30 s.
  - **Komunikat #141** w buildzie nie pojawił się: w knyszyn było wolne miejsce. Pokrywa go PlayMode
    `StartSafetyTests.NoFreePlace_…` (zielony w przebiegu 3).
- **P2-int-2:** etykieta buildu `13104cf215-dirty`, mimo że skrypt przed buildem cofnął zmiany i `git status` był czysty.
  Unity zapisuje efekty uboczne (`M_Sky.mat`, `URP_Ultra.asset`, `UniversalRenderPipelineGlobalSettings.asset`,
  `ProjectSettings.asset`, `materials_spec.json`) w trakcie buildu, a `BuildInfo` odczytuje `dirty` już po nich.
  Do rozważenia w `BuildCommands`: odczyt sha i `dirty` przed importem albo ignorowanie tych plików.

## Otwarte P1/P2 po integracji

- P1: brak (P1-141-1 naprawione).
- **#113:** wycofany, FIX opisany wyżej (stałe parzystości, P2-113-1 siła 71–79 kN, P2-113-2 wygładzanie FFB).
- **P2-117-1:** teksty panelu w kodzie; ustawienia kierownicy dotykowej i żyroskopu widoczne na PC.
- **Koszt okien lusterek na Low** (#117): nie mierzyłem. W przebiegu 3 na High `[DIAG] mir=2.00/f cpu≈0.8 ms`.
  Pomiar na Low trzeba zrobić `pc-metrics` na referencyjnym PC (WORKING_VALUE do ustalenia z właścicielem).
- **P2-141-1:** komentarz `StartSearch.cs:95` i ADR 0277 nadal podają 0,88 m przy dk65-06 `startS` 90; na main jest 340.
  Na danych main maksimum to 0,587 m.
- **P2-141-4:** `tools/spawn-runner` poza CI.
- **P2-142-1:** „dotnet 38/38” bez projektu w repo.
- **P2-142-3:** przesunięcie menu 87 px przy 1080p nie jest zmierzone. Zrzut powyżej jest w 1600×900.
- **P2-int-1, P2-int-2:** opisane wyżej. Do tego „74 km/h przy autopilot=off” do wyjaśnienia.
- Opcjonalnie (lider): `Unity.InputSystem.TestFramework` + `testables` i przepisanie `PcInputGc0244Tests` na `InputTestFixture`.

## Komendy do odtworzenia

```
git fetch origin && git checkout int-h3-s23
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64
pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64
uv run --no-project --with pytest pytest tests/dist tools/pcperf -q
pwsh scripts/build-windows.ps1 -Slot -Regions knyszyn
pwsh scripts/build-windows.ps1 -SkipBuild -Exe <artifacts/win/kamion-…-regions/Kamion.exe> -Run -Scene knyszyn -RunSeconds 50 -ShotSeconds 35
```

# Przekazanie SBS — zatrzymanie na prośbę właściciela

Stan: 12 listopada 2026, około 16:25, Europe/Warsaw. Właściciel polecił zakończyć pracę przy najbliższym bezpiecznym punkcie z powodu kończącego się limitu tygodniowego, bez ubijania zadań. Cel 24-godzinny zostaje wstrzymany, a nie zaliczony. Runda 4 jest niezakończona. Nie rozpoczynać automatycznie nowych rund bez wznowienia przez właściciela.

## Repozytorium i gałąź

- Main: `C:\Users\matma\Documents\Claude\kamion`.
- Własny worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-sbs`.
- Gałąź: `gpt-sbs-r4`. Ostatni checkpoint przed zapisem przekazania: `61597d10`; późniejsze commity dotyczą zapisu zatrzymania. Odczytać aktualny `git log -1`.
- Wykonywana była wyłącznie sesja 4 z `docs/owner/GPT-TASK-05-24H.md`, ADR 0111. R1–r3 zakończono wcześniej; r3 ma końcowy commit `bd5edafb128ff8251fd082eeeb324514c84d1977` i dostawę artefaktów.
- Nie scalano własnej pracy do main, nie pushowano, nie wykonywano operacji na telefonach. Odczytano jedynie istniejący raport pomiaru lidera.

## Pozostawiony proces — nie uruchamiać duplikatu

Sesja narzędzia **31378** pozostaje żywa. Uruchomiona komenda:

```powershell
pwsh -NoProfile -File artifacts/sbs-r4/compose-all.ps1 *> artifacts/sbs-r4/compose-all.log
```

Ostatnia obserwacja: oczekiwanie na heavy, trzy zajęte sloty i trzy wcześniejsze zgłoszenia. `PHONE_RUN` zniknął około 16:16. Procesy: wrapper PID **70780**, jego parent **68916**, Acquire PID **59180**, rozpoczęte około 15:02. Szczegóły i czasy utworzenia są w `PAUSE-STATE.json`. Nie zatrzymano tych procesów, nie usuwano ich biletu ani cudzych blokad. Mogą kontynuować kompozycję po przekazaniu i zapisać `composition-completed.json`.

Proces składa cztery stany, każdy z osobnym Acquire/Release heavy. Nie renderuje nowych obrazów w Unity. Nie rozpoczyna audytu, fidelity, GIS ani następnej rundy. Nie zmieniać podczas jego działania `compose-all.ps1`, `scripts/sbs-gate3.ps1` lub `tools/refs/sbs_gate3.py`, nie zmieniać gałęzi i nie uruchamiać drugiego heavy z właścicielem `gpt-sbs-r4`. Wrapper kontroluje hashe kodu.

Po wznowieniu najpierw sprawdzić tę samą sesję, log i rzeczywiste procesy z ich czasami utworzenia. Brak nowego wpisu w logu lub timeout obserwacji nie oznacza końca procesu. W innym koncie uchwyt sesji może być niedostępny: sprawdzić PID/CreationDate oraz receipt i log. Nie restartować zadania wyłącznie z powodu braku uchwytu. Zamknięcie aplikacji lub restart komputera może przerwać pozostawione procesy.

## Potwierdzone wyniki r4

- Baza generacji: main `0023f39d`; materiały 505 s, świat 505,9 s, exit 0, bez `fallback=True`. 64 chunki, Low i High, import zakończony.
- Pełne **168 raw**: 42 kamery × cztery stany. Wspólny HEAD renderu `80159a70e7cea39146a465208da5471cb9beb915`. Manifest świata SHA `5f90bdb17c5e545070b086bedd419def6ee2288efef3feb68a4c3bf54e698b00`, materiały `c552a473f4e2849cd6aedcd839210f39416292ca16c422aecc46517e23d60afb`. Dokładne wejścia w `evidence/inputs.zip`.
- Test core SBS **51 passed / 1,87 s**, test skryptu dowodowego **20 passed / 28,43 s**, EditMode **366/366**, bez pominięć. Receipt i logi są w katalogu rundy.
- Niezależny świeży D51 Low-overcast: **FAIL, 13 rozpoznawalnych, 11 częściowych, 1 nierozpoznawalna**. 25 B, 17 C, brak A. Rejestr `sbs_recognition.json` zawiera nową ocenę i historię r3/r1. Nie promowano C.
- Niezależnie obejrzano **wszystkie 100 B raw czterech stanów** i odpowiednie 25 zdjęć. Recenzje natywne, SHA oraz archiwa są zapisane. Ogląd pozostałych 75 raw nie tworzy nowego D51. Recenzent nie oglądał przyszłych arkuszy 960 px.
- Przegląd C jest **częściowy**. Ostatni odczytany checkpoint: 20/68 raw, 5/17 źródeł. Aktualny licznik i brakujące ID są w `c-native-visual-inspection.json`; agent otrzymał polecenie zakończenia na bieżącej kamerze i zapisu checkpointu. Nie przedstawiać tego jako ukończonego oglądu 17 C.

Recenzent zakończył pracę na dokładnie 20/68 raw i 5/17 źródeł. Wznowienie oglądu od `sbs-g3-b-962702164479831`; oba Commons pozostają nieobejrzane w tym przeglądzie. Dla 294859 wskazał nadal niezgodną projekcję: zbieg pochylonej jezdni nie potwierdza poziomego horyzontu. Nie awansowano klasy.
- Wszystkie 168 liczników rozdzielają statykę i instancje. Maksimum Low 810 draws = 445 + 365, High 1376 = 945 + 431. Względem r3 draws +0, tris bez przekroczenia 2%. Skumulowane Low względem r2: 38/84 wzrostów draws i 34/84 przekroczeń 2% tris. Brak PASS budżetu.
- Zewnętrzny raport lidera A16 dla APK `11db0552fd` podaje GPU p95 35,54/35,17 ms i FAIL p99. Zachowano identyczną bajtowo kopię raportu. To inna epoka niż obrazy r4; nie łączyć tych wartości z licznikami r4 jako jednego pomiaru.

## Zmiany narzędzi i dowody

`tools/refs/sbs_gate3.py` dopuszcza ścisłe `--inputs` bez wymuszania trybu historycznego; kontrole pochodzenia pozostają obowiązkowe. `scripts/sbs-gate3.ps1` obsługuje `Inputs`, bezpieczne zapisywanie migawek RenderOnly, walidację raw/rosteru/epoki/wymiarów i dzierżawy heavy per stan. Własny istniejący slot lub bilet chroni przed równoległym zadaniem z tym samym właścicielem. Kod i testy otrzymały niezależny przegląd.

`audit_baseline.py` przygotowano do pełnego audytu 168 raw, 268 arkuszy, 128 GLB, liczników, archiwów i dokładnego powiązania ocen. Sprawdzono AST i przegląd kodu; **nie wykonano jeszcze audytu**. Poprawkę wymagającą dokładnie czterech wpisów archiwum dodatkowej recenzji zatwierdzono w scoped code review, zapisanym w `additional-review-audit-code-review.json`. Częściowa recenzja C nie została jeszcze włączona do tego audytu.

## Nowszy main — nie powtarzać zastąpionych prób

Po zamrożeniu r4 main scalił ADR 0130 (`abf15f9e`), zmieniający sześć spornych póz. Nasze raw nie zawierają tych zmian. Przepis 15 własnych prób starej bazy oznaczono **SUPERSEDED_BEFORE_EXECUTION**: zero przygotowanych i wyrenderowanych prób. Nie uruchamiać go. Częściowe G3-B 6/10 z recenzji 0130 nie jest wynikiem pełnej kohorty r4 i nie wolno dodawać go do naszych ocen G3-A.

Po zamknięciu r4 r5 ma scalić aktualny main i wykonać świeżą generację, import oraz wszystkie cztery stany. Zachować zaakceptowane dane Claude. Preflight `git merge-tree` z 16:11 był czysty i zachowywał pozy main oraz własne narzędzia/rejestr; to nie jest wykonany merge i nie gwarantuje stanu przyszłego main. Kolejnym osobnym problemem kamery jest pitch B150280. Braków pierzei, portali, ekranów i pomostu nie leczyć przesunięciem kamery.

## Co zostało do zamknięcia r4 po wznowieniu

1. Poczekać na terminalny wynik istniejącej kompozycji. Sprawdzić log, `composition-completed.json` i komplet czterech stanów. Nie uznawać samej obecności części plików za sukces.
2. Po zwolnieniu własnego heavy wykonać osobno audyt, fidelity oraz na końcu pełny GIS. Gotowy helper pobiera i zwalnia slot:

```powershell
Set-Location C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-sbs
pwsh -NoProfile -File artifacts/sbs-r4/run-heavy.ps1 -Task Audit *> artifacts/sbs-r4/audit.log
uv run --project tools/refs python artifacts/sbs-r4/build-history-report.py
pwsh -NoProfile -File artifacts/sbs-r4/run-heavy.ps1 -Task Fidelity *> artifacts/sbs-r4/fidelity.log
pwsh -NoProfile -File artifacts/sbs-r4/run-heavy.ps1 -Task FinalGis -EndOfRound *> artifacts/sbs-r4/pytest-gis.log
pwsh -NoProfile -File artifacts/sbs-r4/record-validation.ps1
```

Wykonywać kolejno i sprawdzać każdy wynik. Generator historii to lekka operacja JSON/kopiowania plików, bez dekodowania obrazów; wymaga gotowych metryk wszystkich stanów. Pełny GIS jest dozwolony tylko na końcu rundy. `finalgis-completed.json` jest nazwą receipt helpera. Zapis walidacji zachowuje fidelity QA przed przywróceniem pochodnych; nie daje automatycznie PASS świata, D51 lub GPU.

3. Obejrzeć rzeczywiste arkusze 960 px, sprawdzić gotowy raport HTML z historią r1–r4, uzupełnić ADR i końcowy `REPORT.md`. Aktualny `REPORT-DRAFT.md` pozostaje raportem roboczym.
4. Dopiero po wymaganych audytach przywrócić dokładnie znane pochodne generatorów, z zapisem hashy przed/po do `generated-restoration.json`. Nie robić szerokiego resetu. Fidelity może dodać ósmy plik `generated/fidelity_qa.json`.
5. Uruchomić `artifacts/sbs-r4/deliver.ps1` dopiero po rzeczywistym zamknięciu. Ma guard brakujących dowodów i czystych plików produkcyjnych, kopiuje artefakty bez MIR i sprawdza SHA. Obecna kopia zatrzymania jest WIP, nie końcową dostawą.
6. Dopiero potem utworzyć `gpt-sbs-r5` w tym samym worktree i scalić bieżący main, jeżeli właściciel wznowi pracę.

## Zachowane pliki i zasady bezpieczeństwa wznowienia

Siedem plików po generatorach celowo pozostawiono w worktree, bo są potrzebne do audytu bazy. Ich dokładna lista, rozmiary, SHA i kopie fizyczne w `pause-generated/` są w `PAUSE-STATE.json`. Kopie pochodnych i PNG pozostają poza gitem, ale są objęte kopią artefaktów zatrzymania. Nie kasować worktree ani jego wygenerowanych GLB przed audytem. `evidence/inputs.zip` i archiwa recenzji są zacommitowane. Nie ruszano wcześniejszych nieśledzonych `.playwright-cli/` i `output/`.

Sloty zawsze przez kanoniczny `C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1`: Unity owner `gpt-sbs`, ciężki Python owner aktualnej gałęzi, obecnie `gpt-sbs-r4`. Heavy max 3, Unity max 4, bez Priority dla GPT. Helpery używają `-StaleHours 87600`, aby nie wygaszać cudzych slotów. Nie usuwać cudzych slotów, biletów ani PHONE_RUN. Po Unity przywracać wyłącznie `game/Assets/_Project/Rendering/Settings` i `game/ProjectSettings`. Nie merge do main, nie pushować, nie używać telefonów/adb, nie zmieniać innych dziedzin lub plików Claude.

Spis i wynik kopiowania przy zatrzymaniu zapisuje `PAUSE-DELIVERY.json`. Kopiowanie oznaczono jako **PAUSED_WIP_NOT_FINAL_ROUND_DELIVERY**. Aktywny `compose-all.log` wyłączono z kopiowania; zachowano jego nieruchomą kopię `compose-all-at-pause.log`. Proces może dopisywać dalsze wyniki już po tej kopii. Po wznowieniu źródłem prawdy są nadal aktualny worktree, rzeczywiste procesy, log i receipt, nie sama kopia zatrzymania.

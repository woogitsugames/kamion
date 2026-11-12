# Przekazanie vegetation — wstrzymanie na prośbę właściciela

**Runda r4 jest otwarta. NIE SCALAĆ jej jako zaakceptowanej poprawki.** Właściciel poprosił o zakończenie pracy z powodu zbliżającego się limitu tygodniowego, bez ubijania zadań. Zatrzymano dalszą pracę agenta i przygotowanie nowych rund. Nie wykonano push ani scalenia do main. Nie używano telefonów lub adb.

## Miejsce pracy i zapis

Repo główne: `C:\Users\matma\Documents\Claude\kamion`.
Worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation`.
Gałąź: **gpt-vegetation-r4**. Baza po merge main do własnej gałęzi: **c3cf303d**, pierwotnie **7c9b4ca6**. Ostatni sprawdzony HEAD przed zapisem przekazania: **0586000c4de478d74653b6a53cc60e12a7ab0fb4**. Kolejne commity dotyczą zapisu tego przekazania; pozostawiony proces może później dodać własne WIP.

Produkcja D jest w `tools/worldgen/streetscape/plantings.py`. Jej SHA-256 przy zapisie: `6B25CE013DC206D563D3CBD039A44466FF2B6E9F345E6CDC5DD103BAA7851FB5`. Hash testu i próbki terenu oraz pełny wykaz kopii są w `OWNER-PAUSE-SNAPSHOT.json`. Kod i testy zapisano w commitach WIP; nie dodawano do gita surowych Megascans ani dużych snapshotów JSON.

Oryginalne zlecenie 24-godzinne rozpoczęto 11 listopada około 21:30:50, z terminem 12 listopada 21:30:50. Prośba właściciela o zakończenie zastępuje dalszą automatyczną pracę do tego terminu. **Nie wznawiać nowych etapów lub rund bez nowego polecenia właściciela.**

## Pozostawione zadanie — nie zostało ubite

Kontrola o **16:21:41** potwierdziła żywe oczekiwanie na heavy: **uchwyt narzędzia 68527**, cztery zgłoszenia przed nim, trzy zajęte sloty, PHONE_RUN nieaktywny. Aktualizacja przy końcowym zapisie **16:31:13**: ten sam uchwyt nadal żyje, przed nim zostało **jedno zgłoszenie**; nadal brak logów testów i World D. Nie ponawiano zadania. Procesy w odczycie z 16:21:

| Rola | PID | Początek |
|---|---:|---|
| zewnętrzny proces wykonania | 60052 | 15:15:16 |
| `green-d-and-world.ps1` | 57980 | 15:15:16 |
| Acquire heavy, owner gpt-vegetation-r4 | 64772 | 15:15:17 |

To dane z konkretnego odczytu, nie gwarancja ich aktualności później. Przed jakąkolwiek operacją sprawdzić również czas uruchomienia i polecenie, ponieważ PID może zostać ponownie użyty. Nie zatrzymywano żadnego z tych procesów i nie zwalniano slotu spod działającego zadania.

Istniejący kontroler po przydzieleniu heavy wykona **45 testów celowanych**, następnie tylko przy ich powodzeniu `build_world.py`, potem dekodowanie kolizji 64 Low chunków. Na końcu zwolni własny slot i zapisze WIP/STATUS. **Nie uruchamia Unity, importu, kolejnych prób lub nowej rundy.** Został pozostawiony, aby mógł naturalnie dokończyć już zleconą sekwencję. Może więc zmienić wyniki generatora i HEAD po sporządzeniu tego pliku.

Najważniejsze pliki w `artifacts/vegetation-r4/`:

- `pytest-green-d.log` — wynik 45 testów, jeżeli już ruszyły.
- `world-candidate-d.log`, `collision-candidate-d.log` — kolejne etapy.
- `green-d-and-world.done` — powstaje dopiero po sukcesie całej sekwencji.
- `green-d-pipeline-resume.log` — transcript; nie gwarantuje przechwycenia całego natywnego stdout/stderr. Szczegóły w `POLLING-NOTE.md`.
- `STATUS.md`, `session.json` — stan i chronologia; po zakończeniu zadania odczytać również logi i procesy.

**Nie uruchamiać ponownie `green-d-and-world.ps1` w ciemno.** Ma strażnika przeciw nadpisaniu istniejących logów i transcriptu. Poprzednia sekwencja 24975 zakończyła się kodem 1 na Acquire, zanim uruchomiła testy lub World. Szczegół przyczyny nie został zachowany; kontrolowane wznowienie 68527 opisano w `D-ACQUIRE-FAILURE.md`.

## Co jest rzeczywiście ukończone

R1 jest zamknięta jako PARTIAL, z poprawą trawy/poboczy i prześwitu berberysu. Raport jest w `artifacts/vegetation-r1/REPORT.md`; lider wcześniej ją zintegrował. R3 jest zamknięta jako REJECTED/NO-OP: próby drzew nie uzasadniły nowego kształtu w obrazie, kod przywrócono. Raport i dowody są w `artifacts/vegetation-r3/`. Nie traktować historycznych pozycji kamer jako aktualnie zaakceptowanych na main.

R4 dotyczy berberysu. Wykonano świeży baseline po zmianach main: **368 PNG**, 67 kamer kontrolnych i 25 fotograficznych B, Low/High × clear/overcast. Autor obejrzał wszystkie 40 arkuszy. Nie używano PNG wcześniejszych rund. Materiały ukończono w 446 s, World baseline w 614,8 s. Referencja wyglądu: Rakoon, CC0, 2020-11-02; zgodność pozy i sezonu UNVERIFIED.

| Próba | Wykonane i zmierzone | Ocena |
|---|---|---|
| A | 18 testów w 3,27 s; World 538,6 s; 18 402 tris nasadzeń; import i 16 ujęć. | Osiem arkuszy autora i krytyka: boki drobniejsze, ale duża płaska pokrywa. Odrzucona jako końcowa. |
| B, pierwotny loft | 8 failed, 19 passed w 4,16 s; skrzyżowane paski. | World nie ruszył; odrzucona przed renderem. |
| B2 | 33 testy w 10,29 s; World 534,6 s; 20 347 tris; kolizja, import, 16 ujęć. | Poprawna geometria, lecz gładki blat. FAIL końcowego realizmu. |
| C / B3 | 40 testów w 11,56 s; World 515,6 s; 21 697 tris; kolizja, import, 16 ujęć. | Autor i krytyk obejrzeli po 16 arkuszy baseline–C i B2–C: PARTIAL pokrywy, FAIL końcowego realizmu. |
| D | Kod i zestaw 45 testów przygotowane. Lekka analiza nadal 21 697 tris. | **Brak wyniku testów, World, importu i obrazów w ostatnim odczycie.** |

**Na dysku były wygenerowane GLB C i zaimportowana scena C, a źródła zawierają D.** Tego rozjazdu nie wolno przedstawiać jako wyrenderowanego D. Pozostawiony proces może później wygenerować GLB D; scena Unity pozostanie C do osobnego importu.

## Istota kodu i dowody

B2 naprawił samoprzecinające ringi: dokładne offsety, niezależne liczby punktów, lokalne CDT pasów z otworem i capów, spójne dzielenie trójkątów, szwy UV. Nie edytowano triangulatora dróg, stage.py ani overrides.yaml. Zmiana produkcyjna ogranicza się do plantings.py; inne rodziny zachowują starą ścieżkę.

C dodało deterministyczną pokrywę niezależną od wierzchołków capu, z korzeniami na jego rzeczywistych trójkątach i istniejącym atlasem pędów. D zachowuje liczbę próbek i kart, atlas i materiał; zmienia szerokość na 0,16–0,28 m, długość 0,12–0,22 m, pochylenie 1,10–1,45 rad od pionu i zagłębienie podstawy 45%. To WORKING_VALUE. Nad płaskim capem planowane wystawanie wynosi najwyżej około 5,5 cm. Domyślne zagłębienie innych pędów pozostaje 25%.

C ma maksymalnie **+0 drawsEst i +1,020408% trisK w małej próbie Low** względem baseline. Względem B2: +0 i +0,337838%. To nie pełny budżet kamer i nie pomiar GPU. Instancje i statyczne wywołania zapisano osobno. Wszystkie osiem kontrolnych PNG C jest identycznych z B2; sześć z baseline. Dwa High remizy zachowują różnice po sześć pikseli, których przyczyna nie została potwierdzona. Oba arkusze różnic obejrzano przy B2.

Piny C potwierdzają tylko plantings.py jako zmienione źródło, chunk_6_6 Low/High oraz metadane QA/manifest. Wszystkie 64 pliki instancji, dekodowana kolizja i far-field GLB są bez zmian. Dostępnych było 15 Megascans, bez fallback. Nie przenosić tego dowodu na D bez jego kontroli.

Nowa próbka `tests/gis/fixtures/berberis_0109_ground_c.json` zawiera 1527 rzeczywistych węzłów terenu C po dopasowaniu dróg, w rozstawie 1 m i kwantyzacji eksportu 1 mm. Cztery nowe przypadki prześwitu używają region-local XY, aby zachować fazę `_crown`. Mapowanie i poprawkę niezależnie sprawdził krytyk. Test nie dowodzi osadzenia całych pochylonych kart ani działania collidera 4 m. Po World D `candidate-d-probe.ps1` ma porównać regularne pozycje terenu i wszystkie próbki z C przed importem. Szczegóły: `ACTUAL-GROUND-TEST.md`, `VISUAL-CRITIC-ground-code.md`.

Autor obejrzał również osiem wycinków C w skali pikseli PNG; gładki blat pozostał widoczny. To dodatkowe arkusze, nie nowe rendery. Kontrola importu wykazała poprawne Repeat, skalę 1×1, GUID tekstury, alpha-cutoff i zgodne bajty PNG. Materiał używa **URP/Lit**, nie własnego WorldPBR. Nie potwierdzono hipotezy błędu Clamp lub brakującej tekstury. Dalsze informacje: `NATIVE-C-REVIEW.md`, `ATLAS-COVER-READONLY.md` i pliki JSON pomiarów.

## Zachowane pliki i brudny worktree

`OWNER-PAUSE-SNAPSHOT.json` zawiera SHA-256 i lokalizacje **dziewięciu sprawdzonych kopii**: siedmiu zmienionych plików wynikowych generatora oraz dwóch bieżących GLB C. Kopie leżą w `owner-pause-backup-20261112/`, z zachowaną strukturą ścieżek. Oryginałów nie zmieniano. Binarne kopie nie są dodawane do gita; mają pozostać w artefaktach lokalnych i ich kopii na main.

Siedem brudnych plików to metadane far-field, underdeck, streetscape/world, manifest far-field oraz props_meta i street_props.glb. **Nie wykonywać `git add -A`, masowego resetu ani przywracania ich podczas aktywnej generacji.** Po zakończeniu zadania porównać je z kopią i jawnie przywrócić skutki uboczne cudzych dziedzin przy zamykaniu rundy. Szczegółowe ścieżki są w manifeście kopii. Repo pozostaje celowo brudne w tych siedmiu plikach; nie jest to niezapisana praca utracona przy pauzie.

Cały katalog `artifacts/vegetation-r4/` skopiowano do `C:\Users\matma\Documents\Claude\kamion\artifacts\vegetation-r4`: 1116 plików w zestawie, 1113 skopiowanych, trzy pominięte jako istniejące, około 1,252 GB, zero błędów. Sprawdzono SHA przekazania i wszystkich dziewięciu kopii bezpieczeństwa; dowód to `OWNER-PAUSE-COPY-PROOF.json`, log `OWNER-PAUSE-COPY.log`. Kopia jest migawką przy przekazaniu. Jeżeli pozostawiony proces dopisze później logi lub STATUS, **najnowszy stan jest w źródłowym worktree**, dopóki nie wykona się kolejnego robocopy. Nie ma końcowego REPORT.md r4; `REPORT-DRAFT.md` jest wyłącznie szkicem. ADR: `docs/adr/0109-vegetation-24h.md`.

## Wznowienie — dopiero po nowym poleceniu właściciela

1. Przeczytać aktualne HANDOVER, feedback i `docs/owner/GPT-TASK-05-24H.md`. Sprawdzić gałąź, git status, procesy oraz logi. Uchwyt 68527 jest związany z obecną sesją narzędzia; jego brak w nowym czacie nie dowodzi, że proces zakończono. Nie restartować na podstawie samego timeoutu lub pliku blokady.
2. Jeśli D nadal żyje, pozwolić mu dokończyć. Jeśli zakończyło się błędem, zachować logi i ustalić etap. Błąd testów oznacza brak World; błąd World może zostawić częściowo nadpisane wyniki, których nie należy importować. Plik done wymaga zgodnego wyniku testów, World i kolizji.
3. Po rzeczywistym sukcesie D uruchomić `pwsh artifacts/vegetation-r4/candidate-d-probe.ps1` **raz**, jeśli snapshot D jeszcze nie istnieje. Najpierw sprawdzi teren względem próbki C, następnie piny, import i 16 ujęć. Gdy snapshot lub część ujęć już istnieje, wznowić właściwy etap po analizie zamiast ponawiać całość.
4. Przygotować standardowe porównania baseline–D i C–D przez `review_berberis.py --after-root probe-d --snapshot candidate-d`, dodatkowo `--before-root probe-c`; opcja `--native-crop` tworzy osobne wycinki. Autor i niezależny krytyk muszą je obejrzeć. D musi ograniczyć zarówno sterczące pędy, jak i gładki blat. Nie uznawać samych testów za realizm.
5. Dopiero po dobrej małej próbie można przejść do pełnych 368 after przez `after-approved.ps1`. Instrukcja jest w `AFTER-CONTROLLER.md`. Plik approved-probe.json **nie istnieje**; kontroler prawidłowo odmawia startu bez własnej zapisanej oceny autora i krytyka. To nie prośba o dodatkowe zatwierdzenie użytkownika, lecz zapis wyniku wymaganej oceny.
6. Obowiązują wszystkie kamery Low: draws +0, tris ≤+2%, instancje osobno. Obejrzeć 40 nowych arkuszy after i właściwe pary zdjęć. Pełny GIS wyłącznie na końcu rundy: `heavy-task.ps1 -Task GisFinal` zapisze też JUnit xunit1 z marginesami prześwitu. EditMode przez `editmode-safe.ps1`. Dotychczasowe historyczne porażki stale road fidelity trzeba ponownie rozpoznać w bieżącym wyniku, a nie automatycznie ignorować.
7. Zamknąć r4 dopiero uczciwym REPORT z SHA, wynikami, parami ≤960 px, ograniczeniami i konfliktami. Przywrócić jawne skutki uboczne, zachowując kopie, i skopiować artefakty. Następna gałąź w tym samym worktree to wolna gpt-vegetation-r5, potem merge main do niej. **Nie rozpoczynać tego teraz automatycznie.**

Przed każdym Unity używać aktualnego `C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1` z owner `gpt-vegetation`; po zakończeniu Release. Ciężki Python: ten sam skrypt, `-Pool heavy -Owner gpt-vegetation-r4`, Release w finally. Bez Priority, bez usuwania cudzych slotów lub PHONE_RUN. Aktualny skrypt main f7d0e5a0 dopuszcza heavy podczas PHONE_RUN, lecz stare uruchomione pętle Acquire mogą nadal blokować czoło FIFO. Odczyty i wcześniejsze nawroty są w `RESOURCE-WAIT.md`; nie są zgodą na sterowanie innymi sesjami.

B8, pobocza i pozostały backlog nie zostały rozwiązane w r4. Przed powrotem do sadzenia z fotografii sprawdzić najnowszą ocenę pozy 297817 na main; nie przenosić starych wniosków o pozach po nowych zmianach SBS. GPU A16 i zachowanie w ruchu pozostają UNVERIFIED — telefony należą do lidera.

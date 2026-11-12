# Przekazanie sesji 9 — edge

Stan sprawdzony 12 listopada 2026 o 16:23 CET. Właściciel polecił zakończyć pracę wcześniej z powodu kończącego się limitu tygodniowego, zapisać wszystko i nie ubijać procesów. Nie zaczynać następnej rundy bez nowego polecenia.

## Repozytorium i zapis

- Repo główne: `C:\Users\matma\Documents\Claude\kamion`.
- Worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-edge`.
- Bieżąca gałąź: `gpt-edge-r6`. Baza rundy: merge `dcf1b4e18fd76f449888033b64238493ce329609`, pobrany main `863a25b938ae5d53f0df2f966c0ed951f2595f65`.
- Ostatni checkpoint narzędzi przed zatrzymaniem: `5c5096e7bd99540b94457746242a5f9707be30e3`. Miękkie zatrzymanie: `d2bf682a`. Ten dokument i końcowy zapis otrzymają kolejny commit; aktualny SHA sprawdzić przez `git rev-parse HEAD` w worktree.
- Szczegółowy dziennik: `artifacts/edge-r6/STATUS.md`. Migawka procesów: `artifacts/edge-r6/handover-live-state.json`. Wszystkie ścieżki względne poniżej dotyczą worktree, chyba że zaznaczono inaczej.
- Na chwilę kontroli brak zmian produkcji r6 względem jej bazy: `git diff dcf1b4e1 -- game tools Data` jest pusty. Kandydaty pozostają w artifacts. Nie scalano do main, nie pushowano i nie używano telefonów ani adb.
- Pierwotna doba miała zakończyć się 12.11 o 21:31:27 CET; najnowsze polecenie właściciela zatrzymuje sesję wcześniej. Nie przedłużać automatycznie terminu po wznowieniu.

## Co zostało ukończone

Rundy r1–r5 mają osobne gałęzie, REPORT.md, STATUS.md, ADR 0121 oraz kopie swoich artefaktów w main. Ograniczenia i niezaliczone kontrole starszych rund pozostają zapisane w ich raportach — nie zastępować ich wynikiem z późniejszej bazy.

| Runda | Rezultat i ograniczenia |
|---|---|
| r1 | Rzeczywisty profil apron pod przedłużeniami dróg i rozróżnienie pobliskich jezdni; 24 → 35 kontynuacji, minimum prześwitu około 0,0403 m. Ocena obrazu częściowa. |
| r2 | Wysokości sylwetki z LoD1 i pochodzenie danych; 5390 dopasowanych budynków. Nie utożsamiać geometrii z rozpoznawalnością na zdjęciu; końcowy GIS tej rundy miał udokumentowane porażki. |
| r3 | Usunięcie nadwagi powielonych narożników w wygładzaniu apron; rzeczywisty Red/Green, EditMode 297/297 i końcowy GIS 591 passed, 1 xfailed. Resztkowy kontakt kurtyn i B9 otwarte. |
| r4 | Diagnoza klina na tle nieba: ablacje wykluczyły apron/far-field i wskazały obcięcie chmur. Bez zmiany produkcji edge; naprawę światła wykonał właściciel tej dziedziny. |
| r5 | Stonowanie hali i usunięcie wyglądu elektrociepłowni nadawanego samą wysokością. Addytywne panele/szkło za flagami danych WorldSurface. Obraz PARTIAL; walidacja techniczna zaliczona. |

Ostatnia zamknięta runda to **gpt-edge-r5, `a3479bac`**. Jej produkcyjna poprawka jest w `1366907a`. Lider scalił r5 do main jako `05cd2a76` i ocenił ją jako częściową poprawę (recenzja batch E).

R5: pełny build After 521,8 s bez `fallback=True`; Red 18/20 z dwiema oczekiwanymi porażkami, Green 20/20 na identycznym teście; EditMode 340/340; końcowy GIS 710 passed, 1 xfailed, 0 failed w 1154,93 s. Wszystkie 472 pary, w tym 236 Low, mają zerowe delty draws statycznych, instancji, cieni i zaokrąglonych trisK. GPU telefonu nie zmierzono.

Pakiet r5 dostarczono i zweryfikowano: 1302 pliki bez receipt, 2 761 142 507 bajtów, 17 krytycznych SHA. REPORT SHA256: `0555264C02EF325D9B85DB196342C17B7229D90AA2F245606EFA2365BA17B926`. Raport i zdjęcia są w main `artifacts/edge-r5/`.

## R6: co jest prawdą, a czego jeszcze nie wykonano

R6 rozpoczęła się około 14:20. Przyjęła recenzowane pozy kamer G3-B i nowy main, odświeżyła cache bez fallbacków pozorowanych przez brak plików, sprawdziła brak pointerów LFS i zamroziła wejścia dowodowe. Gotowe mapy materiałów pochodzą ze sprawdzonej r4, ponieważ ich źródła i specyfikacja nie zmieniły się; import ma sprawdzenie kompletności i czasu źródeł.

Główna macierz r6: **43 kamery plikowe** (42 kanoniczne + edge-pietrasze-driver), 25 zdjęć B i diagnostyczne 2948 w native, 26 kamer native na konfigurację. Nie przenosić liczby 472 par z r5; wynik ma być wyznaczony z rzeczywistych nowych stats.

Na 16:23 **nie istnieją** `Baseline.ready`, ukończone Before, wynik kontaktu, Red/Green ani After r6. Nie wykonano nowego EditMode ani pełnego GIS r6. Nie zmieniono WorldEdgeBuilder, far_field.py lub shadera w tej rundzie. Kontrole składni narzędzi zaliczono; nie są wynikami Unity ani pomiarami geometrii.

### Ustalenie kamery NW

Własny archiwalny statyw `edge-nw-ground` ma U=151,733 m, podczas gdy NMT i conformed w jego EN mają 152,13 m: około **0,397 m pod powierzchnią danych**. To błąd diagnostyki, a nie dowód wadliwego apron. Przed jakimkolwiek Before r6 usunięto ten statyw z głównej macierzy. Wstępny draft 44 kamer zachowano jawnie jako preflight. Nie ruszano kanonicznych kamer.

Statyw pozostaje wyłącznie w osobnych maskach i porównaniu z automatycznym posadzeniem na colliderze (diagnostic: nominalnie +2,5 m). Hipoteza: szara podłoga pochodzi z dolnej półsfery nieba widzianej spod gruntu. **Brak jeszcze potwierdzenia na rzeczywistym colliderze/renderze r6**. Dowody danych: `archival-nw-camera-height.json`, `archival-nw-conformed-height.json`; pliki kamer: `ownership-cameras.json`, `height-cameras.json`.

### Kandydaty, nadal poza produkcją

1. **Pierścień apron 280 → 220 m.** Profil near-easing kończy się na 220 m, ale obecna siatka ma pierścienie 160/280. Kandydat zastępuje jeden istniejący pierścień, bez wzrostu budżetu. Najpierw świeże maski i kontakt. `WorldEdgeApronTransitionTests.candidate.cs` ma osiem niezależnych przypadków rzeczywistego BuildApron z wąskim rowem; przewidywany Red 6 porażek + 2 kontrole jest tylko rachunkiem referencyjnym, nie wynikiem NUnit. Przed Red istniejący test narożnika trzeba przenieść z punktu 280 m na wspólny punkt 160 m i przeliczyć pełne oczekiwanie, bez osłabiania tolerancji. Łącznie oczekiwane 16 testów: Red 6 fail/10 pass, Green 16 pass — rzeczywisty wynik dopiero do sprawdzenia.
2. **Hash paneli bez sin.** `FarPanelHash.candidate.hlsl` używa ograniczonej arytmetyki float i nie wymaga podniesienia target 3.0. Jedynie kandydat do nowych znaczników przemysłowych 0,25/0,65; legacy zachować. Referencja arytmetyczna nie jest kompilacją ani pomiarem Mali. Nie zainstalowano.
3. **Zapory końca mapy.** `BOUNDARY-P1.md` opisuje zależność od drivable danych, collision i WorldSafetyNet. Nie ukrywać samych rendererów, nie usuwać cudzych barier ani runtime i nie maskować problemu dla QA. Wymaga koordynacji z właścicielem dróg/runtime.
4. **B9 — bloki na horyzoncie.** Odczyt danych wskazuje kandydatów wewnątrz regionu, więc nie dodawać duplikatów far-field. `artifacts/edge-r3/next-round-review/near-city-ownership.json` ma identyfikatory i przybliżone położenia. Generator regionalny korzysta z height_m, ale merged GLB nie dowodzi jeszcze wysokości/okluzji konkretnego obiektu. Nie edytowano źródeł Claude ani roślinności.

Narzędzia przygotowane w r6: `test-apron.ps1`, `run-after.ps1`, `compare.py`, `audit_contact.py`, `segment_contact.py`, `audit_mesh.py`, `audit_round_geometry.py`, `measure-after.ps1`. Są nieuruchomione w nowej fazie, mają twarde bramki i wymagają slotów. Audyt kontaktu obejmuje rzeczywiste importowane podstawy oraz pełne dolne krawędzie przez trójkąty apron; nie wnioskuje o pokryciu alfa. Niezależne małe kontrole tego algorytmu uruchomią się dopiero wewnątrz heavy. Kontrola geometrii zakłada konkretnie kandydat pojedynczego pierścienia, więc nie używać jej bez adaptacji dla innego rozwiązania.

## Miękkie zatrzymanie i procesy pozostawione bez ubijania

Utworzono `artifacts/edge-r6/STOP.requested`. Nowo ładowane `acquire-slot.ps1` odmawia kolejnych Acquire; `import-baseline.ps1` kończy się kodem **75 przed Unity** i zapisuje `PAUSED-BEFORE-IMPORT.json`. To zamierzone zatrzymanie na polecenie właściciela, a nie niezaliczony test produktu.

**Już załadowanego PowerShella nie aktualizuje edycja jego pliku.** Z tego powodu pozostawione wcześniej w kolejce przygotowanie może jeszcze uzyskać heavy i wykonać jeden bazowy build_world, zapisać receipt/STATUS/WIP i normalnie zwolnić slot. Nie uruchomiono go ponownie. Następny import wczyta miękką bramkę i nie wystartuje. Zależne maski i audyt zakończą oczekiwanie po wyjściu procesu baseline, bez fałszywego Baseline.ready. Późniejsze automatyczne wpisy starego przygotowania w STATUS nie oznaczają polecenia wznowienia.

Migawka z 16:23: heavy 3/3 zajęte przez inne sesje, dwa bilety przed edge, PHONE_RUN=False. Edge **nie posiadał** slotu heavy ani Unity; nie działał jeszcze jego Python ani Unity r6. Nie usuwano cudzych slotów, biletów, PHONE_RUN i nie używano Priority.

| PID z datą startu 12.11 | Zadanie | Sesja exec |
|---|---|---|
| 46048, 14:55:44 | prepare-baseline.ps1, czeka na heavy; może dokończyć jeden świat | 84068 |
| 71536 / 55024, 14:55:44–45 | wrapper / centralny Acquire heavy dla gpt-edge-r6 | w powyższej |
| 74364, 14:56:07 | run-baseline.ps1, zależny od przygotowania; zatrzyma się przed importem | 78151 |
| 65152 / 28720, 14:56:43–44 | run-ownership / pierwsza maska, czekają na Baseline.ready | 36754 |
| 11680, 14:56:43 | audit-contact before, czeka na Baseline.ready bez zajęcia heavy | 55779 |

Powyższe PID są migawką, mogą później zostać ponownie użyte. Przed działaniem sprawdzić CreationDate i CommandLine w `handover-live-state.json`, nie działać po samym numerze. Logi: `prepare-baseline.log`, `build-world-baseline.log` (dopiero po starcie), `run-baseline.log`, `ownership-runner.log`, `contact-before-runner.log`. Szczegóły starszego zatrzymania FIFO: `SLOT-WAIT-DIAGNOSIS.md`, `slot-state-1612.json`. Pierwsza próba Acquire z sharing violation ma zachowane oddzielne logi; nie uruchomiła świata.

Kopia w main jest migawką z chwili przekazania. **Autorytatywny końcowy log i późniejszy receipt pozostawionego przygotowania są w worktree**; po jego zakończeniu skopiować je ponownie. Nie zmieniać gałęzi, nie robić merge i nie odpalać drugiego przygotowania, dopóki stare zadania nie zakończą się normalnie.

## Bezpieczne wznowienie po nowym poleceniu właściciela

1. Odczytać ten plik, STATUS i rzeczywiste procesy/receipt. Potwierdzić, czy przygotowanie zakończyło się poprawnie, czy istnieje `PAUSED-BEFORE-IMPORT.json`, oraz czy wszystkie stare zależności wyszły. Nie zabijać cudzych procesów i nie zwalniać własnego slotu, jeśli nadal działa jego zadanie.
2. Dopiero po świadomym wznowieniu usunąć **własny** STOP.requested. Bramka pozostaje użyteczna na przyszłość. Nie usuwać cudzych locków. Przy poprawnym receipt świata można dokończyć import z istniejącego przygotowania, bez powtórnego build_world; przy braku receipt najpierw zbadać log, nie udawać gotowego baseline.
3. Zakończyć pełny import, Before generic/native i zamrożenie before-source. Obecny `run-baseline.ps1` potrafi czekać na ukończone przygotowanie; przed ponownym wywołaniem sprawdzić brak poprzedniego procesu i brak podwójnych commitów/importów. Odtworzyć zależne maski/kontakt tylko wtedy, gdy stare procesy rzeczywiście już wyszły.
4. Obejrzeć maski i re-seat w ≤960 px. Przeczytać świeży `contact-before.json`; nie przenosić 1/7 z r3 jako wyników r6. Dopiero wtedy zdecydować o kodzie. Zmiany kamery nie są poprawką świata.
5. Dla kandydata pierścienia: zainstalować testy i poprawić punkt testu narożnika **przed Red**, wykonać prawdziwy Red, następnie jedną zmianę 280 → 220 i Green na identycznych SHA testów. Potem pełny build_world, przebudowa edge i After, rzeczywiste audyty oraz przegląd obrazu. `run-after.ps1` i `measure-after.ps1` wymagają odpowiednich markerów i zaliczonego Green.
6. Pełny GIS wyłącznie na końcu rundy, po pojedynczych plikach w trakcie i po ocenie obrazów, na świeżym pełnym manifeście. Odtworzyć obce metadane dopiero po testach z zachowaniem własnych pól. EditMode, REPORT normalnym polskim tekstem, ADR 0121, robocopy i kontrola SHA. Nie przedstawiać wstrzymanej r6 jako ukończonej rundy.

Przed każdym Unity obowiązuje centralny `pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Pool unity -Owner gpt-edge`, po nim Release w finally. Każdy ciężki Python analogicznie `-Pool heavy -Owner gpt-edge-r6`, maksymalnie 3 na maszynie; biblioteki numeryczne po jednym wątku. Pełny GIS tylko na końcu. Bez telefonów, push i merge do main; wyłącznie dziedzina edge.

Uwaga dowodowa z recenzji lidera: High VQA tej bazy zapisuje R8 przed post, więc końcowa fotometria jest UNVERIFIED. Nie naprawiać cudzych narzędzi w tej sesji. Nowe main po 14:20 nie zostało domieszane do r6; nie zmieniać bazy w połowie par Before/After.

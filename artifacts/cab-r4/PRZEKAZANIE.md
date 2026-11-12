# Przekazanie sesji cab

Stan zapisany 12 listopada 2026 około 16:26 CET. Praca została przerwana na wyraźną prośbę użytkownika z powodu kończącego się limitu tygodniowego. Pierwotne okno 24 godzin nie zostało dokończone. Runda 4 pozostaje otwarta i nie jest gotowa do scalenia. Nie uruchamiać dalszej pracy bez nowego polecenia użytkownika.

## Miejsce i Git

- Repo główne: C:/Users/matma/Documents/Claude/kamion
- Jedyny worktree tej sesji: C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-cab
- Aktualna gałąź: gpt-cab-r4.
- Punkt przed zapisaniem przekazania: 8958177ca874d6019cc8b37d34580b7e09a47a3e. Końcowy WIP przekazania zawiera ten plik i STATUS.md.
- Baza r4: r3 aefad847, merge main 8b74c2c5 w commit 6c5c12f8. Nie scalano do main i nie pushowano.
- Własny kod i materiały są commitowane. Pięć niezatwierdzonych plików poza cab to produkty generatora World, zachowane celowo do końcowego GIS. Nie wykonywać git restore całego drzewa ani git add -A.

Ich dokładne ścieżki i SHA256 zawiera preserved-world-state.json. Kopie bajtowe są w preserved-world-state/, a dodatkowo w preserved-world-state.zip; różnicę Git zachowuje preserved-world-state.patch. Plików źródłowych innych dziedzin nie zmieniano. Settings Unity są cofnięte przez wrappery.

## Pozostawiony proces — nie uruchamiać duplikatu

Na prośbę użytkownika nie zabijano istniejącego zadania podczas kończenia pracy. Ostatnia kontrola 16:26 potwierdziła:

- root PID 63712, utworzony 2026-11-12 o 15:52:55.924861 CET;
- sesja narzędzia 19993;
- zadanie MaterialFine, owner gpt-cab-r4, status waiting, próba acquire 1;
- potomek PID 70644 to wyłącznie PowerShell pozyskujący slot;
- brak własnego Pythona lub Unity w trakcie obliczeń w tej kontroli.

Receipt: artifacts/cab-r4/job-MaterialFine-20261112-155256-63712.json. Log oczekiwania: job-MaterialFine-20261112-155256-63712.acquire-attempt-1.log. Log zadania po uzyskaniu slotu: material-fine.log. Snapshot procesu: handoff-state.json.

To już istniejący proces. Gdy dostanie slot, przygotuje offline dwa warianty normalnych Plastic, zapisze fine-verification.json i mapy do material-prep/candidate-hp03 oraz candidate-hp06, zwolni własny slot i zakończy się. Nie integruje ich do gry, nie uruchamia Unity ani kolejnej rundy. Wynik może powstać po zakończeniu tej rozmowy i wtedy będzie przede wszystkim w worktree; kopia main jest migawką z chwili przekazania.

Przed ewentualnym wznowieniem odczytać aktualny receipt i sprawdzić proces, uwzględniając czas utworzenia PID. Sukces wymaga exit_code 0 oraz status PASS w material-prep/fine-verification.json. Samo finished nie wystarcza. Nie ponawiać żywego zadania i nie zwalniać jego slotu. Stare sesje 21503/PID 45068 i 86584/PID 32752 są terminalne; nie wznawiać ich.

## Zakończone rundy

| Runda | Gałąź / końcowy commit | Wynik |
| --- | --- | --- |
| r1 | gpt-cab-r1 / a8651008 | Culling wnętrza w sześciu RT, ramiona i obrzeża luster. EditMode 276/276. GIS 491 pass, 2 fail, 1 xfailed; ograniczenia w REPORT. Artefakty skopiowane do main. |
| r2 | gpt-cab-r2 / d04feba0 | Brown Leather CC0, pochodny Plastic, korekta UV obręczy. Reprodukcja 12/12 SHA, EditMode 279/279. GIS 521 pass, 2 fail, 1 xfailed. Artefakty skopiowane do main. |
| r3 | gpt-cab-r3 / aefad847 | Nocne legendy przycisków za flagą danych, odczytowy audyt prawego lustra. EditMode 301/301. GIS 576 pass, 1 xfailed. Budżety pełnych 78 kamer i 36 RT bez wzrostu. Artefakty skopiowane do main. |

Raporty są w artifacts/cab-r1, cab-r2 i cab-r3. R3 wyjaśnia, że szeroka ciemna część prawego szerokokątnego jest w badanej pozycji treścią RT, a nie szerokim zasłonięciem kanałem drzwi. Nie przesuwać oka/FOV, aby ją ukryć. R1/r2 historyczne porażki GIS dotyczyły staleness Fidelity i deterministyczności World; r3 przeszła na świeżych produktach, bez napraw kodu innych dziedzin.

## Runda 4 — aktualny stan produktu

Do końcowej walidacji wybrano Low Decal 256 px z mip bias −0,75, sterowany cab_legend_atlas.json. Medium/High bez bias. Nie zwiększono atlasu ani renderScale, nie dodano próbek, przebiegów, materiałów lub geometrii. Ikony miejscowo są wyraźniejsze, lecz P1 pełnej czytelności nie jest zamknięty. Migotanie i GPU telefonu pozostają niezmierzone.

Odrzucono atlas Low 512 jako wizualnie znikomy. Odrzucono ogólny cutoff 0,4, który nie sterował widocznym pasmem ikon, oraz osobny próg ikon 0,28, który usuwał cienkie kreski. Ich kod i pola danych wycofano. CabInterior.shader jest dokładnie przywrócony do stanu bazy r4. LEGEND-REVIEW.md podaje obejrzane ROI, hashe i zakres porównań. Uwaga: ostatni BuildBatch był dla odrzuconego eksperymentu; przed nowymi ocenami gry przebudować assety z aktualnych źródeł.

Plastic ma w źródłach nadal eksperymentalny filtr normalnych 1,5 mm. Jest technicznie poprawny, ale High clear nadal wygląda jak tłoczenie skóry; brak akceptacji wizualnej. Mocniejsze 0,3 i 0,6 mm nie zostały jeszcze przygotowane ani zintegrowane w momencie przekazania. To zadanie pozostawionego procesu. Plastic nadal jest pochodną skanu Brown Leather, nie skanem konkretnego tworzywa. Nominalny kafel 10 cm i zachowane UV części 8/6 cm dają proporcjonalnie różne progi fizyczne. Parametry są WORKING_VALUE.

Odtworzenie 12 map bazowych zgadza się SHA256 12/12. Kandydat hp15 zmienia tylko trzy Normal Plastic; Detail/alpha i Leather pozostają identyczne. Małe testy filtra: 7/7 w 1,00 s. Metadane i dowody są w material-prep/verification.json oraz normal-highpass-unit.log.

## Co jest zweryfikowane, a co nadal otwarte

- World r4: exit 0, log 477,4 s, brak fallback=True. Po wykryciu brakującego lokalnego wejścia zdjęciowego naprawiono tylko asphalt_detail_photo i ponowiono import. Niepełny baseline-without-photo jest wykluczony z porównań.
- Poprawiony baseline i hp15: po 42 kadry kabiny, 36 natywnych RT i 78 kamer trasy. comparison-0112-r4.json PASS, wszystkie delty regular/shadow/instanced draws i regular/instanced tris 0, interiorPixels 0 we wszystkich RT. To estymaty CPU, nie GPU A16. Dotyczy hp15 i bias-only.
- Pełny EditMode 346/346 z 13:55 dotyczył wcześniejszego stanu bias-only. Po późniejszych próbach i wycofaniu kodu wymagane jest końcowe uruchomienie.
- Fidelity po World: 23/23 hashów zgodnych w kontroli 12:16. Przed końcowym GIS sprawdzić ponownie; nie uruchamiać ciężkiego Fidelity bez potrzeby.
- Pełnego GIS r4 jeszcze nie uruchomiono.
- Obejrzano dodatkowo sześć kadrów istniejącego Night. Podświetlenie legend nadal słabe względem prywatnej referencji Volvo. Night jest modelem wyglądu na granicy zmierzchu, nie kalibracją astronomicznej nocy. Nie zmieniano światła świata ani luminancji legend w r4.
- Pasmo AO deski i zużycie kontaktowe pozostają otwarte.
- REPORT-DRAFT.md jest szkicem z dotychczasowymi dowodami, NIE końcowym REPORT.md. R4 nie jest gotowa do integracji.

## Kontynuacja, tylko jeżeli użytkownik ją ponownie zleci

1. Przeczytać ten plik, STATUS.md, ADR 0112 i aktualny docs/owner/GPT-TASK-05-24H.md. Pozostać na gpt-cab-r4 w tym samym worktree.
2. Sprawdzić pozostawiony proces i wynik MaterialFine. Jeśli już zakończony poprawnie, obejrzeć mapy hp03/hp06 i fine-verification.json. Nie uznawać ich za zaakceptowane tylko na podstawie testów numerycznych.
3. Po obejrzeniu map uruchomić krótką próbę przez material-variant.ps1 -Variant hp03 lub hp06. Helper weryfikuje SHA, kopiuje tylko normalne Plastic, ustawia sigma, robi WIP, BuildBatch/InstallBatch oraz po dwa kadry High clear/Low overcast. Nie uruchamiać go równolegle z innym własnym Unity.
4. Wybrać materiał po porównaniu obrazów. Zrobić pełne końcowe 42 kadry, 36 RT oraz 78 kamer trasy, a następnie porównanie budżetów. capture-0112.ps1 i route-0112.ps1 przyjmują -Stage. Nie nadpisywać istniejącego wyniku etykietą innego wariantu.
5. review-sheets.py ma obecnie domyślny after=result-0112-hp15; przed użyciem dla zwycięzcy zmienić właściwy etap lub przekazać --after i dostosować wrapper. Pełna obróbka arkuszy odbywa się pod heavy. Arkusze trzeba faktycznie obejrzeć. Pary zdjęcie/render mają maksymalnie 960 px.
6. Uruchomić pełny EditMode przez tests.ps1 -Full. Sprawdzić aktualność Fidelity i wykonać końcowy pełny GIS przez heavy-0112.ps1 -Job GisFinal. Pełny GIS tylko na końcu rundy. Po terminalnym zakończeniu zachować raporty i cofnąć wyłącznie rzeczywiste produkty generatora spoza cab, nie własny kod lub cudzą pracę.
7. Dokończyć REPORT.md normalnym polskim tekstem, z SHA, wynikami, parami, ograniczeniami i konfliktami. Robocopy własne artifacts do main bez /MIR. Dopiero po zamknięciu r4: gpt-cab-r5 od r4, następnie git merge main, zgodnie z protokołem. Bez nowej zgody użytkownika teraz tego nie robić.

## Zasoby i granice

Zawsze używać aktualnego skryptu C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1. Unity: owner gpt-cab. Ciężki Python/Blender/partie obrazów: Pool heavy, owner gałęzi, maksymalnie jedno własne heavy przez mutex. Bez Priority, bez cudzych slotów i bez usuwania PHONE_RUN. Wersja main z 14:49 blokuje PHONE_RUN tylko dla Unity; stare procesy Acquire z wcześniejszą polityką potrafiły blokować FIFO mimo pustej puli. Własne pozyskanie zostało bezpiecznie odświeżone, z zachowaniem ticketu 14:30. Diagnoza w resource-queue-diagnosis.json; innych procesów nie zmieniano.

Nie używać telefonu/adb, nie pushować, nie scalać do main, nie edytować innych dziedzin ani kodu Claude. Materiały wnętrza i lusterka to jedyny zakres. Zdjęcia z copyright/logo i ich pochodne panele pozostają lokalnie poza Git. Nie dublować wpisu Brown Leather w LICENSES. W robocopy do main mogą być prywatne referencje QA; nie są materiałem gry ani publiczną publikacją.

Kopia artefaktów wykonana przy przekazaniu jest opisana w COPY-ON-STOP.json. Jeśli istniejący MaterialFine zakończy się później, jego nowszy receipt/log/wynik trzeba odczytać z worktree i ewentualnie skopiować przy wznowieniu. Nie ma automatycznej kolejnej rundy ani automatycznego uruchomienia Unity.

## Końcowy zapis przy zatrzymaniu

Kopia do main: 769 plików, FAILED 0, robocopy exit 1 (udane kopiowanie), 12 listopada 16:28. Końcowa kontrola procesu: 2026-11-12T16:29:36.1557191+01:00, status finished, root żywy: False. Pełne dane w handoff-final-state.json. Nie uruchomiono nowych buildów, testów ani renderów po poleceniu zatrzymania. Istniejącego zadania nie przerywano.

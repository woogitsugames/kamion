# Aktualny stan R2 — 12.11.2026, 02:00 Europe/Warsaw

Gałąź gpt-sbs-r2, wyłącznie domena SBS. Runda jeszcze niezakończona.

Gotowe: świat kod 0 (457 s, bez fallback=True), 64 GLB o SHA identycznych z r1; import Low+High; EditMode 261/261; 168 nowych renderów z jednego HEAD b9b5574e; 168 wierszy liczników, wszystkie delty Low geometrii/instancji/tris = 0. SHA 143/168 PNG identyczne z r1. Test raportu po rzeczywistej poprawce HTML: 25/25; test zgodności SBS: 40/40, fotometria: 13/13, fidelity: kod 0. Własny i niezależny przegląd sześciu zmienionych B zapisany. Formalna recenzja D51 pozostaje r1 FAIL 12/11/2, klasy 25 B / 17 C / brak A bez zmian.

W toku: końcowy pełny GIS w sesji 87983, przez heavy gpt-sbs-r2 z -EndOfRound, źródła e386b929. Wcześniejsze sekwencje 79348 i 44605 zakończone kodem 0. Audyt, kompozycje, raport, przegląd 100/100 i kontrola UI gotowe. Nie zmieniać kodu źródłowego do zakończenia testu; można dopracować roboczą dokumentację. REPORT-DRAFT.md nie jest jeszcze końcowym REPORT i nie uruchamia dostawy do main.

Do zakończenia: audyt oraz przegląd pozostałych 75 A/B i raportu HTML; niezależny przegląd narzędzia/pakietu; pełny GIS dopiero na końcu; finalny ADR/REPORT; robocopy r2 i latest do main bez commitowania na main; zaraz potem nowa gałąź rundy i merge main. Produkty generatorów spoza SBS nie będą commitowane i zostaną przywrócone po zachowaniu dowodów. Nowe pełne capture wykonano około 00:20; następny odczyt aktualnego main najpóźniej około 06:20.

Cały cel trwa do około 12.11.2026, 21:31 Europe/Warsaw. Nie pushować, nie scalać do main, nie używać telefonów. Unity: owner gpt-sbs. Heavy: owner bieżącej gałęzi. Cudzych slotów i PHONE_RUN nie zmieniać.

## Dziennik wykonanych kroków
# Stan rundy sbs r2
Gałąź gpt-sbs-r2, ten sam worktree. R1 zakończona na 814d3408, artefakty skopiowane i zweryfikowane na main. Wykonano merge main ce3f1a77 (merge bec082b1), bez konfliktów. Zmiany main od bazy r1 dotyczą dokumentacji i ochrony zasobów, bez zmian generatora świata, materiałów i runtime.
Przeczytano nową D51 oraz recenzję REVIEW-2026-11-11-s11-sbs-r1-D51.md. Bramka świata: FAIL według rozpoznawalności, 12 rozpoznawalnych / 11 częściowych / 2 nie. G3-B pozostaje głównym problemem. Fotometria nie jest blokerem bramki. Cztery dodatkowe zastrzeżenia pozy dotyczą 328135, 177786, 494288 i stacji 275528; nie ukrywamy ich przez usuwanie negatywnych ocen świata.
R2 obejmuje metryki obrazu i kontrastu, zgodność kohort/warunków przy trendzie, raport HTML latest oraz ślad D51. Punkty i maski mają wiązać się z konkretnymi obrazami; nie wolno zaliczać świata na podstawie histogramu. Priorytety geometryczne w r3 oprzemy na D51.
Ciężkie zadania wyłącznie przez run-heavy.ps1, właściciel gpt-sbs-r2, max 3. Unity przez osobne sloty gpt-sbs, max 4. Pełny GIS dopiero na końcu rundy. Nie używamy telefonów, nie scalany do main, nie pushujemy.
Następny krok: przegląd metrics/report API i implementacja raportu z jednoznacznym stanem D51 oraz trendami dla zgodnych źródeł.
## Metryki obrazu v2
Wydzielono moduł sbs_photometry: kontrast RMS, zakres percentyli, gradient przy wspólnej rozdzielczości, maski nieba/asfaltu i wyłączenia maski samochodu. Ręcznie zweryfikowane próbki wiążą się z SHA obu obrazów, zgodnym światłem i przybliżoną lub lepszą pozą. Nie stanowią oceny D51 ani awansu klasy. Nowa definicja metryk jest jawna, żeby nie porównywać niezgodnych algorytmów.
Pierwszy test zgodności wykrył niemodyfikowalną tablicę maski PIL; poprawiono operację bez zmiany danych źródłowych. Następny krok: pojedynczo test_sbs_gate3.py i test_sbs_photometry.py przez heavy, potem raport HTML.

## Raport i wynik testów
Zgodność dotychczasowej kompozycji: 40/40, testy fotometrii: 13/13. Dodano raport HTML działający lokalnie oraz bazę 25 ocen D51, związaną z SHA renderów r1. Wynik świata pozostaje FAIL; nowe obrazy nie dziedziczą automatycznie dawnych ocen. Trend odrzuca zmianę pozy, źródła, masek, definicji metryk, tieru lub światła oraz próbki bez ręcznej kwalifikacji. Następny krok: testy raportu i odtworzenie świata przed nowym importem.

## Odświeżenie świata i testy raportu
Uruchomiono regenerację świata z właścicielem heavy gpt-sbs-r2. Testy raportu sprawdzają odrzucanie niezgodnych kohort, liczenie zmiany błędu, nieprzenoszenie recenzji na inne piksele, brak cichego pomijania arkuszy i bezpieczne osadzenie danych w HTML. Wykonanie pojedynczego pliku testowego nastąpi po zwolnieniu naszego slotu przez generator, aby nie współdzielić jednej dzierżawy między zadaniami.

## Kontrola niezależna raportu
Recenzent wskazał trzy blokery: ukrycie D51 przez brak pliku, awans starej diagnostyki i różne rozdzielczości trendu. Poprawiono: domyślnie ładowana jest repozytoryjna recenzja D51, jawnie brakująca ścieżka zgłasza błąd; diagnostyka wymaga identycznej epoki i nie może awansować C; trend porównuje rozdzielczości źródłowe, analityczne i gradientu. Dodano regresje. Arkusz pokazuje końcowy status kwalifikacji próbki. Generator nadal oczekuje na wolny heavy, bez uruchamiania równoległych ciężkich zadań naszej gałęzi.

## Próbki i widok diagnostyczny
Obejrzano trzy pary Low-clear (281855, 397016, 149248). Zapisano małe maski czystego nieba i asfaltu, związane z SHA zdjęcia oraz renderu r1. Uwaga w danych wyraźnie ogranicza interpretację przez różny kierunek słońca i przybliżoną pozę. Nie kwalifikowano innych tierów ani nowych renderów. Skrypt SBS może teraz dodatkowo komponować C do osobnego katalogu diagnostycznego, nigdy do domyślnej kohorty A/B. Obie kompozycje są wykonywane sekwencyjnie w jednym slocie heavy.

## Kontrola przeglądarkowa podglądu
Wygenerowano lekki raport z istniejących metryk r1 (bez obliczeń obrazów i bez nowego renderu). Obejrzano zrzuty 1280×960 oraz 390×844 w izolowanej przeglądarce. Działa wybór stanu i przełącznik diagnostyki C, wynik D51 i zakres starej recenzji są widoczne; brak nowych metryk v2 jest jawny. Jedyny wpis konsoli: brak favicon, bez błędu skryptu. Przeglądarkę zamknięto. Podgląd nie jest finalnym raportem r2 ani nowym dowodem świata.

## Domknięcie identyfikacji pary
Drugi przegląd potwierdził zamknięcie trzech blockerów, wskazując dodatkowo potrzebę sprawdzania SHA zdjęcia przy przenoszeniu recenzji oraz obecności wymiaru gradientu. Poprawiono oba przypadki i dodano regresje. Kontrola składni trzech modułów przechodzi. Przygotowano trzy małe nakładki masek do wizualnej kontroli.

## Kontrola masek
Obejrzano wszystkie trzy nakładki próbek: fiolet oznacza wolne niebo, zielony asfalt. Próbki są małe, bez pojazdów i oznakowania; w drugim renderze fragment asfaltu zawiera cień, co pozostaje ograniczeniem fotometrii, zapisanym w adnotacji. Nie są pomiarem albedo. Logi podglądu przeglądarkowego przeniesiono do artefaktów rundy. Nie pozostawiono aktywnego serwera HTTP ani przeglądarki.

## ADR r2
Uzupełniono ADR 0111 o zmienione kryterium D51, wynik FAIL, ograniczenia metryk, warunki trendu i kontrolę integralności raportu. Zapis jest jawnie roboczy, przed końcową generacją i testami r2.

## Samoczynne migawki dowodów
Skrypt SBS po ukończeniu żądanych stanów sprawdza wspólny commit i zgodność SHA kamer, referencji, świata oraz materiałów ze wszystkimi capture. Dopiero wtedy kopiuje dokładne bajty wejść i tworzy inputs.zip. Migawka nie może zatwierdzić mieszanej lub zmienionej epoki. Dołączane są także autorskie poprawki, intrinsics i rejestry adnotacji. Następny krok: kontrola parsera PowerShell i próba w serii r2.

## Integralność migawki
Parser PowerShell potwierdził składnię wrappera. Dodano ponowne sprawdzanie SHA skopiowanych bajtów oraz odrzucanie nieoczekiwanych starych plików w inputs. Zapis do ponownie użytego katalogu nie może po cichu zostawić usuniętej adnotacji z poprzedniego przebiegu. Próba całościowa pozostaje przed nami.

## Powiązanie adnotacji z kompozycją
Migawka powstaje teraz w nowym katalogu tymczasowym. Weryfikowane są skopiowane bajty oraz SHA fotometrii i punktów względem metryk wszystkich żądanych stanów, również diagnostycznych. Dopiero po tych kontrolach powstaje ZIP i publikowane są inputs. Poprzedni katalog jest zachowywany w inputs-history, a każda ścieżka przeniesienia jest sprawdzana jako leżąca wewnątrz własnego OutputRoot. Parser PowerShell przechodzi.

## Próba migawki bez obciążenia generatorów
Lekka kontrola PowerShell na małych sztucznych plikach przechodzi: pierwszy zapis, usunięcie opcjonalnej adnotacji bez pozostawienia starej kopii, zgodny skład ZIP, odrzucenie zmienionej adnotacji i zmienionej kamery oraz zachowanie poprzedniej poprawnej migawki po błędzie. Nie uruchamiano Unity ani testów GIS poza slotem. Właściwy generator wciąż czeka na heavy.

## Dalsza kalibracja — odrzucona słaba przesłanka
Ponownie obejrzano kadr 182011943700132. Zdjęcie nie potwierdza jazdy na pomoście, dlatego różnica około 5 m względem pobliskiej kamery mostowej nie uzasadnia korekty wysokości. Zachowano C i zapisano potrzebę rozdzielenia XY, kursu i epoki danych. Nie wykonano automatycznej korekty na podstawie samej liczby.

## Przygotowanie zgodnego punktu odniesienia trendu
Przygotowano recompose-history.ps1 do ponownego obliczenia metryk v2 dla renderów r1. Pobiera oryginalne bajty wejść z inputs.zip i używa jawnego trybu historical, nie modyfikując r1. Kompozycje A/B i C będą sekwencyjne w jednym slocie heavy, zapis do history/sbs-r1. Przygotowanie skryptu nie jest potwierdzeniem wykonania; uruchomienie dopiero po zakończeniu generatora naszej gałęzi.

## Generator rozpoczął pracę
Około północy po oczekiwaniu uzyskano heavy gpt-sbs-r2 (3/3). Log potwierdza rozpoczęcie pass 1 i przetworzenie węzłów pomostów. Proces nadal trwa; nie uruchamiamy jednocześnie innego ciężkiego zadania tej gałęzi. Wynik generatora nie jest jeszcze zatwierdzony.

## Sekwencja po generatorze
Przygotowano proces oczekujący na zakończenie własnego procesu World (PID 68496). Przypina uchwyt, sprawdza jego końcowy kod, a dopiero po sukcesie uruchomi kolejno trzy pojedyncze pliki testowe, fidelity i ponowne metryki historyczne. Każda ciężka faza ma osobne Acquire/Release i nie nakłada się z generatorem. Nie uruchamia Unity ani pełnego GIS; te kroki wymagają dalszej kontroli.

## Audyt końcowy R2 — przygotowanie
Przygotowano osobny audyt r2, bez nadpisywania wejść zapisanych przez serię. Sprawdzi wszystkie 168 surowych renderów, 100 A/B, pełną diagnostykę, migawkę ZIP, SHA adnotacji i 64 GLB. Eksportuje 168 liczników z oddzielnymi draws geometrii i instancji oraz porównaniem do r1. Ocenę D51 r1 odróżnia od nieocenionych nowych klatek. Kontrola składni przechodzi; właściwy audyt dopiero po renderach, przez heavy.

## Kontrola powiązania metryk z renderem
Audyt r2 dodatkowo wymaga dokładnej zgodności capture w metrykach i katalogu raw, identycznego SHA zdjęcia i renderu dla każdej pary oraz poprawnego tieru/światła. Kontroluje także obecność i poprawność wszystkich 168 diagnostycznych PNG. Te warunki zapobiegają uznaniu starej kompozycji przy nowym renderze.

## Świat po regeneracji i przygotowanie importu
Generacja zakończona kodem 0 po 457 s, bez fallback=True. Wszystkie 64 SHA GLB w nowym manifeście są identyczne z r1. Przygotowano import przez osobny slot Unity gpt-sbs. Wrapper sprawdza, czy import nie uruchomi automatycznie build_world/build_all poza heavy: w razie brakujących lub nieaktualnych materiałów przerwie przed Unity. Fidelity zapisuje tylko QA, nie zmienia GLB, dlatego import może działać niezależnie od kolejki testów heavy. Nowe capture dopiero po obu etapach i zamrożeniu HEAD.

## Import zakończony
IMPORT_RESULT: OK, 64 chunki, oba tiery Low+High. Preflight PBR: 0 brakujących, 0 nieaktualnych; 13 zestawów CC0, 65 plików, 0 problemów. Slot Unity zwolniony. Raport importu podaje geometrię 117,0 MB Low i 259,1 MB High (bez twierdzenia o pełnej pamięci procesu lub telefonu). Przygotowano osobny EditMode przez Acquire/Release gpt-sbs, z zachowaniem świeżego XML w artefaktach r2.

## EditMode i rozdzielenie pul
EditMode: 261/261, 0 porażek i pominięć; świeży XML zachowany, slot Unity zwolniony. Dodano RenderOnly, rozłączne z ComposeOnly. Pozwala wykonać same capture Unity, gdy sekwencja testów i fidelity używa lub oczekuje na heavy. Nie uruchamia kompozycji ani publikacji migawki; te nastąpią osobnym ComposeOnly po zakończeniu wszystkich ciężkich zadań gałęzi. Cała seria raw wymaga niezmiennego HEAD, kamer, świata i materiałów. Parser PowerShell przechodzi. Następny krok: zamrożony pełny render 42 kamer × 4 stany.

## Pełne capture R2 zakończone
Seria RenderOnly zakończona kodem 0. Wszystkie 168 renderów ma capture OK, wspólny HEAD b9b5574e2dd093af3b36b82ff2a84f55643141e3, 42 kamery w każdym stanie. Z metadanych capture: identyczne SHA PNG względem r1: 31 Low-overcast, 38 Low-clear, 36 High-overcast, 38 High-clear, łącznie 143/168. To nie jest dowód poprawy pozostałych 25 klatek. Pełny audyt ponownie sprawdzi rzeczywiste bajty.
Wyeksportowano lekkim parserem tekstu wszystkie 168 liczników (bez obliczeń obrazów). W obu stanach Low delta draws geometrii = 0, instancji = 0, estymacji tris = 0. Nie jest to pomiar GPU ani telefonu. Kompozycje A/B, diagnostyka, raport i pełny GIS pozostają przed nami; test raportu nadal czeka na heavy.

## Sekwencja po walidacji
Przygotowano proces oczekujący na cały własny post-world (PID 105616). Dopiero po jego sukcesie wykona ComposeOnly wszystkich stanów wraz z C i zweryfikowaną migawką, następnie audyt przez heavy oraz lokalny raport latest z historią r1/r2. Każda ciężka faza pozostaje sekwencyjna; nie korzystamy reentrantnie z tej samej dzierżawy. Sekwencja kończy się przed ręcznym przeglądem, pełnym GIS i kopiowaniem do main. Trzy ręcznie sprawdzone kadry fotometrii Low-clear mają w r2 dokładnie te same SHA co r1, więc kwalifikacja dotyczy tych samych pikseli.

## Pierwszy test raportu — wykryty błąd HTML
Pierwsze uruchomienie test_sbs_report: 24 passed, 1 failed. Test z nieufnym autorem zawierającym zamknięcie script wykrył rzeczywisty błąd: literał Unicode był interpretowany przez Pythona jako znak < zamiast sześciu znaków ucieczki JSON. Poprawiono na jawny surowy literał i dodatkowo sprawdzono AST (sześć znaków, pierwszy backslash). Nie osłabiono testu. Stary log zachowano osobno. Dalsza sekwencja zatrzymała się poprawnie; nie wykonano jeszcze kompozycji ani audytu.
Zapisano potwierdzenie ukończonego świata (kod 0, SHA logu i manifestu), aby ponowna walidacja nie wymagała powtarzania generatora. Wszystkie surowe capture pozostają zachowane na HEAD b9b5574e; poprawka raportu nie zmienia renderów, kamer ani świata.

## Poprawiony raport i zgodność SBS — wynik
Ponowne test_sbs_report: 25/25 po poprawce surowego literału JSON; regresja z nieufnym autorem przechodzi bez zmiany testu. Test_sbs_gate3: 40/40. Logi zachowano. Test fotometrii jest kolejnym pojedynczym plikiem i oczekuje na heavy; fidelity oraz kompozycje nadal nie zostały zaliczone. Bramka świata pozostaje według recenzji r1 FAIL, bez nowej automatycznej oceny.

## Powiązanie D51 z nową serią
Manifest review-pair-manifest.json obejmuje wszystkie 25 B w Low-overcast. Dokładnie 19 par ma te same SHA zdjęcia i renderu co recenzja D51 r1. Sześć zmienionych renderów: 320215796381417, 2279538078845158, 837235577143499, 275528677534382, 150280503737744, 1801374876712141. Raport nie przeniesie na nie oceny starych pikseli. Zbiorczy wynik 12/11/2 jest nadal wyraźnie wynikiem ostatniej recenzji r1, a nie nowym pomiarem r2.

## Własny przegląd sześciu nowych obrazów
Obejrzano sześć natywnych renderów Low-overcast R2 obok fotografii w arkuszach r1. Zapisano VISUAL-REVIEW-CHANGED.md. Nadal widoczne główne braki: U-3, bliska kratownicowa bramownica, pierzeja handlowa i proporcje/przezroczystość ekranu. W dwóch rozpoznawalnych kadrach zachowany główny układ drogi. Nie zmieniono formalnego rejestru ocen, klas pozy ani nie podano nowego automatycznego wyniku 12/11/2. Następne wymagane materiały: końcowe kompozycje, przegląd niezależny, pełny GIS.

## Niezależny przegląd nowych kadrów
Krytyk obejrzał sześć zmienionych par Low-overcast, pozostałe 19 przyjął jako te same piksele według manifestu. Nie znalazł podstaw do podważenia ogólnego D51 FAIL. Ważne doprecyzowanie: w 180137 są częściowo przezroczyste zielonkawe panele, więc aktualnego problemu nie należy opisywać jako całkowitego braku ekranu. Pozostają różnice wysokości, ciągłości, osadzenia i otoczenia. W 150280 obecne są hale i blok, ale brak charakterystycznej pierzei. Zapisano REVIEW-INDEPENDENT-CHANGED.md bez nadpisywania historycznej recenzji r1 i bez zmiany klas.

## Potwierdzenie rzeczywistej kolejki heavy
O 00:42–00:43 sprawdzono procesy systemowe bez ujawniania pełnych command line. Trzy sloty odpowiadały trzem aktywnym zadaniom: dwa build_world oraz jeden pytest, rozpoczęte 00:36–00:41. Nie stwierdzono podstaw do traktowania slotów jako porzuconych. Nie zmieniano cudzych blokad ani PHONE_RUN. Własny post-world pozostaje potwierdzonym żywym procesem oczekującym na test fotometrii; dalsza sekwencja czeka na jego kod zakończenia.


## Fotometria i plan topologii
Test_sbs_photometry: 13/13, przez heavy; fidelity rozpoczęte i potwierdzone w logu. Łącznie pojedyncze pliki SBS: 25 + 40 + 13 = 78 testów, bez pełnego GIS w trakcie.
Przygotowano i obejrzano mały wykres pose-topology/putry-camera-topology.png oraz SVG z istniejącego grafu 0,55 MB, bez regeneracji geometrii. Pokazuje osie źródłowe, trasę, pozy 182 (C) i 494 (B) oraz oryginalny GPS. Wektor od pozy 182 do oryginalnego GPS wynosi -2,027 m E i -13,802 m N. To schemat osi, nie dowód położenia na wygenerowanej jezdni ani powód do zmiany wysokości. Nie zmieniono kamer, klasy ani świata. Materiał służy dalszej kalibracji po ukończeniu bieżącego pakietu.


## Fidelity zakończone
Fidelity: kod 0, własny slot heavy zwolniony. Pomiar osi względem OSM: p95 0,04 m; krawędzi względem orto: p95 2,304 m, dane z fidelity_summary.json. To wyniki narzędzia geometrycznego, nie zaliczenie D51 ani pomiar poprawności pozy kamer. Nadal 4 odcinki pasów mają stan unverified, a rozpoznawalność obiektów pozostaje odrębnym problemem. Historyczna kompozycja r1 jest teraz oczekującą fazą aktywnego post-world.

## Pełna kontrola delt liczników
Sprawdzono zbiory wszystkich wartości, nie tylko maksimum: dla 84 Low i 84 High delty static draws, instanced draws, tris i shadow draws wynoszą wyłącznie 0. Low max 812 = 445 + 367 w A454716650857984; High max 1376 = 945 + 431 w A320215796381417. Dopisano pełne zbiory delt i rekordy maksimów do capture-summary.json. To estymacje CPU przed batchingiem, nie rzeczywiste GPU ani pomiar A16.

## Oba warianty GLB
Rozszerzono porównanie o chunk.low: manifesty r1/r2 zgadzają się dla 64 High i 64 Low, czyli 128 plików. Dotychczasowy skrót 64 chunków odnosił się do plików głównych High. Audyt końcowy sprawdzi teraz rzeczywiste bajty obu wariantów, a nie wyłącznie High. Wynik metadanych zapisano w capture-summary.json, jawnie odróżniony od przyszłej kontroli plików. Składnia audytu poprawna; nie wykonywano haszowania dużych siatek poza heavy.

## Jedna dzierżawa dla krótkiej kompozycji partii
ComposeOnly obejmuje teraz cztery sekwencyjne stany jedną dzierżawą heavy. Każdy Python jest wewnątrz Acquire/Release, działa tylko jeden proces obliczeń naszej gałęzi naraz. Release jest w zewnętrznym finally również przy błędzie migawki. Tryb render+compose nadal zwalnia heavy między stanami, a RenderOnly nie zajmuje heavy. To ten sam wzorzec co historyczny recompose-history: krótkie sekwencyjne kompozycje nie wracają wielokrotnie do kolejki, bez zwiększania równoległości. Parser PowerShell potwierdził składnię. Wykonanie całości nastąpi po historycznej kompozycji i zakończeniu post-world.

## Przygotowanie celowanej diagnostyki 182
Źródłowa najbliższa oś drogi naziemnej znajduje się około 5,72 m na wschód od zapisanej pozy, kurs osi około 352,83 stopnia siatki. To dane grafu, nie dowód faktycznego pasa w GLB. Przygotowano 16 hipotez wyłącznie w artefaktach: przesunięcia E, kurs, dwa warianty horyzontu oraz kontrolne przesunięcia N. Każda ma C i diagnostic_only; nie zmieniono produkcyjnych kamer ani referencji. Render będzie osobny, Low-overcast, przez Unity gpt-sbs, bez kompozycji Pythona i bez wpływu na roster 168 głównych klatek r2. Probe 00 zachowuje bazową geometrię kamery.

## Celowana diagnostyka 182 — wynik
Render 16 hipotez zakończony kodem 0, slot Unity zwolniony. Sprawdzono wszystkie 16 SHA PNG, SHA pliku prób i niezmienność produkcyjnego pliku kamer. Obejrzano wszystkie 16 wariantów i natywne zdjęcie. Niezależny krytyk potwierdził: 12 najlepszy do dalszej pracy, ale C pozostaje z powodu niezgodności dwóch bliższych narożników z dalszą jezdnią, nie z powodu braku sygnalizatorów. Wariant 14 pokazuje niezgodny widok pod pomostem. Zapisano REVIEW-INDEPENDENT-182.md. Nie zmieniono źródeł produkcyjnych, rostra 168 klatek, klasy ani D51. Dalsza kalibracja wymaga pewniejszych kotwic; nie zastępuje zamknięcia pakietu metryk r2.

## Analiza kolejnej nierozwiązanej pozy
Odczytano i obejrzano źródło 326 oraz istniejący loader kamer. Zapisano w CALIBRATION-NOTES.md potrzebę rozdzielenia roll, pitch i zniekształcenia obiektywu; loader nie ma pola roll. Nie wdrożono nowej rektyfikacji ani nie zmieniono C#, kamer, FOV lub referencji. Nie należy uznawać samego nachylenia słupów za zmierzoną wartość roll.


## Kompozycje i przegląd Low-clear
Post-world zakończony kodem 0. Historyczne r1 i aktualne r2: każde ma 100 A/B oraz 168 diagnostycznych arkuszy, bez brakujących renderów. Aktualny ComposeOnly wykonał 8 kompozycji w jednej dzierżawie heavy i zwolnił ją; migawka inputs/inputs.zip przeszła rzeczywiste kontrole SHA, także adnotacji. Audyt oczekuje na osobny heavy.
Obejrzano wszystkie 25 natywnych Low-clear; zapisano ledger z SHA zdjęcia, raw i arkusza. Trzy sprawdzone próbki mają True/REVIEWED_SAMPLES; pozostałe False. Nadal braki podpór, bramownic i oznakowania. Zakres przeglądu końcowego: pozostałe 75 A/B oraz HTML; nie trzeba ponownie oglądać 7 stron Low-clear, skoro komplet obejrzano natywnie.

## Ponowna próba źródeł początku trasy
Mapillary API znów dostępne. Oryginalny mały bbox początku: 0 rekordów. Jedno zapytanie obejmujące pierwsze 300 m z buforem 35 m: 20 rekordów, brak dalszej strony. Wszystkie mają rzutowane stacje 317,017–365,438 m, żadnej do 300 m, także bez odrzucania panoram (rekordów panoramicznych 0). Nie pobrano nowych zdjęć i nie zapisano nic do współdzielonego raw. Wynik nie dowodzi braku wszelkich możliwych źródeł, ale nie dostarczył nowego kandydata na ten odcinek. Metadata są oczyszczone z podpisanych URL i danych autoryzacyjnych.

## Audyt i kontrola HTML
Audyt zakończony kodem 0: rzeczywiste 64 High +64 Low, 168 raw, 100 A/B, 168 diagnostycznych arkuszy, migawka ZIP i 168 liczników zgodne. Oba warianty siatek bez zmian względem r1; identyczne wejście kamer. Raport latest zawiera r1/r2 i cztery stany trendu: Low-clear 3 zgodne próbki, wszystkie trzy mediany zmiany błędu 0; pozostałe stany bez porównywalnych próbek.
Przegląd HTML potwierdził poprawne daty Warszawy, D51 r1 FAIL 12/11/2 oraz rozróżnienie starych i nowych pikseli. Dla czytelności zmieniono samą etykietę STALE na opis próbek dla innego obrazu i dodano skrót do trendu. Nie zmieniono metryk, kwalifikacji ani ocen. Dodano pustą ikonę danych, żeby uniknąć zbędnego żądania favicon. Raport lokalny przebudowany; dalsza kontrola przeglądarkowa i 75 A/B przed pełnym GIS.

## Przegląd wszystkich 100 A/B zakończony
Obejrzano 25 natywnych Low-clear oraz wszystkie 21 stron Low-overcast, High-overcast i High-clear, obejmujących pozostałe 75 par. W sumie 100/100. Zakres i SHA źródłowych arkuszy oraz 21 obejrzanych stron zapisano w visual-inspection.json. Siedmiu stron Low-clear nie oglądano ponownie, ponieważ komplet 25 arkuszy obejrzano natywnie.
W obu tierach pozostają te same istotne braki podpór, oznakowania, bramownic i otoczenia; wyższy tier nie naprawia rozpoznawalności. Różnice nieba i odcienia nie stanowią rozstrzygnięcia D51. Przegląd nie awansuje klas ani nie aktualizuje formalnej recenzji r1. Pozostały końcowy test UI, niezależna kontrola narzędzia i pełny GIS.

## UI końcowe i gotowość do GIS
Sprawdzono desktop 1280×960, wąski widok 390×844, skrót do trendu, zmianę stanu, przełącznik C (42 karty), przełączenie r1/r2 i poprawne epoki. Załadowane obrazy bez braków; konsola 0 błędów i ostrzeżeń. Wykryte 22 px przewijania poziomego kodów pominięć naprawiono zawijaniem długich opisów; wynik po poprawce: dokument 390 px przy viewport 390 px, także dla C. Zrzuty topu i trendu obejrzano, logi w ui-final. Przeglądarka i lokalny serwer zamknięte. Zapisano niezależny PASS narzędzia/kompletności, z jawnym brakiem końcowego GIS i zaliczenia świata. Zmiana CSS nie dotyka metryk ani danych obrazów. Następny krok: jednorazowy pełny GIS na końcu rundy przez heavy.


## Roboczy raport końcowy
Przygotowano REPORT-DRAFT.md z potwierdzonymi liczbami, dwiema parami 960 px, ograniczeniami i ścieżkami dowodów. Pełny GIS oraz dostarczenie do main są jawnie oznaczone jako niewykonane. Kod źródłowy pozostaje na e386b929; późniejsze zmiany tego kroku dotyczą dokumentacji.

## Nowe scalenia main podczas końcowej kolejki
Odczytano main 3ebd95d4 i recenzję REVIEW-2026-11-12-s11-0125.md. Main zawiera teraz gate3-signs oraz kolejne rundy light/asphalt/landmarks/truck. Nie włączono ich do zamrożonej r2 w trakcie końcowego GIS. R2 dokumentuje wcześniejszy stan; nie jest dowodem obrazu po 0125. R3 zacznie się od merge aktualnego main i nowych renderów. Recenzja 0125 wskazuje hipotezy cofnięcia 837235/275528, korekty sekwencji 328135/297817, przesunięcia 180137 i kursu 494288; liczby z recenzji pozostają hipotezami do weryfikacji. Ranking r3 musi uwzględniać już poprawioną geometrię portali, zamiast powtarzać historyczny brak obiektu. Pełny GIS r2 nadal czeka w tej samej kolejce heavy, bez dodatkowego zadania naszej gałęzi.

Plan wejścia w r3 zapisano w NEXT-ROUND.md po odczycie sześciu pozycji. Nie zmieniono kamer ani kodu w trakcie końcowej walidacji.

Wstępnie skopiowano statyczne evidence/history/counters do main przez robocopy (trzy kody 1). SHA ZIP, kamer, referencji i CSV zgodne; receipt PRESTAGE_NOT_FINAL_DELIVERY. Nie skopiowano REPORT (brak końcowego GIS). Pełna końcowa dostawa nadal wymagana.

Doprecyzowano REPORT-DRAFT: 42 klatki w każdym stanie i jawna granica względem nowych scaleń main. Ponownie odczytano capture-summary, AUDIT i niezależny przegląd: 168 zerowych delt, trend tylko dla trzech Low-clear, bez nowego zaliczenia D51. Źródła nadal zamrożone.

Kontrola zakresu przed zamknięciem: scope-audit.json zapisuje listę źródeł względem początkowego main oraz pusty diff kodu/danych od zamrożenia GIS e386b929. Zmiany produkcyjne wyłącznie SBS, testy i dokumentacja; osiem pochodnych generatora nadal niestaged.

Korekta oczekiwania: po ponad 30 minutach i zmianach właścicieli slotów potwierdzono własny proces Acquire PID 110744, rodzic 33232, nadal przed startem pytest. Zatrzymano wyłącznie ten waiter, który zakończył wrapper kodem 1; test GIS nie wystartował. Log zachowano jako pytest-gis-wait-poll7.log. Runner artefaktu otrzymał PollSeconds 1 zamiast 7, aby nie pomijać krótkich wolnych okien. Limity 3, cudze sloty i kod zamrożony e386 bez zmian. Nastąpi ponowne oczekiwanie na tę samą końcową walidację, nie drugi równoległy test.

Końcowy GIS uzyskał slot gpt-sbs-r2 (3/3) i wystartował; o 02:30 log osiągnął 12% bez zgłoszonego błędu. To pierwszy start pełnego pytest tej rundy; poprzedni log dokumentuje wyłącznie oczekiwanie. Źródła kodu/danych bez zmian od e386b929. Nowy uchwyt procesu wykonania 48940.

Podczas GIS obejrzano sześć gotowych par ADR 0125 oraz dwa natywne źródła 328135/297817, bez dodatkowego Pythona. PRE-R3-VISUAL.md i ledger zachowują wynik: 297817 ma portal daleko w tle, kolejność źródłowa zgadza się ze zbliżaniem do portalu; brak dowodu zamiany ID. Wspólne cofnięcie pozostaje hipotezą do renderów r3. Źródeł produkcyjnych nie zmieniono.

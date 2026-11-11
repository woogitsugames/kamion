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

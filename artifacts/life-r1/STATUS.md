# Status sesji life — runda 1
Przeczytano wymagane instrukcje, recenzję 0089 i feedback. Utworzono worktree z main 5f2aa277 na gpt-life-r1.
Poprzednia gałąź gpt-car-paint zawiera już ukończone techniczne R4, 368 par i raport z ograniczeniem: realizm kurzu PARTIAL. Nie należy ponownie implementować napraw ani kopiować starych plików innych dziedzin.
Następny krok: pwsh -File artifacts/life-r1/prepare-worktree.ps1; następnie selektywnie przenieść wyłącznie zmiany life z gpt-car-paint, zachowując aktualne main.
Sesja rozpoczęta 11.11.2026; planowany czas pracy 24 godziny. Bez scalania do main, pushowania i telefonów. Właściciel slotu Unity: gpt-life.

Krok 2: skopiowano wymagane zasoby i utworzono junctiony; git lfs checkout zakończony bez błędu. Selektywnie zastosowano patch R4 dotyczący aut, bez starych generatów i zmian budynków/dróg. Zależności eksportera/importera i generatora car_grime są wyłącznie opt-in dla aut/tablic; pliki wspólne scalane trójstronnie.
Następny krok: uv run --project tools/worldgen python -m pytest tests/gis/test_car_deposition.py tests/gis/test_car_map_fields.py tests/gis/test_car_plate_payload.py tests/gis/test_cars_r11.py -q

Krok 3: przygotowano kontrakt 92 kamer z poprzedniego R4 i skrypt czterech warunków. Baseline korzysta z kopii scen main i shadera main; po pomiarze shader wraca do commita kandydata. Każde osobne uruchomienie Unity pobiera i zwalnia slot gpt-life. Nie przypisujemy starych pomiarów do nowej gałęzi.
Następny krok: pwsh artifacts/life-r1/capture.ps1 -Stage before

Krok 4: testy ukierunkowane zakończone: 50 passed w 38,28 s. Baseline Unity uruchomiony ze slotem gpt-life; pozostałe zmiany świata nie są jeszcze importowane.
Następny krok: uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py, a następnie generator build_world i weryfikacja braku fallback=True.

Krok 5: obejrzano lokalny arkusz zdjęć Mapillary; nie jest kalibrowaną referencją albedo. Przygotowano skrypt porównujący wszystkie kamery, osobno draws świata i instancji, oraz pary przed/po do 960 px. Pierwszy import Unity trwa, nie wykonano jeszcze oceny nowych PNG.
Następny krok po renderze AFTER: uv run --project tools/worldgen python artifacts/life-r1/compare.py

Krok 6: analiza następnej rundy wykonana bez zmiany produkcji. Zapisano trójkąty i grupy materiałowe wszystkich statycznych ciągników/naczep w yard-prototype-baseline.json. Potencjalny problem: koła naczep LOD1 są długimi pryzmami, a warunek dodający chlapacze LOD0 jest nieosiągalny wewnątrz if lod > 0. Weryfikacja wizualna i poprawki dopiero w rundzie 2.
Następny krok: zakończyć bieżący baseline 92 kamer × 4, regenerację materiałów i build_world przed importem kandydata.

Krok 7: pierwszy baseline Low/clear zakończony: VISUALQA_RESULT OK, 92 PNG. Obejrzano nowe r10_wheel_02 i r10b_black_05 w 960 px: kadry pokazują właściwe auta, stary pas brudu i powtarzalne tablice. Czarny lakier w słońcu nadal wygląda szaro, więc nie zamykamy tego problemu jako naprawionego. Trwają pozostałe trzy warunki.
Następny krok: zakończyć capture.ps1 -Stage before, potem import kandydata dopiero po build_world bez fallback=True.

Krok 8: zapisano osobne wejścia importu i EditMode z obowiązkowym slotem gpt-life i cofnięciem efektów ubocznych Unity. Materiały są regenerowane kanonicznie; import kandydata jeszcze nie został uruchomiony.
Następny krok po zakończeniu baseline i generatora: pwsh artifacts/life-r1/unity-phase.ps1 -Phase Import

Krok 9: audyt wejść generatora wykrył brak opcjonalnego zdjęcia asfaltu w nowym worktree. Skopiowano wyłącznie istniejący plik źródłowy Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg z main przed dojściem generatora do warstwy detalu. Zapobiega to pominięciu istniejącego materiału innych dziedzin; nie zmieniono jego kodu ani ustawień.
Następny krok: sprawdzić log materiałów pod kątem SKIP/fallback i diff specyfikacji; do commita brać wyłącznie konieczne różnice car_grime_clean.

Krok 10: baseline Low/overcast ukończony, również 92 PNG. Obejrzano r10b_black_05: czerń jest czytelna w pochmurnym świetle, brud to nadal jednolity stary pas. Nagłówek stats potwierdza Low renderScale=0.75 i msaa=2; wartości draws/instancji są szacunkami CPU, nie pomiarem GPU telefonu. High/clear w toku.
Następny krok: zakończyć dwa zestawy High, dopiero potem przywrócić shader kandydata i zaimportować zregenerowany świat.

Krok 11: ADR 0089 uzupełniono po polsku o r1 sesji life, selektywne przeniesienie R4 i jawne ograniczenia. Historyczne wyniki nie są przypisywane do obecnej gałęzi; raport końcowy powstanie po nowych testach i obejrzeniu porównań.
Następny krok: monitorować baseline i generatory, bez kolejnego uruchamiania tych samych zadań.

Krok 12: pełny build_all zakończony poprawnie w 1036 s. Diff materials_spec.json to wyłącznie 106 nowych linii car_grime_clean, istniejące zestawy bez zmian. Baseline obejmuje obecnie Low/clear, Low/overcast i High/clear po 92 PNG; High/overcast czeka w capture.ps1 na slot. Shader WorldPBR w katalogu roboczym pozostaje tymczasowo wersją main do końca baseline; finally skryptu przywróci wersję kandydata z indeksu/HEAD. Nie commitować tego tymczasowego cofnięcia.
Procesy w toku: capture.ps1 (sesja exec 94597), materiały -> build_world (sesja exec 24311). Generator materiałów jest zakończony, build_world pracuje; nie uruchamiać duplikatu. Po obu procesach sprawdzić world-build.log i brak fallback=True, commitować tylko poprawne generaty. Następnie pwsh artifacts/life-r1/unity-phase.ps1 -Phase Import; pwsh artifacts/life-r1/capture.ps1 -Stage after; uv run --project tools/worldgen python artifacts/life-r1/compare.py; pełne GIS i EditMode oraz oględziny wszystkich par. REPORT.md dopiero na koniec rundy, potem robocopy do main i od razu gpt-life-r2 + git merge main. Zakaz scalania/push do main nadal obowiązuje.

Krok 13: zweryfikowano żywy proces właściwego generatora: python PID 28064 (potomek 103344 w worktree gpt-life), CPU 275,75 s. Pusty początkowo world-build.log wynika z buforowania stdout, nie jest dowodem zatrzymania. Nie uruchomiono duplikatu. Przygotowano pełne GIS z ochroną kanonicznego manifestu i zapisaniem kodu zakończenia oraz SHA przed/po.
Następny krok po zakończeniu sesji generatora 24311: pwsh artifacts/life-r1/run-gis.ps1

Krok 14: przygotowano dowód zgodności wszystkich 192 produktów raw z manifestem, liczby gotowych zasobów Fab oraz hashów istniejących modeli/prefabów/materiałów zestawu gracza. Skrypt nie modyfikuje produktów i nie korzysta z historycznego bootstrapu innej gałęzi. Generator PID 28064 nadal postępuje: CPU wzrosło z 275,75 do 316,89 s.
Następny krok po generatorze: uv run --project tools/worldgen python artifacts/life-r1/source-proof.py candidate

Krok 15: sprawdzono 192 produkty raw (0 rozbieżności) i 15 gotowych zasobów Fab. Pełne GIS działa. Sprawdzono kodowanie własnych plików tekstowych: wszystkie były poprawnym UTF-8, więc nie wymagały konwersji (encoding-repair.json = []); logi pozostawiono w oryginalnym UTF-16. Następny krok: zakończyć baseline High/overcast i sprawdzić zgodność generatów ze skopiowanym main.

Krok 16: wszystkie 368 renderów skopiowanego main ukończone; capture 94597 zakończony kodem 0 i przywrócił shader kandydata. Porównanie kanonicznych raw z manifestem bazy 5f2aa277 wykazało 159 różnic/192, więc te rendery są wyłącznie dowodem starego cache i nie będą bazą kosztu r1. Pełne GIS zgłosiło F przy około 66% i nadal trwa; nie zmieniać źródeł do jego końca. Przygotowano source-mode.ps1, który odwracalnie przełącza jedynie 23 własne pliki produkcji/testów, bez zmiany indeksu, gałęzi lub innych dziedzin. capture.ps1 nie miesza już shadera z przesuwającego się main; źródła są ustawiane jawnie. Następny krok: po GIS zachować jego wynik i traceback, przenieść before do main-cache-before, wykonać source-mode.ps1 -Mode Main, kanoniczny build_world, import i nowy baseline; potem -Mode Candidate i powtórna regeneracja/import/AFTER.

Krok 17: przygotowano import kanonicznie zbudowanych wejść bez ponownego generowania wszystkich zestawów wyłącznie z powodu mtime zmienionego przez git restore. PreparedImport przed Unity weryfikuje 192 hashe raw, 15 zasobów Fab oraz obecność i hashe wszystkich map PBR Medium, potem wywołuje standardowy RegionImporter.ImportBatch ze slotem gpt-life. Każda próba ma osobny dowód i log. Parser PowerShell potwierdził poprawną składnię capture/source-mode/unity-phase; nie uruchomiono jeszcze przełączania źródeł ani nowego importu. Następny krok: zakończyć aktualne GIS i odczytać traceback przed kanonicznym baseline.

Krok 18: oryginalne 368 PNG zachowano bez zmian w main-cache-before (przeniesienie wewnątrz sprawdzonego katalogu własnych artifacts). CACHE-BASELINE.md wyjaśnia ograniczenia i pochodzenie wstępnych miniatur. Kanoniczny before jest jeszcze do wykonania. Zakończono wyłącznie zbędny własny odczyt git show PID 500/110752 po potwierdzeniu dokładnego polecenia i drzewa rodziców; pełny manifest odczytano niezależnie przez git cat-file. Generatorów, GIS ani Unity nie restartowano. Następny krok: odczytać końcowy wynik aktywnego GIS (sesja 59801, właściwy Python PID 48024).

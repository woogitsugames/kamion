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

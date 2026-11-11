# Status edge r2
Start: 11 listopada 2026, 23:43 CET. Pierwotny termin sesji: 12 listopada 2026, około 21:31 CET.
R1 zakończona i skopiowana do main: 1003 pliki, ponad 2,15 GB; ostatni commit 5b221381. Kod geometrii r1 pozostaje w tej gałęzi.
Gałąź gpt-edge-r2 utworzono od r1 i scalono main (merge 54bb70ca). Historyczną, czystą i scaloną gpt-edge-r2 @027e7589 zachowano jako gpt-edge-0085-r2-archive, bez usuwania jej worktree ani danych.
Cel: rzeczywiste wysokości dalekiej zabudowy z przypiętego LoD1; parser produkcyjny nadal zwraca 0, prototyp znalazł 36971 rekordów i 5390 dopasowań. Zgodnie z nową D51 priorytetem jest rozpoznawalna sylwetka, położenie i proporcje, a nie drobna korekta materiałów.
Po merge zestaw sbs ma 25 B i 17 C; w porównaniach fotograficznych r2 odrzucamy C. Budżet raportujemy dla wszystkich kamer, także diagnostycznych. Pozy B pozostają przybliżone.
Ciężkie operacje wyłącznie przez centralny -Pool heavy, właściciel bieżąca gałąź; pełny GIS tylko na końcu. Unity osobno pod gpt-edge, release w finally. Bez main merge, push i telefonów.
Następny krok: dostosować własne skrypty do katalogu r2, zamrozić kamery/klasy i wykonać bazowe rendery przed zmianą parsera.
Krok 2: skrypty r2 mają własny STATUS, centralne pule, limitów nie podnoszą i nie usuwają cudzych starych slotów. Kamery: 42 aktualne sbs + własne ujęcie DK8 + kontrolne sceny; w zdjęciach akceptowane tylko A/B, C wykluczone, SHA zdjęć kontrolowane. Capture zapisuje i sprawdza SHA wejść po pobraniu slotu. Merge main nie zmienił geometrii świata, więc bazą jest lokalny wygenerowany i sprawdzony świat z r1. Następny krok: pwsh artifacts/edge-r2/validate.ps1 -Phase Before.
2026-11-11T23:51:14.3738539+01:00 Zapisano rendery before/Low-clear wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-11T23:51:49.8820657+01:00 Zapisano rendery before/Low-overcast wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-11T23:52:30.1063581+01:00 Zapisano rendery before/High-clear wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-11T23:53:08.6229993+01:00 Zapisano rendery before/High-overcast wszystkich kamer; ocena PNG i budżetu nadal w toku.
Krok 3: parser LoD1 odczytuje strumieniowo wszystkie GML/XML, identyfikator i wysokość tylko w granicach jednego budynku; konfliktujące duplikaty odrzuca. Cache /11 wymusi odświeżenie. Cache, QA i manifest zapisują pochodzenie wysokości i audyt parsera; szacunki mają WORKING_VALUE, tagi OSM pozostają UNVERIFIED. Dodano testy regresji rzeczywistego układu archiwum, brakujących wartości, duplikatów i wysokości niepoprawnych. Zmiana kodu jeszcze bez regeneracji.
Krok 4: baza ukończona: po 91 kamer w Low/High × clear/overcast, łącznie 364 PNG; wejścia nie zmieniły SHA podczas zrzutów. Test pojedynczego pliku pod heavy: 11/11 zaliczonych (0,85 s). Zachowano cache GIS i QA sprzed zmiany. Następny krok: wymagany build_world pod heavy, sekwencyjnie przed kolejnymi testami.
Krok 5: obejrzano bazowe edge-east i edge-south w 960 px: rzadka sylwetka miasta nadal widoczna, bez przypisywania winy materiałom. Generator czeka na wolny heavy; cudzych procesów ani slotów nie ruszano.
Przygotowano audyt różnic wysokości, tożsamości obrysów oraz lasów, kominów i masztów. Test QA sprawdzi zgodność pochodzenia wysokości w cache/QA/manifeście.
Następny krok po build_world: pwsh artifacts/edge-r2/heavy.ps1 -Task AuditHeights, potem pojedynczy test_far_field.py.
Krok 6: zapisano decyzję r2 w ADR 0121 i kopię obu źródłowych GLB przed regeneracją do odtworzenia bazy. Obejrzano także parę B 381800493259507: zdjęcie pod słońce, więc bez oceny fotometrycznej; to nie dowód zgodności całego horyzontu.
Następny krok: poczekać na zakończenie bieżącego build_world, bez uruchamiania równoległej generacji lub pełnego GIS.
Krok 7: kontrola pierwszych 64 KiB rzeczywistego GML ujawniła uom="meter". Początkowa lista jednostek m/#m byłaby zbyt wąska; poprawiono ją o równoważne meter/metre, a fixture odtwarza teraz rzeczywisty zapis. Dodano cztery przypadki jednostek. Wynik 11/11 dotyczył poprzedniego stanu.
Bieżący build_world już działa pod heavy. Jeśli załadował moduł przed poprawką, po jego zakończeniu wymuszona zostanie ponowna ekstrakcja i FarField, przed jakimkolwiek renderem po zmianie.
Następny krok: sprawdzić lod1_height_audit.usable_ids, potem ponowić test_lod1 i audyt wysokości pod heavy.
Krok 8: przed przebudową zapisano SHA aktualnych scen i siatek edge z Unity (snapshot po bazowych renderach, bez udawania pomiaru w trakcie ich wykonywania). Kolejne zrzuty sprawdzą również SHA sceny, apron i siatki far-field przed/po każdym renderze.
Następny krok nadal zależy od końca build_world; testów Python z tym samym właścicielem slotu nie uruchamiamy równolegle.
Krok 9: build_world działa i przeszedł etapy dróg/budynków/placów (ostatnio 340,8 s czasu generatora). Bez drugiego zadania Python tej sesji. Skrypt heavy dla kolejnych uruchomień zapisuje osobny kwit z pulą, właścicielem, czasem oczekiwania, czasem pracy i kodem zakończenia.
Następny krok: po końcu budowy test_lod1 → AuditHeights → test_far_field, sekwencyjnie i każdy przez heavy.
Krok 10: build_world zakończył się komunikatem done po 459,9 s i zwolnił heavy. Far-field High 118524 trójkątów, Low 24500 (baza 24508). Log nie zawiera fallback=True. Weryfikacja rzeczywistych rekordów i budżetu kamer nadal przed nami.
Następny krok: pwsh artifacts/edge-r2/heavy.ps1 -Task GisFile -TestFile tests/gis/test_far_field_lod1.py.
Krok 11: QA po budowie potwierdza 31 GML, 36971 poprawnych wysokości i 0 duplikatów/konfliktów; 5390 budynków z LoD1, 97 szacunków BDOT, 2921 szacunków OSM i 39 tagów OSM UNVERIFIED, łącznie 8447. Są 16 kominów, 302 maszty/słupy i 107 linii.
Test parsera czeka na heavy. Dodano polecenie ScopeGenerated do tej samej puli: przed renderami odtworzymy uboczne metadane dróg/props i zachowamy wyłącznie pola far-field w world_manifest, zgodnie z własnością dziedzin.
Następny krok po teście: AuditHeights → ScopeGenerated → test_far_field.py → validate.ps1 -Phase After.
Krok 12: test parsera po poprawce rzeczywistej jednostki meter: 15/15 w 0,60 s, heavy zwolniony. Następna komenda: pwsh artifacts/edge-r2/heavy.ps1 -Task AuditHeights.
Krok 13: zapisano własny QA i manifest źródeł nowej siatki; uboczne metadane pozostałych dziedzin pozostają niezatwierdzone do odtworzenia przez ScopeGenerated. Audyt wysokości oczekuje na heavy, nie równoleglimy go z innym Pythonem.
Następny krok: po potwierdzeniu kodu 0 audytu wykonać ScopeGenerated i sprawdzić diff world_manifest.
Krok 14: po około 14 minutach kolejki zatrzymano wyłącznie własny proces oczekujący na AuditHeights (PID 58904; własny slot nie istniał), bez zatrzymywania obliczeń. Log kolejki zachowano. Kolejne heavy sprawdzają dostępność co 2 s zamiast 7 s; MaxSlots nadal 3, StaleHours zapobiega usuwaniu cudzych slotów.
Następny krok: ponowny AuditHeights tą samą pulą; bez omijania blokady zasobów.
Uzupełnienie kroku 14: zatrzymanie wrappera pozostawiło jego własny proces Acquire (PID 71344, rodzic 58904), który trzymał log. Sprawdzono tożsamość i zatrzymano także ten proces oczekujący; nie działał żaden Python audytu i nie było własnego slotu. Pierwsze wznowienie nie wystartowało przez otwarty log. Log przeniesiono dopiero po zamknięciu obu procesów.
Następny krok: ponowne uruchomienie AuditHeights, kod wyniku odczytać z nowego kwitu zadania.
Krok 15: podczas kolejki przygotowano 10 bazowych par G3-B z atrybucją i klasą B w baseline-photo-review; obejrzano arkusze 1–3 (9 par), do 960 px. Ujęcia pod słońce nie nadają się do werdyktu fotometrycznego. W dziennym 150280503737744 kominy i miejska sylwetka wymagają szczególnej oceny po regeneracji; samo poprawienie źródła wysokości nie zamyka jakości zdjęcie–render.
Następny krok: wynik audytu, ograniczenie metadanych i nowe rendery; dotychczasowe pary są wyłącznie bazą, nie dowodem poprawy r2.
Krok 16: audyt zakończony kodem 0: 5384 zmienione wysokości (2253 bloki, 1564 biurowe, 1065 hale, 502 domy); wszystkie 8447 obrysów oraz lasy, kominy, maszty i linie bez zmian. ScopeGenerated zweryfikował oba SHA GLB i odtworzył metadane innych dziedzin; world_manifest zachowuje wyłącznie aktualizację far-field.
Następny krok w tym samym heavy: pojedynczy tests/gis/test_far_field.py, potem pula zwolniona i Unity After.
Krok 17: pojedynczy test_far_field.py zaliczony; wynik w test-far-field.log. Następna komenda: pwsh artifacts/edge-r2/validate.ps1 -Phase After.
2026-11-12T00:27:42.2969366+01:00 Przebudowano wyłącznie WorldEdge w scenach Low i High; wynik wizualny do sprawdzenia.
2026-11-12T00:28:14.3942004+01:00 Zapisano rendery after/Low-clear wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-12T00:28:46.3714482+01:00 Zapisano rendery after/Low-overcast wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-12T00:29:21.4129652+01:00 Zapisano rendery after/High-clear wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-12T00:29:56.4945532+01:00 Zapisano rendery after/High-overcast wszystkich kamer; ocena PNG i budżetu nadal w toku.

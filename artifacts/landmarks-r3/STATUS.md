# Status rundy 3 — kominy EC Białystok
Krok 1: gałąź gpt-landmarks-r3 od r2 310e9fab, merge main 14ccbaf1. Konflikty wygenerowanych streetscape_qa/world_manifest przyjęte z main, do regeneracji. materials.py: zachowano obie niezależne sekcje addytywne (podpomost i asfalt), bez zmiany ich parametrów.
Zakres: wyłącznie własne landmarki; bez zmian life_props.py, props.py, roads, overrides.yaml i plików Claude. Wysokości 120 m zachowane; odrzucona hipoteza pełnych pasów od ziemi nie będzie wdrażana. Najpierw baseline na nowej bazie i kalibracja zdjęcia oraz własna ścieżka assetów.
Ciężkie zadania tylko pod heavy gpt-landmarks-r3; Unity pod gpt-landmarks, zgodnie z poleceniem właściciela. Bez obchodzenia watchdoga i priorytetu lidera. Termin całej sesji: 2026-11-12 21:31:16 CET.

Krok 2: przygotowano kolejny baseline pełnego świata po merge. Skrypty korzystają z aktualnych limitów main; brak równoległego generatora tej sesji. Kamery szczegółowe kominów będą dodane po analizie pozy, przed importem.

Krok 3: robocze dopasowanie fotograficzne obu osi z wysokościami 120 m i średnicą pojedynczego komina ENEA. Usunięto z pomiaru szerokości okno przecinające galerię. Wynik i reszty w photo-pose-fit.json, poza nadal WORKING_VALUE (GPS ma przesunięcie, brak modelu dystorsji, ręczne piksele głowic). Dodano trzy kamery EC; pełny kadr referencji zachowa całą wysokość zdjęcia. Źródła runtime kominów jeszcze bez zmian, trwa oczekiwanie baseline na heavy.

Krok 3a: dodanie kamer wykonano skryptem prepare_cameras.py po błędzie cytowania polecenia inline; dopiero teraz plik zawiera 13 dodatkowych kadrów, w tym 3 EC. Poprzedni zapis kroku 3 wyprzedził wykonanie tej części.

Krok 4: przygotowano niewłączony szkic własnego generatora i konfiguracji w artifacts (candidate_ec_chimneys.*). Nie zmienia jeszcze świata baseline. Trzy materiały Low, cztery High jak dotąd; galerie i odrębne trzy wyloty bez shaderów. Wysokości i pozycje zachowane, średnice pojedynczego z ENEA, wieloprzewodowego i granice pasów oznaczone WORKING_VALUE. Przed wdrożeniem wymagane baseline oraz pojedynczy plik testów fallbacku i geometrii.
Krok 5: wznowienie po restarcie Windows, LastBootUpTime 2026-11-12 09:01:27 CET. Uchwyt procesu 1113 nie istnieje, brak procesów build_world/build_all/pytest/fidelity/Unity oraz brak baseline-world.log; poprzednia kolejka nie wykonała generatora. Trzy cudze sloty heavy z 03:27/03:30/03:38 pozostają nietknięte. Ponownie uruchamiam własną kolejkę acquire, bez równoległego zadania i bez automatycznego kasowania starych slotów. Następny krok: pwsh artifacts/landmarks-r3/heavy-step.ps1 -Step World -Log artifacts/landmarks-r3/baseline-world.log.

Krok 6: w artifacts zapisano szkic pojedynczego pliku testów: wymiary i osie, materiały LOD, brak wpływu na BDOT/keepout, brakujący/stary/zmieniony asset i deterministyczność bajtów. Jeszcze nie wykonywano pytest; wdrożenie po obejrzeniu baseline. Generator baseline uzyskał własny slot o 09:04:46.

Krok 6a: skrypt kontynuacji baseline oczekuje wyłącznie na potwierdzony proces 49724, nie uruchamia ponownego generatora. QA zachowa wszystkie znane kadry r2 i trzy nowe EC; pełny faktyczny spis czterech warunków będzie zapisany i porównany, bez założenia liczby 48. Narzędzia budżetu i arkuszy przygotowane do tego spisu.

Krok 6b: przygotowano pary EC 960 px z pełną wysokością zdjęcia CC BY 3.0; tylko centralne przycięcie renderu 2340→1920 i jawne powiększenie detali 2x. Bez osobnego skalowania kominów, przekształcania pozy i korekty barwy. Ograniczenia źródła i atrybucja zapiszą się przy każdej parze. NASTĘPNY KROK po baseline: uv run --project tools/worldgen python artifacts/landmarks-r3/photo_pair.py before.

Krok 6c: przygotowano odczyt rzeczywistych macierzy WorldInstances.SyncOrigin w Unity, do uruchomienia po baseline. Ma odróżnić pochylenie modelu od perspektywy. Tymczasowy skrypt Editor nie zapisuje scen i jest usuwany po uruchomieniu pod slotem. Jeszcze nie wykonany.

Krok 7: świeży baseline świata po merge main ukończony bez fallback=True. Zachowano manifest, QA i własną bibliotekę proceduralną do porównań kominów. NASTĘPNY KROK: import przygotowanych danych i pełne cztery zestawy QA, pod Unity.

Krok 6d: dopisano test integracji rejestracji landmarków z hero apply: dla zweryfikowanego assetu i dla fallbacku musi pozostać dokładnie jedna instancja danego źródła. Testy nadal są szkicem, nie raportuję ich jako PASS. Poprawiono też zwalnianie slotu sondy: kontrola istniejącego pliku następuje przed acquire.

Krok 6e: ADR 0116 rozszerzony o r3 z pełnymi ograniczeniami źródeł, pozy i roboczych wymiarów; bez deklaracji wyniku nieuruchomionego wariantu. Przygotowano baseline_sheets.py do przeglądu całego faktycznego spisu kamer.

Krok 8: import i baseline QA zakończone; faktyczny spis kamer w baseline-result.json. Następnie obejrzenie pełnych zestawów i pary zdjęcia EC przed wdrożeniem.
Krok 9: obejrzano wszystkie 16 arkuszy baseline (244 obrazy). Sylwetki EC mają za wąski trzon wieloprzewodowy, gęste pasy na zbyt krótkim odcinku i nierozróżnione głowice. Remiza/podpomost są kontrolami zachowania poprzednich rund. Poza zdjęcia EC pozwala porównać obie osie i zwieńczenia, ale szerszy kontekst dróg/budynków ma odstępstwa poza zakresem tej sesji.
Krok 10: runtime-probe-before.json potwierdza dokładnie dwie macierze kominów z up=(0,1,0), axisTiltDeg=0. Submeshes High/Low 4/3; LOD650/20000. Sonda zakończona, plik tymczasowy usunięty i slot zwolniony. Następnie włączono ec_chimneys.py + własną konfigurację i pojedynczy plik testów; hero_building.plan dodaje dwa własne assety, landmarks.build pomija stary stożek tylko przy zweryfikowanym spec/config/builder/GLB. Brak zmian life_props/props/overrides/dróg. NASTĘPNY KROK: testy jednostkowe jednego pliku, generator i kontrola wygenerowanej pojedynczej instancji pod heavy.

Krok 10a: uruchamiam kolejno jednostki bez testu wyjścia, generator, pełny pojedynczy plik EC, import i 244 obrazy after-silhouette. Każda ciężka część pod heavy, Unity osobno; pełny GIS dopiero na końcu rundy. NASTĘPNY KROK: pwsh artifacts/landmarks-r3/candidate-silhouette.ps1.

Krok 10b: pomiar pikselowy bazowych pasów zapisany w chimney-pixels-before.json. To czerwone/nie-czerwone piksele, nie reflektancja ani dowód białej farby. Wykluczono dolny fragment prawego komina zasłonięty dachem w renderze i podniesiono próg chromy tak, by brudna kremowa farba ze zdjęcia nie była klasyfikowana jako czerwona. Okna pozostaną stałe dla kandydata. Kolejka heavy nadal czeka; brak nowego generatora poza nią.

Krok 10c: samokontrola zapisuje pomiar osi runtime, wszystkie 244 obejrzane obrazy i ograniczenia pozy/fotografii. Doprecyzowano budżet do LOD0/LOD1 4/3 (Low z bliska także LOD0). Próg pomiaru pasów uzupełniono o wykluczenie ochry/brązu przed obejrzeniem kandydata; aktualny baseline mismatch 49,0%/55,5%. Opcjonalne pobranie oryginału zostało odrzucone przez automatyczną kontrolę przed wykonaniem; brak pliku oryginalnego i brak twierdzenia o jego weryfikacji.

Krok 10d: zachowano i zweryfikowano SHA wszystkich 64 plików instancji baseline, przed uruchomieniem kandydata. audit_ec.py sprawdzi 128 meshy chunków, roads_qa, materiały, wszystkie instancje poza dwoma EC oraz faktyczne wierzchołki i macierze GLB. Różnice e/n/z/yaw kominów będą jawnie raportowane, bez utożsamiania innego próbkowania gruntu z identyczną pozycją. NASTĘPNY KROK po generatorze: uv run --project tools/worldgen python artifacts/landmarks-r3/audit_ec.py.

Krok 10e: przygotowano NIEURUCHOMIONE skrypty końca rundy: pełny GIS raz, physics/gate3, EditMode oraz strumieniowe porównanie 192 plików runtime i własnych źródeł/assetów przed i po testach. Nie rozpoczynam pełnego GIS w trakcie iteracji. audit_ec.py także hashuje pliki w blokach 1 MB.

Krok 11: jednostkowe testy pojedynczego pliku test_ec_chimneys.py zakończyły się powodzeniem (wynik artifacts/landmarks-r3/silhouette-world.log.units); celowo wyłączony test wyjścia generatora. Pod tym samym heavy rozpoczyna się kolejno generator, bez równoległego Pythona tej sesji.

Krok 11a: recenzja s12 zaakceptowała/scaliła r2, lecz zgłosiła P1 błędnych szarych faz i zbrązowienia pigmentu oraz P2 ciemnego równoległoboku. Plan korekty w P1-FEEDBACK-PLAN.md, do wykonania po bieżącym izolowanym przebiegu EC. Próba anulowania kolejki nie wykonała Stop-Process (waiter już nie istniał); slot był już przydzielony. Jednostki EC 15 PASS, 1 deselected, 1.92 s; działa generator. Kandydat równoległoboku w kodzie to paint_blobs, wymaga potwierdzenia PNG.

Krok 11b: przygotowano odczyt semantycznych hashy prymitywów GLB. Po pierwszym wariancie EC snapshot jest dopuszczony tylko przy identycznych 128 SHA względem baseline. Po korekcie filarów porównanie wyłączy tylko trzy własne materiały w node bridge, zachowując dokładne bajty dróg, barier, budynków, terenu i kolizji; nie będzie fałszywej deklaracji identyczności całych chunków po zmianie farby.

Krok 12: generator EC i cały pojedynczy plik test_ec_chimneys.py zakończone; brak fallback=True. Następny krok: import i pełny zestaw czterech warunków after-silhouette, bez zmiany kamer baseline.

Krok 13: pierwszy wariant EC: wszystkie 128 GLB chunków i 125468 instancji poza EC identyczne; XY/yaw bez zmian, Z +3/+9 mm przez inne próbkowanie NMT; obie osie runtime pionowe. Low draws +0, ale dwie nowe kamery głowic przekraczają tris o 3,57%/6,90%. Obejrzane pary głowic ujawniają też znikanie płaskich galerii Low od dołu. Wariant NIE jest końcowy.

Krok 14: zastosowano P1/P2 z recenzji: fazy w tej samej farbie, stary musztardowy pigment, wyłączona abstrakcyjna plama. EC: obrzeża galerii 0,25 m na obu LOD, białe malowanie i trzy materiały na obu LOD; 24-segmentowy trzon High, prostsze rurki i usunięte zbędne ścianki den wylotów. Dodano testy widocznej fascii i domyślnego malowania filarów. Uściślono otwarte źródła: starsze zdjęcie Hiuppo potwierdza jasny dół; EMKA tylko tekst H120 m, bez użycia zamkniętej fotografii jako materiału D43. NASTĘPNY KROK: pojedyncze pliki EC i podpomostu pod heavy, potem generator i 244 obrazy after-corrected.

Krok 14a: przygotowano kolejną kolejkę z dwoma osobnymi wywołaniami pojedynczych plików przed i po generatorze. Test wygenerowanego podpomostu wymaga już zgodności aktualnych flag faz/plam. Nie nadpisuje się obrazów ani logów pierwszego wariantu; nowe wyjście after-corrected. NASTĘPNY KROK: pwsh artifacts/landmarks-r3/candidate-corrected.ps1.

Krok 14b: obejrzano wszystkie 32 arkusze pierwszego wariantu (244 pary, 123 PNG identyczne). Zmiana czytelna na kominach, bez widocznej regresji remizy/kabiny/podpomostu; powierzchnie kominów nadal zbyt gładkie i szare wobec fotografii, pozostają PARTIAL. Audyt korekty dopuszcza tylko pigment pier_yellow i trzy grupy materiałów w bridge, z obowiązkowym aktualnym dowodem zachowania reszty prymitywów; oś trzonu jest mierzona na pełnych pierścieniach, z wyłączeniem białych galerii.

Krok 14c: przed uzyskaniem slotu (potwierdzony brak własnego heavy) porównano budżet starych prototypów: LOD0 700, LOD1 204 tris każdy. Dalsze uproszczenie drobnych barierek i trzonu (20 stron, galerie 8 boków i 4 słupki) ma utrzymać oba nowe LOD0 poniżej 700 bez usuwania wylotów ani obrzeży galerii. Ostateczne liczby i wygląd po generatorze, bez deklaracji PASS.

Krok 14d: test geometrii EC wymaga LOD0 ≤700 tris, czyli rzeczywistego budżetu poprzedniego komina. Kontrola pionowej fascii sprawdza obecność zamkniętego obrzeża z normalnymi na zewnątrz, bez wymuszania poprzedniej liczby segmentów.

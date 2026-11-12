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

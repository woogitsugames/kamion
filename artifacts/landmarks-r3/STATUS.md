# Status rundy 3 — kominy EC Białystok
Krok 1: gałąź gpt-landmarks-r3 od r2 310e9fab, merge main 14ccbaf1. Konflikty wygenerowanych streetscape_qa/world_manifest przyjęte z main, do regeneracji. materials.py: zachowano obie niezależne sekcje addytywne (podpomost i asfalt), bez zmiany ich parametrów.
Zakres: wyłącznie własne landmarki; bez zmian life_props.py, props.py, roads, overrides.yaml i plików Claude. Wysokości 120 m zachowane; odrzucona hipoteza pełnych pasów od ziemi nie będzie wdrażana. Najpierw baseline na nowej bazie i kalibracja zdjęcia oraz własna ścieżka assetów.
Ciężkie zadania tylko pod heavy gpt-landmarks-r3; Unity pod gpt-landmarks, zgodnie z poleceniem właściciela. Bez obchodzenia watchdoga i priorytetu lidera. Termin całej sesji: 2026-11-12 21:31:16 CET.

Krok 2: przygotowano kolejny baseline pełnego świata po merge. Skrypty korzystają z aktualnych limitów main; brak równoległego generatora tej sesji. Kamery szczegółowe kominów będą dodane po analizie pozy, przed importem.

Krok 3: robocze dopasowanie fotograficzne obu osi z wysokościami 120 m i średnicą pojedynczego komina ENEA. Usunięto z pomiaru szerokości okno przecinające galerię. Wynik i reszty w photo-pose-fit.json, poza nadal WORKING_VALUE (GPS ma przesunięcie, brak modelu dystorsji, ręczne piksele głowic). Dodano trzy kamery EC; pełny kadr referencji zachowa całą wysokość zdjęcia. Źródła runtime kominów jeszcze bez zmian, trwa oczekiwanie baseline na heavy.

Krok 3a: dodanie kamer wykonano skryptem prepare_cameras.py po błędzie cytowania polecenia inline; dopiero teraz plik zawiera 13 dodatkowych kadrów, w tym 3 EC. Poprzedni zapis kroku 3 wyprzedził wykonanie tej części.

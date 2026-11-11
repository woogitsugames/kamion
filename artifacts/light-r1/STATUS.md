# Status rundy 1 — światło
Przeczytano instrukcję 24 h, HANDOVER s10, CLAUDE, reguły agentów, standard grafiki, budżety, decyzje D48–D50, recenzje 0088/0098 i J/K oraz feedback.
Gałąź gpt-light-r1 utworzona z main 4c9905b1. Start 2026-11-11; koniec okna pracy po 24 godzinach od startu.
Następny krok: przygotować kopie danych i junctiony według protokołu, git lfs checkout, potem baseline High/Low i ablacja RCAS.
Geometria komina poza własnością light: przekazanie w REPORT, bez zmian instancji.
Wyniki wizualne i wydajności na tej gałęzi: UNVERIFIED. Telefonów nie używam.

Krok 2: skopiowano wymagane dane, Megascans i _Generated; junctiony istnieją, git lfs checkout zakończony. Kopiowane są też PNG materiałów i cache Library. Następny krok: baseline przez scripts/visual-qa.ps1 z blokadą gpt-light.

Krok 3: kopia Library zakończona (kod robocopy 1 = skopiowane pliki). Ruszyła ablacja RCAS, każdy render bierze i zwalnia slot gpt-light. Generator baseline działa równolegle. Stwierdzono w Sky.shader: chmury mnożone przez overcast, więc clear=0 wyłącza całą strukturę. Następny krok: pomiary PNG i poprawka nieba clear w istniejącym przebiegu.

Krok 4: zapisano ADR 0108 z kryteriami r1, granicami własności i oknem pracy do 12.11.2026 21:30 Europe/Warsaw. Następny krok: zakończyć ablacjas RCAS, obejrzeć i zmierzyć PNG.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 5: przygotowano compare_rcas.py, który liczy RMS z oryginalnych PNG i zapisuje arkusze ≤960 px. Następny krok: uv run --project tools/worldgen python artifacts/light-r1/compare_rcas.py po zakończeniu ablacji.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0.25. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0.5. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Punkt kontrolny 21:42: baseline clear obejrzany; RMS nieba 1,5 px = 0,5503, asfaltu = 3,4372. RCAS 0,25: niebo 0,6076, asfalt 4,0386. Runda NIEZAKOŃCZONA. W toku: rcas-ablation.ps1 (pozostałe warianty) i build-world-baseline.log. Następny krok: po zakończeniu procesów uv run --project tools/worldgen python artifacts/light-r1/compare_rcas.py; obejrzeć arkusze. Nie zmieniać źródeł w trakcie ablacji. Kolejno: import baseline z osobnym Acquire/Release, baseline Low i sbs, poprawka chmur clear i wybór RCAS, cienie/ekspozycja, testy i REPORT. Cel 24 h aktywny, koniec 12.11.2026 21:30 Warszawa.

Krok 6: budget_compare.py porównał wszystkie 5 kamer RCAS 0 i 0,5: osobne draws instancji, zmiana liczby draws i trójkątów = 0. To estymaty CPU SceneStats, nie pomiar GPU. Proces generatora 98884 potwierdzony żywy (CPU 298 s o 21:42). Następny krok: dokończyć renderowanie i obejrzeć pełną ablacjas.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0.75. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 7: dodano clearCloudCover w LightingPreset (clear 0,42 WORKING_VALUE; inne presety 0), global atmosfery i warstwę chmur w istniejącym przebiegu Sky.shader. Clear ablacjas zakończone przed zmianą. Overcast zachowuje oryginalny wzór i coverage 0. Źródła zmienione, preset asset jeszcze nie zsynchronizowany; wygląd nowego nieba UNVERIFIED. Następny krok: zakończyć overcast RCAS, potem import/synchronizacja presetów i rendery nieba clear.

Krok 8: dokončene clear RCAS: 0,75 daje asfalt HF 5,6999 i niebo HF 0,6418 (r=1,5 px). Wybrano 0,75 jako kandydat odzyskujący detal, próg nieba ≤0,6 pozostaje niespełniony o 0,0418, bez deklaracji PASS. Applier rozwiązuje historyczne High/FSR/zero do 0,75, zachowuje jawne Rq i pozostałe profile. Dodano test granic Low/High/Linear/jawne zero. Bez nowego pola QualityProfile ani migracji. Następny krok: dokończyć overcast ablacjas i zweryfikować kandydata w pełnym renderze.

Krok 9: skybox zachowuje kontrakt cap-off przy przechwytywaniu odbić: chmury używają radiancji modelu zamiast limitu wyświetlania. Następny krok: import i oględziny nieba oraz odbić po zakończeniu bieżącej serii.
Render ablacji zakończony: artifacts/light-r1/rcas/High-overcast-0. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 10: preset LP_Clear zapisany z pokryciem 0,42 zgodnie z fabryką. Dodano LightQaBatch: wiele porównań w jednym procesie/slotcie Unity, z istniejącym rendererem QA i przywróceniem profilu/pipeline w pamięci. Nie zmienia asmdef. Następny krok: kompilacja i mały smoke batch po zakończeniu bieżącej serii; potem pełna matryca światła.

Krok 11: dodano rq_clearcover do izolowania pokrycia chmur bez edycji assetów i ruszania pozostałych dziedzin. Parse bez argumentu przywraca preset. Następny krok: smoke batch pokrycia 0 / 0,42 i ditheringu w jednym procesie Unity po zakończeniu ablacji.

Krok 12: build_world baseline zakończony (log: [world 1089.0s] done); uruchomiono wymagane python -m pytest tests/gis -q. Przygotowano cloud-smoke.json (5 zadań / 15 PNG) i run-light-batch.ps1 z Acquire/Release i przywracaniem efektów ubocznych. Następny krok: po zakończeniu rcas-ablation.ps1 uruchomić pwsh artifacts/light-r1/run-light-batch.ps1 -Jobs artifacts/light-r1/cloud-smoke.json; po GIS wykonać import aktualnych wygenerowanych danych.
Render ablacji zakończony: artifacts/light-r1/rcas/High-overcast-0.25. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 13: przygotowano validation-followup.ps1. Czeka na potwierdzony własny proces RCAS 93600, sprawdza komplet 40 PNG, potem kolejno import, 15 PNG smoke i pełne EditMode. Każde nowe Unity ma osobne Acquire/Release gpt-light. GIS w toku, na 58% wystąpiła jedna porażka — przyczyna do odczytu po końcu testów, bez zgadywania.

Krok 14: przygotowano kontrolowane próby ramienia bieli 1,2/1,4/1,6/1,8 oraz filtrów cienia Medium/High, podziałów kaskad i 4096 px. LightQaBatch przywraca presety między zadaniami; filtr cieni ustawiany tylko dla bieżącego zadania, bez zmiany domyślnej polityki Low. Wyniki tych prób jeszcze UNVERIFIED. Następny krok: po smoke obejrzeć niebo, następnie uruchomić shadow-ablation.json i white-shoulder-ablation.json.

## Stan bieżący po zmianie limitów — 11 listopada, około 22:28
Gałąź gpt-light-r1; własny worktree gpt-light. Okno pracy do 12 listopada 21:30, Europe/Warsaw.
Ciężki Python wyłącznie przez run-heavy.ps1 i aktualny helper slotów z main: pula heavy, właściciel gpt-light-r1, max 3. Pełny GIS tylko na końcu rundy (-Task GisFinal -RoundEnd).
40/40 PNG ablacji RCAS gotowych. Poprawiony kontroler PID 60592 rozpoczął import w slotach heavy (gpt-light-r1) i Unity (gpt-light); przebudowa PBR build_all jest objęta heavy. Nie uruchamiać równolegle drugiego własnego heavy z tym samym właścicielem.
GIS pierwszy pełny: 492 PASS / 1 FAIL (stary fidelity) / 1 XFAIL. Po odświeżeniu pełny przebieg zatrzymano na pilne polecenie limitu; nie jest zaliczony. Pojedynczy test_road_fidelity.py po odświeżeniu: 9 PASS / 1 XFAIL w puli heavy, slot zwolniony.
RCAS .75 jest kandydatem, nie zamknięciem P0: asfalt HF 5,6999, niebo HF 0,6418 > 0,6. Niezależna recenzja w review-rcas/REVIEW.md. Nowe chmury i próby bieli/cieni wymagają renderów i oględzin.
Następny krok: Get-Content artifacts/light-r1/rcas-ablation.log -Tail 6; Get-Content artifacts/light-r1/validation-followup-heavy.log -Tail 6. Nie uruchamiać drugiej kopii tych procesów. Po smoke obejrzeć PNG, potem próby cieni/bieli i pełne SBS; EditMode w kolejce, pełny GIS na końcu.

## Dziennik kroków
# Status rundy 1 — światło
Przeczytano instrukcję 24 h, HANDOVER s10, CLAUDE, reguły agentów, standard grafiki, budżety, decyzje D48–D50, recenzje 0088/0098 i J/K oraz feedback.
Gałąź gpt-light-r1 utworzona z main 4c9905b1. Start 2026-11-11; koniec okna pracy po 24 godzinach od startu.
Następny krok: przygotować kopie danych i junctiony według protokołu, git lfs checkout, potem baseline High/Low i ablacja RCAS.
Geometria komina poza własnością light: przekazanie w REPORT, bez zmian instancji.
Wyniki wizualne i wydajności na tej gałęzi: UNVERIFIED. Telefonów nie używam.

Krok 2: skopiowano wymagane dane, Megascans i _Generated; junctiony istnieją, git lfs checkout zakończony. Kopiowane są też PNG materiałów i cache Library. Następny krok: baseline przez scripts/visual-qa.ps1 z blokadą gpt-light.

Krok 3: kopia Library zakończona (kod robocopy 1 = skopiowane pliki). Ruszyła ablacja RCAS, każdy render bierze i zwalnia slot gpt-light. Generator baseline działa równolegle. Stwierdzono w Sky.shader: chmury mnożone przez overcast, więc clear=0 wyłącza całą strukturę. Następny krok: pomiary PNG i poprawka nieba clear w istniejącym przebiegu.

Krok 4: zapisano ADR 0108 z kryteriami r1, granicami własności i oknem pracy do 12.11.2026 21:30 Europe/Warsaw. Następny krok: zakończyć ablację RCAS, obejrzeć i zmierzyć PNG.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 5: przygotowano compare_rcas.py, który liczy RMS z oryginalnych PNG i zapisuje arkusze ≤960 px. Następny krok: uv run --project tools/worldgen python artifacts/light-r1/compare_rcas.py po zakończeniu ablacji.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0.25. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0.5. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Punkt kontrolny 21:42: baseline clear obejrzany; RMS nieba 1,5 px = 0,5503, asfaltu = 3,4372. RCAS 0,25: niebo 0,6076, asfalt 4,0386. Runda NIEZAKOŃCZONA. W toku: rcas-ablation.ps1 (pozostałe warianty) i build-world-baseline.log. Następny krok: po zakończeniu procesów uv run --project tools/worldgen python artifacts/light-r1/compare_rcas.py; obejrzeć arkusze. Nie zmieniać źródeł w trakcie ablacji. Kolejno: import baseline z osobnym Acquire/Release, baseline Low i sbs, poprawka chmur clear i wybór RCAS, cienie/ekspozycja, testy i REPORT. Cel 24 h aktywny, koniec 12.11.2026 21:30 Warszawa.

Krok 6: budget_compare.py porównał wszystkie 5 kamer RCAS 0 i 0,5: osobne draws instancji, zmiana liczby draws i trójkątów = 0. To estymaty CPU SceneStats, nie pomiar GPU. Proces generatora 98884 potwierdzony żywy (CPU 298 s o 21:42). Następny krok: dokończyć renderowanie i obejrzeć pełną ablację.
Render ablacji zakończony: artifacts/light-r1/rcas/High-clear-0.75. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 7: dodano clearCloudCover w LightingPreset (clear 0,42 WORKING_VALUE; inne presety 0), global atmosfery i warstwę chmur w istniejącym przebiegu Sky.shader. Clear ablację zakończone przed zmianą. Overcast zachowuje oryginalny wzór i coverage 0. Źródła zmienione, preset asset jeszcze nie zsynchronizowany; wygląd nowego nieba UNVERIFIED. Następny krok: zakończyć overcast RCAS, potem import/synchronizacja presetów i rendery nieba clear.

Krok 8: zakończone clear RCAS: 0,75 daje asfalt HF 5,6999 i niebo HF 0,6418 (r=1,5 px). Wybrano 0,75 jako kandydat odzyskujący detal, próg nieba ≤0,6 pozostaje niespełniony o 0,0418, bez deklaracji PASS. Applier rozwiązuje historyczne High/FSR/zero do 0,75, zachowuje jawne Rq i pozostałe profile. Dodano test granic Low/High/Linear/jawne zero. Bez nowego pola QualityProfile ani migracji. Następny krok: dokończyć overcast ablację i zweryfikować kandydata w pełnym renderze.

Krok 9: skybox zachowuje kontrakt cap-off przy przechwytywaniu odbić: chmury używają radiancji modelu zamiast limitu wyświetlania. Następny krok: import i oględziny nieba oraz odbić po zakończeniu bieżącej serii.
Render ablacji zakończony: artifacts/light-r1/rcas/High-overcast-0. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 10: preset LP_Clear zapisany z pokryciem 0,42 zgodnie z fabryką. Dodano LightQaBatch: wiele porównań w jednym procesie/slotcie Unity, z istniejącym rendererem QA i przywróceniem profilu/pipeline w pamięci. Nie zmienia asmdef. Następny krok: kompilacja i mały smoke batch po zakończeniu bieżącej serii; potem pełna matryca światła.

Krok 11: dodano rq_clearcover do izolowania pokrycia chmur bez edycji assetów i ruszania pozostałych dziedzin. Parse bez argumentu przywraca preset. Następny krok: smoke batch pokrycia 0 / 0,42 i ditheringu w jednym procesie Unity po zakończeniu ablacji.

Krok 12: build_world baseline zakończony (log: [world 1089.0s] done); uruchomiono wymagane python -m pytest tests/gis -q. Przygotowano cloud-smoke.json (5 zadań / 15 PNG) i run-light-batch.ps1 z Acquire/Release i przywracaniem efektów ubocznych. Następny krok: po zakończeniu rcas-ablation.ps1 uruchomić pwsh artifacts/light-r1/run-light-batch.ps1 -Jobs artifacts/light-r1/cloud-smoke.json; po GIS wykonać import aktualnych wygenerowanych danych.
Render ablacji zakończony: artifacts/light-r1/rcas/High-overcast-0.25. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 13: przygotowano validation-followup.ps1. Czeka na potwierdzony własny proces RCAS 93600, sprawdza komplet 40 PNG, potem kolejno import, 15 PNG smoke i pełne EditMode. Każde nowe Unity ma osobne Acquire/Release gpt-light. GIS w toku, na 58% wystąpiła jedna porażka — przyczyna do odczytu po końcu testów, bez zgadywania.

Krok 14: przygotowano kontrolowane próby ramienia bieli 1,2/1,4/1,6/1,8 oraz filtrów cienia Medium/High, podziałów kaskad i 4096 px. LightQaBatch przywraca presety między zadaniami; filtr cieni ustawiany tylko dla bieżącego zadania, bez zmiany domyślnej polityki Low. Wyniki tych prób jeszcze UNVERIFIED. Następny krok: po smoke obejrzeć niebo, następnie uruchomić shadow-ablation.json i white-shoulder-ablation.json.

Krok 15: przygotowano pełne porównanie SBS przed/po na 40 pozach × Low/High × clear/overcast. Źródłowych plików SBS nie edytowano. Osobna lista wyklucza sześć odrzuconych póz i zdjęcia zachodu z fotometrii; całych klatek z maską auta nie używam do kalibracji. Skopiowano lokalne sprostowane referencje. Następny krok: po smoke uruchomić sbs-before.json i sbs-after.json z -Gate3 Data/Regions/bialystok-industrial-c/sbs_cameras.json.

Krok 16: GIS pierwszy przebieg: 492 PASS / 1 FAIL / 1 XFAIL, powodem FAIL jest stary fidelity_qa.json. Odświeżanie przez fidelity/run.py i ponowny pełny GIS uruchomione, bez zmian kodu dróg i ratchetów. Sprawdzenie logu build_world: fallback=True = False. Następny krok: odczytać wynik odświeżonego GIS i kontynuować kolejkę Unity.
Render ablacji zakończony: artifacts/light-r1/rcas/High-overcast-0.5. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 17: niezależny visual-critic obejrzał 20 PNG clear i 10 zestawów natywnych wycinków; recenzja review-rcas/REVIEW.md. Najlepszy kandydat 0,75, lecz żaden wariant nie spełnia obu progów; podkreśla też ziarno tynku i kontury. Autor dodatkowo obejrzał wszystkie 5 kontaktówek i główne wycinki. Runda pozostaje bez werdyktu PASS. Następny krok: smoke z ditheringiem on/off i nowym niebem; nie zwiększać globalnej ostrości ponad 0,75.

PILNA ZMIANA PROTOKOŁU 22:20: pełny GIS PID 102644 i jego właściwy proces potomny 60756 zatrzymano; przerwany przebieg nie jest wynikiem PASS. Zatrzymano oczekujący stary kontroler importu PID 107476 (bez potomków). Od teraz ciężki Python wyłącznie w puli heavy, właściciel gpt-light-r1, max 3; pełny GIS tylko na końcu rundy. Kontroler importu obejmuje heavy również niejawne build_world/build_all. Helper slotów używany z aktualnego main bez edycji cudzych plików. Dodano run-heavy.ps1 z blokadą pełnego GIS bez -RoundEnd. Następny krok: uruchomić poprawiony kontroler, oczekujący na istniejącą serię RCAS.

Krok 18 — potwierdzenie limitów po pilnej zmianie: parser PowerShell zaakceptował run-heavy.ps1, validation-followup.ps1 i run-light-batch.ps1. O 22:23 stwierdzono ZERO własnych procesów Pythona; zatrzymane PID 60756/102644/107476 nie istnieją. Poprawiony kontroler czeka na istniejący proces RCAS 93600; nie uruchomiono kolejnego ciężkiego Pythona. Pełny GIS z odświeżonym fidelity został przerwany przy końcowych testach, bez deklaracji PASS; wróci na końcu rundy w heavy. Następny krok: kontynuować oczekiwanie na slot Unity i realizować poprawioną kolejkę.
Zadanie heavy TestFile zakończone kodem 0. Log: C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\heavy-TestFile-20261111-222614.log. Następny krok: odczytać wynik i wykonać tylko uzasadnioną następną operację.


Krok 19: dodano preflight ustawień przed nowymi uruchomieniami Unity; przy wcześniejszych niezacommitowanych zmianach start zostaje odrzucony bez ich cofania. Pełny restore po Unity pozostaje zgodny z jawnym protokołem użytkownika. Następny krok: zakończyć istniejącą kolejkę i zweryfikować smoke.

Krok 20: niezależny przegląd harnessu wykrył niejednoznaczne wielkości liter tieru i akceptowanie niepełnej sceny. Poprawiono kanonizację nazwy tieru, odrzucanie nieznanych profili, wymaganą liczbę kamer i sprawdzenie EnvironmentLighting/presetu/aktywnego tieru przed OK. Dotychczasowe 35 PNG RCAS wykonał stary renderer, nie ten batch; poprawki dotyczą nadchodzących porównań. Następny krok: smoke potwierdzający zastosowane stany po imporcie.
Render ablacji zakończony: artifacts/light-r1/rcas/High-overcast-0.75. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza.

Krok 21: RCAS zakończony, 40/40 PNG. Porównanie samych tekstowych metadanych (lekki skrypt, bez dużego przetwarzania obrazów) obejmuje wszystkie 5 kamer w clear i overcast: draws, osobne draws instancji i trójkąty bez zmian między RCAS 0 i 0,75. Poprawiony kontroler czeka obecnie na heavy; NIE uruchamiać drugiej własnej operacji heavy z tym samym właścicielem, bo helper traktuje ponowne Acquire jako odświeżenie. Następny krok: import → cloud-smoke → EditMode z istniejącego kontrolera.


Krok 22 (22:34): import uzyskał heavy i Unity, trwa niejawna przebudowa PBR (set asphalt_* w logu). Slot heavy pozostaje zajęty przez ten import. Następny krok: śledzić validation-followup-heavy.log; po zakończeniu importu istniejący kontroler sam uruchomi smoke i EditMode. Nie startować kolejnej kopii.
Import świeżego świata zakończony. Następny krok: cloud-smoke.json w LightQaBatch i testy EditMode.
Batch światła zakończony: artifacts/light-r1/cloud-smoke.json; log C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\cloud-smoke.20261111-224335.log. Następny krok: obejrzeć PNG i policzyć metryki, nie deklarować PASS z samego kodu wyjścia.
EditMode zakończony bez błędów. Następny krok: obejrzeć wszystkie PNG smoke, porównać niebo ze zdjęciami i wybrać dalszą poprawkę.

Krok 23: import zakończony, smoke 5 zadań / 15 PNG wykonany, EditMode 262/262. Uzupełniono brakującą lokalną kopię Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg; importer wcześniej zachował istniejącą specyfikację oraz wszystkie cztery PNG detalu asfaltu (potwierdzono pliki). Nie zmieniano generatora ani materiału asfaltu. Dodano analizę obrazów do run-heavy.ps1, aby także większe analizy PNG respektowały limit. Następny krok: smoke-review.py i oględziny trzech kontaktówek.
Zadanie heavy Analyze zakończone kodem 0. Log: C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\heavy-Analyze-20261111-224605.log. Następny krok: odczytać wynik i wykonać tylko uzasadnioną następną operację.

Krok 24: 20/20 świeżych PNG cieni potwierdzonych. Proces zakończył się -1073741819 PO LIGHT_QA_RESULT: OK, Cleanup mono i abort_threads, bez znacznika/stacka awarii — dokładnie warunek znanego wyjątku ADR 0083, nie D3D12 SaveCache. Dowód w shadow-shutdown-proof.json, oryginalny log zachowany. Wrapper otrzymał te same wąskie wyjątki co scripts/visual-qa.ps1 oraz kontrolę wszystkich świeżych plików. Nie powtarzam 20 renderów; następny krok: analiza obrazów i próba bieli.
Batch światła zakończony: artifacts/light-r1/white-shoulder-ablation.json; log C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\white-shoulder-ablation.20261111-225133.log. Następny krok: obejrzeć PNG i policzyć metryki, nie deklarować PASS z samego kodu wyjścia.

Krok 25: po obejrzeniu 15 PNG odrzucono proceduralne chmury (duże białe płaskie płaty, rozmycie Low). Zweryfikowano oficjalną stronę i CC0 Poly Haven; pobrano Kloofendal 48d Partly Cloudy Pure Sky 4K HDR (20 674 857 B), rozmiar/MD5 zgodne z publicznym API, SHA256 3061c00a16ecae748e84fd6c44c04804f539c118bb66325db858bad87b11bf88. Przygotowano pochodną fotograficzną maskę chmur i luminancji. Następny krok: wykonać build-photo-clouds.py w heavy, obejrzeć podgląd, potem podłączyć do istniejącego przebiegu nieba.
Zadanie heavy Analyze zakończone kodem 1. Log: C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\heavy-Analyze-20261111-230224.log. Następny krok: odczytać wynik i wykonać tylko uzasadnioną następną operację.

Krok 26: poprawiono pojedynczy nadmiarowy nawias w skrypcie podglądu; poprzedni start zakończył się błędem składni i zwolnił heavy, bez przetworzenia HDRI. Następny krok: ponownie wykonać skrypt w heavy.
Zadanie heavy Analyze zakończone kodem 0. Log: C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\heavy-Analyze-20261111-230239.log. Następny krok: odczytać wynik i wykonać tylko uzasadnioną następną operację.

Krok 27: podłączono fotograficzną mapę chmur CC0 w istniejącym skyboxie (1 odczyt zamiast 2–3 odczytów proceduralnych w clear). Kierunek źródłowego słońca zmierzony z HDRI: 47,856°; mapa obracana do słońca modelu. Dodano jawny kontrakt importu linear + ASTC 6×6, metadane i wpis licencyjny. High: końcowy dither domyślnie wyłączony zgodnie z pomiarem smoke; Rq nadal go nadpisuje, inne tiery bez zmiany. Before-SBS jawnie przywraca stary dither. Nowy obraz nieba jeszcze UNVERIFIED. Następny krok: PrepareBatch dla tekstury i cloud-photo.json, obejrzeć PNG.

Krok 28: obejrzano podgląd źródła i wyodrębnionej maski; widoczne osobne cumulusy i samocieniowanie. Pochodna 4096×2048 ma 3 162 892 B PNG. Skrypt prepare-photo-sky.ps1 skonfiguruje tylko własną teksturę i po osobnym Acquire uruchomi 15 porównań fotograficznego nieba. Następny krok: uruchomić i obejrzeć cloud-photo.
Import fotograficznej mapy nieba zakończony: linear, mipmapy, ASTC 6x6, oś źródłowego słońca zweryfikowana. Następny krok: cloud-photo.json i oględziny.
Batch światła zakończony: artifacts/light-r1/cloud-photo.json; log C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r1\cloud-photo.20261111-230639.log. Następny krok: obejrzeć PNG i policzyć metryki, nie deklarować PASS z samego kodu wyjścia.

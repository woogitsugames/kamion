# Przekazanie sesji 7 — landmarks

Praca zakończona wcześniej na polecenie właściciela z powodu kończącego się limitu tygodniowego. Nie kontynuować automatycznie pętli 24 h. Nie uruchamiać nowych generatorów ani testów bez wznowienia zadania. Uruchomiony przed poleceniem końca pełny capture B zostaje naturalnie dokończony; jego wynik zostanie zapisany poniżej.

## Miejsce i zakres

Repo główne: `C:\Users\matma\Documents\Claude\kamion`.
Worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-landmarks`.
Bieżąca gałąź: `gpt-landmarks-r4`. Ostatni checkpoint modelu i audytów: `273682bb`; checkpoint decyzji po podglądzie: `7b58edd3`. Końcowy commit przekazania jest późniejszy; sprawdzić `git log -1` w worktree.
Baza main rundy r4: `b23b4df7`, merge do własnej gałęzi: `e0fa8a6d`. Nie scalano do main i nie pushowano. Po zakończeniu skopiowano tylko własne artifacts do głównego repo, bez commitowania tam.
Zakres wyłącznie remiza, wiadukt pod pomostem i dwa kominy EC. Nie używano telefonu ani adb. Nie usuwać cudzych slotów lub PHONE_RUN. Nie ruszać dróg, overrides.yaml, budynków Claude, globalnej roślinności ani shaderów/profili.

## Zakończone rundy

- r1: `gpt-landmarks-r1`, finalny commit `cb699d74`. Iglaki, szkło, zacieki i flaga remizy. Model High/Low/LOD2 9584/2818/164 tris. Wynik fotograficzny częściowy. Raport i obrazy: `artifacts/landmarks-r1/REPORT.md`.
- r2: `gpt-landmarks-r2`, finalny `310e9fab`, źródła `73170057`. Usunięto niepotwierdzone schody, malowanie/zużycie podpór, netto −906 tris. 232 obrazy; Low draws +0. Raport: `artifacts/landmarks-r2/REPORT.md`.
- r3: `gpt-landmarks-r3`, finalny `c8a5a900`, geometria `b4da1f8e`. Autorskie modele kominów, biały dół, galerie, rytm pasów; poprawki farby podpór po recenzji. 244 obrazy, wszystkie 32 arkusze obejrzane. Low draws siatek i instancji +0; tris −0,3185% do +0,3718%. EditMode 317/317, physics/gate3 48/48. GIS 643 PASS, 1 XFAIL, 1 FAIL: zewnętrzne stale fidelity, źródła dróg identyczne z bazą; dowód w `stale-fidelity-proof.json`. Raport: `artifacts/landmarks-r3/REPORT.md`. Lider później integrował r3; przed wznowieniem sprawdzić świeży main.

## Runda r4 — stan modelu B

Runda nie jest zamknięta jakościowo. Zmiana dotyczy tylko rdzeni trzech iglaków remizy: nieregularne promienie, przesunięcia poziomów i normalne wynikające z powierzchni. Pozycje, wysokości, promienie projektowe, atlas, wszystkie karty alfa, UV i materiały zachowano. Produkcyjne pliki to `tools/blender/world/landmarks/make_fire_station.py`, `art-source/world/landmarks/fire_station_jrg2/dims.json` oraz ich wygenerowane GLB/meta/spec i QA.

World B zakończony po 680,0 s, bez fallback=True. GLB SHA256: `d1835d0ef30229011942e226edf2f0e59962ff61c1c97f537122e41c564dcc71`. Model nadal 9584/2818/164 tris. Audyt rzeczywistego GLB: zmieniono 336 High/210 Low trójkątów wyłącznie w trzech koronach; pozostałe 12020 trójkątów i wszystkie atrybuty identyczne. Cała alfa identyczna bajtowo. Manifest i materiały bez zmian; 128 chunków GLB i 64 pliki instancji identyczne. Dowody: `crown-asset-audit.json`, `source-scope.json`, `world-scope.json`.

Import B zakończony. Obejrzano wszystkie osiem PNG podglądu (Low/High overcast, ref7197/abeam/above/route) i obie natywne pary ze zdjęciem. B usuwa równe, szerokie półki baseline i poprawia obrys, zwłaszcza High. Low wciąż jest zbyt pełnym stożkiem wobec ażurowych gałęzi zdjęcia. To częściowa poprawa, bez niezależnej akceptacji. `PREVIEW-B-REVIEW.md` zapisuje decyzję. Pary <=960 px: `review/preview-crowns-b/*photo-crowns-native.jpg` i `*photo-gable.jpg`. Źródło Rakoon 7197 CC0, zapisane SHA i stałe kadry; poza kamery WORKING_VALUE, bez lokalnego prostowania drzew.

Wariant A odrzucony po obrazach: wąski stożek z płaskimi klinami/otworami. Zachowany w `variants/a/`, opis `REJECTED-A.md`. Nie przywracać go jako poprawy. Oczekiwanie na pojedynczy test A anulowano przed uruchomieniem pytest, bez zabijania generatora. Propozycja C pozostaje wyłącznie analizą małego modelu, nigdy nie eksportowana ani renderowana; `NEXT-IF-B-FAILS.md`, `proposal_c.py`, `proposal-c-metrics.json`. Nie utożsamiać jej z modelem produkcyjnym B.

## Czego brakuje w r4

Nie wykonano żadnego pytest r4, pełnego GIS, physics/gate3 ani EditMode. Statyczna kontrola składni PS/Python przeszła, ale nie zastępuje testów. Pełny capture uruchomiono tuż przed poleceniem końca; jego obrazy nie są jeszcze pełnym przeglądem wizualnym. Nie ma `FINAL-CANDIDATE.json` i nie wolno go tworzyć na podstawie samej liczby PNG. Nie ma pomiaru A16 ani akceptacji lidera. Pigment tynku D48 pozostaje bez zmiany. Kominy nadal wymagają pracy nad powierzchnią i głowicami; pozycja rury pod pomostem niepotwierdzona.

## Wznowienie dopiero na nowe polecenie

1. Sprawdzić `git status`, `git log -1`, ten plik, `STATUS.md`, końcowy log capture i `capture-after-b-result.json`. Nie restartować w ciemno już zakończonych etapów.
2. Jeżeli pełne 244 PNG są kompletne: `pwsh -NoProfile -File artifacts/landmarks-r4/analyze.ps1 -Phase after-b`. Skrypt bierze heavy, zwalnia go przed ręcznym przeglądem. Obejrzeć wszystkie 32 arkusze oraz pary ze zdjęciem; sprawdzić osobno draws siatek, instancji i tris wszystkich 122 ujęć Low.
3. Dopiero po rzeczywistym przeglądzie zapisać `FINAL-CANDIDATE.json` z SHA siedmiu wymaganych wejść (opis w `final-python.ps1`), następnie `final-python.ps1` i `final-editmode.ps1`. GIS tylko raz na końcu rundy, osobne lease heavy dla GIS i physics/gate3. Kontrole cache muszą pozostać zgodne z wyrenderowanym modelem.
4. Zaktualizować ADR 0116 sekcję r4, REPORT i STATUS, commit WIP, robocopy własnych artifacts do main `/E /R:2 /W:1` bez `/MIR`, sprawdzić hashe. Dopiero potem nowa gałąź `gpt-landmarks-r5` w tym samym worktree i `git merge main`; konflikty generated/GLB/meta: main + regeneracja, kod: przemyślana unia. Nie merge do main, nie push.
5. Heavy: absolutny `C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-landmarks-r4`, finally Release. Unity: ten sam skrypt, bez Pool, Owner `gpt-landmarks`, finally Release i restore ustawień Unity. W kolejnej gałęzi zmienić właściciela heavy. Nie używać Priority ani omijać kolejki/PHONE_RUN/watchdoga. Nie trzymać heavy podczas Unity lub oglądania obrazów.

Skrypty zachowane w katalogu r4: `candidate-b.ps1` (już wykonany, NIE uruchamiać ponownie), `capture-full.ps1` (bieżący etap), `analyze.ps1`, `final-python.ps1`, `verify_cache.py`, `final-editmode.ps1`. Wszystkie ścieżki względne liczone z worktree. Źródłowe fotokopie i wszystkie nieudane próby są zachowane dla audytu.

## Wynik bezpiecznego zakończenia

Uzupełniany po naturalnym zakończeniu capture; nie uruchamiać kolejnej rundy.

Capture zakończył się naturalnie 12.11.2026 o16:26CET, exit0. Komplet244 PNG (61×4) w `after-b`, potwierdzony `capture-after-b-result.json` i zgodnością SHA modelu/manifestu/kamer. Nie przeprowadzono analizy ani pełnego przeglądu tych244 obrazów. Wszystkie wcześniejsze8 podglądów B zostały obejrzane. Slot Unity zwolniony, ustawienia Unity przywrócone. Kontrola procesów po zakończeniu: brak aktywnego Unity/Python/Blender/pwsh z tą ścieżką worktree i brak slotu/waitera gpt-landmarks. Nie zatrzymano cudzych ani własnych pracujących zadań; pipeline zakończył się sam. Nie uruchomiono nowych testów ani rundy r5.

Wszystkie pliki r4, w tym fotografie, baseline, wariant A, podglądy B, pełny capture, logi i narzędzia, pozostają w worktree i są skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\landmarks-r4`. Końcowy `COPY-RECEIPT.json` potwierdza hashe244 końcowych PNG oraz REPORT/HANDOFF/STATUS. Stan źródeł zapisano w commitach WIP; brak push, merge do main i commitów w main. R4 przekazana jako PARTIAL do wznowienia, nie jako zakończona walidacja.

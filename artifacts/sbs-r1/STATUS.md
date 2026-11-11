# Stan rundy sbs r1
Przeczytano zlecenie i zasady. Gałąź gpt-sbs-r1, baza main 4c9905b1.
Trwa przygotowanie lokalnych danych worktree; nie uruchomiono Unity.
Następny krok: uv run --project tools/refs python tools/refs/sbs_gate3.py --help

Dane worktree skopiowane; junctiony referencji tylko do odczytu. Dodano klasy A/B/C; J1, J2 i J3 wy??czone z domy?lnego zestawu dowodowego do kalibracji. Fotometria domy?lnie wy??czona do sprawdzenia masek. Skrypt SBS pobiera i zwalnia slot przed ka?dym startem Unity.
Nast?pny krok: uv run --project tools/refs python tools/refs/sbs_gate3.py prepare
## Kalibracja i przygotowanie renderu
Ukończono kopiowanie danych i cache Library bez Bee/BuildPlayerData/PackageCache. Przygotowano 40 referencji z jawną klasyfikacją pozy. Dla 2948 wskazano dwie krawędzie jezdni na wyprostowanym zdjęciu; ich przecięcie wyznacza horyzont roboczy, z zastrzeżeniem spadku drogi.
Następny krok: pwsh scripts/sbs-gate3.ps1 -EditMode
## Pokrycie początku trasy
Przeszukano lokalny manifest; brak kandydatów z pierwszych 300 m G3-A w promieniu 100 m. Próba pobrania dodatkowych zdjęć: błąd DNS graph.mapillary.com. Przygotowano 40 prób pozy bocznej dla ośmiu par J2 (−6, −3, 0, +3, +6 m). Nie zmieniono geometrii świata.
Następny krok: Get-Content artifacts/sbs-r1/render-validation.log -Tail 20
## Weryfikacja świeżości importu
Skopiowane sceny _Generated są z 17:11, a bieżąca regeneracja main zakończyła eksport GLB około 21:35. Przerwano oczekujące uruchomienie SBS przed uzyskaniem slotu; nie wystartowało Unity. Konieczna własna regeneracja i import, aby nie prezentować starych scen jako aktualnych.
Następny krok: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
## Integralność dowodów
Testy narzędzia SBS: 13/13 zaliczone. Dodano rejestr SHA kamer, SHA referencji, commitów gałęzi i main oraz czasu renderu. Kompozycja odmawia użycia zapisu renderu ze starym SHA kamer; odrzucone pary są usuwane z katalogu arkuszy dowodowych przy ponownym składaniu.
Pełne testy GIS i własna generacja świata nadal pracują. Unity nie było jeszcze uruchomione.
Następny krok: Get-Content artifacts/sbs-r1/build-world.log -Tail 20
## Walidacja metadanych
14/14 testów SBS zaliczone; parser PowerShell sprawdzony bez uruchamiania Unity. Zapisano ADR 0111 i migawkę danych wejściowych. Horyzont 2948 po przecięciu wybranych linii: 0,5249381; status nadal roboczy.
Następny krok: Get-Content artifacts/sbs-r1/build-world.log -Tail 20
## Czytelność arkuszy
15/15 testów SBS zaliczone. Arkusze pokazują flagę użycia fotometrii i wiek zdjęcia; 2948 ma nakładkę dwóch wybranych krawędzi oraz ich punktu zbiegu. Test integralności wykrywa podmianę pikseli renderu po zapisaniu metadanych.
Generacja PBR trwa niezależnie od generacji geometrii. Następny krok: Get-Content artifacts/sbs-r1/build-materials.log -Tail 20
## Liczniki kamer
Zebrano historyczne statystyki 160 wierszy kamer (40 × Low/High × clear/overcast), z draws geometrii i instancji osobno. Te dane są estymacją CPU edytora, nie licznikami GPU telefonu; różnic względem starego main nie przypisujemy kosztowi narzędzia SBS.
Następny krok: uv run --project tools/refs python artifacts/sbs-r1/summarize_stats.py --renders artifacts/sbs-r1/evidence/renders --baseline C:/Users/matma/Documents/Claude/kamion/artifacts/sbs-gate3/renders --output artifacts/sbs-r1/counters
## Przygotowany następny etap
Zapisano skrypt import-and-baseline.ps1: osobny slot gpt-sbs dla importu, przywrócenie ustawień w finally, następnie EditMode i baseline Low overcast. Uruchomienie nastąpi dopiero po udanej generacji geometrii i PBR.
Następny krok: pwsh -NoProfile -File artifacts/sbs-r1/import-and-baseline.ps1
## Generacja świata zakończona
build_world zakończył się kodem 0 po 918,0 s; wyeksportowano 64 GLB. W logu brak wystąpień fallback=True. Budowa PBR jest na końcowych warstwach. Pełne GIS nadal działa i ma niepowodzenia wymagające odczytania po zakończeniu.
Następny krok: pwsh -NoProfile -File artifacts/sbs-r1/import-and-baseline.ps1
## Ponowne kontrole po generacji
18 testów zaliczonych: wcześniej niespójne far field, kotwice wiaduktu, prototypy instancji i cały aktualny zestaw SBS. Pierwszy GLB ma SHA zgodne z aktualnym manifestem i zapisaną migawką. Odtworzono brakującą warstwę asfaltu z istniejącego w main publicznego zdjęcia (build_all --only asphalt_detail_photo, kod 0). Import nadal czeka na slot; Unity jeszcze nie wystartowało.
Metadane renderu rozróżniają bazę main faktycznie zawartą w gałęzi i obserwowany bieżący tip main; zapisują też SHA manifestu świata i specyfikacji materiałów.
Następny krok: Get-Content artifacts/sbs-r1/import-baseline.log -Tail 20
## Odtwarzalne próby pozy
Rozszerzono sondy J2 do siatki XY −5,5/0/+5,5 m (72 warianty), ponieważ przesunięcie względem jezdni nie musi być prostopadłe do osi zdjęcia. Skrypty generatora, renderu ze slotami i galerii 960 px zapisano w artifacts/sbs-r1. Sondy nie zmieniają pozy przyjętych do bramki.
Następny krok po baseline: pwsh -NoProfile -File artifacts/sbs-r1/render-pose-probes.ps1
## Spójność świata i fidelity
Sprawdzono SHA wszystkich 64 GLB względem aktualnego manifestu: 64/64 zgodne. Raport fidelity odtworzono w artifacts/sbs-r1/fidelity z bieżących wejść bez zmian kodu dróg. Nie commitujemy produktów innych dziedzin. Import nadal oczekuje w kolejce Unity.
Następny krok: Get-Content artifacts/sbs-r1/import-baseline.log -Tail 20
## Kandydaci do uzupełnienia pierwszych 300 m
Z lokalnego manifestu Commons dodano dwa rzeczywiste zdjęcia: cm109685822 (Rakoon, CC0, 2021-09-04, około s=230 m / odległość 8 m) i cm92458760 (Rakoon, CC BY 3.0, 2020-07-11, około s=249 m / 6 m). To kandydaci klasy C, nie potwierdzone pokrycie bramki; miniatury nie mają EXIF, a kierunek/FOV/oko są WORKING_VALUE. Odcinek 0–200 m nadal bez referencji. Prepare odtwarza teraz 42 kamery (25 B, 17 C); manifesty i atrybucja obejmują osobne licencje. Dodano cache rektyfikacji związany z SHA źródła i parametrami obiektywu oraz grupowanie renderów po proporcjach obrazu zamiast rozdzielczości źródłowej.
Cache pakietów Unity skopiowany z main, aby nie zależeć od niedziałającego DNS. Testy SBS 15/15.
Następny krok: Get-Content artifacts/sbs-r1/import-baseline.log -Tail 20
## Pilna zmiana limitów zasobów
Przeczytano aktualny punkt 3 zlecenia. Poprzednie generacje świata/PBR, pełny GIS i fidelity są zakończone; po poleceniu właściciela nie stwierdzono aktywnego procesu Pythona z tego worktree. Kolejne ciężkie zadania i testy uruchamiamy przez run-heavy.ps1: Acquire/Release -Pool heavy z właścicielem równym bieżącej gałęzi, finally gwarantuje zwolnienie. Pełny GIS wymaga jawnego -EndOfRound i nastąpi wyłącznie na końcu rundy. Podczas pracy używamy pojedynczych plików testów.
Wrappery wskazują aktualny skrypt slotów z main, aby obsługiwać nową pulę bez edytowania wspólnego skryptu w swojej gałęzi. Oczekujące Unity nadal używa limitu czterech procesów i właściciela gpt-sbs.
Następny krok: Get-Content artifacts/sbs-r1/import-baseline.log -Tail 20
## Bezpieczne oczekiwanie na zasoby
PBR Medium jest kompletny i aktualny: missing=0, stale=0, więc import nie powinien uruchomić ukrytego build_all. Testy SBS: 16/16. Oczekiwanie slotów sprawdzamy co 7 s; limity pozostają 4 Unity i 3 heavy. Długi próg stale w naszych wywołaniach zapobiega automatycznemu usuwaniu cudzych slotów przez współdzielony skrypt. Przed ponownym ustawieniem kolejki potwierdzono brak Unity z tego worktree i zwolniono wyłącznie własny slot.
Następny krok: pwsh -NoProfile -File artifacts/sbs-r1/import-and-baseline.ps1
## Dokumentacja i limit czasu
Uaktualniono ADR 0111 o 42 źródła, rzeczywiste wyniki walidacji, limity heavy/Unity i cel pracy do około 12.11, 21:31 czasu polskiego. Parser PowerShell potwierdził poprawność czterech wrapperów bez uruchamiania Unity ani Pythona obliczeniowego.
Następny krok: Get-Content artifacts/sbs-r1/import-baseline.log -Tail 20

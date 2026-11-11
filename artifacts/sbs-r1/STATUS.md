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

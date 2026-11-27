# Regeneracja świata — fala 15, sesja 25

## Zakres

[Kolejka podstawowa](queue.csv) obejmuje pięć pełnych przebiegów po fali 14. `prepare.ps1` migruje `streetscape_sources.json` do schematu 2 we wszystkich 54 gotowych regionach w jednym odczycie PBF. Pomiar na stanie z początku zadania wykazał **100 nowych fragmentów linii OSM w 27 kaflach**, w tym 7 w Mickiewicza. W pozostałych 27 zmienia się wersja schematu. Listę i liczniki per kafel zawiera [odczyt źródeł](../codex-wave15-prep-s25/osm-power.csv). Raport gałęzi przewodów wykazał zmianę geometrii bliskiego planu tylko w Mickiewicza.

| Łańcuch | Kafel | Powód | Budowa (s) | Budowa, trasa i fidelity (s) | Fala |
| --- | --- | --- | ---: | ---: | ---: |
| A | `bialystok-mickiewicza` | Podpięcie pięciu słupów do linii SN z OSM | 12 038 | 13 168 | 12 |
| B | `bialystok-industrial-c` | Raport fidelity C i manifest do porównania bajtów GLB | 2 230 | 3 477 | 13 |
| C | `dk65-04` | Zachodnia strona szwu Sadowa / Szkolna i scena kontrolna | 1 184 | 1 490 | 13 |
| D | `dk65-05` | Przywrócony koniec Sadowej w sieci, nawierzchni i kolizji | 917 | 1 226 | 13 |
| E | `tykocin` | Pomnik Czarnieckiego r3/r4 z main | 908 | 1 171 | 13 |

Pomiar Sadowej znalazł **1 pasujący fragment w 11 380 krawędziach 54 grafów**. Ponowne przeliczenie czterech szwów zależnych od dk65-05 wykazało zmianę wyniku wyłącznie na dk65-04 / dk65-05. Sprawdź przejazd Sadowa → Szkolna po imporcie obu kafli.

`test_road_fidelity.py::test_report_not_stale` porównuje wejścia jednego raportu (C) z grafem, trasą, overrides i śledzonymi modułami `roads/*.py`. Zmiany `build_world.py`, `network.py`, `meshing.py` i `junctions.py` unieważniają raport C. `decals.py` również podlega hashowaniu. Jego hash był już inny w raporcie sprzed końca fali 14, a wskazane gałęzie nie zmieniają tego modułu. Sam raport można odtworzyć przez `fidelity/run.py --region bialystok-industrial-c`, które buduje model dróg w pamięci. `test_determinism.py` porównuje siatkę dróg C przy seedach 0, 4 i 9. `test_world_roads.py::test_export_is_deterministic` wykonuje tymczasowy rebuild C i porównuje SHA-256 chunków z wcześniejszym manifestem. Zakres geometrii obejmuje więc cztery wskazane kafle oraz przebudowę C dla pewnego punktu odniesienia pełnego GIS. Sam hash wymaga jedynie nowego raportu C. Jeżeli manifest C z fali 14 nadal odpowiada nowemu generatorowi, przebieg fidelity C wystarczałby jako piąta operacja bez eksportu i importu C. Zgodność tego manifestu po integracji jest **UNVERIFIED**.

[Kolejka pełna](queue-full.csv) obejmuje wszystkie 54 regiony z `region.yaml`. Użyj jej, jeśli potrzebna jest aktualna proweniencja **wszystkich** raportów i GLB albo po integracji pojawią się zmiany wykraczające poza zmierzony zasięg.

## Czasy

Czasy historyczne pochodzą z kolejki fali 14, sporządzonej z udanych wpisów fali 13 oraz fali 12 dla Mickiewicza i Wygody. Fala 14 trwała podczas przygotowania. Do przydziału sortowano malejąco według `total_s` i dokładano kafel do najkrótszego łańcucha. Mickiewicza sam wyznacza ścieżkę krytyczną małej kolejki. W pełnej kolejce łańcuchy mają **21 989–22 196 s** prac Python każdy, czyli około **6 h 7 min** w równoległym wykonaniu według historycznych wag.

| Wariant | Najdłuższy łańcuch Python | Praca Python łącznie | Rezerwa czasu na całość |
| --- | ---: | ---: | ---: |
| Podstawowy | 3 h 39 min | 5 h 42 min | 4–6 h `WORKING_VALUE` |
| Pełny | 6 h 10 min | 30 h 37 min | 8–12 h `WORKING_VALUE` |

Czasy historyczne łańcuchów obejmują trasę i fidelity. Rezerwa uwzględnia osobny `far_field.py`, importy, visual QA i finał przy pięciu dostępnych slotach heavy i rozgrzanej `Library` Win64. W buildzie #10 pięć podstawowych importów zajęło łącznie 19 min 03 s, a wszystkie 54 około 3 h 09 min. Nowa `Library`, dostępność slotów i stan cache mogą wydłużyć wykonanie.

## Uruchomienie przez lidera

1. Poczekaj, aż fala 14 zakończy pracę na współdzielonym `Data/raw/derived` i zintegruj jej dane. Zintegruj `agy-poles-wires-s25`, `codex-sadowa-seam-s25` i tę gałąź przygotowawczą na main. Utwórz nowy worktree z tego main, uwzględniając zatwierdzone r3/r4.

   ```powershell
   pwsh -NoProfile -File scripts/new-agent-worktree.ps1 -Name regen-wave-15-s25 -Base main
   Set-Location .claude/worktrees/regen-wave-15-s25
   ```

   Wymagane są gotowe GLB i trasy fali 14, junction `Data/raw/derived` do głównego repozytorium, lokalne dane GIS, Unity Win64 i kabina LOD0 sprawdzana przez `scripts/cab-lod0.ps1`. Zamknij edytor w tym worktree i rozpocznij z czystym drzewem roboczym. Python działa przez absolutny `C:\Users\matma\Documents\Claude\kamion\scripts\cli-jobs\wgpy.cmd`. Shim `uv` obowiązuje w imporcie i przekazuje wybrane polecenia do tego wrappera.

2. Sprawdź plan jednego kafla, a potem przygotuj bazę. Wybierz zakres przy pierwszym `prepare.ps1`. Dla pełnej wersji dodaj `-Full` tylko do `prepare.ps1`. Pozostałe skrypty odczytują wybrany zakres z lokalnego `run/scope.txt`.

   ```powershell
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Tile dk65-04 -WhatIf
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/prepare.ps1
   ```

   Przygotowanie zapisuje audyt przewodów i renderuje GLB fali 14. Audyt stosuje już reguły zintegrowanej gałęzi i dla schematu 1 może dodać linie OSM w pamięci. Do porównania starej reguły użyj liczb z raportu gałęzi przewodów. Po renderach przygotowanie migruje źródła OSM i zapisuje commit WIP. Obejrzyj PNG „przed” przed rozpoczęciem łańcuchów.

3. Uruchom polecenia na pierwszym planie w pięciu terminalach z tego samego worktree albo wykonaj je kolejno. Slot heavy obejmuje GIS i operacje Unity. Blokada w worktree serializuje Unity. Błąd zatrzymuje dany łańcuch. Po naprawie ponów polecenie. Wznowienie wykorzysta ukończony etap GIS. `STOP` obok kolejki zatrzymuje łańcuch przed następnym kaflem.

   ```powershell
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain A
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain B
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain C
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain D
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain E
   ```

   Jeśli trzeba powtórzyć cały kafel po naprawie generatora, wykonaj `pwsh -NoProfile -File artifacts/regen-wave-15-s25/redo-one.ps1 -Tile <id>`. Skrypt zapisuje commity po imporcie. `autocommit.ps1` zapisuje ukończone kafle z zaległymi zmianami.

4. Po ukończeniu wszystkich łańcuchów uruchom finał. Aktualizuje linki tras, graf kafli i katalog regionów. Obejmuje audyt szwów i przewodów dla 54 kafli, przeszkody na trasie dla aktywnej kolejki, cztery zestawy budżetowe, pełny pytest GIS oraz PNG „po”.

   ```powershell
   pwsh -NoProfile -File artifacts/regen-wave-15-s25/final.ps1
   ```

## Kontrola obrazu i dowody

`vqa.ps1` pracuje w High PC, w clear i overcast. Przed regeneracją importuje oba kafle szwu. Dla `World_dk65-04_High` wywołuje `-Neighbours dk65-05 -Cameras top_szkolna`. Dla Mickiewicza używa jawnie zapisanej kamery [Gate3](mickiewicza-cameras.json) patrzącej na słupy i przewody SN w chunkach `7_0` i `7_1`. Kadr jest **WORKING_VALUE**, więc podczas przeglądu sprawdź widoczność przęseł i oparcie przewodów na trawersach. Dla Tykocina porównaj widok pomnika, a dla C kamery kontrolne. W razie potrzeby powtórz `vqa.ps1 -Phase after` po zakończonym imporcie.

PNG, `stats.txt`, raporty i logi zapisują się w `C:\Users\matma\Documents\Claude\kamion\artifacts\regen-wave-15-s25\`. Porównaj parami pliki z `vqa/before` i `vqa/after`, sprawdź raport szwu oraz przejazd, a ocenę zapisz w STATUS. `run/` zachowaj do końca fali. Podczas przygotowania skryptów wykonano [plan na dk65-04](dry-run.log), kontrolę składni i cztery zestawy budżetowe. Wykonanie fali i odbiór PNG są krokiem lidera.

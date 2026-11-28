# Regeneracja świata — fala 15, sesja 25

## Zakres

[Kolejka podstawowa](queue.csv) zawiera 19 pełnych przebiegów. Pomiar wykazał zmianę w 17 kaflach, a `dk65-04` i `dk65-monki-01` ujęto jako drugie strony kontroli szwów. [Inwentarz 54 kafli](scope.csv) wskazuje powód przebudowy, zmianę profili lub oznakowania, pochodzenie roads QA i liczbę nowych części OSM. Porównanie przypięto do `regen-wave-14-s25` `4499ff9de`. Na tym commicie 41 manifestów pochodzi z fali 14, a 13 z fali 13. Ostatnia zmiana treści `roads_qa.json` pochodzi z fali 14 dla 41 kafli, z fali 12 dla 12 kafli oraz z wcześniejszego eksportu prototypu `knyszyn-w`. Fala 13 zmieniła manifesty tych 13 kafli przy identycznej treści `roads_qa.json`.

- **DK19 i S8** obejmują Bojary, Mickiewicza, `dk65-01`, Jeroniki oraz `s8-02`, `s8-04` i `s8-05`. D94, uzgodnienie osi i wygładzanie zmieniają profile. Na `s8-02` różnica przekroju ma ok. 0,918 mm.
- **DK65 do Moniek** obejmuje `dk65-monki-02…07` i `monki` po zmianie P‑7b. `dk65-monki-01` jest drugą stroną obowiązkowej kontroli szwu.
- **Sadowa i Szkolna** obejmują `dk65-05` z przywróconym cięciem 0,04884 m oraz `dk65-04` po drugiej stronie szwu. Porównaj oba kafle w `top_szkolna`.
- **Przewody** obejmują Mickiewicza (8 170 → 8 518 tris) i Industrial C (18 014 → 18 294 tris) w pomiarze siatki z płaskim podłożem. `prepare.ps1` migruje źródła wszystkich 54 kafli do schematu 2 w jednym odczycie PBF. W 27 kaflach pojawia się 100 części linii OSM. W pozostałych 27 zmienia się wersja schematu.
- **Tykocin** ma nowszy wypieczony pomnik r4 na main. Fala 14 raportuje LOD0/LOD1 26 670/1 914 tris, metadane r4 podają 26 710/1 964. Sprawdź figurę, cokół i kadr z ulicy.

`bialystok-industrial-c` wymaga też odświeżenia raportu fidelity i manifestu używanego przez `test_report_not_stale` i test determinizmu eksportu. Pierwszy sprawdza hashe wejść generatora, a drugi bajty chunków. Kontrola sum samego raportu nie zastępuje przebudowy C, ponieważ zmienia się siatka przewodów.

[Kolejka pełna](queue-full.csv) zawiera 54 regiony. Wybierz ją, jeśli po integracji zmienią się wejścia innych kafli albo potrzebna jest aktualna proweniencja wszystkich raportów i GLB. Gałęzie `codex-csharp-review-fixes-s25` i `codex-horn-button-s25` zmieniają kod runtime, shader i testy Unity. Ich zakres GIS wynosi 0 kafli.

## Czasy

`build_s` i `total_s` pochodzą z poprawnie zakończonych wpisów fali 14 dla 44 kafli. `total_s` obejmuje budowę, daleki plan, trasę i fidelity. Dla pozostałych 10 kafli zachowano wagi fali 13, bez osobnego czasu dalekiego planu. Przydział do pięciu łańcuchów stosuje malejące wagi i najkrótszy dotąd łańcuch.

| Wariant | Najdłuższy łańcuch GIS | Praca GIS łącznie | Całość |
| --- | ---: | ---: | ---: |
| Podstawowy, 19 kafli | 3 h 25 min | 10 h 14 min | 5–8 h `WORKING_VALUE` |
| Pełny, 54 kafle | 4 h 35 min | 22 h 44 min | 7–11 h `WORKING_VALUE` |

Udane importy fali 14 dają częściowy pomiar kosztu Unity. Import 13 z 19 kafli zajął 1 h 02 min, a 42 z 54 kafli 3 h 28 min. Dziesięć historycznych przebiegów visual QA trwało po 33–88 s. Plan fali 15 ma 32 przebiegi visual QA w obu fazach oraz 12 importów scen do przygotowania bazy. Szacunki całości obejmują przygotowanie i finał. Zakładają pięć dostępnych slotów heavy i rozgrzaną `Library` Win64. Importy i renderowanie są serializowane w worktree. Część importów może zachodzić równolegle z GIS pozostałych łańcuchów.

## Uruchomienie przez lidera

1. Poczekaj, aż fala 14 zakończy pracę na współdzielonym `Data/raw/derived` i zintegruj jej dane. Na main zintegruj `codex-seam-steps-s25` (zawiera Sadową), `agy-poles-wires-s25` oraz czekające poprawki runtime przewidziane do wydania. Przenieś pliki `artifacts/regen-wave-15-s25/` z gałęzi zakresu i sprawdź obecność wypieczonego pomnika r4 (`91ed526b3`). Z tak przygotowanego main utwórz worktree fali 15.

   Na main, po zakończeniu fali 14 i z czystym drzewem roboczym:

   ```powershell
   git merge regen-wave-14-s25
   git merge codex-seam-steps-s25
   git merge agy-poles-wires-s25
   git restore --source=codex-wave15-scope-s25 --staged --worktree -- artifacts/regen-wave-15-s25
   git commit -m "docs(wave15): kolejki i odbior fali 15"
   ```

   Po zintegrowaniu poprawek runtime przewidzianych do tego wydania:

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

`vqa.ps1` pracuje w High PC, w clear i overcast. Przed regeneracją importuje z fali 14 każdy potrzebny kafel raz i ładuje sąsiada podczas renderu szwu.

| Scena | Sąsiad | Kamery |
| --- | --- | --- |
| `dk65-04` | `dk65-05` | `top_szkolna` |
| `bialystok-mickiewicza` | — | `wave15-mickiewicza-przewody` |
| `bialystok-mickiewicza` | `bialystok-bojary` | `dk19_piastowska_seam_n` |
| `dk65-monki-01` | `dk65-monki-02` | `dk65_west_edge_in` |
| `s8-04` | `s8-05` | `route_s1980` |
| `dk65-01` | `dk8-s8-jeroniki` | `s8_corner_eye`, `s8_corner_top` |
| `tykocin` | — | `look_tykocin_czarniecki`, `czarniecki_figure_0320b`, `czarniecki_pedestal_0320b` |
| `bialystok-industrial-c` | — | zestaw kamer sceny C |

[Pozycja kamery przewodów](mickiewicza-cameras.json) jest **WORKING_VALUE**. Sprawdź widoczność przęseł w chunkach `7_0` i `7_1` i oparcie przewodów na trawersach. Na kadrach szwów porównaj jezdnię, ciągłość P‑7b oraz pobocza. Po imporcie można powtórzyć `vqa.ps1 -Phase after`.

PNG, `stats.txt`, raporty i logi zapisują się w `C:\Users\matma\Documents\Claude\kamion\artifacts\regen-wave-15-s25\`. Porównaj parami pliki z `vqa/before` i `vqa/after`, sprawdź raport szwu oraz przejazd, a ocenę zapisz w STATUS. `run/` zachowaj do końca fali. W tym zadaniu sprawdzono [plan na dk65-04](dry-run.log), składnię PowerShell oraz obecność wskazanych kamer w danych bazowych. Świeże PNG i przejazd pozostają częścią wykonania fali.

# Regeneracja świata — fala 15, sesja 25

## Zakres

[Kolejka podstawowa](queue.csv) zawiera **26 pełnych przebiegów** (19 pierwotnych + 7 dopisanych po analizie `agy-props-carriageway-s25`). Pomiar wykazał zmianę w 25 kaflach, a `dk65-monki-01` ujęto jako drugą stronę kontroli szwu (`dk65-04` jednocześnie dostaje poprawkę `signal_rail` w `clear_carriageway`, pozostając też drugą stroną kontroli Sadowej). [Inwentarz 54 kafli](scope.csv) wskazuje powód przebudowy, zmianę profili lub oznakowania, pochodzenie roads QA i liczbę nowych części OSM. Porównanie bazowe przypięto do `regen-wave-14-s25` `4499ff9de`. Na tym commicie 41 manifestów pochodzi z fali 14, a 13 z fali 13. Ostatnia zmiana treści `roads_qa.json` pochodzi z fali 14 dla 41 kafli, z fali 12 dla 12 kafli oraz z wcześniejszego eksportu prototypu `knyszyn-w`. Fala 13 zmieniła manifesty tych 13 kafli przy identycznej treści `roads_qa.json`.

- **DK19 i S8** obejmują Bojary, Mickiewicza, `dk65-01`, Jeroniki oraz `s8-02`, `s8-04` i `s8-05`. D94, uzgodnienie osi i wygładzanie zmieniają profile. Na `s8-02` różnica przekroju ma ok. 0,918 mm.
- **DK65 do Moniek** obejmuje `dk65-monki-02…07` i `monki` po zmianie P‑7b. `dk65-monki-01` jest drugą stroną obowiązkowej kontroli szwu.
- **Sadowa i Szkolna** obejmują `dk65-05` z przywróconym cięciem 0,04884 m oraz `dk65-04` po drugiej stronie szwu. Porównaj oba kafle w `top_szkolna`.
- **Przewody** obejmują Mickiewicza (8 170 → 8 518 tris) i Industrial C (18 014 → 18 294 tris) w pomiarze siatki z płaskim podłożem. `prepare.ps1` migruje źródła wszystkich 54 kafli do schematu 2 w jednym odczycie PBF. W 27 kaflach pojawia się 100 części linii OSM. W pozostałych 27 zmienia się wersja schematu.
- **Tykocin** ma nowszy wypieczony pomnik r4 na main. Fala 14 raportuje LOD0/LOD1 26 670/1 914 tris, metadane r4 podają 26 710/1 964. Sprawdź figurę, cokół i kadr z ulicy.
- **Propsy na jezdni i wysepka bramy (`agy-props-carriageway-s25`)** — usunięcie martwej strefy `−0,05 m` oraz zaokrąglenia do 1 cm w `furniture.clear_carriageway`, dodanie prefiksu `signal_rail` do `GROUND_PROPS` oraz zachowanie `collision_curb` wysp bramowych `override:*:island` w `meshing.cull_sides_on_carriageway` zmieniają wynik generatora w **11 kaflach** (pomiar w pamięci na wszystkich 54 kaflach z `Data/raw/derived`):
  - **4 kafle już w pierwotnej kolejce:** `bialystok-mickiewicza` (`clear_carriageway`: 3 propsy), `bialystok-bojary` (`clear_carriageway`: 5 propsów), `bialystok-industrial-c` (`clear_carriageway`: 1 prop + zachowanie `collision_curb` wysepki `override:kwadrat-park-gate-kit:island`), `dk65-04` (`clear_carriageway` + `signal_rail`: 1 `signal_rail_saltire_g3` na +5,47 cm wewnątrz jezdni);
  - **7 kafli dopisanych do `queue.csv`:** `bialystok-wygoda` (2 × `sign_post`), `bialystok-kleeberga` (1 × `sign_post`), `bialystok-maczka` (1 × `sign_post`, 1 × `bollard`), `bialystok-knyszynska` (1 × `sign_post`), `bialystok-krywlany` (1 × `lamp_10m`), `dk65-02` (2 × `signal_rail_saltire_g3`: 1 przesunięty, 1 usunięty), `s8-03` (1 × `lamp_old_steel_8m`). `bialystok-dojlidy` i `bialystok-porosly` mają 0 zmian w generatorze Pythona.

`bialystok-industrial-c` wymaga też odświeżenia raportu fidelity i manifestu używanego przez `test_report_not_stale` i test determinizmu eksportu. Pierwszy sprawdza hashe wejść generatora, a drugi bajty chunków. Kontrola sum samego raportu nie zastępuje przebudowy C, ponieważ zmienia się siatka przewodów.

[Kolejka pełna](queue-full.csv) zawiera 54 regiony. Wybierz ją, jeśli po integracji zmienią się wejścia innych kafli albo potrzebna jest aktualna proweniencja wszystkich raportów i GLB. Gałęzie `codex-csharp-review-fixes-s25` i `codex-horn-button-s25` zmieniają kod runtime, shader i testy Unity. Ich zakres GIS wynosi 0 kafli.

> **Ważne — `agy-prop-colliders-s25` (C#) i kolizje placów:** po scaleniu `agy-prop-colliders-s25` **każdy importowany kafel** dostaje rozdział `col_asphalt` (jezdnia) od `col_yard_asphalt` (warstwa `paved`) oraz przywrócone kolizje zaparkowanych pojazdów i rekwizytów placowych. Ponieważ logika C# korzysta z węzła `paved` obecnego już w `chunk_*.low.glb` fali 14, **pełny reimport 54 kafli nie wymaga regeneracji Pythona** — wystarczy `scripts/import-region.ps1` (bez `-Build`). Jeśli fala 15 biegnie w wariancie podstawowym (26 kafli), pozostałe **28 kafli** spoza `queue.csv` należy przeimportować poniższym wariantem **reimport-only** przed buildem #11.

### Wariant „reimport-only” (kafle spoza fali 15 przed buildem #11)

Dotyczy **28 kafli** z `queue-full.csv`, których nie ma w `queue.csv` (albo pełnego reimportu **54 kafli** bez przebudowy Pythona — szacunek pełnych 54 kafli: **~54 × 5 min ≈ 4 h 30 min** `WORKING_VALUE`; dla samych 28 kafli spoza fali 15: **~28 × 5 min ≈ 2 h 20 min** `WORKING_VALUE`). Wymaga zintegrowanej gałęzi `agy-prop-colliders-s25`, gotowych GLB z fali 14 w `Data/raw/derived/<tile>/world/` oraz `route_start.json`. Uruchamiać na pierwszym planie (serializowany Unity w jednym worktree, pod slotem `heavy`, z kontrolą `PHONE_RUN` i cofnięciem plików ubocznych Unity):

```powershell
$wave15 = (Import-Csv artifacts/regen-wave-15-s25/queue.csv).tile
$reimportOnly = (Import-Csv artifacts/regen-wave-15-s25/queue-full.csv).tile | Where-Object { $_ -cnotin $wave15 }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner wave15-reimport-only
try {
    foreach ($tile in $reimportOnly) {
        while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep -Seconds 60 }
        pwsh -NoProfile -File scripts/import-region.ps1 -Region $tile -BuildTarget Win64 -Tiers High -MaterialTier High
        if ($LASTEXITCODE) { throw "Reimport failed for $tile ($LASTEXITCODE)" }
        git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset
    }
}
finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner wave15-reimport-only
}
```

## Czasy

`build_s` i `total_s` pochodzą z poprawnie zakończonych wpisów fali 14 dla 44 kafli. `total_s` obejmuje budowę, daleki plan, trasę i fidelity. Dla pozostałych 10 kafli zachowano wagi fali 13, bez osobnego czasu dalekiego planu. Przydział do pięciu łańcuchów stosuje malejące wagi (`build_s`) i najkrótszy dotąd łańcuch (dla 26 kafli: A `11 183 s`, B `10 327 s`, C `10 309 s`, D `10 139 s`, E `10 288 s` `build_s`).

| Wariant | Najdłuższy łańcuch GIS | Praca GIS łącznie | Całość |
| --- | ---: | ---: | ---: |
| Podstawowy, 26 kafli | 3 h 41 min (`total_s` w E; `build_s` max 3 h 06 min w A) | 17 h 08 min (`total_s`; 14 h 31 min `build_s`) | 6–9 h `WORKING_VALUE` |
| Pełny, 54 kafle | 4 h 35 min | 22 h 44 min | 7–11 h `WORKING_VALUE` |
| Reimport-only, 28 kafli spoza fali 15 | 0 min (bez Pythona) | 0 min | ~2 h 20 min `WORKING_VALUE` (~28 × 5 min, serializowany) |
| Reimport-only, 54 kafle (pełny przed buildem #11) | 0 min (bez Pythona) | 0 min | ~4 h 30 min `WORKING_VALUE` (~54 × 5 min, serializowany) |

Udane importy fali 14 dają częściowy pomiar kosztu Unity. Import 13 z 19 kafli zajął 1 h 02 min, a 42 z 54 kafli 3 h 28 min (mediana ~5 min/kafel). Dziesięć historycznych przebiegów visual QA trwało po 33–88 s. Plan fali 15 ma 32 przebiegi visual QA w obu fazach oraz 12 importów scen do przygotowania bazy. Szacunki całości obejmują przygotowanie i finał. Zakładają pięć dostępnych slotów heavy i rozgrzaną `Library` Win64. Importy i renderowanie są serializowane w worktree. Część importów może zachodzić równolegle z GIS pozostałych łańcuchów.

## Uruchomienie przez lidera

1. Poczekaj, aż fala 14 zakończy pracę na współdzielonym `Data/raw/derived` i zintegruj jej dane. Na main zintegruj `codex-seam-steps-s25` (zawiera Sadową), `agy-poles-wires-s25`, `agy-props-carriageway-s25`, `agy-prop-colliders-s25` oraz czekające poprawki runtime przewidziane do wydania. Przenieś pliki `artifacts/regen-wave-15-s25/` z gałęzi zakresu (`agy-wave15-props-s25`) i sprawdź obecność wypieczonego pomnika r4 (`91ed526b3`). Z tak przygotowanego main utwórz worktree fali 15.

   Na main, po zakończeniu fali 14 i z czystym drzewem roboczym:

   ```powershell
   git merge regen-wave-14-s25
   git merge codex-seam-steps-s25
   git merge agy-poles-wires-s25
   git merge agy-props-carriageway-s25
   git merge agy-prop-colliders-s25
   git restore --source=agy-wave15-props-s25 --staged --worktree -- artifacts/regen-wave-15-s25
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

5. Jeśli fala 15 biegła w wariancie podstawowym (26 kafli), przed buildem #11 wykonaj wariant **reimport-only** (sekcja wyżej) na pozostałych **28 kaflach** spoza `queue.csv` (lub na wszystkich 54 kaflach, ~54 × 5 min), aby odzyskać kolizje placów i parkingów z `agy-prop-colliders-s25` w całym świecie bez regeneracji Pythona.

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

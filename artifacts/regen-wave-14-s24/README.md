# Regeneracja świata — fala 14, sesja 24

Fala obejmuje 54 gotowe regiony z kolejki fali 13 i odświeża daleki plan każdego z nich. Pozostałe 10 katalogów w `Data/Regions` zawiera dane autorskie planowanych regionów i nie ma jeszcze `region.yaml`.

Zakres zmian obejmuje Rynek w Tykocinie (ADR 0320), budynki gospodarcze (0238, r2 i r3), gatunki drzew, korony, ogrody i szpalery (0352), łaty i styki zjazdów (0335/0349), sieć WN/SN i daleki plan (0351) oraz chmury w renderze High.

## Kolejka i czas

[`queue.csv`](queue.csv) jest kolejką wykonawczą. Czasy w sekundach pochodzą z ostatniego udanego wpisu `chain.status` fali 13 dostępnego w chwili przygotowania. Dla `bialystok-mickiewicza` i `bialystok-wygoda` użyto końcowego logu fali 12 (`artifacts/regen-wave-12-s24/worktree-logs/chain.status`). `total_s` obejmuje również trasę i fidelity. Algorytm sortuje malejąco po `build_s` i przypisuje kolejny kafel do łańcucha o najmniejszej sumie. Remisy rozstrzygają identyfikator kafla i litera łańcucha.

| Łańcuch | Kafle | Budowa (s) | Budowa, trasa i fidelity (s) |
| --- | ---: | ---: | ---: |
| A | 8 | 17 848 | 21 144 |
| B | 9 | 17 844 | 20 667 |
| C | 11 | 18 041 | 21 653 |
| D | 13 | 18 038 | 24 396 |
| E | 13 | 18 075 | 22 330 |

Rozstęp sum samej budowy w logu fali 12 wynosił 8 666 s (12 053–20 719 s). Dla nowego przydziału historyczne wagi z obu fal dają rozstęp 231 s (17 844–18 075 s). Najdłuższy łańcuch z trasą i fidelity to 6 h 47 min według tych wag. Dodatkowe wywołanie `far_field.py` następuje po `build_world --context`, który już tworzy pierwszy zestaw danych dalekiego planu. Osobny przebieg zapisuje końcowe GLB, manifest i QA przed importem.

W logu build #10 (`artifacts/full-build-10-s24/chain.status`) 54 importy Win64 w rozgrzanej `Library` zajęły 3 h 09 min łącznie (185–304 s/kafel, Low+High, materiały Medium). Tu importujemy High z materiałami High, po jednym kaflu, równolegle z pracą innych łańcuchów Python. Zarezerwuj **8–12 h** (`WORKING_VALUE`) z pięcioma slotami i gotową `Library`. Pierwszy import w nowym katalogu, oczekiwanie na sloty, ponowna ekstrakcja GIS i powtórki mogą wydłużyć przebieg. Przy wykonaniu kolejno w jednym terminalu same historyczne prace Python sumują się do 30 h 36 min.

## Miejsce na dysku

Zmierzono **41,1 GiB** danych 54 kafli w współdzielonym `Data/raw/derived`. Zostają na junctionie i są nadpisywane po kaflu. Referencyjny worktree build #10 używał **39,4 GiB** w `game/Assets/_Generated/World` oraz **17,5 GiB** w `game/Library`. Przed startem zaplanuj przynajmniej **80 GiB wolnego** na woluminie wspólnym dla worktree i derived (`WORKING_VALUE`, z zapasem na cache, materiały, etap przejściowy i dowody). Jeżeli dodatkowo archiwizujesz cały stan derived, dolicz około **42 GiB**. Zmierzono **345,3 GiB wolnego** podczas przygotowania. Sprawdź ponownie przed startem.

## Uruchomienie przez lidera

1. Poczekaj na koniec fali 13 i jej integrację. Uruchom z katalogu głównego osobnego worktree na gałęzi fali 14 zawierającej oba zestawy commitów. Upewnij się, że inne procesy zakończyły zapis do współdzielonego `Data/raw/derived`, indeks Git jest pusty, a `game/` zamknięty. Skrypty oczekują junctionu derived do głównego repo, źródeł GIS, działającego Unity Win64 oraz pliku kabiny sprawdzanego przez `scripts/cab-lod0.ps1`. Mogą wykorzystać istniejącą `Library` Win64. Python pochodzi z istniejącego venv `agent-a492e5af856a32ed3`, a `PYTHONPATH` wskazuje bieżący worktree. `trees_meta.json` powinien mieć LF, ponieważ profil koron haszuje surowe bajty (`git ls-files --eol -- art-source/world/vegetation/trees_meta.json`).
2. Najpierw sprawdź plan i przygotuj bazę, wykonując polecenia kolejno.

   ```powershell
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Tile dk65-monki-03 -WhatIf
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/prepare.ps1
   ```

   Przygotowanie zapisuje audyt WN i renderuje bazę wysokiej jakości w obu wariantach światła na gotowym derived fali 13. Bazowe importy używają kodu aktualnego worktree, więc różnice w shaderach, chmurach i współdzielonych assetach mogą już być widoczne w klatkach „przed”. Jeżeli potrzebujesz porównania tych zmian, użyj również klatek builda #10 lub klatek z gałęzi źródłowej. Po tej bazie przygotowanie zapisuje `tree_crown_profile --write` raz. Obejrzyj PNG „przed” przed startem łańcuchów.

3. W pięciu terminalach wskaż ten sam katalog i wykonaj po jednym poleceniu na pierwszym planie. Możesz też wykonać je kolejno. Slot heavy obsługuje cały krok GIS i każdy start Unity. Blokada w worktree serializuje Unity, a shim `uv` obowiązuje tylko podczas importu.

   ```powershell
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Chain A
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Chain B
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Chain C
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Chain D
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/chain.ps1 -Chain E
   ```

   Błąd zatrzymuje dany łańcuch. Po naprawie ponów to samo polecenie. Pomyślne kafle są pomijane, a po błędzie importu wznowienie korzysta z wyniku ukończonego GIS. Skrypty zapisują WIP i STATUS po udanym imporcie z nowymi danymi. `autocommit.ps1` jednorazowo zapisuje gotowe kafle z pominiętymi commitami. Plik `STOP` obok kolejki wstrzymuje łańcuchy przed następnym kaflem. Jeśli trzeba powtórzyć **cały** kafel po poprawce generatora, wykonaj `pwsh -NoProfile -File artifacts/regen-wave-14-s24/redo-one.ps1 -Tile <id>` i ponownie uruchom finał. Zachowaj lokalny `run/` do końca fali.

4. Gdy pięć poleceń się zakończy, uruchom finał.

   ```powershell
   pwsh -NoProfile -File artifacts/regen-wave-14-s24/final.ps1
   ```

   Finał aktualizuje linki tras, graf kafli i katalog regionów, zapisuje raporty szwów, przeszkód na trasach i audyt WN, uruchamia cztery pliki budżetowe i pełny `pytest tests/gis`, a następnie renderuje klatki „po”. Sprawdź `seams_after.md`, `route_obstacles.json` i porównaj liczniki z `hv_wires_before.json` oraz `hv_wires_after.json`. Audyt szwów i audyt WN raportują wyniki w plikach także przy kodzie wyjścia 0.

## Dowody

Wyniki wykonania trafią do `C:\Users\matma\Documents\Claude\kamion\artifacts\regen-wave-14-s24\`. Porównaj parami PNG `vqa/before|after/<kafel>/High-clear|High-overcast` oraz towarzyszące `stats.txt`. Skrypty wybierają C, Tykocin, Knyszyn-W, DK65-07 i DW671-Tykocin-03. Obie strony porównania izolują kafel (`-Neighbours none`). Szwy między kaflami mają osobny raport GIS. Zapisz ocenę obejrzanych kadrów i raportów w STATUS przed integracją.

W sesji przygotowania wykonano tylko plan `-WhatIf` na `dk65-monki-03` (236 s budowy według fali 13). Dowód jest w [`dry-run.log`](dry-run.log). Właściwa regeneracja i rendery są krokiem lidera.

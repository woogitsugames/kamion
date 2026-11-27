# Recenzja scaleń z 27 listopada 2026

Przejrzałem 34 scalenia osiągalne z `main` w migawce `bfaccaf1a120dadf73b87c47c95942a384d4aba5`, w tym 33 na pierwszym rodzicu i wewnętrzne scalenie `4835292a0`. Zakres wyznaczyło `git log --merges --since="2026-11-27 00:00" main` z lokalną strefą CET. Porównałem każde scalenie do pierwszego rodzica, sprawdziłem pliki zmienione względem obojga rodziców i prześledziłem wspólne ścieżki w końcowej migawce. Pliki i linie poniżej odnoszą się do tej migawki. Łączny diff od `2d5744863^1` obejmuje 841 ścieżek, w tym 157 plików C#, shaderów, HLSL, Pythona i PowerShella.

**Potwierdzone znaleziska obejmują 6 ważnych i 2 drobne.** Nie stwierdziłem błędu krytycznego. Cztery obowiązkowe bramki GIS przeszły. Rozszerzony przebieg 21 zmienionych plików testowych ujawnił 9 niepowodzeń, które wynikają z dwóch rozbieżności między asercjami a wdrożonymi zmianami. Na danych 54 kafli wykryłem ponadto niespójności grafu WN po redukcji LOD.

## Ważne

### 1. Daleki plan zachowuje niepodłączone wieże, a audyt ich nie wykrywa

**Pliki** `tools/worldgen/streetscape/far_field.py:2362`, `:2381`, `:2385`, `:2698`, `:2984` i `tools/worldgen/qa/hv_wires_audit.py:103`. Scalenie `bb575a59b` nad zmianami fali 12.

`power_plan` filtruje podpory względem przęseł wejściowych. Następnie `_select_far_hv` odrzuca część podpór przez odległość lub zagęszczenie. Gdy w łańcuchu zostanie tylko jedna wieża, trafia do `kept_ids`, a pętla `zip(chain_kept, chain_kept[1:])` nie tworzy dla niej żadnego przęsła. Eksport mimo to generuje wieżę. Audyt liczy `unwired_power_pylons` z planu sprzed selekcji LOD.

**Dowód i scenariusz.** Odczytałem istniejące `far_field_gis_cache.json` 54 kafli. Dla każdego uruchomiłem w pamięci `power_plan` i `_select_far_hv`, a następnie policzyłem wieże z listy renderowanej, które nie wystąpiły na żadnym końcu zwróconych przęseł. Plan przed LOD wykazuje 0 niepodłączonych. Po LOD jest **23 w 9 kaflach Low** i **41 w 14 kaflach High**. Sam `bialystok-industrial-c` ma odpowiednio 3 i 6. Są to wyniki generatora dla cache GIS, bez ponownego eksportu i importu scen.

**Poprawka.** Po złożeniu `render_spans` pozostawić wieże WN należące do co najmniej jednego przęsła albo zachować im reprezentację przewodów, jeśli samotna sylweta ma być widoczna. Dodać do QA wynik po selekcji osobno dla Low/High i test z łańcuchem, w którym drugi koniec wypada po redukcji. Maszty z `plan["masts"]` mają osobną semantykę.

### 2. Margines kukurydzy wchodzi do obszaru maski przeszkód

**Pliki** `tools/worldgen/streetscape/field_crops.py:336`, `:355`, `:368`, `:378` i `tests/gis/test_fields_r4_0334.py:45`. Scalenie `e5e39f1dd`.

`_maize_edge` sprawdza położenie `C`, po czym przesuwa i obraca kartę. Po tej transformacji zapisuje oba końce bez ponownego sprawdzenia maski `blocked`. Krótkie karty poprzeczne mają tę samą lukę. Test miedz bada środki kart, a końcową asercję o odstępie ogranicza przez `[:nr]` do zwykłych rzędów.

**Dowód i scenariusz.** Na scenie syntetycznej z helperów `_crop_world()` i `_maize_origin()` z `test_fields_r3_0334.py` ustawiłem `blocked[:, 250:251] = True` i wywołałem `field_crops.build`. Sprawdziłem końce u podstawy kart przez `_Ground.ij`. **13 z 7303 kart `maize_edge` ma koniec w masce**, a środki 3 kart też są w masce. Dla pasów maski o szerokości 3 m i 5 m pozostała po 1 karcie z końcem w masce. Zwykłe rzędy i ich poprzeczki miały w tych próbach 0 takich kart. Maska w ścieżce produkcyjnej obejmuje m.in. przeszkody i ich margines.

**Poprawka.** Sprawdzić podstawę po transformacji, w tym końce i punkty pośrednie odcinka, pod kątem `blocked`. Reguła nieregularnej krawędzi może nadal dopuszczać rośliny na trawiastym marginesie. Rozszerzyć test o maskę przeszkody i sprawdzać rzeczywiste trójkąty eksportowe kart brzegowych.

### 3. `DepthOnly` i kolor roślinności stosują różne progi odrzucania

**Pliki** `game/Assets/_Project/Rendering/Shaders/Vegetation.shader:238`, `:315`, `:494`, `:666` oraz `game/Assets/_Project/World/Runtime/WorldInstances.cs:131`. Interakcja `763f6fd25` i `157a114c2`.

`ForwardLit` i przebieg wypełnienia głębi przed kolorem używają `VegCutoffFill`. Osobny przebieg URP `DepthOnly` wywołuje samo `VegCardEdge`, więc pomija obniżenie progu alfy od skali tekstury. Kiedy działa prepass `DepthOnly`, tekstura głębi może zawierać tło tam, gdzie przebieg koloru rysuje liść.

**Dowód i scenariusz.** Dla karty poza przejściem LOD z `_Cutoff=0.5`, `m=2`, `_KamionTreeFade.w=0.3`, kątem poza zakresem tłumienia krawędzi i alfą 0,4, próg w kolorze wynosi 0,2, a w `DepthOnly` 0,5. Z wyłączonym A2C oba przebiegi wykonują twarde `clip` i dają przeciwne wyniki. Przy włączonym A2C dodatkowo różni się sposób liczenia pokrycia. Zweryfikowałem warunki i wynik `clip` statycznie. Wpływ na obraz w playerze pozostaje `UNVERIFIED`.

**Poprawka.** Użyć jednego helpera progu i pokrycia w przebiegach koloru i głębi, z uwzględnieniem liczby próbek celu renderowania. Zestawić maskę koloru i głębi dla kart na Low i High, przy prepassie URP, z A2C i bez.

### 4. Wyjście z jazdy omija zwalnianie klonów materiałów pierścienia

**Plik** `game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:1033`, `:1079`, `:1272`. Scalenie `063deeef2`.

`MarkFarRing` tworzy klony `Material` z `HideFlags.DontSave`. Są niszczone przez `Clear(t)` przy wyładowaniu kafla przez streamer. `OnDestroy` tylko zeruje globalną liczbę prostokątów, odpina listener i oddaje dzierżawy scen. Flaga `DontSave` wymaga jawnego zniszczenia obiektu. [Unity 6.3 Scripting API – HideFlags.DontSave](https://docs.unity.com/en-us/engine/6000.3/script-reference/unityengine/hideflags/dontsave)

**Dowód i scenariusz.** Start regionu z aktywnym pierścieniem klonuje materiał sektora zawierającego `_FAR_FACADE`. Wyjście do menu, gdy taki kafel nadal jest aktywny, prowadzi do `OnDestroy` bez `Clear(t)`. Kolejny start tworzy kolejne klony. Prześledziłem deklaracje właściciela i oba przebiegi zwalniania. Przyrost pamięci pozostaje `UNVERIFIED`.

**Poprawka.** Wyodrębnić zwalnianie `farClones` i wywołać je przy wyładowaniu kafla oraz w `OnDestroy`, również dla kafla startowego. Zweryfikować liczbę obiektów `Material` po powtarzanym wejściu w region i powrocie do menu.

### 5. Test wież ma stare wartości dla obu tierów

**Pliki** `tests/gis/test_embankment_pylons_s24.py:109`, `:114` i `tools/worldgen/streetscape/far_field.py:2415`. Kolejność `b116028eb` → `bb575a59b`.

**Dowód i scenariusz.** Uruchomiłem helper `pylon_primitive(tier, 0.0)` z implementacjami obu stron scaleń w pamięci. Liczba trójkątów Low/High to **38/222 → 26/222** w fali 12 oraz **26/222 → 24/150** przy przebudowie sylwetek. Asercja po fali 12 nadal oczekuje 26/222 na końcowej migawce. Polecenie `python -m pytest tests/gis/test_embankment_pylons_s24.py -k test_pylon_has_open_lattice_and_crossarms_in_every_tier` daje 8 niepowodzeń, po jednym na każdą parę tier i obrót.

**Poprawka.** Zaktualizować test do kontraktu ADR 0351, utrzymać limit trójkątów osobno dla tierów i sprawdzać liczbę oraz położenie ramion dla właściwej sylwety. Zostawić sprawdzanie geometrii przy wszystkich czterech obrotach.

### 6. Test zjazdu sprawdza stałą ogólną po wprowadzeniu specjalnego progu dla zjazdów

**Pliki** `tests/gis/test_buildings_r7.py:174` i `tools/worldgen/streetscape/plots.py:90`, `:947`. Scalenie `e85e4d60e` nad zmianami `e09173d47`.

**Dowód i scenariusz.** Odtworzyłem przypadek testu dla `e85e4d60e^1`, `e85e4d60e` i końcowej migawki. W dziewięciu środkowych stacjach zjazdu z kluczem `plot` wynik zmienia się **0,03 → 0,02 m**. `DROP_H_M` nadal wynosi 0,03 m, co daje jedno niepowodzenie w `test_kerb_drop_lowers_the_kerb_only_at_the_driveway`. Ścieżka dla zjazdu stosuje `DRIVEWAY_KERB_H_M`.

**Poprawka.** W istniejącym teście oczekiwać wartości dla zjazdu i sprawdzać rampę oraz zachowanie wysokości poza zjazdem. Oddzielny przypadek powinien potwierdzać respektowanie jawnego `h` dla przejścia.

Gotowa poprawka obu testów jest w commicie `c92a9912e` na `codex-gis-fix-s24`. Odczytałem oba pliki przez `git show` i wykonałem dziewięć zmienionych przypadków w pamięci z modułami z migawki `bfaccaf1a`. Wynik **9/9**. Właściwy przebieg pytest po integracji pozostaje do wykonania.

## Drobne

### 7. Kolejność przęseł wejściowych zmienia wybór podpór WN

**Plik** `tools/worldgen/streetscape/far_field.py:2299`, `:2320`, `:2357`. Scalenie `bb575a59b`.

Kolejność przęseł jest zachowywana w listach sąsiedztwa. Łańcuchy wychodzące z tego samego węzła mają identyczny klucz sortowania i konkurują o globalny odstęp w kolejności wejściowej.

**Dowód i scenariusz.** Dla `half=1024`, węzła ze znacznikiem szwu `(1100, 0)` oraz dwóch podpór `(1200, -10)` i `(1200, 10)`, odwrócenie dwóch przęseł wejściowych zmienia wybraną podporę z południowej na północną w obu tierach. Na 54 cache GIS odwrócenie `plan["spans"]` zmieniło zbiór podpór lub przęseł w **4 kaflach Low i 6 High**. W `bialystok-knyszynska` różnica symetryczna to odpowiednio 5 podpór i 5 przęseł oraz 7 podpór i 9 przęseł. Powtórzenie z tym samym porządkiem wejścia daje stabilny wynik.

**Poprawka.** Uporządkować sąsiedztwo i remisy całych łańcuchów przez stabilny klucz współrzędnych i identyfikatora podpory. Porównać zbiory eksportowanych podpór i przęseł dla permutacji tych samych danych wejściowych.

### 8. Porządek kluczy `young_species` wpływa na dobór gatunków

**Plik** `tools/worldgen/streetscape/tree_rows.py:420`. Scalenie `1665ec6e8`.

Ziarno jest stabilne, ale indeks zwrócony przez `rng.choice` jest interpretowany względem kolejności wstawiania kluczy mapy gatunków. Formatter YAML albo ponowne wygenerowanie mapy wag może zmienić gatunki przy tych samych wagach.

**Dowód i scenariusz.** Wywołałem `plan` dla autorskiego szpaleru `review` od `(0,60)` do `(600,60)`, równoległej drogi primary na `n=40`, `missing_share=0.8`, `replant_share=1` i domyślnych wag. Odwróciłem tylko kolejność kluczy `young_species`. Oba przebiegi dają 32 nasadzenia uzupełniające, a pierwsze trzy gatunki listy wynikowej zmieniają się z `maple, linden, birchyoung` na `birchyoung, linden, maple`. To test wejścia syntetycznego.

**Poprawka.** Zbudować listę gatunków w jednym kanonicznym porządku przed powiązaniem z wagami. Zastosować tę samą zasadę w starszej gałęzi `species` i dodać test równoważnych map z przestawionymi kluczami.

## Weryfikacja i dowody

| Sprawdzenie | Wynik |
|---|---|
| Obowiązkowe pliki `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py` | **62 przeszły**, 60,29 s |
| 21 plików `tests/gis/test_*.py` zmienionych w zakresie diffu | **289 przeszło, 9 niepowodzeń**, 119,33 s |
| Obliczenia i reprodukcje z punktów 1, 2, 5–8 | Wskazany Python 3.12.16, NumPy 2.5.4, Shapely 2.2.0, bieżący worktree w `PYTHONPATH` |
| Pętla jazdy oraz HUD | Analiza ścieżek Update/FixedUpdate, obsługi wejścia, wycieraczek, audio, instancji i HUD nie potwierdziła nowych stałych alokacji GC ani przeniesienia fizyki do Update. Alokacje w przebudowie buforów i materiałów sprawdzono osobno. Pomiar GC w playerze `UNVERIFIED`. |

Rozszerzony przebieg można powtórzyć z tego worktree na wskazanym interpreterze.

```powershell
$python = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a492e5af856a32ed3\tools\worldgen\.venv\Scripts\python.exe'
$env:PYTHONPATH = (Get-Location).Path
$tests = @(git diff --name-only 2d5744863^1 bfaccaf1a -- tests/gis | Where-Object { $_ -match '/test_.*\.py$' })
& $python -B -m pytest -p no:cacheprovider @tests
```

Obejrzałem istniejące PNG High dla clear i overcast. W DrivingLab po zmianie widać oba człony prawego mocowania we wszystkich trzech FOV. Na parze OFF/ON z playera #10 dla `dw671-tykocin-03` pojawiają się las i zabudowa przy horyzoncie w obu warunkach. To dowody autorów dla ich wersji, więc nie weryfikują obrazu końcowej migawki. [DrivingLab clear](../codex-mirror-right-s24/comparison-clear.png), [DrivingLab overcast](../codex-mirror-right-s24/comparison-overcast.png), [pierścień clear](../codex-farring-diag-s24/pairs/player__dw671-tykocin-03__edge-north__clear.png), [pierścień overcast](../codex-farring-diag-s24/pairs/player__dw671-tykocin-03__edge-north__overcast.png).

Zgodnie z zakresem nie uruchamiałem Unity, `build_world`, nowego importu ani visual-qa. Raport nie zawiera świeżego pomiaru FPS, GC, pamięci ani nowych renderów. Zmienione pliki na gałęzi recenzji to `STATUS.md` i niniejszy `REVIEW.md`.

## Wykaz porównanych scaleń

| SHA | Zakres |
|---|---|
| `2d5744863` | Weathering dachów i płotów, materiały, generatory i testy |
| `063deeef2` | Pierścień, streamer, warianty i testy |
| `143a56bae` | Kurtyny lasu, UV i importer krawędzi |
| `b116028eb` | Fala 12, cięcie LOD WN i testy |
| `4835292a0` | Wewnętrzne scalenie main do fields4, wspólne `far_field.py` |
| `10fa2e93e` | Plac Tykocina, generator pomnika, materiały i testy |
| `e552fd448` | Gatunki drzew, importer i `Vegetation.shader` |
| `a2c0ad80f` | Zabudowania gospodarcze, materiały i testy |
| `48a3c4a69` | Warianty chmur, warstwy szyby, generatory tekstur |
| `4945614c6` | Lusterka, naczepa, HUD, Blender i testy |
| `e09173d47` | Zjazdy, szew osi jezdni, roślinność pobocza i testy |
| `763f6fd25` | LOD koron, tiery i pokrycie w shaderze |
| `01a572a5a` | Pierwsza zmiana modeli drzew ogrodowych i testy |
| `1665ec6e8` | Szpalery, odnowienia i testy deterministyczności |
| `bb575a59b` | Sylwety wież, selekcja WN/SN i zanikanie przewodów |
| `4cf74778e` | Wsporniki luster, rozmiar RT, tiery i testy |
| `e85e4d60e` | Profile poboczy, krawężniki zjazdów i łaty |
| `c8ca07835` | Chmury przy horyzoncie, wybór kafla i streamer |
| `b5477ea44` | Plac Tykocina, drzwi stodół i testy |
| `e7b7dda26` | Prawe lusterko i testy układu/GC |
| `bb5befa1a` | Skrypty fali 14, kolejka i wznowienia |
| `7a677979a` | Druga zmiana drzew ogrodowych, UV1 i testy |
| `4705f7007` | Dopisek ADR 0354 z diagnostyką A/B |
| `762941c74` | Wycieraczki i pisk hamulca, HUD, wejście i audio |
| `6879771d5` | Generator wyposażenia deski |
| `e5e39f1dd` | Fala 13, pola r4, daleki las i testy |
| `157a114c2` | Impostory, rozmiar atlasu i wygaszanie kart |
| `34e92938a` | Dachy, kanały importu i warianty powierzchni |
| `382f569ce` | Geometria i patyna pomnika |
| `d50697692` | Reguły propów Low/Medium, LOD i cienie |
| `89a695549` | Zużycie znaków, dane instancji i shadery |
| `d15ca070e` | Binarny zasób nawigacji Krywlany i jego .meta |
| `fae4647eb` | Typy chodników, krawężniki i wspólny shader |
| `6f574c7b7` | Końcowe wpisy opt-in dachów i płotów dla DK65 |

## Następny krok dla lidera

W pierwszej kolejności rozszerzyć audyt WN na graf po redukcji LOD, sprawdzić diff `git show c92a9912e` i po zintegrowaniu poprawek powtórzyć GIS. Potem poprawić geometrię marginesu, ujednolicić przebiegi roślinności i sprawdzić cykl życia klonów materiałów w playerze. Raport można odczytać poleceniem `git show codex-review-day27-s24:artifacts/codex-review-day27-s24/REVIEW.md`.

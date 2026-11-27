# Poprawki generatorów przed falą 14

Gałąź `codex-gen-fix-s25`, baza `e8b5d5e8f` ze scalonym GIS s24. **224/224 testy przeszły** w 140,54 s. W tym komplet 62 testów budżetowych.

| Błąd | Poprawka | Przed → po | Testy i dowody |
|---|---|---|---|
| Samotne wieże WN po redukcji LOD | Eksport wież ograniczony do końców wybranych przęseł. QA zapisuje `tiers.Low.power_lod` i `tiers.High.power_lod`. Maszty mają osobną ścieżkę. | 54 cache, samotne wieże Low **23 → 0**, High **41 → 0**. Kafel C w audycie z cache ma 34 wieże i 31 przęseł Low oraz 61 wież i 54 przęsła High. | Łańcuch z drugim końcem poza zasięgiem w `test_hv_wires_0351.py`. [Baza](before.json), [wynik](after.json), [audyt C](audit-cache-c.json). |
| Karta brzegowa kukurydzy przecina maskę | Po transformacji sprawdzane są oba końce i komórki przecięte przez podstawę. Reguła obejmuje karty poprzeczne i pojedyncze rośliny na marginesie. | Pasy 1/3/5 m, karty z końcem w masce **13/1/1 → 0/0/0**. Wszystkie karty brzegu **7303/7245/7224 → 7290/7244/7223**. Największy ubytek to 0,18%. | `test_fields_r4_0334.py` sprawdza podstawy z rzeczywistych trójkątów oraz krótkie przecięcie narożnika komórki. [Pomiar](after.log), [21 testów pól](fields-pytest.log). |
| Kolejność przęseł zmienia topologię WN po LOD | Sąsiedztwo i remisy łańcuchów rozstrzyga klucz współrzędnych i identyfikatora podpory. Zachowano priorytet odległości i podpór szwu. | Kafle różniące się po odwróceniu wejścia, Low **4/54 → 0/54**, High **6/54 → 0/54**. | Permutacje i odwrócenie końców, także dwie podpory w tych samych współrzędnych. [Testy WN](hv-pytest.log), [wyniki dla kafli](after.json). |
| Porządek kluczy zmienia gatunki w szpalerach | `species` i `young_species` są sortowane przed powiązaniem z wagami. | Zmiana kolejności mapy wpływa na gatunki w **2/2 → 0/2** przypadkach. Pozycje, liczby i wysokości młodych nasadzeń są zgodne dla równoważnych map. | `test_treerows_0222.py` i `test_trees_0352.py`. [Przed](tree-rows-before.log), [26 testów po](tree-rows-after.log). |
| Test układu atlasu zakłada równe całkowite szerokości | ADR 0023. Atlas 4096 × 1024, dla `pineyoung` 2048 × 512. Granice sześciu widoków zgodne z `round(k · W / 6)`. Test zachowuje kontrole mapy normalnej, pokrycia, dylatacji koloru i widoczności nieba. | Dawne 683 × 6 = 4098 kolumn → **4096 kolumn**, z pełnym zakresem atlasu. | `test_world_v34.py::test_impostors_multi_view_and_lit`. [Testy atlasów i roślinności](impostors-pytest.log). |
| Limit liczby komponentów sosny po rebake | Maska alfy sprowadzona do 2048 × 512 przed progowaniem. Bramka na każdy widok ogranicza łączną powierzchnię odłączeń do 2% i największą wyspę do 1,25% pokrycia. | Komponenty źródłowe **37 → 403**. Przy rozdzielczości importu maks. powierzchnia odłączona **1,78% → 1,88%**, największa wyspa **0,70% → 1,02%**. | `test_vegetation_r2.py::test_shipping_pine_impostors_retain_branch_connections`. [Dane 18 widoków](pine-import-proxy.tsv), [PNG z odłączeniami](pine-view0-connectivity.png). |

## Koszt dalekiego planu

Pomiar w pamięci z wysokością brzegów z istniejących danych, tymi samymi funkcjami budowy siatki i 54 plikami `far_field_gis_cache.json`. Dotyczy części WN, która wyznacza zmianę liczby trójkątów całego dalekiego planu. Pozostała geometria korzysta z tych samych ścieżek generatora.

| Profil | Wieże WN | Przęsła grafu po LOD | Trójkąty WN | Podsiatki z WN |
|---|---:|---:|---:|---:|
| Low | 976 → 955 | 892 → 894 | 30 496 → 30 020 | 107 → 107 |
| High | 1424 → 1384 | 1283 → 1284 | 148 336 → 146 368 | 129 → 127 |

Liczba trójkątów łącznie spadła. Lokalne wzrosty po rozstrzygnięciu remisów to `bialystok-kleeberga` +36 Low i +114 High oraz `bialystok-knyszynska` +60 High. W 54 kaflach geometria WN nie weszła do żadnego nowego sektora, więc nie dodaje podsiatki. Rzeczywiste draw calle w playerze pozostają `UNVERIFIED`. Audyt mierzy topologię po selekcji i przed osobnym wygaszaniem geometrii przewodów. Stare raporty bez pomiaru LOD są w audycie oznaczone kreską. [Sektory przed/po](power-by-sector.json), [próba na starym raporcie](audit-legacy.log).

## Oględziny impostorów

Prawa strona porównania maski `pine_0`, widok 0, pokazuje drobne wyspy przy końcach korony zaznaczone na żółto. Główne konary pozostają połączone z pniem. Część odłączeń pozostaje przy 2048 × 512, więc wzrost liczby komponentów ma zarówno przyczynę rozdzielczościową, jak i mierzalny ślad w sylwecie. Pomiar używa filtra BOX 2:1 dla rebake i bilinearnego powiększenia starego atlasu jako przybliżeń rozmiaru importu przed kompresją DXT5. Kontrolna symulacja otwarcia maski 3 × 3 w tym rozmiarze odłącza do 31,22% korony i daje największą wyspę 15,74%. Przekracza oba limity. Obejrzano archiwalne porównania High przed/po rebake w obu warunkach oświetlenia. [Analiza maski](pine-view0-connectivity.png), [clear](archived-pine-high-clear.png), [overcast](archived-pine-high-overcast.png), [dziennik pomiaru](pine-diagnostics.log).

## Zmienione pliki i przekazanie

- Generatory i audyt: `tools/worldgen/streetscape/far_field.py`, `field_crops.py`, `tree_rows.py`, `tools/worldgen/qa/hv_wires_audit.py`.
- Testy: `tests/gis/test_hv_wires_0351.py`, `test_fields_r4_0334.py`, `test_treerows_0222.py`, `test_world_v34.py`, `test_vegetation_r2.py`.
- Raport i stan: `WYNIKI.md`, `STATUS.md`. Przebieg obejmował 13 wskazanych plików, w tym cztery bramki budżetowe, testy dalekiego planu, wież, pól, szpalerów i impostorów. [Log](targeted.log), [JUnit XML](targeted.xml).

Zadanie obejmowało tylko Pythona. Świeży visual-qa High clear/overcast, import, regeneracja kafli i pełny GIS pozostają do wykonania w fali 14. Danych w `Data/Regions/*/generated` i `Data/raw/derived` nie zapisywano.

Lider może zacząć od `git diff --stat e8b5d5e8f..codex-gen-fix-s25`. Po integracji zastosować kolejkę opisaną w `artifacts/regen-wave-14-s24/README.md`, zweryfikować nowy `power_lod` dla obu tierów i obejrzeć świeże kadry High clear/overcast.

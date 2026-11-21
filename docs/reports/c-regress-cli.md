# Regresje kafla C — c-regress-cli

Baza: `83345868e` (origin/main przy starcie; różnica od `e16a5e240` wyłącznie HANDOVER).
Zakres: tylko ten worktree, bez Unity i bez przebudów innych kafli. Wejścia raw są współdzielone tylko do odczytu; wyniki derived C są prywatną kopią.

## Wynik wejściowy

Dostarczony `pytest-wave5.log`: **28 failed, 2779 passed, 4 skipped, 2 xfailed**, 3398,15 s.
To historyczny wynik bazowy, nie ponowne uruchomienie przed zmianami w tym worktree.

## Diagnozy i poprawki

| Objaw | Przyczyna z historii i kodu | Poprawka |
|---|---|---|
| 12 wolnych końców barier mostowych | `34ad24ea3`, `tools/worldgen/streetscape/furniture.py:2451`, maska `kw >= 0.90`, następnie wyzerowanie mostowych stacji; kapa przy przyczółku zwęża się poniżej 0,90 m | Warunek obecności bariery zgodny z aktywną kapą meshing: 0,30 m; test ciągłości przez oba przyczółki |
| Brak `andersa-se-ramp-median-barrier` | `a207f2cd4`, `tools/worldgen/streetscape/furniture.py:2058` / `_clip_rails_to_pavement`: ślad authored przed poszerzeniem jest zbyt blisko finalnej jezdni, więc znika cały bieg | Ograniczone dopasowanie śladu do obwiedni finalnej jezdni przed łączeniem i przycinaniem; finalny test całych segmentów nadal obowiązuje |
| Low far-field 67 421 > 30 000; skyline 3174 > 3000 | `bd8af626a`/`3a3719771`: 190 pylonów po 204 tris także Low; `33db1f4cf`: zamknięte dachy/pasy z pozostawionymi detalami Low | `tools/worldgen/streetscape/far_field.py:1355,1681`, ADR 0318: Low 32 tris/pylon, zachowane otwory i wszystkie pylony; dobór małych dalekich kopert po rozmiarze, nadbudówki High, pominięcie niewidocznych ścian kominów; budżety bez zmian |
| Szerokość hero bridge 11,37 > 10,6 | D94 + bufor kapy 0,30 m `34ad24ea3`; test nadal zakładał starą całkowitą szerokość | `tests/gis/test_hero_bridge.py:70`: asercja kapy względem faktycznych krawędzi jezdni `lg/rg`, jawnego bufora i authored cap_w=1,0; tolerancja tylko na zapis współrzędnych do 1 mm |
| Stare kolizje kapy: 8 testów | Test czytał przypadki z regenerowanego QA i próbował odtwarzać starą kolizję przez samo `kind=URBAN`, przy zachowaniu nowych ograniczeń | `tests/gis/test_bridge_clearance.py:124`: historyczne punkty zapisane jako świadkowie z commitami źródłowymi; wszystkie muszą klasyfikować się jako jezdnia; syntetyczne testy nadal sprawdzają całe powierzchnie i bariery |
| Ogrody/plots | `5be3ad38e`, stage: do starego licznika `inst_trees_kept` doliczano nowe korony High ADR 0308 | `tools/worldgen/streetscape/stage.py:428`: rozdzielono raportowanie starych instancji i nowych koron, nie wyłączając roślinności |
| Rest szlabanu poza wysepką | D94 przesuwa nos mediany w poszerzający się odcinek wyjazdu; stały szlaban LP.BOOM_L przestaje dosięgać stripu | `tools/worldgen/streetscape/gate.py:386`: wybór najbliższego pasującego przekroju według finalnych szerokości i faktycznej długości sprzętu, z marginesem pod stopę |
| Uskok profilu 0,033 m przy s=275 | Stary błąd `1bcd7ddd9`, `PatchHeight.blend`: waga wpływu jezdni zanika do 0 przy out=0,5 m, po czym przeskakuje na niezerowe IDW; D94 zmieniło położenie próbek | `tools/worldgen/roads/meshing.py:1058`: wspólne tło IDW i płynnie dodawany wpływ jezdni; crossfall poza jezdnią ograniczony do jej krawędzi; regresja ciągłości wartości i pochodnej |
| Jeroniki → DK65-01 0,375 m | D94: na jednym kaflu w305447699 10,45 m, na drugim 9,95 m; authored lane_edges wyłącza seam taper, link nie pobierał końca poprzednika | `head_from: link:jeroniki-dk8-to-s8`, regeneracja tylko link metadata; pomiar po zmianie 0,0 m, route_start nie zmieniono |
| Determinism | `41293d95c`/`9b4fbba31`: sesyjny fixture world tworzył geometrię pomiarową 0, CLI generuje D94 0,25 | `tests/gis/test_world_roads.py:83`: fixture świata jawnie używa konfiguracji CLI podczas build; pozostałe fixture pomiarowe zachowują własny kontrakt |
| Separator DK8 1,23 > 1,0 m | Bufor kapy `34ad24ea3` odsunął końce deck od dwóch authored końców przypiętych przez `free_ends: false`; ogólny join celowo je pomijał | `tools/worldgen/streetscape/furniture.py:2152`: dopasowanie wyłącznie do końca deck o zgodnej stycznej i poziomie, bez łączenia z drugim authored separatorem; końcowy clipping nadal aktywny |
| Filar 2,49 < 2,5 m | `45a9fe467`, QA `_footprint` zakładało prostokąt, rzeczywisty underdeck collider to ośmiokąt ze ścięciem 0,25 m (nie boxed collider osobnego hero assetu) | `tools/worldgen/qa/check_piers_vs_roads.py:98` i `streetscape/hero_bridge.py:488`: wspólna geometria generatora/collidera/QA. Ten sam punkt i stacja: 2,494704 → 2,643306 m, globalne minimum 2,59 m. Próg bez zmian |
| Pasy zieleni ponad ratchetem | D94 zmieniło geometrię narożników; niezależne ograniczanie promieniem gwałtownie obracało krawędź skarpy i zapadał się jej poprzeczny zasięg | `tools/worldgen/roads/meshing.py:266`: dwustronnie wygładzana obwiednia ograniczenia promienia (przejście szerokości 1:4, WORKING_VALUE), tylko redukcja rozpiętości. 1666 emisji na rzeczywistym HF: 270 → 32 stromych trójkątów, 52238 → 52154 tris łącznie, bez usuwania powierzchni |
| `marking_off_carriageway` 4 > 3 | `ad6f732d2` dodał krawędź GP z jednym pasem, ujawniając błąd `a721521fe` klasyfikatora: niższa trawa sąsiedniej drogi wygrywała z asfaltem w oknie ±0,8 m; używano średniej wysokości trójkąta | `tools/worldgen/roads/consistency.py:116`: interpolacja wysokości w rzeczywistym punkcie i pierwszeństwo przeszkody tylko na/ponad jezdnią. Punkt E983,06/N−934,05: asfalt 138,778988, trawa 138,534454 m (poniżej o 0,244534 m). Zachowane DZ_M i ratchety |
| Zebry, węzły 2882674819 / 2882674820 | D94 poszerzył nominalny przekrój w nierównoległym wlocie; zewnętrzny pasek/kwadrat trafiał na krawężnik ze skokiem 0,14 m, odrzucając całe przejście | `tools/worldgen/roads/markings.py:930`: obcięcie wyłącznie zewnętrznych kolizyjnych elementów; wewnętrzna przeszkoda nadal odrzuca całość, P11 ma wspólny ciągły zakres obu rzędów. Replay rzeczywisty: oba False → True, P10 7 pasków / 112 tris, P11 14 kwadratów / 28 tris |
| Typology C / Dojlidy | `c1f535291` (ADR 0316): nowe pokrycia dachów zmieniają hash liczby trójkątów per materiał, C używa dodatkowego `roof_karp_red`; nie zmieniły geometrii | `tests/gis/test_typology_0238.py:316` i pliki baseline: dokładnie 12 domów Dojlidy / 16 C. Wyłączenie `roof_variant` odtwarza stare hashe wszystkich tych domów; pozostałe wpisy nietknięte. Jawna lista dopuszczonych nazw materiałów, budżety tris/kamer bez zmian. C harness 958445/99502 tris pozostał identyczny |

## Weryfikacja przed przebudową

Testy celowane: bridge_clearance 23 passed; patch/hero 8 passed; filary i regresje barier 16 passed; typology 4 passed; pylony/embankment 19 passed + 32 widoki z rogów; dodatkowe far-field 6 passed; crossing/verge 7 passed; klasyfikacja powierzchni 6 passed.
`pytest -m unit` przed przebudową: 3 failed, 187 passed, 1 skipped, 2634 deselected, 1 xfailed. Trzy porażki czytają stare `guardrail_runs` (12 końców i brak median barrier), więc wymagają przebudowy.

## Odtworzenie i dowody

Analiza: historia `git log -p`/`git show` i `git blame`, następnie numeryczne replaye geometrii; bez pełnego bisect z wielokrotnymi przebudowami kafli. Wybrane patche i SHA w `artifacts/c-regress-cli/history-*.patch` oraz `history-summary.txt`.
Przebudowa C na `ba7332f8d`: skrypt `artifacts/c-regress-cli/build-c.ps1`, slot heavy, log `build-c.log`, znaczniki czasu i exit obok.
Pylony obejrzane offline: `pylons-low-before-after.png`, `pylons-owner-views.png`, skrypt `preview_pylons.py`. Widok boczny spoza kafla właściciela może być krawędziowy; 32 regresje sprawdzają widoczność z każdego rogu właściciela. Bez Unity na wyraźne polecenie użytkownika; to nie jest ocena obrazu w grze.

Pełny wynik po przebudowie będzie uzupełniony po zakończeniu pytest.

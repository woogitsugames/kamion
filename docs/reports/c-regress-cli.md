# Regresje kafla C — c-regress-cli

Baza: `83345868e` (origin/main przy starcie; różnica od `e16a5e240` wyłącznie HANDOVER).
Zakres: tylko ten worktree, bez Unity i bez przebudów innych kafli. Wejścia raw są współdzielone tylko do odczytu; wyniki derived C są prywatną kopią.

## Wynik wejściowy

Dostarczony `pytest-wave5.log`: **28 failed, 2779 passed, 4 skipped, 2 xfailed**, 3398,15 s.
To historyczny wynik bazowy, nie ponowne uruchomienie przed zmianami w tym worktree.

## Diagnozy i poprawki

| Objaw | Przyczyna z historii i kodu | Poprawka |
|---|---|---|
| 12 wolnych końców barier mostowych | `34ad24ea3`, `furniture.py`, maska `kw >= 0.90`, następnie wyzerowanie mostowych stacji; kapa przy przyczółku zwęża się poniżej 0,90 m | Warunek obecności bariery zgodny z aktywną kapą meshing: 0,30 m; test ciągłości przez oba przyczółki |
| Brak `andersa-se-ramp-median-barrier` | `a207f2cd4`, `_clip_rails_to_pavement`: ślad authored przed poszerzeniem jest zbyt blisko finalnej jezdni, więc znika cały bieg | Ograniczone dopasowanie śladu do obwiedni finalnej jezdni przed łączeniem i przycinaniem; finalny test całych segmentów nadal obowiązuje |
| Low far-field 67 421 > 30 000; skyline 3174 > 3000 | `bd8af626a`/`3a3719771`: 190 pylonów po 204 tris także Low; `33db1f4cf`: zamknięte dachy/pasy z pozostawionymi detalami Low | ADR 0318: Low 32 tris/pylon, zachowane otwory i wszystkie pylony; dobór małych dalekich kopert po rozmiarze, nadbudówki High, pominięcie niewidocznych ścian kominów; budżety bez zmian |
| Szerokość hero bridge 11,37 > 10,6 | D94 + bufor kapy 0,30 m `34ad24ea3`; test nadal zakładał starą całkowitą szerokość | Asercja kapy względem faktycznych krawędzi jezdni `lg/rg`, jawnego bufora i authored cap_w=1,0; tolerancja tylko na zapis współrzędnych do 1 mm |
| Stare kolizje kapy: 8 testów | Test czytał przypadki z regenerowanego QA i próbował odtwarzać starą kolizję przez samo `kind=URBAN`, przy zachowaniu nowych ograniczeń | Historyczne punkty zapisane jako świadkowie z commitami źródłowymi; wszystkie muszą klasyfikować się jako jezdnia; syntetyczne testy nadal sprawdzają całe powierzchnie i bariery |
| Ogrody/plots | `5be3ad38e`, stage: do starego licznika `inst_trees_kept` doliczano nowe korony High ADR 0308 | Rozdzielono raportowanie starych instancji i nowych koron, nie wyłączając roślinności |
| Rest szlabanu poza wysepką | D94 przesuwa nos mediany w poszerzający się odcinek wyjazdu; stały szlaban LP.BOOM_L przestaje dosięgać stripu | Wybór najbliższego pasującego przekroju według finalnych szerokości i faktycznej długości sprzętu, z marginesem pod stopę |
| Uskok profilu 0,033 m przy s=275 | Stary błąd `1bcd7ddd9`, `PatchHeight.blend`: waga wpływu jezdni zanika do 0 przy out=0,5 m, po czym przeskakuje na niezerowe IDW; D94 zmieniło położenie próbek | Wspólne tło IDW i płynnie dodawany wpływ jezdni; crossfall poza jezdnią ograniczony do jej krawędzi; regresja ciągłości wartości i pochodnej |
| Jeroniki → DK65-01 0,375 m | D94: na jednym kaflu w305447699 10,45 m, na drugim 9,95 m; authored lane_edges wyłącza seam taper, link nie pobierał końca poprzednika | `head_from: link:jeroniki-dk8-to-s8`, regeneracja tylko link metadata; pomiar po zmianie 0,0 m, route_start nie zmieniono |
| Determinism | `41293d95c`/`9b4fbba31`: sesyjny fixture world tworzył geometrię pomiarową 0, CLI generuje D94 0,25 | Fixture świata jawnie używa konfiguracji CLI podczas build; pozostałe fixture pomiarowe zachowują własny kontrakt |

Pozostałe pozycje i wyniki końcowe zostaną uzupełnione po przebudowie i pełnym pytest.

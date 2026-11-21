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


## Dokończenie (Claude, 2026-11-21, po limicie Codexa)

Przebudowa C na `ba7332f8d` (Codex) dała `deck_run_ends_free` 7 (było 12): poprawka progu kapy 0,30 m usunęła tylko 5 końców. Testy CI `tests/gis/test_barrier_ends.py:102` i `tests/gis/test_barriers_0159.py:113` (REGION_ID = C) padały na main z tej samej przyczyny — dane C fali 5. Replay etapu barier na rzeczywistym świecie (`artifacts/c-regress-cli/real-road-world.pkl`) pokazał trzy niezależne przyczyny:

| Objaw | Przyczyna plik:linia | Poprawka |
|---|---|---|
| 5 końców: przejście deck->approach ucięte 0,09–0,43 m od nawierzchni | `a207f2cd4` (ADR 0310), `tools/worldgen/streetscape/furniture.py` `_clip_rails_to_pavement` + `roads/surface_safety.py:carriageway`: utwardzone pobocze z profilu bocznego (`<chain>:<side>:<k>`, `road_asphalt`) liczone jako jezdnia; linia słupków reguły stoi z założenia 0,25 m za nim (ADR 0272, `rural_barrier_line`), więc każde przejście przy poboczu było cięte. Dane C nie były przebudowane między ADR 0310 a falą 5, stąd ujawnienie dopiero teraz | `surface_safety.py:40` `own_shoulder()`: run reguły nie jest sprawdzany względem utwardzonego pobocza **tej samej strony tego samego łańcucha**; pasy ruchu łańcucha, inne łańcuchy, pobocza drugiej strony i bariery authored/podpór zachowują pełny bufor 0,47 m. Zmiana zamierzona w kontrakcie ADR 0310 — test kafli `test_drive_s24_surface_safety.py:118` stosuje ten sam wyjątek; nowy test jednostkowy `test_c_barrier_regressions.py` (pobocze własne vs druga strona / inny łańcuch / authored / pasy) |
| 1 koniec: w177895177 L przy E 426 N −649 urwany 1,0 m pod barierą sąsiedniego pomostu | `furniture.py:_dedup_guardrail` (ADR 0100/0110) dedup tylko w planie; po buforze kapy ADR 0317 krawędzie dwóch pomostów (w177895177 / w175157461, różnica wysokości 1,0 m) zbliżyły się do 0,02 m i niższa bariera była cięta i doprowadzana do wyższej | `furniture.py:1837–1880` `_keep_other_level`: duplikat tylko przy |dz| ≤ 0,8 m (`GUARDRAIL_DEDUP_DZ` = `barrier_audit.FREE_END_DZ`); zbudowane runy zapisywane z Z; linie bez Z (podpory) po staremu |
| przejście w173956078 R przy E −731 N 49 ucięte (0,41 m od pasów bliźniaczej jezdni w173956079) | D94: obie jezdnie poszerzone ku sobie | `furniture.py:2106` ograniczone dopasowanie runów reguły do obwiedni (max 0,25 m, `RULE_RAIL_FIT_MAX_M` WORKING_VALUE; tu 0,06 m). Replay: `rule_pavement_fit_pts` 7, `pavement_cut_segments` 57 → 2 |

Replay po trzech zmianach: 7 → **1** wolny koniec. Pozostały: w173956078 R, E −749,2 N 50,7 — 12-metrowy pomost, którego kapa zwęża się do 0,145 m przez odstęp kapy od bliźniaczej jezdni (`BRIDGE_CLEAR_M`); między jezdniami po D94 zostaje 1,15–1,65 m, więc bariera nie mieści się w buforze ADR 0310 po żadnej stronie. To nie jest błąd kodu do załatania progiem — **decyzja lidera**: wspólna bariera środkowa między bliźniaczymi pomostami (jedna linia dla obu jezdni) albo świadome zakończenie barier przed obiektem. Nie podnosiłem progów ani nie wyłączałem audytu.

### Pytest po przebudowie C na 80718647d (dane ad4062d25)

`uv run --project tools/worldgen pytest tests/gis -q`: **5 failed, 2857 passed, 6 skipped, 2 xfailed** w 3879 s (przed: 28 failed / 2779 passed, `pytest-wave5.log`). Log: `artifacts/c-regress-cli/pytest-after.log`.

| Porażka | Przyczyna | Działanie |
|---|---|---|
| `test_barrier_ends.py:102`, `test_barriers_0159.py:113` | 1 wolny koniec w173956078 R (E −749,2 N 50,7), brak miejsca po D94 — opis wyżej | decyzja lidera, bez zmiany progu |
| `test_depot_yard.py:150` rest_on_strip exit | poprawka Codexa `gate.py:386` szacowała zasięg ramienia wzorem 2·hw ≤ 4,8 m; pominięte: poszerzanie wyjazdu między obudową a podporą (2,38 → 2,42 m), skos ramienia (lat 2,691 zamiast 2,77 m) i krawężnik w roads_poly; podpora 0,03 m przed wnętrzem pasa | `gate.py` `_boom_rest`/`_rest_clear`: wybór stacji po faktycznym punkcie podpory (|lat| ≥ hw(s podpory) + krawężnik + 0,20 m, WORKING_VALUE). Replay: stacja 18,0 → 17,0 m, lat 2,741 m przy wymaganych 2,716 m |
| `test_world_roads.py:202` krzywizna profilu 0,0066765 > 1/150 | fixture `world` od `d7e2912fc` (Codex, dla determinizmu) buduje geometrię CLI z D94, a test miał tolerancję 1e-6 zamiast akceptacji generatora `roads/profile.py:111` (k > kmax·1,002) | test używa tej samej tolerancji 1,002 (`PROFILE_KMAX_TOL`) — zmiana zamierzona, generator nie zmieniony |
| `test_world_roads.py:212` szerokość 7,5 ≠ 7,0 | ta sama zmiana fixture: D94 dodaje do authored 7,0 m raz `gameplay_widen_m` = 0,5 m | test sprawdza bazową szerokość authored (`width − gameplay_widen_m` = 7,0) |

Pełny wynik po przebudowie będzie uzupełniony po zakończeniu pytest.

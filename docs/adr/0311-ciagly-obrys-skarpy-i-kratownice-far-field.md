# ADR 0311 — Ciągły obrys skarpy i ażurowe pylony far-field

Status: przyjęte w generatorze; kontrola playera po regeneracji pozostaje otwarta.
Data: 2026-11-20. Zakres: drive-review-s24, P3 #13 i #15.

Teren przy drodze jest już próbkowany co 1 m. Źródłem schodków jest również
konformowanie względem zrasteryzowanej maski: EDT mierzy odległość od węzła
wewnątrz nawierzchni zamiast od rzeczywistej krawędzi. Ukośna droga przenosi
w ten sposób zęby rastra do skarpy. Dalsze filtrowanie Gaussa z maską zakopanej
nawierzchni ponownie wprowadza ten wzór i twarde granice pasma filtrowania.

Decyzja: dla produkcyjnego konformowania mierzymy odległość do odcinków
wektorowego obrysu drogi, powierzchni utwardzonych i działek w pasie 16 m.
STRtree ogranicza wyszukiwanie do pobliskich odcinków; zapytania są porcjowane
po 65 536 punktów. Przedłużenie wysokości krawędzi interpolujemy filtrem sigma
0,8 m. Ostatnie 4 m pasa płynnie wracają do dotychczasowej metryki rastra.
Parametry są WORKING_VALUE. Zachowujemy maskę nawierzchni, spadek projektowy,
obniżenie terenu pod drogą i geometrię jezdni. `tidy` nadal wyrównuje zamknięte
wysepki, ale nie filtruje ponownie ciągłej skarpy. Wywołania bez obrysu
zachowują wcześniejszą ścieżkę. Nie zwiększamy liczby trójkątów terenu;
istniejący pas siatki 1 m w importerze High pozostaje w użyciu.

Pylony tła miały pełny trzon z dwóch skrzyżowanych płaszczyzn. Zastępujemy
go czterema nogami, trzema panelami naprzemiennych przekątnych i poziomych
belek oraz dwoma podpartymi poprzecznikami. Pręty to niezamknięte graniastosłupy
trójkątne. Każdy słup ma 204 trójkąty zamiast 12, dla obu tierów. Promienie
prętów i podział paneli są WORKING_VALUE dla czytelności dalekiej sylwetki,
bez deklarowania odwzorowania konkretnego typu słupa. Materiał, sektory,
foreshortening i odsiew Low pozostają dotychczasowe. Brak nowych tekstur,
zasobów zewnętrznych i dodatkowych submeshy.

Konsekwencje: bez wzrostu geometrii terenu, dodatkowe wyszukiwanie obrysu
w generatorze; maksymalnie +192 trójkąty na widoczny pylon. Dla 179 pylonów
w QA dw671-tykocin-09 daje to górną granicę +34 368 trójkątów (przed odsiewem).
FPS i wygląd przełączeń LOD wymagają osobnego przejazdu. Testy obejmują
końcowy profil skarpy, niezmienność rzeczywistej jezdni DK65-10 oraz otwory
w sylwetce pylonu. Podgląd offline nie zastępuje renderu Unity.

## Dopisek props-fix-s24 (26.11, agent `agent-a60f5c7ffe98fe7c7`): smuga tekstury na skarpie (krytyka s24 fala 11, pkt 9)
**Objaw.** `tykocin/High-clear/route-s0160` (x 1050-1750, y 600-1080; krytyk podal kafel `dw671-tykocin-03`, ale `route-s0160`
jest w `tykocin`): oliwkowo-brazowa, ukosna wstega na skarpie przy krawezniku.
**Hipoteza 1 - ODRZUCONA (zmierzona).** 99,9 % z 262 520 stromych trojkatow `terrain_lod0` `tykocin` ma wektor normalny w gore, wiec
`WorldPBR` rzutowalby je z gory. Poprawka shadera (rzut z normalnej geometrycznej) wyrenderowana na tej samej kamerze:
smuga bez zmian - cofnieta. Skirty chunkow sa niewidoczne, a skarpa ma nachylenie <= 8,4 deg (`dw671-tykocin-03` przy s0157).
**Przyczyna (zmierzona na GLB).** W `terrain_lod0` leza trojkaty-drzazgi o krawedziach 44-92 m i 1 m (np. `tykocin` chunk 0_6:
92 / 92 / 1 m, 26 sztuk; chunk 0_7: 44 m, 71 sztuk): to paski trawnika za krawezniem (`roads.meshing._emit_verge`, `:vg`) wlaczane
do terenu przez `merge_verge_into_terrain`. COLOR_0 (maski gruntu) probkowane jest tylko w wierzcholkach, czyli na koncach
40-90 m paska, a interpolacja liniowa rozmywa je w ukosna wstege (UV terenu i tak = XZ w metrach, nie jest rozciagane).
**Decyzja.** `build_world.subdivide_long_edges`: kazdy trojkat paska o najdluzszej krawedzi > `VERGE_MAX_EDGE_M = 3 m` jest dzielony w
polowie tej krawedzi (wspolne krawedzie = wspolny punkt, bez T-spoin), az zadna krawedz nie przekracza 3 m; wysokosci i normalne
interpolowane liniowo, wiec powierzchnia sie nie zmienia, a maski czytane sa co <= 3 m. Test:
`test_verge_strip_triangles_are_split_so_ground_masks_are_sampled_every_3_m`.
**Poza zakresem:** `WorldSurface.shader` (tier Low) bez zmian; problem jest w danych, wiec dotyczy obu shaderow.

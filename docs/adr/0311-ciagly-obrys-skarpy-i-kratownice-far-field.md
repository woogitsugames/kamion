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
**Objaw.** `tykocin/High-clear/route-s0160` (x 1050–1750, y 600–1080, krytyk podał kafel `dw671-tykocin-03`, ale ujęcie
`route-s0160` jest w `tykocin`): oliwkowo-brązowa, rozciągnięta ukośna smuga na skarpie przy krawężniku.
**Przyczyna (zmierzona na GLB `tykocin`, `terrain_lod0`, 8 675 570 trójkątów).** 262 520 trójkątów (3,0 %) ma normalną
geometryczną z `|n.y| < 0,6` (uskoki przy jezdni, wcięcia drogi, skirty chunków), a **262 192 z nich (99,9 %) ma uśredniony
wektor normalny skierowany w górę** (`n.y > 0,8`; 8 998 z 64 067 trójkątów o `0,6 ≤ |n.y| < 0,9` też). `WorldPBR.shader`
wybierał oś rzutu świata z interpolowanej normalnej wierzchołkowej (`|n.y| ≥ 0,7` → płaszczyzna XZ), więc prawie pionowy pasek
dostawał rzut z góry: jeden rząd tekseli rozciągnięty wzdłuż paska. To nie jest błąd UV (UV terenu = XZ w metrach) ani
nachylenie skarpy (maks. 8,4° na `dw671-tykocin-03` przy kamerze s0157).
**Decyzja.** W wariancie terenu (`_GROUNDMASKS`) oś rzutu i ramka styczna (`T`, `B`) wynikają z **normalnej geometrycznej**
(`cross(ddy(pw), ddx(pw))`, dokładna dla płaskiego trójkąta); oświetlenie nadal z normalnej wierzchołkowej (skirty i uskoki
świecą jak grunt, jak dotąd). Drogi, rekwizyty, dekale i budynki bez zmian (ten sam kod, słowo kluczowe nieaktywne).
Koszt: 1 `cross` + 1 `length` na piksel terenu, 0 próbek tekstur. Nie zmieniono geometrii ani normalnych (zmiana normalnych
przestawiłaby oświetlenie wszystkich spadków).
**Poza zakresem (do właściciela `Rendering/Shaders`):** `WorldSurface.shader` (tier Low) ma tę samą `ProjectUV(pw, n)` z normalną
wierzchołkową — ten sam defekt może występować na Low; nie ruszany (katalog nie jest mój).

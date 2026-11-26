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

## Dopisek props-fix-s24 (26.11, agent `agent-a60f5c7ffe98fe7c7`): smuga tekstury na skarpie (krytyka s24 fala 11, pkt 9) - NIEROZWIAZANE
**Objaw.** `tykocin/High-clear/route-s0160` (x 1050-1750, y 600-1080; krytyk podal kafel `dw671-tykocin-03`, ale `route-s0160`
jest w `tykocin`): oliwkowo-brazowa, ukosna wstega na skarpie przy krawezniku (crop: `artifacts/props-fix-s24/after2/bank-crop.png`).
**Hipotezy sprawdzone i ODRZUCONE (kazda: zmiana + import Win64 + ten sam render, wstega bez zmian):**
1. Rzut tekstury z normalnej wierzcholkowej: 99,9 % z 262 520 stromych trojkatow `terrain_lod0` `tykocin` ma wektor normalny w gore, ale
   poprawka `WorldPBR` (rzut z normalnej geometrycznej) nic nie zmienila - cofnieta.
2. Trojkaty-drzazgi paskow trawnika (`merge_verge_into_terrain`, krawedzie 44-92 m, COLOR_0 tylko na koncach): dzielenie krawedzi > 3 m
   usunelo je z GLB (skan: 0 drzazg w `terrain_lod0`), wstega zostala - cofniete.
3. Nie jest to karta `verge_flora` (manifest `tykocin`: 0 kart) ani nachylenie (skarpa <= 8,4 deg).
**Stan:** przyczyna nieustalona. Nastepny krok (nie wykonany): zrzut debug tego ujecia z wymuszonym kolorem per material / per primitive
(`terrain_lod0` vs `road` `verge_grass` vs `curb`), zeby zobaczyc, ktora siatka rysuje wstege; podejrzane: pas `back-of-sidewalk batter`
i maska `COLOR_0` (R = odleglosc od drogi, B = nieskoszona) przy obrysie drogi `ditch_colours`/`conform`.

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

## Dopisek bank-smear-s24 (26.11): smuga na skarpie `tykocin/route_s0160` - przyczyna ustalona, poprawka czesciowa
**Render diagnostyczny** (`KAMION_QA_DIAG` w `VisualQaRunner`, nowe tryby: `colorby:renderer|material|slot` = plaski kolor per
klucz + legenda `<kamera>_colorby.txt`; `colorby:prim` = kolor per trojkat, `vcol`/`vcolb` = COLOR_0, `nrm` = |n.y| normalnej
wierzcholkowej vs geometrycznej, `wpos` = rampy E/N/wysokosci; `mat:<prop>=v`, `noshadows`; shader
`Editor/VisualQA/DiagPrimitive.shader`, tylko edytor). Smuge rysuje **`terrain_band` / `M_terrain_grass` (WorldPBR)** - nie decal,
latka, banks ani far field.
**Geometria jest poprawna.** Pasmo High to siatka 1 m budowana w imporcie (`WorldMeshBake.TerrainBand`, max wysokosci w wezle
siatki); wierzcholki paskow trawnika spoza siatki (`merge_verge_into_terrain`) do High w ogole nie trafiaja - dlatego dzielenie
ich krawedzi (hipoteza 2) niczego nie zmienilo. Skarpa nasypu ma 33 deg (0,65 m/m): krawednik 108,7 m, dno rowu 105,5 m
(hipoteza 3 "<= 8,4 deg" byla bledna).
**Przyczyna.** Kamera (oko 2,5 m nad jezdnia) widzi te skarpe prawie stycznie (`wpos`: 3-5 m skarpy w kilku pikselach w poprzek;
`prim`: pas trojkatow widzianych krawedzia). Slad tekstury planarnej jest 15-100x dluzszy niz szeroki, ponad anizotropie samplera
(PC High 8x), wiec kafel trawy rozmazuje sie w smugi wzdluz skarpy. Rzut z normalnych wierzcholkowych **nie** jest przyczyna
(`nrm`: normalna wierzcholkowa i geometryczna wybieraja ten sam rzut w calym kadrze) - zatem `WorldSurface.shader` (Low) bez
zmian; Low tego pasa nie pokazuje (`after5/Low-normal`). Druga wada przy okazji: mapa Var zestawu `grass_verge` (B = pokrycie gola
ziemia) byla bez mipmap i z filtrem point, a refill `_GRASS_DETILE` czyta ja samplerem BaseColor - przy stycznym widoku refill
wlaczal sie w aliasowanych pasach (`mat:_AlbedoScale=0`: zielona wstega przed, brak po).
**Poprawka.** (1) `WorldPbrMaterials`: Var zestawow trawy (`slots` z terrain_grass / verge_grass / plot_lawn) z mipmapami (box) i
filtrem trilinear; Var paving/asfaltu bez zmian (kanaly id/spoina czytane LOD 0 samplerem point); +1/3 pamieci jednej tekstury.
(2) `WorldPBR` (`_GRASS_DETILE`): na fasetach nachylonych (geometryczne n.y 0,98 -> 0,88) przy sladzie 4 -> 12x dluzszym niz
szerokim kafel jest czytany drugi raz z izotropowym sladem (`SAMPLE_TEXTURE2D_GRAD`, os dluga na obu osiach); z tej probki tylko
luminancja na skalibrowanym kolorze darni `_GrassFill`, normal/AO/gladkosc do plaskich/sredniej kafla. Plaski teren bez zmian.
+2 probki tylko w tej galezi, 0 draw calli (route_s0160 drawsEst 780 przed i po). Progi WORKING_VALUE (ocena na renderze).
**Efekt** (Win64 High clear, `artifacts/bank-smear-s24/sbs/`): smugi wzdluz skarpy wyraznie slabsze, pas gladszy i w tonie skarpy;
roznice tylko w pasie stycznym (mapa roznic), 4 inne kamery `tykocin` RMSE <= 0,0004. **Otwarte:** cienka zielonkawa linia w miejscu
stycznosci zostaje - to sylwetka skarpy (w rzeczywistosci widac tam zdzbla); dalej tylko geometria (karty trawy na skarpie za
krawednikiem albo lagodniejsza skarpa w `conform`) - poza zakresem, do decyzji lidera.

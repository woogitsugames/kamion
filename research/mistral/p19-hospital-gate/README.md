# mistral-p19-hospital-gate — brama szpitala (Żurawia 14, Dojlidy), kadr referencyjny P11-129

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą; świat Białegostoku 1:1 (OSM + GUGiK); gra komercyjna, budżet 0 zł.
**Zadanie M62 (+ M62-FIX):** kadr referencyjny P11-129 (brama szpitala w Dojlidach) jest dziś najgorzej odwzorowany w regionie. Cel: komplet danych do odtworzenia bramy rozpoznawalnej dla gracza z Białegostoku (decyzja D60, region Dojlidy).
**Gałąź:** `research/mistral-p19-hospital-gate` (PR #53). **Data:** 2026-11-13, poprawki M62-FIX 2026-11-14 (po przeglądzie `docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md`; zamiast rebase scalono `origin/main` do gałęzi). **Język:** polski.

---

## 0. Zmiany M62-FIX (2026-11-14) — skrót
1. **Kierunek odwrócony i poprawiony:** ulica Żurawia leży ~16 m na **E/NE** od bramy, szpital na W/SW. Wjazd (od ulicy w głąb terenu) ma kierunek **~242°** (siatka EPSG:2180; ≈245,6° geogr.). Way 883955523 = dojazd od ulicy, way 73881452 = droga już na terenie szpitala; node 874174701 to NIE skrzyżowanie z Żurawią. Dopisano maxspeed=40.
2. **Kadry innych obiektów usunięte z „kadrów bramy” i ze wszystkich odczytów:** F05/F06 (budynek z masztem kratowym, landuse=military na E od Żurawiej), F15/F16 (budynek z blachy innej instytucji), F19 (stalowa brama przesuwna przy budowie, 190 m na SE). Opisy F03, F12, F13, F16 napisane od nowa z obrazu. Duplikaty F22 (= F11) i F23 (= F17) usunięte. F09 (PNG) obejrzany. URL F14 poprawiony.
3. **F01 opisany z obrazu:** mur z jasnej cegły, 5 poziomych bordowych tablic (2 + 3), filar końcowy muru bez daszka, po N dwa filary ze wspólnym daszkiem (jasna belka + ciemna blacha trapezowa). Wysokość muru policzona z warstw cegieł.
4. **Znaki:** C-2 / B-33 „20” / tabliczka na słupku przy szlabanie; B-20 na filarze; tablica „WJAZD NA PODSTAWIE…” i „OPŁATA ZA WJAZD 3 zł” dodane; B-2 osobno w głębi terenu; wysokości ESTIMATED z kotwicą.
5. Tablica izby przyjęć niebieska, na własnym białym słupku. Chodnik = kostka. Tło: niskie budynki i dwa kominy.
6. **Kryterium ≥ 12 kadrów z ≥ 3 stron: NIESPEŁNIONE (1 kadr bramy: F01).**
7. Nowa samokontrola: seed 20261114, 14 wierszy, **12 zgodnych / 2 niezgodne**.

## 1. Cel
Ustalić z OSM dokładne położenie wjazdu na teren szpitala przy ul. Żurawiej 14 (Dojlidy, Białystok) wraz z identyfikatorami obiektów, a z kadrów odczytać: mur (materiał, wysokość, tablice), filary i daszek, szlaban, znaki (kody wg Dz.U. 2019 poz. 2310, wymiary wg poz. 2311) z wysokościami zamocowania, tablicę izby przyjęć, nawierzchnię przed bramą i tło — w konwencji statusów SOURCED / ESTIMATED / UNVERIFIED / REJECTED.

## 2. Metoda
- **OSM (ODbL):** eksport API 0.6 `map?bbox=23.1870,53.1070,23.1950,53.1120` (2026-11-13); w M62-FIX ponownie `map?bbox=23.1880,53.1085,23.1935,53.1105` oraz `way/{73881451,236884785,239477156}/full` (2026-11-14). Overpass: overpass-api.de (reset połączenia) i kumi.systems (timeout) nie odpowiedziały; zapytanie o węzły z zadania wykonane na `maps.mail.ru/osm/tools/overpass`, drogi z OSM API 0.6. Układ lokalny: środek bramy (node 2448457849) = (0,0), X = wschód, Z = północ [m]. Azymuty: „geogr.” = względem północy geograficznej (przybliżenie lokalne cos φ), „EPSG:2180” = kąt w siatce PUWG 1992 (różnica ~3,4° = zbieżność południków przy λ ≈ 23,19°).
- **Kadry:** Wikimedia Commons (geosearch r = 300 m + kategorie). Miniatury 960 px; F01 dodatkowo 3840 px do wycinków (Python + PIL, `python -I`). **Każdy kadr obejrzany OSOBNO** (jeden plik = jedno wywołanie modelu wizyjnego), zdanie „co widać” pisane z obrazu. Liczby z wizji tylko z jawną kotwicą: znak B-20 średni (koło wpisane 800 mm), znaki 600 mm, moduł warstwy cegły 75 mm (65 + 10 mm, **założenie**).
- **Wysokość muru:** liczenie warstw cegieł na wycinkach F01 (profil jasności spoin w kolumnie pikseli + kontrola wzrokowa wycinka).
- **Dz.U.:** kody znaków wg Dz.U. 2019 poz. 2310 (znaki i sygnały drogowe); wymiary i wysokości wg Dz.U. 2019 poz. 2311 (szczegółowe warunki techniczne dla znaków i sygnałów drogowych…); cytaty ze stronami w manifest.csv.
- **Ortofotomapa:** GUGiK WCS (nalot 2025, GSD 0,05 m) — tylko potwierdzenie jakościowe (niski kontrast).
- **Źródła niestosowane:** Google Maps/Street View/Earth/3D Tiles — ZAKAZ (D43), nieużyte. Mapillary — brak tokenu, nie sondowano.
- **Licencje:** CC0 (Rakoon), CC BY 3.0 pl (Podlaski Urząd Wojewódzki — „referencja, nie tekstura”, atrybucja), ODbL (OSM), otwarte dane (GUGiK), dokument urzędowy (Dz.U.). Napisy instytucji z tablic NIE trafiają do gry — „napis instytucji, nie odtwarzamy”.

## 3. Położenie wjazdu (OSM, sprawdzone 2026-11-14)

| Obiekt | Identyfikator OSM | Ustalenie |
|---|---|---|
| **Brama (szlaban)** | **node 2448457849** (barrier=lift_gate, foot=yes, fee=yes, payment:coins=yes) | **środek bramy: 53.109457, 23.190647** (WGS84); EPSG:2180 E=780370,119 N=590887,441 |
| **Kierunek wjazdu** | way 883955523 → way 73881452 | **~242°** (siatka EPSG:2180) / ≈245,6° geogr. — **od ulicy (E/NE) w głąb terenu (W/SW)**; oś 62°/242° |
| **Dojazd od ulicy** | **way 883955523** (service) | node **874174759 (węzeł Żurawiej)** → 3323248759 (styk z footway 325708420) → szlaban; 16,4 m |
| **Droga za bramą (teren szpitala)** | **way 73881452** (service) | szlaban → node **874174701** (−7,7; −3,4); 8,4 m. 874174701 łączy się z wewnętrznymi service **642905692** i **1552407066**. **To NIE jest skrzyżowanie z Żurawią** |
| Obrys szpitala | way 239477156 (amenity=hospital, Żurawia 14) | przechodzi przez node bramy |
| Portiernia | way 296211509 (name=Portiernia) | narożnik przy bramie node 3000014175 (+0,9; +3,4) — **po N / prawej stronie wjazdu** |
| Ogrodzenie przy murze | way 883955509 (barrier=fence) | kończy się przy bramie node 8220895799 (+1,2; −3,1); biegnie na SSE (~158°), **równolegle do Żurawiej** — **po SE / lewej stronie wjazdu**; na tym odcinku stoi mur z F01 |
| Ogrodzenie od portierni na N | way 883955508 (barrier=fence) | od node 3000014181 |
| **Ulica** | **way 73881451** (Żurawia, unclassified, **maxspeed=40**, hgv=no, maxweight=3.5, surface=paved) | biegnie NNW–SSE; oś **~16,4 m na E/NE** od bramy (kierunek ~68° geogr.) |
| Budynek A | way 236884780 (building=hospital, name=A) | najbliższy punkt ~43,9 m od bramy, na SW |
| Teren na E od Żurawiej | way 236884785 (landuse=military, barrier=fence) + maszt node 8220945933 (man_made=mast, lattice) | obiekt z kadrów F05/F06 — NIE szpital |
| Inne | node 3323248741 (barrier=gate, w ogrodzeniu way 236884785, ~32 m E); node 14123795058 (traffic_mirror, +13,8; −3,1) | |
| **Mur (barrier=wall) przy bramie** | **BRAK w OSM** | mur widoczny tylko na F01 = luka w OSM |

**Szerokość światła wjazdu:** 6,6 m (cięciwa node 8220895799 → node 3000014175; ponowne przeliczenie: 6,51 m) / 6,1 m prostopadle — ESTIMATED (geometria OSM), nie pomiar.

## 4. Kadry

### 4.1 Inwentarz (wszystkie obejrzane osobno 2026-11-14)
Pozycje z geotagów Commons; kierunek kamery — UNVERIFIED, chyba że wynika z treści kadru i OSM.

| Kadr | Plik (Commons) | Odl. od bramy | Data | Licencja | Co widać (z obrazu) | Rola |
|---|---|---|---|---|---|---|
| **F01 = P11-129** | 6739 Uniwersytecki Szpital Kliniczny… November 2019 | 0,9 m (EXIF) | 2019-11-10 | CC0 | widok z ulicy na SW: po lewej mur z jasnej cegły z 5 bordowymi tablicami i filarem końcowym, po prawej dwa filary ze wspólnym daszkiem, STOP na filarze, słupek z C-2 i „20”, szlaban biało-czerwony z tabliczką opłaty, niebieska tablica izby przyjęć, w głębi B-2, niskie budynki i dwa kominy | **jedyny kadr bramy** |
| F02 | 8858 November 2022 | 86 m | 2022-11-03 | CC0 | pętla autobusowa z kostki, przegubowy autobus miejski, czerwona wiata przystanku, niebieska toaleta przenośna, maszt kratowy w tle | kontekst (nie brama) |
| F03 | 20230814 182338 August 2023 | 87 m | 2023-08-14 | CC0 | wnętrze autobusu: żółty kasownik na poręczy, niebieskie fotele | odrzut (wnętrze) |
| F04 | 20230814 181655 August 2023 | 88 m | 2023-08-14 | CC0 | skrzyżowanie z przejściem dla pieszych, łąka, ogrodzenie z siatki, domy w tle | kontekst (nie brama) |
| F05 | 20200726 084447 Białystok July 2020 | 81 m | 2020-07-26 | CC0 | wieloskrzydłowy budynek z brązowymi wielospadowymi dachami i masztem kratowym; ogrodzenie z żółtymi ceglanymi słupkami i stalowymi przęsłami, B-2 na bramie | **REJECTED — inny obiekt** (landuse=military, E od Żurawiej) |
| F06 | 8860 November 2022 | 87 m | 2022-11-03 | CC0 | ten sam budynek z masztem co F05, za zieloną siatką; osoba i niebieska naczepa przy ogrodzeniu | **REJECTED — inny obiekt** |
| F07 | 20230814 180637 August 2023 | 100 m | 2023-08-14 | CC0 | skrzyżowanie z przejściem, samochód nauki jazdy, parking, budynki | kontekst (nie brama) |
| F08 | 8861 November 2022 | 118 m | 2022-11-03 | CC0 | budynek WORD z łukowym dachem, zielona brama stalowa, baner; znaku STOP nie widać | odrzut (inny obiekt) |
| F09 | Szpital tymczasowy … 01.png | 124 m | 2020-12-10 | CC BY 3.0 pl | nowy biały 3-kondygnacyjny budynek z przeszklonym parterem i szerokimi schodami, plac z kostki | odrzut (inny obiekt) |
| F10 | 20200726 084816 WORD | 131 m | 2020-07-26 | CC0 | hala WORD z napisem, maszty flagowe, ogrodzenie z zielonej siatki | odrzut (inny obiekt) |
| F11 | Szpital tymczasowy … 03.jpg | — (brak geotagu) | 2020-12-10 | CC BY 3.0 pl | wnętrze: biurko z monitorem podglądu kamer i panelem przywoławczym | odrzut (wnętrze) |
| F12 | 20221117 130338 | 161 m | 2022-11-17 | CC0 | korytarz przychodni: rejestracja, rząd krzeseł, drzwi gabinetów | odrzut (wnętrze) |
| F13 | 20221117 122654 | 162 m | 2022-11-17 | CC0 | korytarz z krzesłami i wieszakiem, na końcu przeszklone drzwi wyjściowe | odrzut (wnętrze) |
| F14 | 20200726 084417 Żurawia Street in Białystok | 158 m | 2020-07-26 | CC0 | Żurawia wzdłuż: jezdnia asfaltowa, chodnik z kostki, po lewej płot z jasnymi słupkami i wierzby, po prawej budynek z masztem | kontekst ulicy |
| F15 | 8857 November 2022 | 169 m | 2022-11-03 | CC0 | parterowy budynek z blachy falistej z zielonymi pasami (napis innej instytucji — nie odtwarzamy), 2 samochody za siatką | **REJECTED — inny obiekt** |
| F16 | 20221117 122456 | 176 m | 2022-11-17 | CC0 | wejście z przezroczystym daszkiem do budynku z blachy falistej z F15 | **REJECTED — inny obiekt** |
| F17 | Szpital tymczasowy … 05.jpg | — (brak geotagu) | 2020-12-10 | CC BY 3.0 pl | sala chorych z łóżkiem, dwie osoby, za oknem śnieg | odrzut (wnętrze) |
| F18 | Szpital tymczasowy … 06.jpg | 146 m | 2020-12-10 | CC BY 3.0 pl | pusta sala z dwoma łóżkami szpitalnymi | odrzut (wnętrze) |
| F19 | 20200726 084355 ul. Żurawia July 2020 | 190 m | 2020-07-26 | CC0 | stalowa brama przesuwna z siatką, słupek z jasnej cegły, tablice informacyjne i żółte budowlane, koparka, biały wielokondygnacyjny budynek w budowie | **REJECTED — inny obiekt** (190 m SE) |
| F20 | 20221117 124435 | 229 m | 2022-11-17 | CC0 | ulica osiedlowa z kostki, słup energetyczny, żywopłot z tui, znak zakazu dla ciężarówek | kontekst (nie brama) |
| F21 | 20221117 124436 | 246 m | 2022-11-17 | CC0 | biały dom jednorodzinny, tuje, brama z kutymi elementami | kontekst (nie brama) |
| F24 | Szpital tymczasowy … 07.jpg | — (brak geotagu) | 2020-12-10 | CC BY 3.0 pl | dwie osoby przed budynkiem, mikrofony prasy | odrzut |

Obejrzano **22 pliki** z inwentarza (F01–F21, F24) oraz 4 dodatkowe pliki z kategorii ulicy (§4.3). F22 i F23 usunięto jako duplikaty F11 i F17.

### 4.2 Commons geosearch r = 300 m od bramy (2026-11-14) — pełna lista: 25 plików
Odległość [m] — plik: 0,9 — 6739 Uniwersytecki Szpital Kliniczny… (F01); 80,8 — 20200726 084447 (F05); 86,2 — 8858 (F02); 86,7 — 8860 (F06); 86,9 — 20230814 182338 (F03); 87,6 — 20230814 181655 (F04); 100,4 — 20230814 180637 (F07); 117,8 — 8861 (F08); 124,3 — Szpital tymczasowy… 01.png (F09); 130,7 — 20200726 084816 WORD (F10); 145,9 — Szpital tymczasowy… 06 (F18); 157,6 — 20200726 084417 Żurawia Street (F14); 161,0 — 20221117 130338 (F12); 162,2 — 20221117 122654 (F13); 169,4 — 8857 (F15); 173,6 — Szpital tymczasowy… 04; 175,6 — 20221117 122456 (F16); 182,5 — Szpital tymczasowy… 02; 189,6 — 20200726 084355 (F19); 229,1 — 20221117 124435 (F20); 246,2 — 20221117 124436 (F21); 255,1 — 20200726 084948 Wiewiórcza Street; 269,8 — 20200726 085300 Borsucza Street; 292,9 — 20221117 124441; 298,5 — 8856 November 2022.
**W promieniu 40 m: 1 plik (F01).** Pliki 02, 04 (szpital tymczasowy) i 4 pliki > 250 m nie były wcześniej w inwentarzu; leżą > 170 m od bramy, więc nie mogą pokazać bramy z ≤ 40 m — nie oglądano ich.

### 4.3 Sprawdzone źródła i liczba wyników (2026-11-14)
| Źródło | Zapytanie | Wynik |
|---|---|---|
| Commons geosearch | r = 300 m od node 2448457849 | 25 plików, ≤ 40 m: 1 (F01) |
| Commons kategoria | `University Hospital in Białystok (Żurawia)` | 9 plików (F01, F19, szpital tymczasowy 01–07) — żaden nowy kadr bramy |
| Commons kategoria | `Żurawia Street in Białystok` | 14 plików + 4 podkategorie. Seria Rakoon z 2019-11-10 bez geotagu: obejrzano osobno 6731 (jezdnia z latarniami, pylon parku technologicznego), 6733 (hala logistyczna z naczepami za żywopłotem), 6735 (tabliczki ul. Żurawia / ul. Borsucza, nowoczesne budynki), 6740 (skrzyżowanie z Wiewiórczą, B-5, budynek w budowie) — **żaden nie pokazuje bramy**. 6729 (skrzyżowanie z Kuronia), 6736 (Borsucza), 6741 (Wiewiórcza) — według nazw inne skrzyżowania, nie oglądano |
| Commons wyszukiwanie | `Żurawia Białystok` (ns 6); `6737`, `6738` | 23 trafienia — wszystkie już wyżej lub poza bramą; 6737 = park technologiczny, 6738 = ul. Borsucza (kadr tuż przed F01 w serii) |
| Commons kategoria | `Szpital tymczasowy przy ul. Żurawiej w Białymstoku` | kategoria nie istnieje (0) |
| Panoramax | `place_position` r = 0–300 m; bbox ~300 m | 0; 0 (kontrola pozytywna w bbox Białegostoku: 5) |
| KartaView | `photo/?lat,lng,radius=300` | 0 (kontrola pozytywna Warszawa: wyniki są) |
| Openverse | 5 zapytań tekstowych | 1 wynik (= F01, Wikimedia); 1 × 0; 3 × HTTP 504 |
| Mapillary | — | nie sondowano (brak tokenu) |

### 4.4 Kryterium „≥ 12 obejrzanych kadrów bramy z ≥ 3 stron”
**Kryterium niespełnione: 1 kadr bramy (F01), 1 strona (od ulicy, widok na SW).** Pozostałe kadry nie pokazują bramy P11-129. W dozwolonych źródłach nie znaleziono innych kadrów ≤ 40 m od bramy (tabela 4.3). Do uzupełnienia na miejscu (zdjęcia z ≥ 3 stron) albo z Mapillary po udostępnieniu tokenu.

## 5. Tabela elementów (skrót; pełne dane w manifest.csv, 68 wierszy)

Kotwice skali (ESTIMATED): **K1** = B-20 średni, koło wpisane 800 mm (Dz.U. 2019 poz. 2311, zał. 1) → ~345 px/m w płaszczyźnie filara na F01 3840 px; **K2** = C-2 i B-33 o tej samej średnicy w px → oba 600 mm → ~205 px/m na słupku znaków, podstawa przyjęta na poziomie stopy obudowy szlabanu; **K3** = moduł warstwy cegły 75 mm (założenie).

| Element | Wartość | Metoda / kotwica | Status |
|---|---|---|---|
| Brama — środek | 53.109457, 23.190647 | node 2448457849 | SOURCED |
| Kierunek wjazdu | ~242° (EPSG:2180) / ≈245,6° geogr., od ulicy na W/SW | geometria OSM | ESTIMATED |
| Szerokość światła | 6,6 m (cięciwa) / 6,1 m (prostopadle) | geometria OSM | ESTIMATED (geometria OSM) |
| Szlaban | jedno ramię biało-czerwone; napęd czerwony po N; ramię ~1,0 m | F01; K2 | ESTIMATED |
| Mur — materiał | cegła jasna szarobeżowa (silikat / jasny klinkier — UNVERIFIED) | F01 | ESTIMATED |
| **Mur — wysokość** | **1,80–1,95 m bez nakrywy** (24 widoczne warstwy na lewym końcu, 26 przy filarze) | K3; kontrola K1 sugeruje moduł ~80 mm → do ~2,1 m | ESTIMATED (1 kadr) |
| Mur — nakrywa | płaska betonowa, ~0,06 m | F01; K3 | ESTIMATED |
| Mur — tablice | **5 poziomych bordowych, 2 kolumny (2 + 3)**, ~0,65 × 0,26 m; napisy — nie odtwarzamy | F01; K3 | ESTIMATED |
| Filar końcowy muru (SE) | cegła jasna, ~28 warstw ≈ 2,1 m + płaska nakrywa, **bez daszka** | F01; K3 | ESTIMATED |
| Filary N (2 szt.) | cegła jasna; lewy szerszy z odsadzką; między nimi zielona siatka (furtka/przęsło) | F01 | ESTIMATED |
| **Daszek** | **wspólny nad 2 filarami N:** jasna belka/gzyms + ciemna blacha trapezowa; spód ~2,7 m, wierzch ~3,0–3,1 m | F01; K1 | ESTIMATED |
| B-20 STOP | na licu zadaszonego filara (N); dolna krawędź **~1,3–1,4 m** (~1,5–1,6 m gdyby duży) | F01; K1 | ESTIMATED |
| C-2 | najwyżej na słupku przy szlabanie; dolna krawędź **~2,5 m** | F01; K2 | ESTIMATED |
| B-33 „20” | pod C-2; dolna krawędź **~1,7 m** | F01; K2 | ESTIMATED |
| Tabliczka pod B-33 | biała, zaklejona żółtą kartką (treść UNVERIFIED); dolna krawędź ~1,3 m | F01; K2 | ESTIMATED |
| Tablica „WJAZD NA PODSTAWIE przepustki / skierowania / biletu wjazdowego” | niebieska, na filarze pod STOP, ~0,8 × 0,45 m, dolna krawędź ~1,0 m | F01; K1 | ESTIMATED |
| Tabliczka „OPŁATA ZA WJAZD 3 zł” | niebieska, na ramieniu szlabanu; zgodna z OSM fee=yes | F01 | ESTIMATED |
| B-2 | osobno, w głębi terenu (~20–30 m za bramą), własny słupek przed niskim kremowym budynkiem | F01 (odległość z perspektywy, niemierzona) | ESTIMATED |
| Wymiary znaków (normowe) | B-20: 900/800; B-33: 900/800/600/400; C-2: 900/600/600/400 mm | Dz.U. 2019 poz. 2311, tab. 1.1 i 3.1 | SOURCED |
| Wysokość znaków (normowa) | min. 2,00 (2,20) m w obszarze zabudowanym; 0,90–1,20 m na/za urządzeniach BRD | Dz.U. 2019 poz. 2311, tab. 1.11 | SOURCED (zakres) |
| Tablica izby przyjęć | **niebieska z żółtym i białym napisem**, na własnym białym słupku przed prawym filarem; ~0,8 × 1,0 m, dolna krawędź ~1,3 m; napis — nie odtwarzamy | F01; K1 | ESTIMATED |
| Oświetlenie | wysoki słup z oprawą na wysięgniku za filarem + latarenka na szczycie słupka znaków | F01 | ESTIMATED |
| Nawierzchnia przed bramą | asfalt mokry z łatami i włazami | F01 | ESTIMATED |
| Chodnik (lewa) | kostka betonowa szara z czerwonym pasem, krawężnik betonowy | F01 | ESTIMATED |
| Nawierzchnia za szlabanem | kostka prostokątna szara | F01 | ESTIMATED |
| Tło | budynki 1–2 kondygnacje, ściany beżowe/żółte/kremowe, dachy płaskie lub niskie; w głębi dwa wysokie smukłe kominy; po lewej ciemna wyższa bryła, po prawej za drzewami żółta wyższa bryła (kondygnacje nieczytelne) | F01 | ESTIMATED |
| Zieleń | za murem kolumnowe iglaki; po prawej drzewa liściaste z resztką liści (XI) | F01 | ESTIMATED |

## 6. Szkic sytuacyjny (układ lokalny: środek bramy = (0,0); X = wschód [m]; Z = północ [m])

Kamera F01 stoi po stronie ulicy i patrzy na **SW** (~245°), w głąb terenu. **Lewa strona kadru = SE** (mur), **prawa = N/NW** (portiernia, filary z daszkiem, znaki).

```
                     Z (północ)
                     ↑
   teren szpitala    |   portiernia (way 296211509), narożnik 3000014175 (+0,9; +3,4)
   (W/SW)            |   [2 filary N ze wspólnym daszkiem; STOP + tablica „WJAZD NA PODSTAWIE” na filarze;
                     |    słupek C-2 / B-33 „20” / tabliczka przy obudowie szlabanu; tablica IP na białym słupku]
  874174701 ●────────■ szlaban (0,0) ──────● 3323248759 (+6,7; +3,0) ──────● 874174759 (+14,9; +6,8)
  (−7,7; −3,4)       |   way 73881452 ← | → way 883955523 (dojazd od ulicy)     ║ Żurawia (way 73881451)
  → service 642905692|                                                          ║ biegnie NNW–SSE,
    i 1552407066     |   filar końcowy muru (+1,2; −3,1) = node 8220895799      ║ oś ~16,4 m na E/NE
   (teren szpitala)  |     \  mur z jasnej cegły, 5 tablic (2+3),                ║ maxspeed=40, hgv=no
                     |      \ wzdłuż fence 883955509 na SSE (~158°),             ║
                     |       \ równolegle do Żurawiej                            ║
                     |                                   lusterko 14123795058 (+13,8; −3,1)
   B-2 (osobno, ~20–30 m w głębi terenu, ESTIMATED)                              → X (wschód)
   kierunek wjazdu: od ulicy (E/NE) → brama → teren (W/SW) = ~242° (EPSG:2180)
```

Potwierdzenia: pozycje liczbowe z geometrii OSM (2026-11-14); strony (lewa/prawa) z F01 + OSM; elementy bez węzłów OSM (mur, filary, znaki, tablice) — tylko z F01.

## 7. Wymiary znaków — Dz.U. 2019 poz. 2311 (szczegółowe warunki techniczne), zał. 1
- Tabela 1.1 „Podstawowe wymiary znaków kategorii A, B, C i D (wymiary podane w mm)” (Dz.U. str. 4, PDF str. 9): kategoria B (zakaz) średnica — duże 900, średnie 800, małe 600, mini 400; kategoria C (nakaz) — duże 900, średnie 600, małe 600, mini 400.
- Tabela 3.1 „Wymiary znaków zakazu i znaków uchylających zakaz (w mm)” (Dz.U. str. 92, PDF str. 97); przypis: „(*) Nie dotyczy znaku B-20, który występuje tylko jako duży i średni.”
- B-20 (Dz.U. str. 91, PDF str. 96): „wymiary średnicy dla ośmiokątnego znaku B-20 odnoszą się do średnicy koła wpisanego w ten ośmiokąt.”
- B-33 (Dz.U. str. 135, PDF str. 140); C-2 (Dz.U. str. 154, PDF str. 159).
- Wysokości i odległości: tabela 1.11 (Dz.U. str. 32, PDF str. 37); str. 26 (PDF str. 31) — manifest P19-039, P19-047.
- Kody znaków (B-2, B-20, B-33, C-2) wg Dz.U. 2019 poz. 2310 (znaki i sygnały drogowe).

## 8. Samokontrola 20 % (nowy seed 20261114)
Losowanie: `random.Random(20261114).sample(ids, ceil(0.2·68))` → **14 wierszy** (20,6 %): P19-002, -009, -010, -016, -017, -028, -029, -031, -032, -048, -051, -055, -062, -065. Wiersze z kadru porównano z OBRAZEM (nowe wycinki F01 z miniatury 3840 px, F05 960 px, każde osobnym wywołaniem modelu wizyjnego), wiersze OSM przeliczono ponownie.

**Wynik: 12 zgodnych, 2 niezgodne.** Z kadru: 9 wierszy — 8 zgodnych, 1 niezgodny (P19-032: pominięta latarenka na słupku znaków — poprawione). OSM: 5 wierszy — 4 zgodne, 1 niezgodny (P19-048: lusterko w OSM leży na +13,8 E, −3,1 N, manifest podaje −2,3 N; różnica 0,8 m; wiersz jest na liście „nie ruszaj” zadania M62-FIX, więc nie poprawiono — do decyzji lidera). Szczegóły: **audit_20_percent.json**. Poprzedni audyt (seed 20261113) zastąpiono — przepuścił błędny P19-033.

## 9. Luki
- **1 kadr bramy (F01).** Kryterium ≥ 12 kadrów z ≥ 3 stron niespełnione (§4.4). Wszystkie wymiary mają po jednym odczycie z jednego kadru (dwa miejsca liczenia warstw muru to ten sam kadr).
- **Moduł cegły 75 mm to założenie** — kotwica STOP daje ~80 mm; wysokość muru 1,80–1,95 m (do ~2,1 m).
- **Rozmiar znaków tej instalacji UNVERIFIED** — kotwice K1/K2 to założenia (B-20 średni; C-2 i B-33 po 600 mm), podstawa słupka znaków niewidoczna.
- **Mur nie istnieje w OSM** (brak barrier=wall); w grze odtwarzać z F01.
- **Odległość B-2 od bramy** oceniona z perspektywy (~20–30 m), niemierzona; brak węzła OSM.
- **Treść tabliczki pod B-33** zakryta (UNVERIFIED).
- **Aktualność** (stan z 2019-11-10, m.in. opłata 3 zł) — UNVERIFIED.
- Mapillary nie sondowano (brak tokenu).

## 10. Zgodność z kryteriami akceptacji
- „≥ 12 obejrzanych kadrów bramy z ≥ 3 stron”: **NIE — 1 kadr bramy (F01)**. Obejrzano 22 pliki, ale pozostałe 21 nie pokazuje bramy P11-129.
- „Mur, słup, daszek: po ≥ 2 niezależne odczyty wymiaru”: **NIE** — jeden kadr; mur policzony w dwóch miejscach tego samego kadru + kontrola kotwicą STOP; filary i daszek — jeden odczyt z kotwicą.
- „Wszystkie znaki z wysokością zamocowania”: **TAK (ESTIMATED)** — B-20, C-2, B-33, tabliczka, tablica wjazdu, tablica IP z wysokością dolnej krawędzi i jawną kotwicą; zakresy normowe osobno jako SOURCED.
- „Środek bramy z OSM z id”: **TAK** — node 2448457849.
- „Brak wartości RGB z pikseli”: **TAK** (kolory opisowo; piksele użyte tylko do liczenia warstw i wymiarów w px).

## 11. Pliki i archiwum
Zdjęcia i wycinki poza gitem (`files/` i `*.zip` w .gitignore). Archiwum M62-FIX: **`mistral-p19-hospital-gate-files-fix.zip`** — nazwa, rozmiar i sha256 w komentarzu PR #53. Zawiera: 22 kadry 960 px (F01–F21, F24), F01 3840 px, wycinki F01 użyte do odczytów i samokontroli, eksporty OSM (API 0.6), wyniki geosearch/kategorii Commons, Panoramax, KartaView, FILES.md z sumami sha256. Właściciel przekazuje archiwum liderowi.

## 12. Struktura
```
research/mistral/p19-hospital-gate/
├── README.md             (ten plik)
├── manifest.csv          (68 wierszy P19-001…068; UTF-8)
├── sources.md            (pełne URL-e źródeł + licencje + daty dostępu)
├── audit_20_percent.json (samokontrola 20 %, seed 20261114)
├── .gitignore            (files/ + *.zip)
└── files/                (poza gitem — w archiwum ZIP; patrz §11)
```

## Errata lidera (s20, 2026-11-14, przegląd `docs/reports/REVIEW-2026-11-14-s20-mistral-m62-fix.md`)
- P19-048 (lusterko): offset +13,8 / −3,1 m.
- P19-006 / P19-007: offsety ujednolicone do +0,88 / +3,45 i +1,24 / −3,07 m.
- F20: jezdnia asfaltowa (nie kostka).
- P11-129 w manifeście P11: znak = C-2 (nie „C-1/C-2”).
- W grze (siatka EPSG:2180) kierunek wjazdu = 242°; WORKING_VALUE: strony wewnętrzne muru/filarów, tył portierni, dalszy ciąg muru (na F14/F19 słupki z przęsłami — pełny mur tylko odcinek z F01), występ daszka w prawo, rozmiary znaków, odległość do B-2. Kryteria „≥ 12 kadrów bramy” i „≥ 2 niezależne odczyty” NIESPEŁNIONE (1 kadr bramy w źródłach otwartych).

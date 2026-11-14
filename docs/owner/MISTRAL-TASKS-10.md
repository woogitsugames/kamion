# Zadania dla Mistrala — runda 10: dane referencyjne dla agentów świata s20 (2026-11-13) — M62–M69

Repo `woogitsugames/kamion`. **Każda sesja Mistrala dostaje jeden blok (skopiuj całość z ramki) — w NOWEJ sesji.** Zasady wspólne są wpisane w każdy blok, bo Mistral w osobnej sesji nie widzi tego nagłówka. Poprzednia runda: `docs/owner/MISTRAL-TASKS-9.md` (M56–M61) — tych tematów tu nie powtarzamy; gdzie temat się styka (M64 z M58, M67 z M57, M69 z M60), blok mówi dokładnie, co jest NOWE.

## Skąd tematy (luki realne, nie wymyślone)

| paczka | luka (źródło w repo) | co odblokowuje |
|---|---|---|
| M62 | brama szpitala P11-129: brak muru z cegły z tablicami, słupów z daszkiem, znaków STOP / B-33 „20” / C-2, tablicy izby przyjęć; w tle placeholdery (`REVIEW-2026-11-13-s19-0179.md`, P11-129 = N) | follow-up 0179, bramka 3 (Dojlidy) |
| M63 | Rosti (P11-094): wysokość ~12 % za duża, schodek wschodni, bez pasma okien, 2 bramy segmentowe; zakład po prawej P11-063: ciemna wyższa część frontowa + długa niska biała (`REVIEW-…-s19-0179.md`) | `building_part` w 0179, follow-up |
| M64 | pas Krywlany: brak kamery kontrolnej i dowodu w kadrze (`REVIEW-…-0179.md` P2, warunek 2; `artifacts/live/dojlidy-vis-0179.md`: oznakowanie „nie rysowane”) — M58 daje oznakowanie i ogrodzenie z AIP/ortofoto; brak: widoku z oka kierowcy/płotu, nawierzchni, obiektów lotniska | kamera `krywlany_runway`, 0179 follow-up |
| M65 | brak DDR z czerwonego asfaltu: P11-001 (Kuronia) i P11-056 (przejazd rowerowy przez wlot) — „polski wyróżnik ulicy” (`REVIEW-…-0179.md`); trasa C | follow-up 0179, generator nawierzchni |
| M66 | tarcza sygnalizatora: duża biała prostokątna za komorą (P11-063) — w Białymstoku czarna z obwódką albo brak (`REVIEW-…-0179.md`); 182011 maszt z wysięgnikiem (ADR 0172) | sygnalizatory `StreetFurniture` |
| M67 | maszty/anteny GSM na dachu wieżowca (`REVIEW-…-0180-r2.md` P2-5/P2-7; ADR 0180 „Otwarte”) — M57 ustala, co stoi na TYM dachu; brak: geometria samych elementów | dach wieżowca, ewent. inne dachy |
| M68 | las przy Krywlanach: „pnie z oderwanymi kulami liści”, ściana lasu z pionową krawędzią, brak podszytu, nieregularna linia lasu na horyzoncie P11-056 (`REVIEW-…-0179.md` route-2, P11-056) | zadanie roślinności/horyzontu |
| M69 | pule światła latarni: brak, rozstaw/rozsył niepotwierdzone (`REVIEW-…-0182.md` P1-4, P2-8) — M60 daje klasy PN-EN 13201, wymagania i próby z BIP; brak: konkretny typ opraw i geometria z nocnych kadrów | follow-up 0182 (oświetlenie) |

Sprawdzone, że nie dublują M56–M61: M56 estakady Andersa; M57 elewacje i dach wieżowca (położenie/liczba masztów); M58 słupki z łańcuchem + oznakowanie pasa + ogrodzenie z drogi + szlabany; M59 lampy pojazdu; M60 fizyka zmierzchu, klasy oświetlenia, zapalone okna; M61 brud naczepy. Istniejące: `research/mistral/p9-furniture-3` (wysokości latarni), `p11-dojlidy-photos` (kadry P11-NNN), `p12-dojlidy-landmarks`, `p6-dojlidy-gates`, `p8-restrictions-3`, `p2-surfaces-2`, `research/g5-street-furniture`.

**Kolejność (od najpilniejszej): M62 → M65 → M68 → M63 → M66 → M69 → M64 → M67.** Uzasadnienie na końcu pliku.

---

## M62 — brama i mur szpitala P11-129 (Dojlidy): wjazd, ceglany mur, słupy z daszkiem, znaki

```
Repo woogitsugames/kamion. Gałąź research/mistral-p19-hospital-gate od NAJNOWSZEGO origin/main (z myślnikiem po „mistral”, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna, budżet 0 zł. Region Dojlidy (decyzja D60). Bramka rozpoznawalności: gracz z Białegostoku ma rozpoznać miejsce po układzie i obiektach. Kadr referencyjny P11-129 (brama szpitala w Dojlidach) jest dziś najgorzej odwzorowany w regionie: w grze brak muru z cegły z tablicami, ceglanych słupów z daszkiem, znaków STOP, B-33 „20”, C-2 i tablicy izby przyjęć; w tle generyczny blok. Przeczytaj w repo: research/mistral/p11-dojlidy-photos/README.md + manifest.csv (wiersz P11-129 i sąsiednie kadry), research/mistral/p6-dojlidy-gates/README.md (bramy regionu), research/g5-street-furniture/README.md. Piszesz po polsku.

ZADANIE:
1. Ustal z OSM/BDOT10k dokładne położenie wjazdu (way_id drogi dojazdowej, id budynków przy bramie, id obrysu terenu szpitala, odcinek ogrodzenia barrier=wall/fence/gate jeśli jest w OSM) — podaj środek bramy WGS84 (6 miejsc) i azymut osi wjazdu.
2. Z P11-129 i NOWYCH kadrów (Panoramax, KartaView, Wikimedia Commons, Openverse; Mapillary tylko bez cudzego tokenu) — dla każdego kadru OBEJRZYJ obraz i odczytaj: (a) mur: materiał (cegła czerwona/klinkier), wysokość [m], rytm przęseł/filarów, cokół, nakrywa, tablice (liczba, wymiary, treść w formie opisu — nazwy instytucji tylko jako „tablica informacyjna szpitala”); (b) słupy bramy: przekrój, wysokość, daszek (kształt, pokrycie, kolor), lampy; (c) skrzydła/szlaban: typ, szerokość światła wjazdu [m], kolor; (d) znaki: STOP (B-20), B-33 z liczbą (podaj prędkość), C-2 i inne — wysokość zamocowania i położenie względem krawędzi jezdni; (e) tablica izby przyjęć: kształt, kolory, wysokość (bez rekonstrukcji logo); (f) nawierzchnia przed bramą (asfalt/kostka/łaty — opis), krawężnik, chodnik; (g) tło: kondygnacje i materiał budynków widocznych za bramą (opis, nie marki).
3. Skala: każdy wymiar ESTIMATED z jawną metodą (proporcja do krawężnika 0,15 m, płyty chodnika 0,5 m, znaku B-33 o średnicy z Dz.U. 2019 poz. 2311, wysokości człowieka) albo SOURCED z dokumentu. Wymiary znaków: zał. 1 rozporządzenia (rozmiar „mały/średni/duży”, cytat + strona).
4. Szkic sytuacyjny (tekstowy, współrzędne lokalne od środka bramy w metrach: oś X = wschód, Z = północ): ustawienie muru, słupów, znaków, szlabanu, krawężnika. Bez rysowania z pamięci — tylko to, co potwierdzają ≥ 2 kadry; reszta UNVERIFIED.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google (także zrzuty z nich w artykułach). Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, BDOT10k, NMPT), OSM (ODbL), ISAP/ELI (Dz.U.).
- Tylko licencje komercyjne (CC0, CC BY, CC BY-SA, dokumenty urzędowe); NC/ND/bez licencji — tylko link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”, z atrybucją.
- Nie zmyślaj: każdy wymiar z kadru lub dokumentu, nie widać = UNVERIFIED. Nazwy marek/instytucji z tablic NIE trafiają do opisów odtwarzanych w grze (zapisz „napis instytucji, nie odtwarzamy”).
- Każdy kadr OBEJRZANY; w uwagach jedno zdanie „co widać”. Pozycja kamery WGS84 (6 miejsc), kierunek_deg (z API/EXIF albo UNVERIFIED), data, sezon, pora_dnia. Przypisanie do bramy: ≤ 40 m od środka bramy, odległość w uwagach. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % pozycji z jawnym seedem: ponownie sprawdź link, cytat/stronę i ponownie OBEJRZYJ kadr, porównaj ze zdaniem „co widać”. Wynik w README i audit_20_percent.json.

KRYTERIA AKCEPTACJI: ≥ 12 obejrzanych kadrów bramy z ≥ 3 stron (przód, ukos z lewej, ukos z prawej); dla muru, słupa i daszka po ≥ 2 niezależne odczyty wymiaru; wszystkie znaki z wysokością zamocowania; środek bramy z OSM/BDOT z id; brak wartości RGB z pikseli (kolor tylko opisem).

WYNIK w gałęzi: research/mistral/p19-hospital-gate/ z README.md (cel, metoda, położenie, tabela elementów „element → wymiar → metoda → źródło → status”, szkic sytuacyjny, luki), manifest.csv (utf-8; id P19-NNN; kolumny: element mur|słup|daszek|brama|znak|tablica|nawierzchnia|tło|położenie, parametr, wartość, jednostka, lat, lon, osm_id, kierunek_deg, odległość_do_bramy_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p19-hospital-gate-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p19-hospital-gate/.
ODDANIE: commit + push co ok. godzinę; na końcu jeden PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M62 gotowe, PR #<numer>” i koniec.
```

## M63 — zakład z dominantą i bramy segmentowe (P11-094 i P11-063): bryła schodkowa, okładzina, bramy

```
Repo woogitsugames/kamion. Gałąź research/mistral-p20-plant-gates od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Region Dojlidy / Krywlany (D60). Dwa zakłady przy trasie: (A) hala przemysłowa z kadru P11-094 (długa jasnoszara ściana, narożnik, dwie bramy segmentowe, lampy na ścianie, skarpa z trawą i żywopłot u podstawy); (B) zakład po prawej stronie kadru P11-063 (ul. Mickiewicza / Kuronia): ciemniejsza, wyższa część frontowa + długa niższa, biała hala. W grze oba są jednym pudełkiem: wysokość A ~12 % za duża (LoD1 18,92 m dla całego obrysu), brak schodka wschodniego, okładzina jak „siatka bloczków” z nieistniejącym paskiem okien, brak 2 bram segmentowych. W OPISACH ODTWARZANYCH W GRZE NIE UŻYWAMY NAZW MAREK ani logo: pisz „hala A”, „zakład B”, napisy firmowe = „napis firmowy, nie odtwarzamy”. Przeczytaj w repo: research/mistral/p11-dojlidy-photos/README.md + manifest.csv (P11-063, P11-094 i sąsiednie), research/mistral/p3-buildings-2 (jeśli jest) i docs/REFERENCES.md. Piszesz po polsku.

ZADANIE:
1. Identyfikacja z OSM/BDOT10k: way_id/id budynków A i B, obrysy (liczba segmentów, długości boków [m]), funkcja (BDOT: kod), liczba kondygnacji i wysokość z LoD1/LoD2 GUGiK, NMPT (wysokość punktów dachu — różnica segmentów).
2. Wysokości segmentów: dla A i B oddzielnie — wysokość attyki każdego segmentu [m] (NMPT − NMT albo LoD2; jeśli oba, podaj oba i rozbieżność), położenie uskoków. ESTIMATED tylko z jawną metodą i id kadru.
3. Okładzina i podział ścian: dla każdej ściany z kadru — rodzaj okładziny (panele warstwowe poziome / kasety / blacha trapezowa / tynk / beton), kierunek paneli, moduł [m] jeśli czytelny, pas cokołu (kolor opis, wysokość), pasma okien (JEST/BRAK, wysokość położenia), drzwi, rampy, zacieki. OBEJRZYJ każdy kadr; nie zakładaj, że ściana niewidoczna „jest jak widoczna” — UNVERIFIED.
4. Bramy segmentowe i wjazdy: dla każdego kadru liczba bram, szerokość × wysokość [m] (ESTIMATED z proporcji do drzwi ~2,0 m / człowieka 1,75 m / tira 4,0 m wysokości), liczba paneli, okienka (liczba), kolor (opis), położenie na ścianie jako ułamek długości ściany, rampa/dok (jest/brak). Typowe wymiary bram przemysłowych: tylko liczby z kart katalogowych (BEZ nazw producentów w opisach) lub norm (np. PN-EN 13241) — URL + cytat ≤ 25 słów.
5. Otoczenie: ogrodzenie (typ, wysokość, kolor — czy w ogóle jest, bo na zdjęciu nie widać białego płotu panelowego), skarpa, żywopłot, latarnie, D-6 i inne znaki z pozycją względem kamery (korekta: znak w grze jest ~2–3 m za blisko).
6. ≥ 10 nowych kadrów A i ≥ 10 kadrów B (Panoramax, KartaView, Wikimedia Commons, Openverse; Mapillary bez cudzego tokenu), z różnych stron i dat; wskaż 3 najlepsze kadry dla artysty z uzasadnieniem.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, NMPT, NMT, BDOT10k, LoD1/LoD2), OSM (ODbL).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: wymiar = źródło lub ESTIMATED z metodą; nie widać = UNVERIFIED. Kolor tylko opisem słownym (bez RGB z pikseli).
- Każdy kadr OBEJRZANY, zdanie „co widać” w uwagach; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data, sezon, pora_dnia; przypisanie do obiektu ≤ 60 m od obrysu (way_id i odległość w uwagach). JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru + ponowne sprawdzenie cytatu i odczytu z NMPT) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: tabela segmentów wysokości A i B z metodą; dla A rozstrzygnięte „ile bram, gdzie, jakie wymiary”; dla każdej ściany okładzina OPISANA lub UNVERIFIED z powodem; ≥ 20 obejrzanych kadrów łącznie; żadnej marki w polach „opis” przeznaczonych dla gry.

WYNIK w gałęzi: research/mistral/p20-plant-gates/ z README.md (identyfikacja, tabela segmentów, tabela ścian, tabela bram, otoczenie, 3+3 najlepsze kadry, luki), manifest.csv (id P20-NNN; kolumny: obiekt A|B, element segment|ściana|brama|ogrodzenie|znak|latarnia, parametr, wartość, jednostka, lat, lon, osm_id, kierunek_deg, odległość_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p20-plant-gates-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p20-plant-gates/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M63 gotowe, PR #<numer>” i koniec.
```

## M64 — lotnisko Krywlany widziane z drogi: pas 09R/27L, ogrodzenie, obiekty i kadr z oka kierowcy (UZUPEŁNIENIE M58)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p21-krywlany-airfield od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1, gra komercyjna. Region Dojlidy / Krywlany (D60). Recenzja wykazała, że żaden kadr kontrolny nie pokazuje pasa startowego 09R/27L; „30 153 m² pasa” jest tylko w liczbach. Potrzebna kamera kontrolna „krywlany_runway” (oczy 1,7 m przy płocie) i dowód z kadrów. ZAKRES ROZŁĄCZNY Z M58 (docs/owner/MISTRAL-TASKS-9.md, punkt 2): M58 ustala (a) oznakowanie pasa z AIP/ortofoto i (b) werdykt „widoczne z drogi TAK/NIE” oraz (c) typ ogrodzenia z kadrów. Tutaj NIE powtarzaj tych ustaleń — przeczytaj research/mistral/p15-dojlidy-details/ jeśli już jest w origin (git fetch; jeśli nie ma, zrób to, co poniżej bez dublowania i oznacz „do uzgodnienia z M58”). TA paczka dostarcza: wygląd nawierzchni pasa i dróg kołowania, to, co stoi na lotnisku i jest widoczne z dróg publicznych, oraz geometrię widoku. Przeczytaj też research/mistral/p12-dojlidy-landmarks/README.md (P12-001/002: geometria pasów) i p11-dojlidy-photos (kadry P11-0xx z lotniskiem, np. P11-056). Piszesz po polsku.

ZADANIE:
1. Nawierzchnia pasa 09R/27L i 09L/27R (trawiasty/asfaltowy/betonowy — z AIP/karty EPBK: PAŻP, dokument urzędowy, tylko fakty; z ortofoto GUGiK 2023–2025: opis, co widać, arkusz i data), szerokość pasa utwardzonego vs. szerokość pasa trawiastego [m], drogi kołowania (liczba, nawierzchnia, położenie WGS84 początku/końca), płyta postojowa. Kolor nawierzchni i stan (pęknięcia, łaty, mech, trawa w szczelinach) — opis z kadrów, jeśli są.
2. Obiekty na lotnisku widoczne z dróg (ul. Dywizjonu 303, ul. Mickiewicza, ul. Kuronia): hangary (liczba, wysokość ESTIMATED z NMPT/LoD, kolor, rodzaj dachu), wieża/budynek operacyjny, wiatrowskaz (liczba, wysokość, kolor — z kadrów), oświetlenie krawędzi/progu (jest/brak), tablice i znaki przy bramach, brama wjazdowa (szerokość, typ), parking. Dla każdego: pozycja WGS84, way_id/id budynku OSM/BDOT, dowód (kadr).
3. Geometria widoku „oko kierowcy / oko przy płocie”: dla 5 punktów wzdłuż drogi i 3 punktów przy płocie policz (z geometrii GUGiK/OSM + NMPT): odległość oka do krawędzi pasa, wysokość oka 2,5 m (ciężarówka) i 1,7 m (pieszy), wysokość przeszkód (ogrodzenie, wał, krzewy, pas drzew — NMPT) i kąt zasłonięcia; wniosek „pas widoczny/niewidoczny” w każdym punkcie z wzorem w README. Podaj gotowe współrzędne i azymut dla kamery kontrolnej `krywlany_runway` (pozycja przy płocie, patrzy wzdłuż pasa) i dla 2 kamer z drogi — ESTIMATED z metodą.
4. ≥ 12 obejrzanych kadrów lotniska z dróg i od płotu (Panoramax, KartaView, Wikimedia Commons, Openverse; Mapillary bez cudzego tokenu), w tym ≥ 3 z oznaczeniem, co widać za płotem. Dla każdego: OBEJRZYJ i opisz (nawierzchnia, trawa — wysokość i kolor sezonowy, ogrodzenie, tło: las/hangary).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, NMPT, NMT, BDOT10k), OSM (ODbL), PAŻP/AIP (urzędowe — fakty, bez kopiowania map i kart).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: liczby z dokumentu (cytat ≤ 25 słów + strona/AIRAC) lub ESTIMATED z metodą; wszystko inne UNVERIFIED. Nie wnioskuj o wyglądzie nawierzchni z ortofoto bez wskazania arkusza i rozdzielczości (GSD).
- Każdy kadr OBEJRZANY, zdanie „co widać”; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data, sezon, pora_dnia; przypisanie do drogi ≤ 25 m od osi OSM (way_id i odległość). JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru, ponowne obliczenie 2 punktów geometrii widoku, ponowne sprawdzenie cytatów AIP) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: każdy z 8 punktów widokowych ma wynik liczbowy i wzór; podane współrzędne i azymut ≥ 3 kamer kontrolnych; nawierzchnia pasa opisana ze źródłem (AIP + ortofoto z arkuszem); lista obiektów lotniska z pozycją i id; ≥ 12 kadrów; brak powielenia ustaleń M58 (odsyłacz do jego README zamiast kopii).

WYNIK w gałęzi: research/mistral/p21-krywlany-airfield/ z README.md (nawierzchnie, obiekty, geometria widoku, kamery kontrolne, luki, uzgodnienie z M58), manifest.csv (id P21-NNN; kolumny: kategoria nawierzchnia|obiekt|geometria_widoku|kamera|kadr, element, parametr, wartość, jednostka, lat, lon, osm_id, kierunek_deg, wysokość_oka_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p21-krywlany-airfield-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p21-krywlany-airfield/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M64 gotowe, PR #<numer>” i koniec.
```

## M65 — drogi dla rowerów z czerwonego asfaltu: trasa C i Dojlidy (way_id, szerokości, przejazdy)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p22-red-bike-paths od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Polski wyróżnik ulicy: drogi dla rowerów (DDR) z czerwonego/rdzawego asfaltu i przejazdy dla rowerzystów. W grze ich nie ma (recenzja: P11-001 Kuronia 3 i P11-056 przejazd rowerowy przez wlot — czerwony asfalt zastąpiony kostką/zebrą). Dane świata pochodzą z OSM (highway=cycleway, cycleway=track, bicycle=designated, surface=*, colour=*, segregated=*) i BDOT10k. Potrzebna lista konkretnych odcinków z identyfikatorami i parametrami dla (1) trasy C (Białystok przemysłowy: ul. gen. Andersa, Al. Tysiąclecia Państwa Polskiego, ul. Gen. Maczka, rondo Putry, Sokólska/Wysockiego/Kombatantów — region data/Regions/bialystok-industrial-c) i (2) Dojlid (ul. Kuronia, ul. Mickiewicza, ul. Dywizjonu 303, okolice Krywlan). Przeczytaj w repo research/mistral/p2-surfaces-2/README.md (nawierzchnie — NIE powtarzaj ogólnych kolorów asfaltu), research/g5-street-furniture/README.md, research/mistral/p8-restrictions-3/README.md (oznakowanie), docs/05 i REFERENCES.md. Piszesz po polsku.

ZADANIE:
1. Inwentarz odcinków z OSM (Overpass lub eksport; wskaż datę zapytania i treść zapytania): dla każdego odcinka DDR/ciągu pieszo-rowerowego w obu regionach — way_id, tagi (surface, colour, width, segregated, oneway, lit, smoothness), długość [m], końce WGS84, droga równoległa (way_id jezdni i odległość osi do osi), typ rozdzielenia od jezdni (krawężnik/pas zieleni/opornik/brak). Zaznacz, który odcinek jest NA ZDJĘCIU (P11-001, P11-056 itd.) i czy tag colour/surface zgadza się ze zdjęciem. Brakujące tagi = „brak tagu”, nie zgaduj.
2. Szerokości i geometria: szerokość DDR [m] (OSM width, dokumenty: projekty/przetargi BIP Białystok/ZDM — cytat + dokument; zdjęcia — ESTIMATED z proporcji do krawężnika 0,15 m, chodnika z płyt 0,35/0,40/0,50 m i roweru 1,8 m), szerokość sąsiedniego chodnika, szerokość pasa zieleni, krawężnik (wysokość [m]), skosy na wjazdach.
3. Przejazdy dla rowerzystów (P-11 w poprzek jezdni, przejazd z czerwonym asfaltem): lista z pozycją WGS84, way_id jezdni, szerokość przejazdu [m] (Dz.U. 2019 poz. 2311 zał. 2 — oznaczenie P-11, cytat + strona; porównaj z odczytem z kadrów), czy czerwony asfalt przechodzi przez jezdnię (przejazd „czerwony”) czy tylko białe pasy, wyspa/refuż, znaki (C-13/C-16, D-6b, D-6a), sygnalizacja (jest/brak). Osobno: przecięcia DDR z wjazdami do posesji i zakładów (ciągłość czerwonej nawierzchni — typowe w PL).
4. Wygląd czerwonej nawierzchni (do tekstur): odcień opisem słownym i — jeśli w źródle jest — kod RAL/Munsell (liczba tylko ze źródła: specyfikacje techniczne ZDM, katalogi mas bitumicznych barwionych BEZ nazw producentów w opisach), faktura (drobne kruszywo widoczne/gładka), stan (wyblakła, plamy oleju, ślady kół, łaty), lato/zima. Granica asfaltu czerwonego z szarym: ostra/ręczna, uszczelniona spoiną.
5. ≥ 20 obejrzanych kadrów (Panoramax, KartaView, Wikimedia Commons, Openverse; Mapillary bez cudzego tokenu): ≥ 10 z trasy C, ≥ 10 z Dojlid (w tym P11-001 i P11-056 jako punkty kontrolne), po ≥ 5 z przejazdem rowerowym. OBEJRZYJ każdy i opisz (kolor, szerokość względem krawężnika, rozdzielenie, ciągłość przez wjazd, oznakowanie poziome).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, BDOT10k), OSM (ODbL), ISAP/ELI (Dz.U.), BIP Białystok/ZDM (dokumenty urzędowe).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: way_id musi istnieć w OSM w dniu zapytania (podaj datę); wymiar = dokument/tag OSM/ESTIMATED z metodą; kolor tylko opisem (nie RGB z pikseli zdjęć).
- Każdy kadr OBEJRZANY, zdanie „co widać”; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data, sezon, pora_dnia; przypisanie do odcinka ≤ 25 m od osi OSM (way_id i odległość w uwagach). JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne zapytanie o way_id, ponowne obejrzenie kadru i porównanie opisu z tagami) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: kompletny inwentarz DDR obu regionów z way_id (kontrola: suma długości wg OSM podana w README); ≥ 10 przejazdów z pozycją i parametrami; tabela szerokości z metodą; ≥ 20 kadrów; jawna lista rozbieżności „OSM vs zdjęcie” (np. brak colour=red, a zdjęcie pokazuje czerwony).

WYNIK w gałęzi: research/mistral/p22-red-bike-paths/ z README.md (zapytanie Overpass + data, inwentarz, tabela szerokości, przejazdy, nawierzchnia czerwona, rozbieżności OSM↔zdjęcia, luki), manifest.csv (id P22-NNN; kolumny: kategoria odcinek|przejazd|nawierzchnia|kadr, region C|Dojlidy, way_id, tagi_osm (json), długość_m, szerokość, jednostka, lat, lon, kierunek_deg, droga_równoległa_way_id, odległość_do_osi_jezdni_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json oraz overpass-result.json (surowy wynik zapytania, ≤ 5 MB). ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p22-red-bike-paths-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p22-red-bike-paths/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M65 gotowe, PR #<numer>” i koniec.
```

## M66 — sygnalizatory świetlne w Białymstoku: tarcze, komory, daszki, warianty

```
Repo woogitsugames/kamion. Gałąź research/mistral-p23-traffic-signals od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1, gra komercyjna. Sygnalizator w grze ma dużą białą prostokątną tarczę za komorą, większą niż sama komora (recenzja P11-063); w Białymstoku tarcze są czarne z obwódką (biała/żółta odblaskowa) albo ich nie ma. Brakuje listy wariantów: S-1 (pionowy 3-komorowy), S-2 (z sygnałem dodatkowym/strzałką — jeśli jest), S-3 (kierunkowy), S-5 (dla pieszych), S-6/S-7 (dla rowerów), maszty prostokątne/okrągłe, wysięgniki, sygnalizatory na wysięgniku nad jezdnią (ADR 0172: skrzyżowanie 182011 — maszt z wysięgnikiem ~8,8 m, 2 głowice na wysięgniku + 1 na maszcie), daszki (osłony), sygnały dla ciężarówek. Przeczytaj w repo: research/g5-street-furniture/README.md i research/mistral/p9-furniture-3/README.md (co już wiadomo o słupach i masztach — NIE powtarzaj), docs/adr/0172-*.md (skrzyżowanie 182011), research/mistral/p8-restrictions-3/README.md. Piszesz po polsku.

ZADANIE:
1. Przepisy: Dz.U. 2019 poz. 2311 (rozporządzenie w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych…) — załącznik z sygnałami świetlnymi (S-1…S-7): kształt, układ komór, wymiary [mm] (średnica soczewek 200/300 mm), wysokość zawieszenia nad jezdnią/chodnikiem [m], tarcza kontrastowa (czy wymagana, kolor, obwódka — cytat ≤ 25 słów + strona/§), ewentualne polskie normy/wytyczne GDDKiA (WR-D, „Wytyczne projektowania sygnalizacji”) — tylko jawne dokumenty. Jeśli tarcza nie jest wymagana wprost — „UNVERIFIED” i nie zgaduj.
2. Warianty w Białymstoku (z kadrów i zleceń/przetargów BIP ZDM na sygnalizacje): lista skrzyżowań z pozycją WGS84 (≥ 12; trasa C i okolice: rondo Putry, Sokólska/Wysockiego, Al. Tysiąclecia/Maczka, Andersa, Dojlidy — Mickiewicza/Kuronia) i dla każdego: typ masztu (rura okrągła/walcowa/wielokątna, średnica [mm] ESTIMATED), kolor masztu (opis), liczba głowic i układ (pionowo 3 komory / z sygnałem dodatkowym), obecność tarczy kontrastowej (TAK/NIE, kolor, szerokość obwódki ESTIMATED), daszki (jest/brak), wysięgnik (długość [m]), sygnalizatory dla pieszych (jedna/dwie komory, głośnik/przycisk), czujniki/kamery, skrzynka sterownika (wymiary ESTIMATED, kolor, napisy).
3. Typowe wymiary elementów (do modelu 3D): komora (szerokość × wysokość × głębokość [mm]), obudowa (kolor, materiał), soczewki (LED/żarówkowe — wygląd wyłączonej soczewki w dzień), daszek (długość [mm]), tarcza (wymiary [mm] i grubość) — tylko liczby z kart katalogowych/norm (URL + cytat ≤ 25 słów) BEZ nazw producentów w opisach; konstrukcja wsporników (opaski).
4. ≥ 20 obejrzanych kadrów sygnalizatorów z różnych skrzyżowań (≥ 5 z tarczą, ≥ 5 bez, ≥ 3 sygnalizatory dla pieszych, ≥ 3 na wysięgniku). Dla każdego OBEJRZYJ: liczba komór, tarcza TAK/NIE i jej kształt, daszki, kolor obudowy, maszt (przekrój), tło. Marki widoczne = „marka widoczna, tylko referencja”.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto), OSM (ODbL; highway=traffic_signals, traffic_signals:*), ISAP/ELI, BIP.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: wartość = przepis (cytat + strona) / karta (URL) / ESTIMATED z metodą (proporcja do średnicy soczewki 200/300 mm, wysokości człowieka, tarczy znaku); nie widać = UNVERIFIED. Źródła wtórne (sklepy, blogi) nie potwierdzają przepisu.
- Każdy kadr OBEJRZANY, zdanie „co widać”; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data, sezon; przypisanie do skrzyżowania ≤ 40 m od węzła OSM (node/way id i odległość w uwagach). JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru, ponowne sprawdzenie cytatu przepisu i linku do karty) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: jednoznaczny wniosek „tarcza kontrastowa w Białymstoku: tak/nie/mieszanie” z liczbą skrzyżowań w próbie i ułamkiem; ≥ 12 skrzyżowań w tabeli; ≥ 20 kadrów; wymiary komory i tarczy z dokumentu lub oznaczone ESTIMATED; wszystkie warianty z p. 2 jako lista „wariant → liczba wystąpień → przykładowy kadr”.

WYNIK w gałęzi: research/mistral/p23-traffic-signals/ z README.md (przepisy, tabela skrzyżowań, warianty, wymiary elementów, wniosek o tarczach, luki), manifest.csv (id P23-NNN; kolumny: kategoria przepis|skrzyżowanie|wymiar|kadr, wariant, element, parametr, wartość, jednostka, punkt_przepisu, cytat, osm_id, lat, lon, kierunek_deg, odległość_do_węzła_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p23-traffic-signals-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p23-traffic-signals/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M66 gotowe, PR #<numer>” i koniec.
```

## M67 — dachowe instalacje GSM: geometria elementów (maszty, anteny sektorowe, kontenery) — UZUPEŁNIENIE M57

```
Repo woogitsugames/kamion. Gałąź research/mistral-p24-rooftop-gsm od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1, gra komercyjna. Wieżowiec biurowy przy Kwadrat Park (ul. gen. Andersa, 11 kondygnacji, ~41,8 m) ma na zdjęciu maszty i anteny GSM na dachu; w grze dach jest płaski (recenzja 0180 r2 P2-5/P2-7). ZAKRES ROZŁĄCZNY Z M57 (docs/owner/MISTRAL-TASKS-9.md): M57 ustala, ILE i GDZIE stoi na TYM dachu (liczba masztów, wysokość nad dachem, położenie, zgłoszenie UKE/BIP dla tego budynku). Tutaj NIE powtarzaj lokalizacji — jeśli research/mistral/p14-office-tower/ jest już w origin (git fetch), odsyłaj do niego; jeśli nie ma, nie wykonuj jego zakresu. Ta paczka dostarcza GEOMETRIĘ I WYGLĄD GENERYCZNYCH ELEMENTÓW dachowych instalacji radiowych, żeby artysta zbudował 6–10 prefabów wielokrotnego użytku (także na innych dachach w grze). Piszesz po polsku.

ZADANIE:
1. Katalog typów elementów (bez nazw producentów i operatorów w opisach odtwarzanych w grze — „operator A/B”, kolory firm = „kolor operatora, nie odtwarzamy”): (a) maszty dachowe: rura okrągła na trójnogu/ramie balastowej, maszt kratowy 3-nożny, maszt wolnostojący na stopie, ściągany linami; (b) wysięgniki i uchwyty ścienne; (c) anteny sektorowe (panelowe) — wymiary typowe [mm] (wysokość × szerokość × głębokość), kolory (biały/jasnoszary), liczba na sektor, pochylenie; (d) anteny radioliniowe (czasze, średnica 0,3/0,6/0,9/1,2 m — z kart); (e) moduły radiowe zdalne (RRU) przy antenach — wymiary, kolor; (f) szafki/kontenery techniczne na dachu (wymiary, kolor, wentylacje), klimatyzatory szaf; (g) drabiny, tory kablowe, kable w korytkach; (h) czerwone światła przeszkodowe i oznakowanie przeszkodowe masztów (kiedy wymagane — Prawo lotnicze / rozporządzenie ULC: tylko cytat + jawny dokument). Podaj dla każdego: wymiary, kolor (opis), typowe rozmieszczenie na dachu (np. 3 sektory co 120°, odległość od attyki), wysokość nad attyką [m] w przedziale z ≥ 5 kadrów.
2. Pozycje WGS84 i opis 5–8 innych dachów w Białymstoku z instalacjami GSM, które mają kadry z dystansu (Panoramax/KartaView/Commons/Openverse; Mapillary bez cudzego tokenu): wysokość masztu ESTIMATED (metoda: proporcja do kondygnacji 3,0–3,7 m, do budynku z LoD/NMPT GUGiK), układ na dachu (ortofoto GUGiK — rzut, data arkusza), liczba sektorów. Ma to dać rozkład statystyczny „co typowo stoi na dachu 40-metrowego biurowca”.
3. Wygląd na tle nieba: sylwetka z ~100–200 m (czy anteny czytelne jako cienkie pionowe kreski, czy brył), odbicie światła (matowe/połysk), kolor pod światło. Tylko opisy z obejrzanych kadrów.
4. Formalne: wykaz stacji bazowych UKE (Pozwolenia radiowe — baza publiczna, opis co zawiera: lokalizacja, wysokość anteny n.p.m./n.p.t. — jeśli w publicznym wykazie są liczby, podaj z URL; bez danych osobowych); zasady zgłoszenia instalacji (Prawo budowlane — zgłoszenie vs pozwolenie, dla wysokości masztu) — krótko, z cytatem i URL.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, NMPT, LoD1/2), OSM (ODbL; man_made=mast/antenna), UKE (wykaz publiczny), ULC/ISAP (przepisy).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: wymiary elementów tylko z kart katalogowych (URL + liczba + cytat ≤ 25 słów; BEZ producenta w opisie) lub ESTIMATED z metodą i id kadru; nie widać = UNVERIFIED. Nie podawaj danych osobowych ani adresów prywatnych.
- Każdy kadr OBEJRZANY, zdanie „co widać”; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data, sezon, pora_dnia. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru, ponowne sprawdzenie liczb z kart i UKE) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: katalog ≥ 8 typów elementów z wymiarami i kolorem opisem; ≥ 5 dachów z rozkładem wysokości masztu nad dachem (min/mediana/max z metodą); ≥ 15 obejrzanych kadrów; jawny odsyłacz do M57 (bez powielania lokalizacji wieżowca); żadnych nazw producentów w kolumnach „opis”.

WYNIK w gałęzi: research/mistral/p24-rooftop-gsm/ z README.md (katalog elementów, rozkład na dachach, wygląd z dystansu, przepisy/UKE, luki, uzgodnienie z M57), manifest.csv (id P24-NNN; kolumny: kategoria element|dach|kadr|przepis, element, parametr, wartość, jednostka, lat, lon, osm_id, kierunek_deg, odległość_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p24-rooftop-gsm-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p24-rooftop-gsm/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M67 gotowe, PR #<numer>” i koniec.
```

## M68 — ściana lasu przy Krywlanach: sylwetka, krawędź, podszyt, gatunki

```
Repo woogitsugames/kamion. Gałąź research/mistral-p25-forest-edge od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Region Dojlidy / Krywlany. Przy trasie przy lotnisku Krywlany las w grze to proste pnie z oderwanymi kulami liści, korony nie łączą się z pniami, brak runa; ściany lasu kończą się pionową krawędzią „jak dekoracja teatralna” bez podszytu i młodnika; na horyzoncie (P11-056, Dywizjonu 303) zamiast ciemnej ciągłej linii lasu stoją płaskie prostopadłościany i pojedyncze sadzonki. Przeczytaj w repo: research/mistral/p10-greenery-3 (jeśli jest — zieleń; NIE powtarzaj ogólnych gatunków), docs/06 §2 (anti-slop), docs/05 (dane roślinności) i research/mistral/p11-dojlidy-photos (kadry z lasem). Piszesz po polsku.

ZADANIE:
1. Obszar: z BDOT10k (PTLZ — las), OSM (landuse=forest, natural=wood) i NMPT/NMT GUGiK zidentyfikuj lasy przylegające do ul. Dywizjonu 303, Mickiewicza, Kuronia i lotniska Krywlany: way_id/id obiektów, powierzchnie [ha], długość krawędzi widocznej z drogi [m], kierunek krawędzi.
2. Skład gatunkowy i wiek: Bank Danych o Lasach (BDL, Lasy Państwowe — dane otwarte: opis taksacyjny dla leśnictwa/oddziału; nadleśnictwo Żednia/Knyszyn/Supraśl wg położenia — ustal z BDL) — gatunek panujący, wiek [lata], zwarcie, wysokość [m] (bonitacja); jeśli BDL niedostępny, z literatury (Nadleśnictwo — plan urządzenia lasu streszczenie) lub „UNVERIFIED”. Z NMPT − NMT: wysokość drzew przy krawędzi (percentyle 50/90/max na pasie 0–30 m od krawędzi), rozkład wysokości, wysokość podszytu (pas 0–5 m, jeśli NMPT na to pozwala) — metoda i arkusz.
3. Profil krawędzi lasu (z kadrów): wysokość ściany lasu [m], czy jest ciągły płaszcz krzewów/młodnika (szerokość pasa [m]), kolor i gęstość o różnych porach (zima/lato/jesień — opis), czy pnie widoczne przy krawędzi, czy są korony do ziemi (świerk) czy „kolumny” sosnowe z podniesioną koroną, odstęp od ogrodzenia lotniska/drogi [m], rów, nasyp, ściółka. Gatunki widoczne z kadru (opis; do poziomu rodzaju: sosna/świerk/brzoza/dąb) — tylko jeśli rozpoznawalne.
4. Sylwetka lasu na horyzoncie z dróg (z kadrów P11-056 i podobnych): kształt linii lasu (równa / ząbkowana), przeważający odcień opisem (w zimie/lecie), stosunek wysokości lasu do wysokości widocznych budynków (ESTIMATED), pola otwarte w przerwach.
5. ≥ 20 obejrzanych kadrów krawędzi lasu i horyzontu lasu przy Krywlanach i na Podlasiu podobnych siedlisk (≥ 10 z samej okolicy; reszta — sosna/świerk z Podlasia z licencjami CC): Panoramax, KartaView, Wikimedia Commons, Openverse; Mapillary bez cudzego tokenu. Dla każdego OBEJRZYJ i opisz: gatunek panujący, wysokość ESTIMATED (metoda), obecność młodnika i podszytu, ciągłość płaszcza, sezon.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, NMPT, NMT, BDOT10k), OSM (ODbL), BDL Lasy Państwowe (dane otwarte — podaj licencję/warunki z serwisu).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: liczby z BDL/NMPT z id i metodą; z kadrów ESTIMATED z jawną metodą (proporcja do słupa 5,0–5,5 m, człowieka 1,75 m, ciężarówki 4,0 m); gatunek tylko jeśli rozpoznawalny, inaczej UNVERIFIED. Kolor tylko opisem.
- Każdy kadr OBEJRZANY, zdanie „co widać”; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data, sezon, pora_dnia; przypisanie do lasu ≤ 80 m od krawędzi PTLZ (id i odległość w uwagach). JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru, ponowne odczytanie 2 wartości NMPT z podanej metody, ponowne sprawdzenie wpisu BDL) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: lista kompleksów leśnych przy trasie z id i powierzchnią; dla każdego wysokość drzew (NMPT, percentyle) i gatunek panujący (BDL lub UNVERIFIED); profil krawędzi z liczbami (wysokość ściany, szerokość płaszcza krzewów) z ≥ 8 kadrów; ≥ 20 kadrów; gotowy „przepis” w README: 5–8 punktów dla artysty („wysokość korony przy krawędzi X–Y m, płaszcz krzewów Z m, pnie widoczne na ≥ …”), każdy ze źródłem.

WYNIK w gałęzi: research/mistral/p25-forest-edge/ z README.md (obszar, gatunki, wysokości NMPT, profil krawędzi, horyzont, przepis dla artysty, luki), manifest.csv (id P25-NNN; kolumny: kategoria obszar|gatunek|wysokość|krawędź|horyzont|kadr, element, parametr, wartość, jednostka, osm_id, lat, lon, kierunek_deg, odległość_od_krawędzi_m, data_zdjęcia, sezon, pora_dnia, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p25-forest-edge-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p25-forest-edge/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M68 gotowe, PR #<numer>” i koniec.
```

## M69 — nocne zdjęcia ulic: oprawy latarni, rozstaw, barwa i kształt pul światła (UZUPEŁNIENIE M60)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p26-night-lamps od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1, gra komercyjna. Recenzja zmierzchu (0182): pod latarniami nie ma plam światła (plac i jezdnia równo jasne), oprawy bez halo. ZAKRES ROZŁĄCZNY Z M60 (docs/owner/MISTRAL-TASKS-9.md): M60 dostarcza fizykę zmierzchu (niebo, lx), klasy PN-EN 13201, luminancje wymagane, rozstaw z BIP/ortofoto, zapalone okna i ≥ 10 zdjęć z opisem „czy są plamy”. TA paczka dostarcza dane do ustawienia ŚWIATEŁ w silniku: typ i geometria opraw (kształt, wysięg ramienia, pochylenie), rozstaw i układ na KONKRETNYCH ulicach, barwa światła z kadrów oraz kształt i wielkość pul światła (wymiary na jezdni). Jeśli research/mistral/p17-dusk-lighting/ jest już w origin (git fetch) — wykorzystaj jego tabelę ulic jako punkt wyjścia i NIE powtarzaj; jeśli nie, nie wykonuj zakresu M60 (norm, nieba, okien). Przeczytaj też research/mistral/p9-furniture-3/README.md (wysokości latarni — NIE powtarzaj) i docs/adr/0182-*.md. Piszesz po polsku.

ZADANIE:
1. Inwentarz opraw na trasie (ul. gen. Andersa, Al. Tysiąclecia Państwa Polskiego, ul. Gen. Maczka, rondo Putry, ul. Sokólska/Wysockiego/Kombatantów, Dojlidy: Kuronia/Mickiewicza/Dywizjonu 303): z OSM (highway=street_lamp, support, lamp_mount, light:colour, light:method, height) pobierz węzły i policz rozstawy kolejnych słupów [m] dla ≥ 8 odcinków po ≥ 10 par (podaj datę zapytania i treść zapytania; wynik: min/mediana/max, układ jednostronny/obustronny/szachownica/oś rozdzielająca — z kadrów). Rozbieżność OSM vs ortofoto vs kadry — osobno.
2. Typ oprawy (z kadrów dziennych i nocnych; bez marek i modeli): kształt (płaska płyta LED „cobra”, okrągły klosz, latarnia klasyczna/parkowa, projektor), liczba ramion (1/2), wysięg ramienia [m] ESTIMATED, pochylenie oprawy [°] ESTIMATED, wysokość montażu [m] (z p9 jeśli jest, inaczej z kadrów), kolor słupa (opis). Kolumna słup+oprawa: sylwetka. Każdy typ z ≥ 3 kadrami.
3. NOCNE zdjęcia (≥ 20; Panoramax, KartaView, Wikimedia Commons, Openverse; Mapillary bez cudzego tokenu): wybieraj kadry po zmroku lub w ciemności z włączonymi latarniami. OBEJRZYJ każdy i opisz: (a) barwa światła opisem (sodowe pomarańczowe/ciepłe białe/neutralne białe/zimne białe), (b) czy widać pulę światła pod latarnią i jej zasięg względem szerokości jezdni (ułamek szerokości jezdni 0–1 ESTIMATED), (c) ciemne przerwy między pulami (czy jezdnia „skacze” w jasności), (d) halo/rozbłysk wokół oprawy (brak/słabe/silne, promień ułamkiem wysokości słupa), (e) odbicia w mokrym asfalcie, (f) czy chodnik/DDR ma osobne światło. Nie podawaj RGB ani luminancji z pikseli.
4. Barwa: z BIP/przetargów ZDM Białystok — typ źródła na ulicy (HPS / LED 3000 / 4000 K), moc oprawy [W] jeśli w dokumentach, rok modernizacji; podaj CCT tylko jeśli jest w dokumencie (URL + cytat ≤ 25 słów + strona). Powiąż z barwą z kadrów (spójność TAK/NIE).
5. Wnioski „dla silnika” (z liczb powyżej, nie z wyobraźni): tabela ulica → układ → rozstaw mediana [m] → wysokość [m] → barwa → ułamek jezdni oświetlony przez jedną oprawę → halo (brak/słabe/silne).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła dozwolone (D43): Mapillary (bez cudzego tokenu), KartaView, Panoramax (CC BY-SA 4.0), Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto), OSM (ODbL), BIP/ZDM Białystok (dokumenty urzędowe).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: rozstawy z węzłów OSM lub z ortofoto z liczbą próbek; z kadrów ESTIMATED z metodą (proporcja do pasa 3,0–3,5 m, słupa, tira 4,0 m); nie widać = UNVERIFIED. Kolor tylko opisem słownym. Pomiarów z pikseli NIE podawaj jako luminancji.
- Każdy kadr OBEJRZANY, zdanie „co widać”; pozycja WGS84 (6 miejsc), kierunek_deg (API/EXIF albo UNVERIFIED), data i godzina; przypisanie do ulicy ≤ 25 m od osi OSM (way_id i odległość). JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne zapytanie rozstawu dla 2 odcinków, ponowne obejrzenie kadrów i porównanie z opisem, ponowne sprawdzenie cytatów BIP) — README + audit_20_percent.json.

KRYTERIA AKCEPTACJI: ≥ 8 odcinków z rozstawami (n próbek podane); ≥ 4 typy opraw z sylwetką i ≥ 3 kadrami każdy; ≥ 20 nocnych kadrów z odpowiedziami a–f; tabela „dla silnika” dla każdej ulicy; źródło barwy dla ≥ 4 ulic; brak powielenia zakresu M60.

WYNIK w gałęzi: research/mistral/p26-night-lamps/ z README.md (zapytanie OSM + data, rozstawy, typy opraw, nocne kadry, barwa, tabela „dla silnika”, luki, uzgodnienie z M60), manifest.csv (id P26-NNN; kolumny: kategoria odcinek|oprawa|kadr|barwa, ulica, way_id, element, parametr, wartość, jednostka, lat, lon, kierunek_deg, data_godzina, opis_co_widać, ułamek_jezdni_oświetlony, halo, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json oraz overpass-result.json (≤ 5 MB). ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p26-night-lamps-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p26-night-lamps/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M69 gotowe, PR #<numer>” i koniec.
```

---

## Kolejność priorytetów (M62–M69) i uzasadnienie

1. **M62 brama szpitala** — jedyny kadr z grupy P11 oceniony N bez żadnej poprawki; agent świata nie ma żadnych wymiarów muru, słupów ani znaków; bramka 3 (Dojlidy).
2. **M65 DDR z czerwonego asfaltu** — „polski wyróżnik ulicy” brakuje w 001 i 056 i na trasie C; dotyczy dużej liczby odcinków, więc blokuje generator nawierzchni.
3. **M68 las** — P1 w recenzji (route-2, 056); widoczny z całej trasy przy lotnisku; ADR roślinności/horyzontu zależy od danych o wysokościach i krawędzi.
4. **M63 zakład z dominantą i bramy** — Rosti +12 % wysokości, schodek, okładzina, 2 bramy (P1/P2 w 0179); `building_part` już istnieje, brakuje liczb.
5. **M66 sygnalizatory** — tarcza placeholder (P2), ale występuje na każdym skrzyżowaniu; tania poprawka po danych.
6. **M69 nocne latarnie** — P1-4 recenzji 0182 (plamy latarni); uruchamiać po M60 lub równolegle z uzgodnieniem zakresu.
7. **M64 lotnisko Krywlany** — kamera kontrolna pasa ważna dla dowodu, ale część danych dostarcza M58; startować po M58 (git fetch) albo równolegle z uzgodnieniem.
8. **M67 maszty GSM** — P2 wizualny, zależny od M57 (lokalizacja i liczba na dachu).

Równoległość: M62, M63, M65, M66, M68 są niezależne; M64 czeka na M58, M67 na M57, M69 na M60 (lub jawne uzgodnienie zakresu w README). Numeracja gałęzi: `p19…p26`.

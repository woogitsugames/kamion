# P11 — zdjęcia referencyjne regionu Dojlidy / Krywlany (Białystok) — **v2 (M47-FIX)**

Zadanie **M47** z paczki 03 (`docs/owner/MISTRAL-TASKS-8-RESEARCH.md`), kontynuacja serii paczek referencyjnych (kolumny manifestu jak w paczce P1).
Gałąź: `research/mistral-p11-dojlidy-photos`. Zakres zmian w repo: **wyłącznie** katalog `research/mistral/p11-dojlidy-photos/`.

**Wersja v2 (poprawka M47-FIX)** po przeglądzie `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p11-p12.md`. Przegląd wykazał, że kolumna `punkt_opis` i lista „15 najlepszych kadrów" w wersji 1 powstały **bez oglądania zdjęć** — co było niedopuszczalne. W tej wersji:

* **każdy z 143 JPG obejrzał model wizyjny** (2026-11-13); `punkt_opis` opisuje teraz to, co faktycznie widać (obiekt, kadr, poziom kamery);
* 8 kadrów nieprzydatnych (wnętrza, zabawki, makieta/tablica, zbliżenie roślinności) → status **REJECTED** z powodem — usunięte z archiwum ZIP v2;
* dodane kolumny **`typ_kadru`** (widok/detal) i **`w_kaflu_0166`** (przeliczenie WGS84→EPSG:2180);
* nowa lista **15 najlepszych kadrów** wybrana wyłącznie spośród obejrzanych, leżących w kaflu 0166, z poziomu jezdni;
* statusy odrzuceń ujednolicone: `ODRZUCONE` → **`REJECTED`**.

## 1. Kafel 0166

Kafel `bialystok-dojlidy`: **prostokąt w EPSG:2180 (PL-CS92) [779019, 589055, 781067, 591103]** — kwadrat 2048×2048 m (X: 779019–781067, Y: 589055–591103). Kolumna `w_kaflu_0166` w manifeście liczona jest dokładnie wobec tego prostokąta.

Przeliczenie WGS84→EPSG:2180 wykonano własną implementacją odwzorowania **Transverse Mercator (GRS80, λ0=19°, k0=0,9993, FE=500 000, FN=−5 300 000)** — pakiet `pyproj` był **niedostępny** w środowisku wykonawczym poprawki; implementacja (`tm2180.py`) zweryfikowana na narożnikach kafla, zgodność <0,05 m.

Przybliżony odpowiednik WGS84 środka kafla: ~53,1050 N; 23,1910 E (bbox ~ lat 53,096–53,114, lon 23,176–23,206 — aproksymacja z v1; rozstrzygające jest zawsze przeliczenie do EPSG:2180).

W kaflu mieszczą się w całości: strefa SSSE Dojlidy (way 234838470), browar Dojlidy (way 221826898), osiedla Borsucza/Kormoranów/Niedźwiedzia, **park pałacowy Lubomirskich** z pałacem (NE; poprawka nazwy: w v1 błędnie „Park Centralny") oraz **wschodni fragment lotniska Krywlany** (way 234838628 — pas/ogrodzenie od 23,176 do 23,1887; terminal, hangary i apron leżą na zachód, poza kaflem).

**O drogach z założenia zadania:** wg OSM w tym rejonie oznaczone są **DK19** (ref=19: Ks. Suchowolca, Dojlidy Fabryczne, rondo Meyera) i **DK678** (ref=678: Konstantego Ciołkowskiego). **DK65 nie jest oznakowana w bbox**, a **S19** (obwodnica) biegnie daleko poza kaflem.

## 2. Drogi ciężarówek w kaflu (wg OSM, ODbL; eksport API 23,155–23,235 / 53,088–53,122)

| droga | highway | ref | hgv | rola dla ruchu ciężarówek |
|---|---|---|---|---|
| Jacka Kuronia | trunk | — | brak ograniczeń | oś W–E kafla, dojazd do SSSE i browaru |
| Dywizjonu 303 | trunk → primary | — | brak ograniczeń | krawędź zach./wsch., płd. ogrodzenie lotniska |
| Konstantego Ciołkowskiego | trunk/primary | 678 | brak | narożnik NW, wjazd od ronda Meyera |
| Księdza Stanisława Suchowolca | secondary → trunk | 19 | no (odcinki lokalne) | DK19, wlot wsch. + korytarz E |
| Dojlidy Fabryczne | secondary | 19 | no (odcinki) | DK19 północ, rondo Hasbacha |
| Adama Mickiewicza | tertiary | — | brak | oś N–S kafla (Sąd, Archiwum, SSSE) |
| Wiewiórcza | tertiary | — | no | północ kafla, zakłady |
| Myśliwska (tertiary N + unclassified S) | tertiary/unclassified | — | no (tertiary) | oś SSSE — bramy zakładów |
| Franciszka Karpińskiego | unclassified | — | brak | SSSE — bramy, place manewrowe |
| Karola Modzelewskiego | unclassified | — | brak | SSSE północ |
| Pułkownika Czesława Hake | unclassified | — | brak | zachód kafla |
| Żurawia | unclassified | — | no | szpital, BPN-T |
| Borsucza, Kormoranów, Sępia, Ptasia, Niedźwiedzia | residential | — | no (Kormoranów, Sępia, Ptasia, Niedźwiedzia) | osiedla SSSE — place manewrowe |
| service (bez nazw, np. #572484394, #482308216) | service | — | — | bramy zakładów, place składowe |

Ronda w obrębie/z przy granicy kafla: **rondo Artura Hasbacha** (19; Suchowolca × Fabryczne × Myśliwska — w kaflu), rondo Wünschego (zach., korytarz), rondo Meyera (19;678 — płn., korytarz). Wiadukty: w bbox **brak** — mosty na rzece Białej leżą tuż za płn. granicą.

## 3. Metoda naboru

* **Źródła (zgodnie z twardymi zasadami):** Wikimedia Commons API (geosearch `gscoord`+`gsradius`, `imageinfo` z EXIF GPS/licencją; licencje CC0/BY/BY-SA — wszystkie komercyjne), OSM API, Panoramax API, KartaView API, Openverse API. **Zakaz Google/Street View/Earth/3D Tiles dotrzymany.**
* **Wyniki sondaży ujemnych:** Panoramax — 0 kadrów w kaflu (3 w promieniu ~3 km, poza kaflem — wiersze UNVERIFIED); KartaView — 0; Openverse — 2 kandydatów bez geolokalizacji + 2 pliki Flickr NC (tylko referencja). Mapillary — brak tokenu: UNVERIFIED, nie sondowano, kluczy nie zgadywano.
* **Pozycja:** WGS84 z EXIF GPS Commons (`lat`/`lon`, 6 miej. po przecinku).
* **Przypisanie do drogi:** odległość punkt–polilinia (equirectangular, φ0=53,105°) do osi OSM; kategorie `droga`/`skrzyżowanie`/`wlot`/`wylot`/`korytarz` — ≤ 25 m; `rondo` — ≤ 27 m (dokładność GPS EXIF ±10 m; dwa kadry wlotowe 25,1/26,3 m — adnotacja w wierszu). Kategorie `brama_zakład` i `obiekt` to POI — bez reguły ≤ 25 m, rzeczywisty dystans do osi wpisany w `uwagi`.
* **Kierunek (`kierunek_deg`):** `UNVERIFIED` — EXIF `GPSImgDirection` nieobecny w 100 % plików Commons; API Panoramax nie zwraca azymutu. **Luka podstawowa** — kierunki jazdy wymagają odsiewu z kamery produkcyjnej.
* **Jakość 1–5:** heurystyka metadanych (baza 3, +1 za ≥2500 px, −1 za <1200 px, +1 za ≤8 m od osi, −1 za >20 m) — **nie zależy od treści kadru**; treść oceniają oględziny (§4).
* **JPG ≤ 1600 px:** miniatury `thumb.php …width=1600`; wymiary potwierdzone parserem SOF/PIL.
* **Opisy bez marek producentów ciężarówek** — dotrzymane (pojazd pomocniczy na P11-057 opisany neutralnie, bez oznaczeń).

## 4. Oględziny kadrów (nowość v2) — metodologia i wyniki

* **Data:** 2026-11-13. **Każdy z 143 JPG** (wszystkie wiersze pobrane jako SOURCED w v1) **obejrzano przez model wizyjny** w 16 partiach; wyniki zapisane w plikach roboczych oględzin.
* Na podstawie oględzin przepisano **kolumnę `punkt_opis`** każdego wiersza: co widać (obiekt), jaki kadr oraz na jakim poziomie stała kamera.
* Nowa kolumna **`typ_kadru`**: `widok` (kadr wzdłuż/poprzecznie na jezdnię — kandydaci do kamer kontrolnych) albo `detal` (kadr na obiekt poza jezdnią: brama, elewacja, znak, hala — zostają w materiale SOURCED jako referencja modelarska, nie nadają się na kamery kontrolne). Wiersze REJECTED/UNVERIFIED: `-`.
* Nowa kolumna **`w_kaflu_0166`**: `true`/`false` wg przeliczenia WGS84→EPSG:2180 (§1); `UNVERIFIED` dla wierszy bez współrzędnych (P11-151…154).
* **Poziom kamery (wg oględzin, w `uwagi` każdego wiersza):** 100 kadrów pieszo ~1,6 m; **32 kadry z poziomu ~2,5 m (zbliżone do oczu kierowcy)**; 3 kadry z odczytem niejednoznacznym (~1,6 m). Jednolita klauzula z v1 („wszystkie kadry pieszo") była **nieprawdziwa** — usunięta.
* **Odrzucenia po oględzinach (8 wierszy → REJECTED, usunięte z ZIP v2):**

| id | co faktycznie widać | powód REJECTED |
|---|---|---|
| P11-008 | zbliżenie na roślinność (drzewa, krzewy, trawa z kwiatami) | zbliżenie bez kontekstu drogi |
| P11-084 | tablica z planem osiedla Dojlidy | dokument/tablica — nie widok terenu |
| P11-090 | zabawkowy robot edukacyjny na biurku | zabawka — zdjęcie produktowe bez kontekstu drogi; znak towarowy |
| P11-091 | zabawkowy robot edukacyjny z przodu | j.w. |
| P11-092 | zabawkowy robot edukacyjny ustawiony odwrotnie | zabawka — zdjęcie produktowe bez kontekstu drogi |
| P11-124 | wnętrze czytelni (ludzie, książki) w gmachu Archiwum | wnętrze — nie widok terenu |
| P11-125 | wnętrze gmachu — korytarz, posadzka w szachownicę | wnętrze — nie widok terenu |
| P11-132 | wnętrze szpitala tymczasowego — korytarz | wnętrze — nie widok terenu |

* **Prostowanie błędnych opisów z v1:** P11-084 to **tablica z planem osiedla** (nie wlot ronda); P11-094 to **hala Rosti** przy ul. Kuronia (nie brama browaru — brama browaru to P11-120); P11-121 to ceglana zabudowa XIX-wieczna browaru — **kominów w kadrze brak** (lista v1 wskazywała nieistniejące w kadrze kominy); „Park Centralny" → park pałacowy Lubomirskich.
* **Liczniki po poprawkach:** manifest 154 wiersze = **135 SOURCED + 16 REJECTED + 3 UNVERIFIED**; w kaflu 0166: **73 ze 135 SOURCED** (50 `widok`, 23 `detal`); `typ_kadru`: 88 `widok` / 47 `detal`.
* **M47-FIX-3 (2026-11-13, po przeglądzie s20):** kody znaków poprawione w 16 wierszach wg `docs/reports/REVIEW-2026-11-13-s20-mistral-m47-fix2.md` §3 (13 wierszy z błędnym kodem + STOP w P11-120 + sygnalizacja i C-13 w P11-063 + „znak ostrzegawczy” w P11-106 = żółta skrzynka przycisku dla pieszych). Reguły s20: niebieski kwadrat z pieszym to D-6; A-16 to czerwony trójkąt; znak widziany od tyłu opisujemy „<kształt> od tyłu (prawdopodobnie A-7/B-20)” i nie usuwamy; kod wpisujemy tylko przy czytelnym symbolu na wycinku 3× z pełnej rozdzielczości, inaczej „znak nieczytelny”; żółta skrzynka przy sygnalizatorze to przycisk dla pieszych, nie znak. Kody znaków w wierszach niesprawdzonych w REVIEW s20 §3 (m.in. 041, 056, 067, 069, 070, 071, 076, 083, 089, 096, 104, 105, 110, 122, 126) pozostały z audytu M47-FIX-2 — niezweryfikowane na wycinkach s20.

## 5. Tabela pokrycia (bez zmian względem v1 — pozycje i kategorie; opisy przepisane po oględzinach)

*Uwaga: liczby obejmują wiersze SOURCED+REJECTED oglądane; 8 z nich (P11-008, 084, 090–092, 124–125, 132) jest obecnie REJECTED.*

| droga / obiekt | kadry | kategorie | sezony | lata |
|---|---|---|---|---|
| Jacka Kuronia (+ browar, zakłady) | 27 | droga 13, skrzyż. 2, brama 8, obiekt 4 | jesień, lato, zima | 2012–2024 |
| Adama Mickiewicza (+ Sąd, Archiwum) | 20 | droga 13, skrzyż. 4, obiekt 3 | jesień, lato, zima | 2012, 2018–2024 |
| Wiewiórcza | 9 | droga, skrzyż. | jesień, lato | 2019, 2020, 2022, 2023 |
| Myśliwska | 3 | wlot, droga | jesień | 2022 |
| Franciszka Karpińskiego | 7 | droga, skrzyż. | lato | 2010, 2024 |
| Borsucza (+ Starostwo) | 8 | droga, obiekt | jesień, lato | 2020, 2022, 2023 |
| Kormoranów | 2 | droga | lato | 2020 |
| Żurawia (+ szpitale, BPN-T) | 5 | droga, obiekt | jesień, lato, zima | 2019, 2020 |
| Niedźwiedzia | 6 | droga | lato | 2022 |
| Karola Modzelewskiego | 3 | droga, skrzyż. | jesień | 2022 |
| Pułkownika Czesława Hake | 1 | droga | jesień | 2022 |
| Dywizjonu 303 (+ rondo Wünschego, Krywlany) | 12 | droga 2, skrzyż. 1, wlot 1, rondo 3, korytarz 2, obiekt 3 | lato | 2012, 2020, 2023 |
| Konstantego Ciołkowskiego | 4 | droga, korytarz | jesień, lato | 2015, 2022, 2023 |
| Rondo Artura Hasbacha (+ pałac) | 7 | rondo 5, obiekt 2 | lato, zima | 2008, 2012, 2020, 2022, 2023 |
| Rondo Meyera (+ Nowowarszawska) | 6 | rondo, korytarz | lato | 2021, 2023 |
| Ks. Suchowolca (rondo, domy przyfabryczne, korytarz E, park) | 12 | korytarz, obiekt | lato, zima | 2008, 2013–2015, 2020–2023 |
| Dojlidy Fabryczne | 5 | droga, korytarz | lato | 2020, 2021, 2023 |
| Dojlidy Górne (korytarz SE) | 4 | korytarz | lato | 2024 |
| Grabowa (korytarz S) | 2 | korytarz | lato | 2024 |

Wymóg „≥ 3 ujęcia na drogę" spełniają drogi główne z pełnymi seriami; „≥ 6 kadrów na rondo" — rondo Hasbacha (7) i rondo Wünschego (6 z korytarzem zachodnim). „Oba kierunki" — **nieweryfikowalne** (brak azymutów); zamiast tego zróżnicowane pozycje i serie.

## 6. Luki (uczciwie)

1. **Poziom kamery:** po oględzinach — 100 kadrów pieszo ~1,6 m, 32 kadry ~2,5 m (poziom kierowcy), 3 odczyt niejednoznaczny. Brak sterowanych sesii z wysokości 2,5 m; kadry piesze pozostają materiałem pomocniczym, nie kalibracyjnym.
2. **Kierunki jazdy UNVERIFIED** — zero azymutów w EXIF/Panoramax API.
3. **Dywizjonu 303 w kaflu — tylko 3 kadry** (seria zachodnia w korytarzu).
4. **Konstantego Ciołkowskiego w kaflu — 1 kadr**; **Hake — 1**, **Kormoranów — 2**, **Myśliwska — 3 bez drugiego sezonu**, **Modzelewskiego — 3 (jeden sezon)**.
5. **Jeden sezon:** Karpińskiego, Kormoranów, Niedźwiedzia, Hake, Dywizjonu 303 (poza narożnikiem Sądu), Dojlidy Fabryczne, rondo Meyera, rondo Wünschego, Nowowarszawska, Dojlidy Górne, Grabowa.
6. **Lotnisko Krywlany: 0 kadrów w kaflu**; 3 kadry hangarów (P11-133/134/135) leżą na zachód od kafla (`w_kaflu_0166`=false) i są detalami.
7. **Wiadukty: 0** — w bbox nie ma obiektów mostowych.
8. **Panoramax/KartaView: 0** w kaflu; **Mapillary: niesprawdzony** (brak tokenu).
9. Dwa kadry wlotowe ronda Hasbacha na granicy 25–26,3 m od obrysu (dokładność GPS EXIF; adnotacje w wierszach P11-081/P11-082).
10. **Niepewne odczyty szyldów** (jawna adnotacja w `punkt_opis`): P11-019 i P11-028 — dwa niezgodne odczyty modelu → opisane generycznie („szyld firmowy, odczyt niejednoznaczny"). P11-047: w kadrze tablica „ul. Bartnicza" przy pozycji GPS ul. Niedźwiedziej (narożnik).

## 7. 15 najlepszych kadrów do kamer kontrolnych (v2)

Wybór **wyłącznie** spośród kadrów: (a) obejrzanych (§4), (b) `typ_kadru` = `widok` (kadr na jezdnię, z poziomu jezdni), (c) `w_kaflu_0166` = `true`, (d) status SOURCED.

| # | id | miejsce | dlaczego |
|---|---|---|---|
| 1 | P11-001 | Kuronia — SSSE, hala „Contri" z bramą wjazdową | wzorcowy kadr strefy: jezdnia, znak B-33 (20 km/h), latarnie, hala; rozpoznawalny wjazd |
| 2 | P11-002 | Kuronia — hala „Masterpress" | kadr wzdłuż jezdni z poziomu ~2,5 m — najbliższy perspektywie kierowcy |
| 3 | P11-005 | Kuronia — hala „Bravilor Bonamat" | poprzeczny kadr na jezdnię ze znakiem C-2 (nakaz jazdy w prawo); poziom ~2,5 m |
| 4 | P11-014 | Mickiewicza — sygnalizacja świetlna | jedyny kadr z sygnalizacją na osi N–S kafla; poziom ~2,5 m |
| 5 | P11-026 | Mickiewicza — jednojezdniowa z pasem zieleni | charakterystyczny przekrój drogi głównej kafla |
| 6 | P11-027 | Wiewiórcza — zabudowa szeregowa z kostką brukową | kadr osiedlowy północy kafla, czytelna zabudowa |
| 7 | P11-043 | wlot ul. Kormoranów | tablica ulicy + znak B-5 (zakaz wjazdu ciężarówek, z tabliczką o ruchu lokalnym): jednoznaczny punkt nawigacyjny |
| 8 | P11-056 | Dywizjonu 303 — skrzyżowanie przy krawędzi lotniska (bez sygnalizacji) | A-7 + D-6 + otwarta przestrzeń lotniska; poziom ~2,5 m |
| 9 | P11-063 | Mickiewicza — hala „Bravilor" przy jezdni | narożnik Kuronia × Mickiewicza: brama SSSE od północy |
| 10 | P11-066 | Wiewiórcza — B-5 (zakaz wjazdu ciężarówek) + B-20 STOP | znaki istotne dla ruchu ciężarówki, czytelne w kadrze |
| 11 | P11-067 | Wiewiórcza — skrzyżowanie ze sklepem przy Żurawiej (bez sygnalizacji) | D-6 + D-18 + rozpoznawalny szyld sklepu; kadr poprzeczny |
| 12 | P11-077 | Dywizjonu 303 × Mickiewicza — pasy do skrętu przy Sądzie | węzeł Sądu Rejonowego z przystankiem; poziom ~2,5 m |
| 13 | P11-094 | Kuronia — hala Rosti przy jezdni | szara hala Rosti (prost. z v1: to nie brama browaru); charakterystyczna bryła |
| 14 | P11-128 | Borsucza — gmach urzędu przy jezdni | przejście dla pieszych + D-6 + D-18 + gmach Starostwa z flagami: czytelny kadr osiedlowy |
| 15 | P11-129 | Żurawia — wjazd na teren szpitala | brama z tablicami i szlabanem (biało-czerwone ramię), znaki (B-20 STOP, B-33 — 20 km/h, nakaz jazdy w prawo C-1/C-2); jesień |

Wszystkie 15: `w_kaflu_0166`=true, `typ_kadru`=widok, obejrzone 2026-11-13.

## 8. Samokontrola 20 % (seed 20261113) — zdania „co widać"

Losowanie bez zwracania `random.Random(20261113).sample(id_wierszy, ceil(0.2·154))` → **31 wierszy** (ta sama próba co v1). Dla każdego wylosowanego wiersza jedno zdanie opisujące, co widać — zgodne z `punkt_opis` w manifeście (pełne wyniki kontrolei: `audit_20_percent.json`):

| id | status | co widać |
|---|---|---|
| P11-003 | SOURCED | Widać halę z szyldem „Contri" z bramą wjazdową i budką ochrony za ogrodzeniem; w kadrze fragment jezdni i chodnika. |
| P11-004 | SOURCED | Widać jezdnię dwukierunkową z wydzielonym chodnikiem, ogrodzenie z siatki i budynki przemysłowe w tle. |
| P11-005 | SOURCED | Widać jezdnię i halę z szyldem „Bravilor Bonamat"; znak C-2 (nakaz jazdy w prawo za znakiem) i roślinność. |
| P11-008 | REJECTED | Widać wyłącznie roślinność (drzewa, krzewy, trawa z kwiatami) — jezdni brak w kadrze (REJECTED). |
| P11-013 | SOURCED | Widać jezdnię dwupasmową ze znakami (A-7 ×2: przy tablicy ulicy — od tyłu; w głębi nad D-6; D-6 przejście dla pieszych; C-13/16 — pieszy+rower), latarnie i zieleń. |
| P11-014 | SOURCED | Widać jezdnię z pasami ruchu, sygnalizację świetlną, latarnie, pojazdy i drzewa. |
| P11-017 | SOURCED | Widać jezdnię dwukierunkową z wysepką oraz budynek z szyldem „CYPRYS". |
| P11-018 | SOURCED | Widać nowy gmach Archiwum Państwowego z szyldem i flagą, za ogrodzeniem i trawnikiem. |
| P11-025 | SOURCED | Widać jezdnię dwupasmową z wydzielonym chodnikiem, latarnie, drzewa i krzewy. |
| P11-029 | SOURCED | Widać jezdnię dwukierunkową, ogrodzenie z bramą i tablicę z cenami paliwa. |
| P11-034 | SOURCED | Widać jezdnię, budynki przemysłowe i plac z paletami oraz maszty z flagami. |
| P11-037 | SOURCED | Widać ogrodzenie placu budowy z szyldami (m.in. „Starostwo Powiatowe", „budimex") i znak D-1 (droga z pierwszeństwem). |
| P11-046 | SOURCED | Widać bramę wjazdową z siatki, plac budowy z koparką i budynek wielokondygnacyjny w tle. |
| P11-067 | SOURCED | Widać skrzyżowanie bez sygnalizacji świetlnej (wg M47-FIX-2), budynki mieszkalne, szyld sklepu „Biedronka" i znaki D-6/D-18. |
| P11-077 | SOURCED | Widać jezdnię dwupasmową z pasami do skrętu, przystanek autobusowy i budynek biurowy (Sąd Rejonowy). |
| P11-078 | SOURCED | Widać wlot na rondo; jezdnie, chodnik, znaki (A-7, C-12 ×2 — nakaz jazdy dookoła ronda, w głębi B-33 — 70 km/h, B-36, D-3, D-6, C-13, tablice U-3 — szewrony) i latarnie. |
| P11-079 | SOURCED | Widać jezdnię dwukierunkową z pasem rowerowym, znaki (B-33 — 70 km/h, B-36, D-3, C-13 — okrągły, D-6) i ogrodzenie z banerami. |
| P11-086 | SOURCED | Widać jezdnię dwupasmową z pasem rozdziału zieleni, bariery ochronne, latarnie, pojazdy i znaki (B-2, D-6 ×2, tablice z numerem drogi 678). |
| P11-088 | SOURCED | Widać jezdnię przy rondzie oraz budynek z logo McDonald's i billboard. |
| P11-094 | SOURCED | Widać jezdnię i szarą halę z szyldem „Rosti" — to hala Rosti, nie brama browaru. |
| P11-101 | SOURCED | Widać rondo z trawnikiem centralnym i krzewami, latarnie, tablicę i budynki mieszkalne. |
| P11-112 | SOURCED | Widać jezdnię, dom z ogrodzeniem, zaparkowane pojazdy i latarnię. |
| P11-118 | SOURCED | Widać jezdnię oraz dom z czerwonym dachem za ogrodzeniem, latarnie i drzewa. |
| P11-125 | REJECTED | Widać wnętrze gmachu — korytarz z posadzką w szachownicę, kolumny, drzwi i tablicę informacyjną (REJECTED). |
| P11-128 | SOURCED | Widać jezdnię dwukierunkową, budynek urzędu (Starostwo Powiatowe) z flagami, przejście dla pieszych, chodnik, latarnie i znaki (D-6, D-18). |
| P11-130 | REJECTED | Wiersz dokumentacyjny: wg manifestu kadr z serii szpitala tymczasowego przy Żurawiej — oryginał PNG; pliku nie ma w ZIP v2. |
| P11-132 | REJECTED | Widać wnętrze szpitala tymczasowego — korytarz z drzwiami, balustradą, gaśnicą i znakami ewakuacyjnymi (REJECTED). |
| P11-143 | SOURCED | Widać budynek WSWFiT z czerwoną elewacją i szyldem, za szlabanem (biało-czerwone ramię); latarnia i drzewa. |
| P11-144 | SOURCED | Widać pałac Lubomirskich od strony parku — dwukondygnacyjny gmach z parkingiem przed budynkiem. |
| P11-151 | REJECTED | Wiersz referencyjny: wg sources.md zdjęcie „Lotnisko na Krywlanach" — brak geolokalizacji, tylko referencja. |
| P11-152 | REJECTED | Wiersz referencyjny: wg sources.md zdjęcie „Dojlidy Białystok" z Openverse — brak geolokalizacji, tylko referencja. |

Wynik samokontroli: **31/31 zgodnych z manifestem**; 25 plików SOURCED w próbie sprawdzonych w ZIP v2 (wymiary ≤1600 px, licencje komercyjne, dystanse wg reguł), URL-e źródeł odświeżone HTTP 200.

## 9. Pliki

* `manifest.csv` — 154 wiersze (**135 SOURCED + 16 REJECTED + 3 UNVERIFIED**); kolumny: id, ulica, **punkt_opis (po oględzinach)**, **typ_kadru**, lat, lon, **w_kaflu_0166**, kierunek_deg, data_zdjęcia, sezon, pora_dnia, panoramax_id, jakość_1_5, odrzucone_powód, url_źródła, licencja, autor, data_dostępu, status, uwagi.
* `sources.md` — źródła, licencje, daty dostępu, wyniki sondaży ujemnych, suma kontrolna archiwum v2.
* `audit_20_percent.json` — samokontrola 20 % (31/154), seed **20261113**, 31/31 OK (zdania „co widać", pliki, wymiary, licencje, dystanse, URL-e).
* `.gitignore` — `files/` i archiwa ZIP wykluczone z gita (zdjęcia NIE trafiają do repo).
* **ZIP zdjęć v2:** `mistral-p11-dojlidy-photos-files-v2.zip` — **135 plików JPG** (bez 8 odrzuconych po oględzinach), 62 921 246 B (60,0 MB), SHA256 `8fdf147738eb5e5a64cf56c84fc535432bac6794243437b0cd538fefc94668f0`; **poza gitem** — publikowany przez kartę pobrania przy PR. Wewnątrz: `files/P11-NNN.jpg` zgodne z wierszami SOURCED.
  Archiwum v1 (`mistral-p11-dojlidy-photos-files.zip`, SHA256 `13f22c26…`) zostało **zastąpione**: w środowisku wykonawczym poprawki nie był dostępny oryginalny plik roboczy v1, więc v2 zbudowano ponownie z miniatur Wikimedia Commons (≤1600 px); pliki mogą się różnić bajtowo od v1 (re-download), identyfikatory, opisy i licencje bez zmian.

## 10. Legenda statusów

`SOURCED` — pozycja/data z EXIF źródła (Commons), plik pobrany, zweryfikowany i **obejrzany** (2026-11-13); `ESTIMATED` — wartość wyliczona (sezon, pora dnia, jakość); `UNVERIFIED` — nie do zweryfikowania w dostępnym API (kierunek wszystkich kadrów; pozycja/data Panoramax); `REJECTED` — kadr odrzucony z powodem w kolumnie `odrzucone_powód` (licencje NC, brak GPS, duplikaty, poza zakresem, PNG, a po oględzinach: wnętrza, zabawki, tablice/dokumenty, zbliżenia bez kontekstu drogi). Status `ODRZUCONE` z v1 ujednolicony do `REJECTED` (M47-FIX).

---
*Data naboru: 2026-11-13. Oględziny wszystkich kadrów: 2026-11-13 (M47-FIX). Wykonanie: Mistral. Wszystkie licencje komercyjne (CC0 / CC BY / CC BY-SA); NC/ND wyłącznie jako linki „tylko referencja".*

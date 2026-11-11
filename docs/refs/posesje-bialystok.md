# Posesje jednorodzinne: referencje i typologia (runda zabudowy r7, ADR 0114)

Zebrane 2026-11-11 (agent geo-worldgen). Tylko otwarte źródła (D43): Mapillary (CC BY-SA 4.0) i Wikimedia Commons
(CC0 / CC BY / CC BY-SA wg extmetadata). Google Maps/Street View/Earth/3D Tiles: nie użyte. Surowe zdjęcia poza gitem:
`Data/raw/mapillary/posesje/` (manifest.jsonl: id, URL, autor, data, lat/lon, azymut, licencja, SHA256) i
`Data/raw/refs/posesje/` (manifest.jsonl j.w.). Arkusze kontrolne (<= 960 px): `artifacts/refs-posesje/mapillary_sheet1.jpg`
(P01-P16), `mapillary_sheet2.jpg` (P17-P33), `commons_sheet.jpg` (C01-C07). Narzędzia: `tools/refs/posesje_fetch.py`,
`tools/refs/posesje_commons.py`. Zdjęcia są REFERENCJĄ (wzór, proporcje, barwa); piksele nie wchodzą do builda ani tekstur
(BY-SA = share-alike, ADR 0065/0066). Wymiary i barwy poniżej to `WORKING_VALUE` z proporcji, nie pomiary.

## Zasięg i luki (ważne)
- Region `bialystok-industrial-c` ma 269 domów jednorodzinnych (BDOT10k `budynek jednorodzinny`), ale Mapillary pokrywa tam
  tylko ulice główne: z 1004 zdjęć w okolicy domów tylko 28 leży w promieniu 25 m od domu, a bocznych uliczek osiedla brak.
  Z regionu pochodzi 5 użytecznych klatek (P01-P05, Andersa/Bieżeństwa, okolice OSM `Białostoczek`).
- Reszta z najbliższych osiedli domków wg OSM (`building=house|detached|semidetached_house`, pbf `podlaskie-261108`):
  P06-P12 (okolice `Mickiewicza` i `Bojary-Chopina`, 2017-18), P13-P20 (`Piasta II`, 2024), P21-P25 (`Zaścianki`, 2018),
  P26-P33 (okolice `Jakimy`, ok. 53,20 N 23,21 E, 2019). Odległość od regionu 4-7 km. Nazwy z węzłów OSM `place=*`,
  położenie przybliżone (UNVERIFIED).
- LUKI: brak zbliżeń bram przesuwnych, skrzynek na listy/słupków licznikowych, zjazdów z obniżonym krawężnikiem z bliska
  i nawierzchni podjazdów (widoczny tylko żwir w P20 i chodniki z kostki). Do uzupełnienia zdjęciami własnymi właściciela
  (pieszo, Dziesięciny/Białostoczek) albo Panoramax/KartaView; Mapillary z samochodu patrzy wzdłuż ulicy, nie na front posesji.
- Wikimedia Commons: wyszukiwanie tekstowe pod Białystok daje głównie budynki publiczne, przemysł i bloki; 7 użytecznych
  zdjęć (drewniane domy Supraśl/Tykocin z płotami, dom jednorodzinny z płotem ceglano-sztachetowym, brama kuta). Wykluczono
  wynik `Wysoki stoczek 58 Bialystok.jpg` (CC BY 3.0), bo wyglądem przypomina zrzut z panoramy ulicznej Google (brak pewności
  co do pochodzenia, więc nie użyty, plik usunięty).

## Typologia (z odsyłaczami do klatek)

### 1. Ogrodzenia
| Typ | Klatki | Wysokość WORKING_VALUE | Uwagi (barwa, konstrukcja) |
|---|---|---|---|
| Drewno: deski/sztachety pełne lub prawie pełne, rdzawo-czerwone/brązowe, na słupkach drewnianych lub stalowych | P06, P07, P08, P09, P23, P28 | 1,6-2,0 m (pełny płot powyżej linii dachu auta); ok. 1,2-1,4 m przy domkach drewnianych (P02, P07) | Góra prosta lub ukośna; barwa od jasnej rdzy do ciemnego brązu; matowe, spięte poprzeczkami; trawa lub podmurówka u dołu |
| Siatka powlekana zielona w ramie lub na słupkach | P10 (obok pełnego drewnianego), C03, C04 | 1,2-1,5 m (do ok. 1,8 m przy wysokich słupkach P10) | Zieleń zbliżona do RAL 6005 (UNVERIFIED), słupki stalowe lub betonowe tynkowane; za siatką trawnik lub żywopłot |
| Murowane słupki (ceglane/klinkierowe, tynkowane) z przęsłami drewnianymi lub kutymi | P17, P18, P21, P24, P28, C01 | słupki 1,6-2,0 m, przęsła 1,4-1,8 m | Cegła rdzawo-czerwona; kapy betonowe; słupki co ok. 2,5-3 m (z proporcji do przęseł) |
| Metal kuty/spawany, czarny, na ceglanej podmurówce | P12, P24, C05, C06 | 1,2-1,5 m (P12: podmurówka ok. 0,3-0,4 m + sztachety) | Proste sztachety z grotami; brama P24 z ornamentem; żywopłot/bluszcz po stronie ulicy |
| Mur pełny tynkowany lub beton prefabrykowany (szary/grafit) z kapą | P13, P14, P16, P19 | 1,6-2,2 m (nowsze domy, zdjęcia 2024) | Grafit, szary, biały; powierzchnia gładka lub fakturowana |
| Panele poziome (lamele) grafitowe/czarne | P15 | 1,6-1,8 m | Nowoczesne zabudowy; słupki stalowe; cokół betonowy (UNVERIFIED) |

### 2. Bramy i furtki
- Furtka metalowa ramowa z wypełnieniem (siatka/kratka), brązowo-czerwona: P06. Furtka drewniana pełna, rdzawa, w słupkach: C04, P09.
- Brama kuta skrzydłowa czarna na słupach ceglanych: P24 (szerokość ok. 3-3,5 m z proporcji do auta, UNVERIFIED), C05 i C06 (detal).
- Brama przesuwna: brak wyraźnego ujęcia w zbiorze (LUKA).
- Garaż w bryle domu z wjazdem wprost z ulicy: P25 (dwa wjazdy do garażu na rogu); nowe domy z wjazdem przy ogrodzeniu: P13-P16.

### 3. Podjazdy i zjazdy
- Żwir/tłuczeń jasny na wjeździe: P20 (prawa strona kadru, bez wyraźnego krawężnika). Kostka brukowa szara lub ceglasta: chodniki P13-P16 i P29-P31 (kostka czerwona z szarymi pasami), P24 i P25 w kolorze ceglastym.
- Zjazdy z obniżonym krawężnikiem: z bliska NIE uchwycone. Krawężniki ulic osiedlowych wystają ok. 8-12 cm (WORKING_VALUE z proporcji do chodnika; P08, P13, P24) i przechodzą w pochylnie bez zróżnicowania koloru.
- Ulice: P07 i P08 brukowane (kostka kamienna, nieregularna) z wąskim chodnikiem z kostki ceglastej; P29-P31 asfalt z pasem/zatoką z czerwonej kostki.

### 4. Zieleń i drzewa
- Tuje/żywotniki jako żywopłot lub soliter: P13-P19 (Piasta II), C01 (wysokie tuje za płotem ceglano-sztachetowym). Świerki kłujące (srebrnozielone) przy ulicy: P02, P17, P18. Lipy/klony uliczne: P07, P08, P12.
- Żywopłot liściasty lub bluszcz na płocie: P12, P08; rabaty wzdłuż płotu: P06, P28 (nagietki).
- Trawnik z pasem zieleni 1-2 m między chodnikiem a płotem: P13, P14, P19, P20.

### 5. Skrzynki, słupki, wyposażenie
- Słupki liczników/skrzynki na listy: nierozpoznawalne w rozdzielczości klatek (LUKA). Znaki drogowe i tabliczki ulic przy rogach płotów: P06, P09 (tabliczka ulicy), P10, P12.
- Linie napowietrzne i drewniane słupy sieciowe wzdłuż ulicy: P01-P03, P05, P13-P16, P21-P25.

### 6. Barwy (WORKING_VALUE, nie kalibracja)
Rdzawa czerwień/brązy drewna płotów, grafit/szary, kremowo-beżowy tynk, cegła czerwona (klinkierowa), zieleń siatki, czarny kuty metal.
Zdjęcia dzienne w pełnym słońcu (P13-P20, 2024) i zachmurzone (P21-P25). Barwy dashcamów (P21-P33) są niewiarygodne
(winietowanie, balans bieli); do kalibracji użyć P06-P12 lub P13-P20.

## Ostrzeżenia o osobach, tablicach, markach
Mapillary automatycznie zamazuje twarze i tablice, ale nie weryfikowałem tego dla każdej klatki. Oznaczone jako
"tylko referencja, nie publikować": P01-P05, P11, P13, P15, P16, P18, P19, P22, P26-P33 (pojazdy z bliska, tablice
potencjalnie czytelne), P21-P33 (nakładka z nazwą marki rejestratora w kadrze), P02/P04/P09/P11 (banery reklamowe).
Twarzy w zbliżeniu brak w żadnej klatce.

## Rejestr zdjęć Mapillary (wybrane 33; CC BY-SA 4.0)
| Ref | Id (strona) | Autor | Data | Lat, Lon | Azymut kamery | SHA256 (12) |
|---|---|---|---|---|---|---|
| P01 | [1130497537453949](https://www.mapillary.com/app/?pKey=1130497537453949) | szurek | 2017-08-16 | 53.15580, 23.15199 | 156 | 8a2f6612fe4f |
| P02 | [3938894499557394](https://www.mapillary.com/app/?pKey=3938894499557394) | richlv | 2017-07-15 | 53.15555, 23.15217 | 156 | 9f268accacd3 |
| P03 | [309147450842100](https://www.mapillary.com/app/?pKey=309147450842100) | szurek | 2017-08-16 | 53.15534, 23.15233 | 156 | 40f3a7ca20df |
| P04 | [196811878940666](https://www.mapillary.com/app/?pKey=196811878940666) | richlv | 2017-07-29 | 53.15501, 23.15268 | 335 | 4b6670f89eae |
| P05 | [3872847272792229](https://www.mapillary.com/app/?pKey=3872847272792229) | richlv | 2017-07-29 | 53.15475, 23.15287 | 338 | f52907caecf1 |
| P06 | [1566871480311497](https://www.mapillary.com/app/?pKey=1566871480311497) | richlv | 2017-07-29 | 53.11884, 23.17295 | 117 | f09e45f48f8d |
| P07 | [183830386936849](https://www.mapillary.com/app/?pKey=183830386936849) | richlv | 2017-07-29 | 53.13196, 23.17706 | 71 | 26942876002f |
| P08 | [1889914111167007](https://www.mapillary.com/app/?pKey=1889914111167007) | richlv | 2017-07-29 | 53.13190, 23.17673 | 66 | a318015514d0 |
| P09 | [269756941543675](https://www.mapillary.com/app/?pKey=269756941543675) | richlv | 2017-07-29 | 53.11820, 23.17486 | 302 | 56a79fad3922 |
| P10 | [4073869122651585](https://www.mapillary.com/app/?pKey=4073869122651585) | richlv | 2017-07-29 | 53.11852, 23.17400 | 302 | 55fa12386a95 |
| P11 | [505140880845651](https://www.mapillary.com/app/?pKey=505140880845651) | czadzik | 2018-07-21 | 53.11840, 23.17559 | 336 | 53a18eed30f5 |
| P12 | [753485232016344](https://www.mapillary.com/app/?pKey=753485232016344) | richlv | 2017-07-29 | 53.13203, 23.17632 | 12 | 7a634b24613d |
| P13 | [1160266725277203](https://www.mapillary.com/app/?pKey=1160266725277203) | strudel | 2024-08-15 | 53.12604, 23.18992 | 235 | a01470444f3f |
| P14 | [1185672959149756](https://www.mapillary.com/app/?pKey=1185672959149756) | strudel | 2024-08-15 | 53.12688, 23.19171 | 235 | 8b98430da6bf |
| P15 | [1424118101608247](https://www.mapillary.com/app/?pKey=1424118101608247) | strudel | 2024-08-15 | 53.12539, 23.18867 | 234 | abca6ebfd344 |
| P16 | [1581510225736636](https://www.mapillary.com/app/?pKey=1581510225736636) | strudel | 2024-08-15 | 53.12617, 23.19021 | 234 | 2d2c5904145e |
| P17 | [3876655599278130](https://www.mapillary.com/app/?pKey=3876655599278130) | strudel | 2024-08-15 | 53.12658, 23.19111 | 232 | f02f4eccb075 |
| P18 | [517630880682068](https://www.mapillary.com/app/?pKey=517630880682068) | strudel | 2024-08-15 | 53.12521, 23.18833 | 230 | 8b5e284efee0 |
| P19 | [525160500175460](https://www.mapillary.com/app/?pKey=525160500175460) | strudel | 2024-08-15 | 53.12647, 23.19086 | 235 | dadd9c6754e7 |
| P20 | [8131484060278895](https://www.mapillary.com/app/?pKey=8131484060278895) | strudel | 2024-08-15 | 53.12469, 23.18773 | 132 | 0b33d78e37d5 |
| P21 | [300649364945318](https://www.mapillary.com/app/?pKey=300649364945318) | czadzik | 2018-07-21 | 53.12308, 23.23031 | 103 | 4c05af9b015a |
| P22 | [306466047525718](https://www.mapillary.com/app/?pKey=306466047525718) | czadzik | 2018-07-21 | 53.12316, 23.22979 | 107 | 8688c64314ed |
| P23 | [370534997606121](https://www.mapillary.com/app/?pKey=370534997606121) | czadzik | 2018-07-21 | 53.12321, 23.22945 | 110 | 14f233056c42 |
| P24 | [376100606965433](https://www.mapillary.com/app/?pKey=376100606965433) | czadzik | 2018-07-21 | 53.12296, 23.23157 | 99 | af7e237e0b31 |
| P25 | [455909108808026](https://www.mapillary.com/app/?pKey=455909108808026) | czadzik | 2018-07-21 | 53.12298, 23.23126 | 105 | 98cbee3c821a |
| P26 | [1016082292257665](https://www.mapillary.com/app/?pKey=1016082292257665) | grobin | 2019-08-30 | 53.20431, 23.20874 | 195 | e668e97d8b96 |
| P27 | [1048084445719439](https://www.mapillary.com/app/?pKey=1048084445719439) | grobin | 2019-08-30 | 53.20359, 23.20860 | 187 | d259ce543d59 |
| P28 | [1099858447163562](https://www.mapillary.com/app/?pKey=1099858447163562) | grobin | 2019-08-30 | 53.20434, 23.21159 | 278 | 4681c42971b3 |
| P29 | [1207561689702254](https://www.mapillary.com/app/?pKey=1207561689702254) | grobin | 2019-08-30 | 53.20098, 23.20809 | 187 | a0f125ea8318 |
| P30 | [135101958576352](https://www.mapillary.com/app/?pKey=135101958576352) | grobin | 2019-08-30 | 53.19892, 23.20619 | 231 | 01bee87bdc49 |
| P31 | [1440290549650258](https://www.mapillary.com/app/?pKey=1440290549650258) | grobin | 2019-08-30 | 53.20409, 23.20870 | 186 | a0ed126750bf |
| P32 | [158536016225173](https://www.mapillary.com/app/?pKey=158536016225173) | grobin | 2019-08-30 | 53.19887, 23.20372 | 278 | 1f1c82ed6f76 |
| P33 | [163306658984121](https://www.mapillary.com/app/?pKey=163306658984121) | grobin | 2019-08-30 | 53.19883, 23.20433 | 276 | 28de7c8a5bbc |

Pełny rejestr z pełnym SHA256: `Data/raw/mapillary/posesje/manifest.jsonl` (także 31 klatek odrzuconych po przeglądzie,
`selected: false`).

## Rejestr zdjęć Wikimedia Commons (7)
| Ref | Plik (strona) | Autor | Data | Licencja |
|---|---|---|---|---|
| C01 | [8782 October 2022 in Podlaskie Voivodeship.jpg](https://commons.wikimedia.org/wiki/File:8782_October_2022_in_Podlaskie_Voivodeship.jpg) | Rakoon | 2022-10-30 | CC0 |
| C02 | [Dom z mansardowym dachem porośniety pnączami w Tykocinie.jpg](https://commons.wikimedia.org/wiki/File:Dom_z_mansardowym_dachem_poro%C5%9Bni%C4%99ty_pn%C4%85czami_w_Tykocinie.jpg) | Krzysztof Popławski | 2022-08-24 | CC BY 4.0 |
| C03 | [Drewniany dom przy ulicy 11 Listopada 27 w Tykocinie za siatką.jpg](https://commons.wikimedia.org/wiki/File:Drewniany_dom_przy_ulicy_11_Listopada_27_w_Tykocinie_za_siatk%C4%85.jpg) | Krzysztof Popławski | 2026-08-05 | CC BY 4.0 |
| C04 | [Drewniany dom z gankiem za czerwoną furtką w Supraślu.jpg](https://commons.wikimedia.org/wiki/File:Drewniany_dom_z_gankiem_za_czerwon%C4%85_furtk%C4%85_w_Supra%C5%9Blu.jpg) | Krzysztof Popławski | 2026-08-22 | CC BY 4.0 |
| C05 | [Drewniany dom za kutym ogrodzeniem przy ul. 3 Maja 24 w Supraślu.jpg](https://commons.wikimedia.org/wiki/File:Drewniany_dom_za_kutym_ogrodzeniem_przy_ul._3_Maja_24_w_Supra%C5%9Blu.jpg) | Krzysztof Popławski | 2026-08-22 | CC BY 4.0 |
| C06 | [SolecKuj 23 Stycz 13 ogrodzenie furtka.jpg](https://commons.wikimedia.org/wiki/File:SolecKuj_23_Stycz_13_ogrodzenie_furtka.jpg) (Solec Kujawski, nie Podlasie: detal bramy kutej) | Jacek Fink-Finowicki | 2017-06-02 | CC BY-SA 4.0 |
| C07 | [Żółty drewniany dom przy ulicy 11 Listopada 50 w Tykocinie.jpg](https://commons.wikimedia.org/wiki/File:%C5%BB%C3%B3%C5%82ty_drewniany_dom_przy_ulicy_11_Listopada_50_w_Tykocinie.jpg) | Krzysztof Popławski | 2026-08-05 | CC BY 4.0 |

Lokalizacja C01 nie wynika z opisu pliku (znalazło ją zapytanie `Zaścianki Białystok`): UNVERIFIED. Daty z extmetadata Commons.

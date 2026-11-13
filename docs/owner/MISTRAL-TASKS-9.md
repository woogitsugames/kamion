# Zadania dla Mistrala — runda 9: paczka badawcza 03, część 3 (s19, 2026-11-13) — M56–M61

Repo `woogitsugames/kamion`. **Każda sesja Mistrala dostaje jeden blok (skopiuj całość z ramki) — w NOWEJ sesji.** Zasady wspólne są wpisane w każdy blok, bo Mistral w osobnej sesji nie widzi tego nagłówka.

## Zaległe poprawki

FIXES-9 zlecone 2026-11-13 ~21:2x, czekamy na commity.
(`docs/owner/MISTRAL-FIXES-9.md`: M52-FIX-3, M47-FIX-2, M54-FIX-2, M49-FIX-2, opc. M48-FIX-2. Stan origin przy pisaniu tego pliku: ostatnie commity na `research/mistral-p2-surfaces-2` 18:57, `-p11-dojlidy-photos` 15:45, `-p8-restrictions-3` 15:56, `-p6-dojlidy-gates` 15:50, `-p12-dojlidy-landmarks` 15:24 — wszystkie sprzed utworzenia FIXES-9 (19:36), więc żaden FIX z rundy 9 nie jest jeszcze wypchnięty.)

## Skąd tematy (luki realne, nie wymyślone)

| paczka | luka (źródło w repo) | co odblokowuje |
|---|---|---|
| M56 | estakady Andersa: rozpiętości przęseł, filary, ekrany, druga jezdnia = `WORKING_VALUE`/`UNVERIFIED` (`Data/Regions/bialystok-industrial-c/overrides.yaml`: `andersa-viaduct-*`; ADR 0117/0123/0144/0146/0159) | landmark trasy G3-A, bramka 3 |
| M57 | wieżowiec przy Kwadrat Park: elewacje NE/NW i parter bez zdjęcia, maszty na dachu (ADR 0180 „Otwarte”, HANDOVER STOP S18 follow-upy P2) | ADR 0180/0171, bramka 3 |
| M58 | Dojlidy: słupki biało-czerwone z łańcuchem przy P11-063 (brak prototypu), oznakowanie pasa Krywlany „nie rysowane” (`artifacts/live/dojlidy-vis-0179.md`) | ADR 0179 (region D60) |
| M59 | lampy ciągnika/naczepy: płaskie soczewki, lampka tablicy (ciągnik jej nie ma — ADR 0175 „otwarte”), fotometria R148/R150 (P4/M44 ma tylko instalację R48) | ADR 0181, 0175, 0178 |
| M60 | zmierzch: brak pul latarni, „asfalt ≈ 8 %” bez jednostki, zero zapalonych okien, horyzont magentowy (`docs/reports/REVIEW-2026-11-13-s19-0182.md` P1-4, P1-5, P2-6/7/8) | ADR 0182 + follow-up oświetlenia |
| M61 | brud tyłu naczepy: kolor osadu, próg/RUPD, zacieki (REVIEW s19-0182 P1-1…P1-3, P2-10); w `research/` zero materiału o zabrudzeniach | ADR 0182 (warunek scalenia) |

Sprawdzone, że nie dublują: `research/mistral/*` (p1-route-photos-2, p2-surfaces-2, p4-truck-regulations, p5-audio-3, p6-dojlidy-gates, p8-restrictions-3, p9-furniture-3, p11-dojlidy-photos, p12-dojlidy-landmarks), `research/gptpro/*`, `research/g5|g7|g10`. G5 ma ogólne U-12b (słupki 1,10 m, rozstaw 1,5/1,8 m), ale nie konkretne miejsce w Dojlidach. P12 ma geometrię pasa startowego, ale nie jego oznakowanie. P9-furniture-3 ma wysokości latarni, ale nie fotometrii ani rozstawu na trasie.

Kolejność (od najpilniejszej): **M61 → M59 → M58 → M56 → M57 → M60**. M61 i M59 dotyczą gałęzi w toku (0182 czeka na poprawki brudu, 0181 robi soczewki). M58 to 0179. M56 i M57 to bramka 3, ale na trasie mają już wartości robocze.

---

## M56 — estakady Andersa (rondo Putry i rondo Pamięci Bieżeństwa 1915 r.): konstrukcja z dokumentów i zdjęć

```
Repo woogitsugames/kamion. Gałąź research/mistral-p13-andersa-viaducts od NAJNOWSZEGO origin/main (nazwa z MYŚLNIKIEM po „mistral”, nie ze slashem). Zadanie badawcze na wiele godzin — rzetelność ważniejsza niż tempo; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki z naczepą (Unity), Białystok 1:1 z OSM i GUGiK, gra komercyjna, budżet 0 zł. Bramka rozpoznawalności: gracz z Białegostoku ma rozpoznać trasę po układzie i obiektach. Dwie estakady ul. gen. Andersa są landmarkami trasy: (A) nad rondem Putry (DK8/DK19/DK65; OSM way 1101181473, 173956078, 284022563, 606396460), (B) nad rondem Pamięci Bieżeństwa 1915 r. (OSM way 175157461, 177895177). Dziś wymiary konstrukcji są szacowane „na oko” z kilku zdjęć. Przeczytaj w repo: Data/Regions/bialystok-industrial-c/overrides.yaml (wpisy andersa-viaduct-biezenstwa-style, andersa-viaduct-biezenstwa-hero, andersa-viaduct-putry-style — pola reason/verify mówią, czego brakuje) oraz docs/REFERENCES.md. Piszesz po polsku.

ZADANIE (osobno dla A i B, osobno dla każdej jezdni):
1. Dokumenty urzędowe: projekt / decyzja ZRID / pozwolenie na budowę / przetarg / odbiór / przegląd obiektu mostowego (BIP Białystok, BIP ZDiT/ZDM, GDDKiA, przetargi UMB, Dziennik Urzędowy Woj. Podlaskiego, SIMB/system ewidencji obiektów mostowych, publikacje w „Drogownictwie”/„Mostach”/materiałach konferencji mostowych). Szukaj: rok budowy, wykonawca, projektant, schemat statyczny, liczba i rozpiętości przęseł, długość całkowita, szerokość pomostu, typ przekroju (skrzynka, belki), wysokość dźwigara, typ i wymiary podpór (słupy okrągłe/owalne, średnica, rozstaw poprzeczny), skrajnia pod obiektem, ekrany akustyczne (wysokość, rozstaw słupków, materiał, po której stronie której jezdni), bariery (typ, wysokość), kolor gzymsów i słupów.
2. Zdjęcia z legalnych źródeł potwierdzające to, czego dokumenty nie podają: każdy rząd podpór A i B (szczególnie połowa SE estakady B — dziś brak kadru), obie strony obu jezdni A (czy ekran stoi też na jezdni w stronę centrum), gzyms, bariera. Dla każdego kadru OBEJRZYJ obraz i wpisz w `uwagi` jedno zdanie „co widać” (np. „4 rzędy słupów owalnych z czerwonym pasem, ekran przezroczysty po prawej”). Bez tego zdania kadr nie liczy się jako dowód.
3. Tabela „parametr → wartość → źródło → status” zgodna z polami override'ów: liczba rzędów podpór i rozpiętości [m], wymiary słupa [m], rozstaw słupów w rzędzie [m], wysokość ekranu [m], rozstaw słupków ekranu [m], strony z ekranem, wysokość bariery [m], kolor gzymsu/słupów (opis, bez RGB z pikseli).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści pochodzących z Google (także zrzuty z nich w artykułach). Źródła: BIP, GDDKiA, Geoportal/GUGiK (ortofoto, BDOT10k — dane otwarte), OSM (ODbL), Panoramax (CC BY-SA 4.0), KartaView, Wikimedia Commons, Openverse (CC0/BY/BY-SA). Mapillary: tylko jeśli dostęp bez cudzego tokenu — NIE używaj tokenów z kodu stron; inaczej UNVERIFIED.
- Tylko licencje komercyjne (CC0, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 pr. aut.); NC/ND/bez licencji — tylko link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: każda liczba z URL + data dostępu + cytat ≤ 25 słów albo strona/rysunek dokumentu. Brak źródła = UNVERIFIED; szacunek = ESTIMATED z metodą (np. „proporcja pikseli do pasa ruchu 3,5 m”). Blogi/fora nie potwierdzają wymiarów.
- Pozycje WGS84 (6 miejsc), kierunek_deg kadru (z API/EXIF albo UNVERIFIED); przypisanie kadru do obiektu: odległość ≤ 60 m od osi OSM obiektu, w uwagach way_id i odległość.
- JPG ≤ 1600 px. Samokontrola: losuj ≥ 20 % pozycji z jawnym seedem; dla każdej sprawdź ponownie link, cytat/stronę, a dla kadrów — ponownie OBEJRZYJ obraz i porównaj ze zdaniem „co widać”. Wynik w README i audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p13-andersa-viaducts/ z README.md (cel, metoda, ustalenia osobno A i B, tabela parametrów, luki), manifest.csv (utf-8; id P13-NNN; kolumny: obiekt A|B, jezdnia, element, parametr, wartość, jednostka, typ_źródła dokument|zdjęcie|ortofoto|OSM, lat, lon, kierunek_deg, data_zdjęcia, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi), sources.md, audit_20_percent.json. PDF-y urzędowe ≤ 5 MB mogą iść do files/docs/; zdjęcia NIE DO GITA: files/ w .gitignore katalogu, zdjęcia + większe PDF-y w ZIP mistral-p13-andersa-viaducts-files.zip — właściciel przekazuje go liderowi, w PR napisz nazwę i rozmiar ZIP-a oraz sha256.
NIE ZMIENIAJ niczego poza research/mistral/p13-andersa-viaducts/.
ODDANIE: commit + push gałęzi co ok. godzinę; na końcu jeden PR do main (nie draft) z raportem po polsku i SUROWYM wyjściem `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — napisz „M56 gotowe, PR #<numer>” i zakończ.
```

## M57 — wieżowiec biurowy przy Kwadrat Park (ul. gen. Andersa): elewacje NE/NW, parter, dach

```
Repo woogitsugames/kamion. Gałąź research/mistral-p14-office-tower od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Piszesz po polsku. Obiekt: 11-kondygnacyjny biurowiec (LoD1 2024 ok. 41,8 m, BDOT10k „siedziba firmy”, bladożółty/piaskowy tynk) stojący przy wjeździe do kompleksu Kwadrat Park przy ul. gen. Władysława Andersa w Białymstoku, obok stacji paliw (rejon ok. 53,154 N 23,169 E — DOKŁADNĄ pozycję i id budynku ustal z OSM; w README podaj way_id i współrzędne środka). Obrys ma 4 ściany: szczyt SW i NE (~16 m), długa SE (~37 m), długa NW (~37 m). Mamy tylko zdjęcia z południa (szczyt SW: gładki z JEDNĄ kolumną okien; ściana SE: poziome pasma okien na bieli). Brakuje: ściany NE, ściany NW, parteru (wejście, witryny, cokół), dachu. Przeczytaj w repo docs/REFERENCES.md i artifacts/refs/kwadrat-park/INDEX.md (lista już znanych zdjęć Commons — NIE dubluj ich).

ZADANIE:
1. Zdjęcia każdej ściany (NE, NW, SE, SW) i parteru z legalnych źródeł, dowolny rok (data obowiązkowa). Dla każdego kadru OBEJRZYJ obraz i opisz: która ściana (z azymutu kamery i położenia), układ okien (kolumna / pasma / siatka / brak), liczba widocznych kondygnacji, kolor tynku i ram (opis słowny), cokół i parter, elementy na ścianie (rury, klimatyzatory, drabiny). Napisy/marki — tylko „napis firmowy, nie odtwarzamy”.
2. Dach: maszty, anteny, nadbudówka maszynowni, attyka, balustrady — liczba, przybliżona wysokość nad dachem (metoda: proporcja do kondygnacji 3,7 m), kolor. Źródła: zdjęcia z dystansu (np. z wiaduktu Andersa, z ronda), ortofoto GUGiK (rzut: położenie na dachu), NMPT GUGiK jeśli dostępny (wysokość punktów ponad dachem). Jeśli w otwartych źródłach jest pozwolenie na stację bazową / zgłoszenie instalacji radiowej (BIP, UKE — wykaz lokalizacji stacji bazowych), podaj je z URL.
3. Tabela: ściana → układ okien → kolor → źródło → status; dach → element → wysokość → położenie → źródło → status.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła: Panoramax (CC BY-SA 4.0), KartaView, Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, NMPT, BDOT10k, LoD — dane otwarte), OSM (ODbL), BIP/UKE (urzędowe). Mapillary tylko bez cudzego tokenu; inaczej UNVERIFIED.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. CC BY-SA = „referencja, nie tekstura”, z atrybucją autora.
- Nie zmyślaj: każdy opis ściany pochodzi z OBEJRZANEGO kadru z jego id; jeśli ściany nie widać — UNVERIFIED (nie dopisuj „prawdopodobnie jak SE”). Wysokości ESTIMATED z jawną metodą.
- Pozycja kamery WGS84 (6 miejsc), kierunek_deg (z API/EXIF albo UNVERIFIED), sezon, pora_dnia. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem: ponownie OBEJRZYJ wylosowane kadry i porównaj z opisem; wynik w README i audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p14-office-tower/ z README.md (pozycja i id obiektu, tabela ścian, tabela dachu, luki), manifest.csv (id P14-NNN; kolumny: element ściana_NE|ściana_NW|ściana_SE|ściana_SW|parter|dach, opis_co_widać, układ_okien, kondygnacje_widoczne, kolor_opis, lat, lon, kierunek_deg, odległość_m, data_zdjęcia, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore katalogu, ZIP mistral-p14-office-tower-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p14-office-tower/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M57 gotowe, PR #<numer>” i koniec.
```

## M58 — Dojlidy / Krywlany: słupki z łańcuchem, ogrodzenia i oznakowanie pasa startowego widoczne z drogi

```
Repo woogitsugames/kamion. Gałąź research/mistral-p15-dojlidy-details od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Region Dojlidy / Krywlany (decyzja D60). Przeczytaj w repo: research/mistral/p11-dojlidy-photos/README.md + manifest.csv (kadry regionu), research/mistral/p12-dojlidy-landmarks/README.md (P12-001/002: pasy startowe 09R/27L i 09L/27R), research/g5-street-furniture/README.md (ogólne wymiary U-12b). Piszesz po polsku. NIE powtarzaj tego, co tam jest — uzupełnij tylko luki poniżej.

ZADANIE:
1. Słupki biało-czerwone z łańcuchem przy ul. Adama Mickiewicza / Jacka Kuronia (kadr P11-063, Commons „20240623_124644_June_2024_in_Białystok.jpg”, 53,105827 N 23,184707 E) i inne takie wygrodzenia w regionie. OBEJRZYJ P11-063 i każdy nowy kadr; podaj: wysokość słupka, przekrój (okrągły/kwadratowy, średnica), liczba i szerokość pasów biało-czerwonych, rozstaw słupków, zwis łańcucha, kolor łańcucha, przebieg (wzdłuż krawężnika / wokół trawnika), długość odcinka. Podstawa: Dz.U. 2019 poz. 2311 zał. 4 (U-12b — rysunek i wymiary, cytat + strona) + odczyt z kadrów (ESTIMATED z metodą: proporcja do krawężnika 0,15 m / płyty chodnika 0,5 m / wysokości człowieka). Pozycje (lat/lon) końców odcinka z ortofoto GUGiK lub OSM (barrier=chain / bollard, jeśli są — podaj node/way id).
2. Pas startowy 09R/27L Krywlany: jakie oznakowanie ma (progi, oznaczniki numeru drogi startowej, linia osiowa, znaki strefy przyziemienia, krawędziowe) — z AIP Polska / karty lotniska EPBK (PAŻP — dokument urzędowy, tylko fakty, bez kopiowania map) i z ortofoto GUGiK 2023–2025 (opisz, co widać przy rozdzielczości ortofoto, z datą arkusza). Najważniejsze: CZY oznakowanie jest widoczne z drogi publicznej (ul. Dywizjonu 303, ul. Mickiewicza, ul. Kuronia) z oka kierowcy ciężarówki ~2,5 m — oszacuj geometrycznie (odległość drogi od pasa, wysokość ogrodzenia/wału/zieleni, kąt patrzenia) i potwierdź kadrami z drogi, jeśli istnieją. Opisz też ogrodzenie lotniska od strony dróg (typ siatki, wysokość, drut kolczasty, słupy, kolor, brama) z kadrów.
3. Inne drobne wygrodzenia widoczne z dróg ciężarówek regionu (słupki U-5a, U-12a, szlabany przy bramach zakładów — biało-czerwone ramię, jak przy P11-143) — po 1–3 przykłady z pozycją i kadrem.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła: ISAP/ELI (Dz.U.), PAŻP/AIP (urzędowe — fakty), GUGiK (ortofoto, BDOT10k), OSM (ODbL), Panoramax (CC BY-SA 4.0), KartaView, Wikimedia Commons, Openverse (CC0/BY/BY-SA). Mapillary tylko bez cudzego tokenu; inaczej UNVERIFIED.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: każdy wymiar ze źródłem (cytat ≤ 25 słów + strona) albo ESTIMATED z metodą; nie widać = UNVERIFIED. Każdy kadr: OBEJRZANY, w uwagach jedno zdanie „co widać”. Kadry przypisuj do drogi tylko przy odległości ≤ 25 m od osi OSM (podaj way_id i odległość).
- Pozycje WGS84 (6 miejsc), kierunek_deg (z API albo UNVERIFIED), sezon, pora_dnia. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru + ponowne sprawdzenie cytatu) — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p15-dojlidy-details/ z README.md (ustalenia 1–3, tabela wymiarów U-12b: przepis vs odczyt, werdykt „oznakowanie pasa widoczne z drogi: TAK/NIE/częściowo — skąd”, luki), manifest.csv (id P15-NNN; kolumny: kategoria łańcuch|pas_startowy|ogrodzenie_lotniska|wygrodzenie, element, parametr, wartość, jednostka, lat, lon, osm_id, kierunek_deg, odległość_do_drogi_m, data_zdjęcia, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p15-dojlidy-details-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p15-dojlidy-details/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M58 gotowe, PR #<numer>” i koniec.
```

## M59 — lampy ciągnika i naczepy: fotometria (R148/R150, dawne R4/R6/R7/R3), budowa soczewek, lampka tablicy

```
Repo woogitsugames/kamion. Gałąź research/mistral-p16-truck-lamps od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, gra komercyjna, jedna fikcyjna ciężarówka BEZ MARKI: ciągnik siodłowy 4×2 + naczepa firanka 13,6 m, 3 osie. Lampy w grze mają dziś płaskie, jednolite klosze, a tablica rejestracyjna ciągnika nie ma lampki. Przeczytaj w repo research/mistral/p4-truck-regulations/README.md + manifest.csv (M44: INSTALACJA świateł wg R48 — liczba, wysokość, kolor) i NIE powtarzaj tego. Ta paczka dotyczy SAMYCH LAMP: fotometrii i budowy. Piszesz po polsku.

ZADANIE:
1. Fotometria z aktualnych tekstów UNECE: R148 (urządzenia sygnalizacji świetlnej — zastąpił m.in. R4, R6, R7, R77, R91) i R150 (urządzenia odblaskowe — zastąpił R3, R104 w części). Podaj serię, datę wersji i punkt. Dla funkcji: pozycyjne tylne, stop, kierunkowskaz tylny i boczny, obrysowe, boczne pozycyjne, cofania, przeciwmgłowe tylne, oświetlenie tablicy rejestracyjnej (dawne R4) — tabela: min/max światłość w osi [cd], kąty widoczności, stosunek stop/pozycyjne, wymagania jednorodności powierzchni świetlnej (jeśli są), barwa (współrzędne chromatyczności — tylko liczby z tekstu). Dla lampki tablicy: minimalna luminancja na tablicy [cd/m²], gradient (max/min), kąt padania, położenie lampki względem tablicy.
2. Budowa lamp zespolonych (tylnych) ciężarówek i naczep — bez marek i logo: typy optyki (komory z odbłyśnikiem i kloszem z pryzmatami / klosz gładki z wewnętrzną optyką / LED punktowe z soczewkami / LED liniowe ze światłowodem), typowy podział komór (kolejność funkcji od zewnątrz), wymiary typowej lampy 7-komorowej naczepy (dł. × wys. × głęb. w mm z kart katalogowych lub rysunków homologacyjnych — tylko liczby, bez nazw firm w opisach odtwarzanych), wygląd wyłączonej lampy w świetle dziennym (kolor klosza, widoczność pryzmatów). Oznaczenia homologacyjne na kloszu (kółko „E” + numer + symbole funkcji) — opisz zasadę z R148, bez kopiowania cudzych znaków.
3. Lampka tablicy: typowe położenie i budowa na ciągniku (nad tablicą w zderzaku / na belce ramy) i naczepie (w belce RUPD / w obudowie lampy zespolonej) — z kadrów.
4. Zdjęcia CC (Commons, Openverse, Panoramax): ≥ 15 kadrów tylnych lamp zespolonych naczep i ciągników z bliska (włączone i wyłączone, dzień i zmierzch) + ≥ 5 lampek tablicy. Dla każdego kadru OBEJRZYJ obraz i opisz: typ optyki, liczba komór, kolejność funkcji, czy widać pryzmaty/punkty LED, stan (czysty/brudny). Jeśli na zdjęciu widać markę — zaznacz „marka widoczna, tylko referencja kształtu”.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła przepisów: UNECE (pełne teksty PDF), EUR-Lex (Dz.U. UE z regulaminami EKG). Zdjęcia: Commons, Openverse, Panoramax, KartaView — tylko CC0/BY/BY-SA. Karty katalogowe producentów: tylko liczby wymiarów z URL, BEZ nazw marek i logo w opisach do odtworzenia.
- Nie zmyślaj: każda liczba z punktem regulaminu + cytat ≤ 25 słów + wersja; źródła wtórne (sklepy, blogi) nie potwierdzają przepisu. Czego nie da się potwierdzić — UNVERIFIED; szacunek — ESTIMATED z metodą.
- Każdy kadr OBEJRZANY, zdanie „co widać” w uwagach. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (link działa, cytat zgadza się z PDF, regulamin obowiązuje; kadr ponownie obejrzany) — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p16-truck-lamps/ z README.md (tabela fotometrii R148/R150, budowa lamp, lampka tablicy, luki), manifest.csv (id P16-NNN; kolumny: kategoria przepis|budowa|zdjęcie, funkcja, parametr, wartość, jednostka, kategoria_pojazdu N3|O4, punkt, cytat, wersja_przepisu, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p16-truck-lamps-files.zip (PDF-y urzędowe ≤ 5 MB mogą być w gicie w files/docs/ — wtedy NIE ignoruj tego podkatalogu) — właściciel przekazuje ZIP liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p16-truck-lamps/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M59 gotowe, PR #<numer>” i koniec.
```

## M60 — zmierzch w mieście: niebo, luminancja, oświetlenie ulic trasy, zapalone okna

```
Repo woogitsugames/kamion. Gałąź research/mistral-p17-dusk-lighting od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1, gra komercyjna. Pora „zmierzch” = koniec zmierzchu cywilnego (Słońce −6°). Recenzja obrazu wykazała: brak wyraźnych plam światła pod latarniami (plac i jezdnia równo jasne), zero zapalonych okien w blokach, poświata horyzontu za różowa. Przeczytaj w repo research/mistral/p9-furniture-3/README.md (latarnie: typy i wysokości — NIE powtarzaj) oraz research/gptpro/p2-surfaces/README.md (współczynniki odbicia nawierzchni, jeśli są). Piszesz po polsku.

ZADANIE:
1. Pomiary nieba i otoczenia o zmierzchu (literatura naukowa z otwartym dostępem, normy, dane stacji pomiarowych): natężenie oświetlenia poziomego [lx] przy Słońcu −4°…−8° (bezchmurnie i pochmurnie), luminancja nieba w zenicie i przy horyzoncie od strony Słońca i przeciwnej [cd/m²], barwa (CCT lub chromatyczność) nieba przy horyzoncie od strony Słońca vs zenit. Tabela: wysokość Słońca → wartość → warunki → źródło.
2. Oświetlenie ulic Białegostoku na trasie gry (ul. gen. Andersa, Al. Tysiąclecia Państwa Polskiego, ul. Gen. Maczka, rondo Putry, ul. Sokólska/Wysockiego/Kombatantów): klasa oświetleniowa wg PN-EN 13201 (M1–M6/C), wymagana średnia luminancja [cd/m²] i równomierność Uo/Ul, wysokość montażu, rozstaw słupów [m] (z dokumentacji przetargów/projektów BIP albo z ortofoto GUGiK — pomiar odległości kolejnych słupów, ESTIMATED z metodą i liczbą próbek), typ źródła (sód HPS ~2000 K / LED 3000–4000 K) — czy i kiedy dana ulica przeszła na LED (BIP, przetargi modernizacji oświetlenia Białegostoku). Godzina/próg włączania latarni w Białymstoku (zegar astronomiczny / czujnik zmierzchowy — próg lx), jeśli dostępne.
3. Zapalone okna o zmierzchu: dane o odsetku oświetlonych okien w budynkach mieszkalnych i biurowych wieczorem (badania zużycia energii w gospodarstwach domowych, profile obciążenia, prace o „window lighting” / nocnych zdjęciach satelitarnych) — liczba z metodą. Plus ≥ 10 zdjęć CC bloków / biurowców Białegostoku lub podobnych polskich miast o zmierzchu (OBEJRZYJ i policz zapalone okna / wszystkie widoczne w każdym kadrze; podaj wysokość Słońca z daty i godziny EXIF, jeśli są).
4. ≥ 10 zdjęć CC ulic Białegostoku (najlepiej trasa z pkt 2) o zmierzchu lub w nocy: OBEJRZYJ i opisz, czy pod latarniami widać plamy światła i ciemne przerwy między nimi, barwę światła (żółte/białe), czy oprawy mają poświatę (halo).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła: publikacje z otwartym dostępem (DOI/URL), normy (tylko numer + wartości z jawnie dostępnych streszczeń/dokumentów urzędowych — nie kopiuj płatnych norm), BIP Białystok / ZDiT (przetargi, projekty), GUGiK ortofoto, OSM (ODbL; highway=street_lamp), Commons, Openverse, Panoramax, KartaView (CC0/BY/BY-SA).
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”.
- Nie zmyślaj: każda liczba ze źródłem (URL + data dostępu + cytat ≤ 25 słów albo tabela/strona). Źródła wtórne (blogi, fora, sklepy) nie potwierdzają pomiarów. Brak = UNVERIFIED; szacunek = ESTIMATED z metodą. Pomiarów z pikseli zdjęć (RGB) NIE podawaj jako luminancji.
- Każdy kadr OBEJRZANY, zdanie „co widać” w uwagach; pozycja WGS84, kierunek_deg (albo UNVERIFIED), data i godzina. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p17-dusk-lighting/ z README.md (tabele 1–3, tabela ulic: klasa / luminancja / Uo / wysokość / rozstaw / źródło światła, wnioski z kadrów, luki), manifest.csv (id P17-NNN; kolumny: kategoria niebo|ulica|okna|kadr, element, parametr, wartość, jednostka, warunki, wysokość_słońca_deg, lat, lon, kierunek_deg, data_godzina, opis_co_widać, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p17-dusk-lighting-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p17-dusk-lighting/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M60 gotowe, PR #<numer>” i koniec.
```

## M61 — brud tyłu naczepy: wzory zabrudzeń drzwi, progu, belki przeciwnajazdowej i lamp

```
Repo woogitsugames/kamion. Gałąź research/mistral-p18-trailer-soiling od NAJNOWSZEGO origin/main (z myślnikiem, nie ze slashem). Zadanie badawcze na kilka godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, gra komercyjna, fikcyjna naczepa BEZ MARKI: firanka 13,6 m z dwuskrzydłowymi drzwiami tylnymi (biała blacha/sklejka w ramie), belka przeciwnajazdowa (RUPD), lampy zespolone, taśmy odblaskowe. Brud w grze jest dziś: prawie czarną neutralną sadzą przy uszczelce, zbyt równymi pionowymi zaciekami (jak blacha falista) i czystym progiem, belką i lampami. Potrzebujemy materiału, jak NAPRAWDĘ brudzi się tył naczepy na polskich drogach. Piszesz po polsku.

ZADANIE:
1. Mechanizm (literatura z otwartym dostępem: aerodynamika ciężarówek, „rear soiling / rear surface contamination”, badania CFD/tunelowe zabrudzeń tylnych ścian i lamp, zalecenia dla kamer cofania i lamp): które strefy tyłu brudzą się najbardziej (próg, belka RUPD, lampy, dolna część drzwi, okolice uszczelki środkowej), jak rozkłada się brud z wysokością (np. procent pokrycia vs wysokość nad jezdnią), wpływ prędkości i mokrej nawierzchni. Tabela: strefa → intensywność względna → źródło → status.
2. Barwa i faktura osadów drogowych w Polsce: kolor błota pośniegowego z solą drogową, pyłu z asfaltu, piasku — opis słowny + jeśli w literaturze są: współczynnik odbicia/albedo, kolor Munsell/CIELAB (liczby tylko ze źródła). Różnica lato (pył, jasnoszary/beżowy) vs zima (sól, ciemne błoto, białe zacieki solne po wyschnięciu).
3. Zdjęcia CC (Commons, Openverse, Panoramax, KartaView): ≥ 20 kadrów tylnych drzwi naczep/skrzyń ciężarówek, z różnym stopniem zabrudzenia, lato i zima. OBEJRZYJ każdy i opisz: gdzie brud najmocniejszy (próg/belka/lampy/dół drzwi/uszczelka), kształt (film jednolity, rozbryzg kropel przy krawędzi, zacieki — ile, skąd startują: zawiasy/narożniki/rygle/krawędź dachu, długość jako % wysokości drzwi), czy są „wymyte” jasne pasy, czy klamki/uchwyty są wytarte czyściej, kolor osadu (opis słowny: szarobrązowy/oliwkowy/czarny), szacunkowe krycie (słabe/średnie/pełne). Marki na zdjęciu: „marka widoczna, tylko referencja”.
4. Na podstawie kadrów (nie zgadując): zestawienie liczbowe — mediana liczby zacieków na skrzydło, odsetek kadrów z brudnym progiem/belką/lampami, typowa wysokość górnej granicy filmu dolnego [m] (ESTIMATED z proporcji do wysokości drzwi ~2,6–2,7 m — podaj metodę).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles i treści z Google. Źródła: publikacje otwarte (DOI/URL), raporty instytucji (np. ITS, TRL, SAE — tylko streszczenia publicznie dostępne), Commons, Openverse (CC0/BY/BY-SA), Panoramax, KartaView.
- Tylko licencje komercyjne; NC/ND/stocki płatne — link „tylko referencja, nie pobrano”. CC BY-SA = „referencja, nie tekstura”.
- Nie zmyślaj: liczby z literatury z URL + data dostępu + cytat ≤ 25 słów; liczby z kadrów tylko jako ESTIMATED z metodą i id kadru. Kolorów NIE podawaj jako RGB z pikseli zdjęć — tylko opis słowny albo wartości ze źródła.
- Każdy kadr OBEJRZANY, zdanie „co widać” w uwagach; data, sezon. JPG ≤ 1600 px.
- Samokontrola ≥ 20 % z jawnym seedem (ponowne obejrzenie kadru i porównanie z opisem; ponowne sprawdzenie cytatów) — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p18-trailer-soiling/ z README.md (mechanizm, strefy, barwa i faktura lato/zima, zestawienie z kadrów, 5 najlepszych kadrów jako referencja dla artysty z uzasadnieniem, luki), manifest.csv (id P18-NNN; kolumny: kategoria literatura|kadr, strefa, parametr, wartość, jednostka, opis_co_widać, kształt_brudu, liczba_zacieków, krycie, kolor_opis, sezon, data_zdjęcia, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore, ZIP mistral-p18-trailer-soiling-files.zip — właściciel przekazuje liderowi; w PR nazwa, rozmiar, sha256.
NIE ZMIENIAJ niczego poza research/mistral/p18-trailer-soiling/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M61 gotowe, PR #<numer>” i koniec.
```

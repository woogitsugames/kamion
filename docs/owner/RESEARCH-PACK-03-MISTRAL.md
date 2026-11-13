# Zadania dla Mistral — paczka badawcza 03, część 2 (s17, 2026-11-13): luki z przeglądu P2–P10 (M49–M55)

Źródło luk: `docs/reports/REVIEW-2026-11-13-s16-research-pack-02.md` §7. M44–M48 są w `docs/owner/MISTRAL-TASKS-8-RESEARCH.md` i zostały już zlecone. Tutaj ich nie powtarzam. **Każda sesja Mistrala dostaje jeden blok (skopiuj całość z ramki).** Zasady wspólne są wpisane w każdy blok.

Kolejność (od najpilniejszej dla agentów): M49 (Dojlidy — bramy i organizacja ruchu, 0166) → M50 (meble, 0162) → M54 (ograniczenia ciężarówek, graf dróg) → M52 (nawierzchnie i linie) → M53 (zabudowa, 0167) → M51 (zieleń, 0163) → M55 (audio).

**Korekty do już zleconych bloków (przekaż Mistralowi przy odbiorze albo dopisz w PR):**
- **M45 pkt 2 ma błędne założenie.** Zdjęcia 2024 NIE pokazują „Centrum” na osobnej tablicy bramownicy A. Na G3-P013 (2024) i P7-001 (2020) „675 Centrum” to trzeci wiersz tej samej tablicy. Osobny mały panel „↑ 675 Centrum” stoi na portalu C przed rondem Putry (G3-P005). M45 ma to potwierdzić niezależnie i nie budować osi czasu na tej tezie. Dodatkowo M45 nie może używać cudzego tokenu Mapillary (P7 użył tokenu z kodu strony embed — niedopuszczalne).
- **M44 — co z P4 potwierdzić:** P4 oparto na R48 Rev.12 (seria 06, 2014) i R46 Rev.5 (seria 04, 2013). Obie wersje są nieaktualne: istnieje R48 Rev.13 (seria 07) i projekty serii 08, a R46 ma serie 05–07. M44 ma sprawdzić na aktualnych tekstach:
  - wyjątek konturu R104 dla „tractors for semi-trailers” (R48 6.21.1.2);
  - liczby, wysokości i kąty świateł N3/O4 (P4-015…079, m.in. 6.13.5: 80°/5°/20°);
  - obowiązkowe klasy lusterek N3 i dopuszczenie systemów kamera-monitor (CMS) w nowych seriach R46;
  - R58 seria 03, pkt 1.2.2;
  - numer i status aktu zastępującego 96/53/WE (P4 podaje „rozporządzenie (UE) 2024/5450” — podejrzane);
  - rysunek tablicy 520×114 mm (Dz.U. 2024 poz. 1709);
  - miejsce tachografu;
  - aktualny t.j. WT pojazdów: §12, §42 i zał. 10.
- **M46** pokrywa luki zdjęciowe P1 (Batorego, Brzeska, Buska, Olsztyńska, drugi sezon, poziom kierowcy). Bez nowego bloku.

---

## M49 — region Dojlidy / Krywlany: bramy zakładów, łuki i organizacja ruchu (luki P6)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p6-dojlidy-gates od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin — rzetelność ważniejsza niż tempo; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki z naczepą (Unity), świat Białegostoku 1:1 z OSM i GUGiK, gra komercyjna, budżet 0 zł. Następny region: Dojlidy / Krywlany. Przeczytaj research/gptpro/p6-next-regions-2/README.md i manifest.csv (14 bram G01–G14 z node OSM, kafle K01–K05 w EPSG:2180, trasy R) — NIE powtarzaj ich, uzupełnij luki. Piszesz po polsku.

ZADANIE:
1. Szerokość bramy wjazdowej (m) i promień łuku wjazdu (m, krawędź jezdni) dla 14 bram z P6 (12 bez szerokości, 14 bez promieni). Pomiar na ortofotomapie GUGiK (WMS PZGIK ORTO, najnowsza, GSD ≤ 0,25 m): podaj datę ortofoto, metodę (np. 3 pomiary, mediana), niepewność ±m. Dla Elektrociepłowni (Andersa 15) wskaż bramę dla ciężarówek (brak w OSM).
2. Stacja ważenia RS16 WIM przy ul. Zabłudowskiej: dokładna pozycja (dziś ESTIMATED ±150 m) — z dokumentów GDDKiA/ITD, BIP, OSM lub ortofoto.
3. Adres i brama Podlaskich Zakładów Zbożowych: „Elewatorska 14” (G2) czy ul. Zbożowa (OSM) — rozstrzygnij źródłem.
4. Organizacja ruchu (zarządzenia/projekty stałej organizacji ruchu, uchwały, komunikaty ZDM/ZDiT w BIP Białystok) na końcówkach dojazdów: Myśliwska, Karpińskiego (KAN), Dojlidy Fabryczne (zakaz 3,5 t od XII 2025?), rondo Meyera (hgv=no w OSM), Adama Mickiewicza (maxweight 8). Dla każdego: numer dokumentu, data, treść ograniczenia, odcinek.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: GUGiK (ortofoto, BDOT10k — dane otwarte), OSM (API 0.6; ODbL), BIP Białystok / ZDM / GDDKiA (urzędowe, art. 4 pr. aut.), Panoramax/Commons (CC0/BY/BY-SA). Mapillary — brak tokenu: UNVERIFIED, nie zgaduj kluczy, nie używaj cudzych tokenów.
- Nie zmyślaj: każda liczba ma źródło (link + data dostępu + cytat ≤ 25 słów albo strona) albo status UNVERIFIED/ESTIMATED z metodą.
- Samokontrola: losuj ≥ 20 % pozycji z jawnym seedem, sprawdź ponownie — wynik w README i audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p6-dojlidy-gates/ z README.md (cel, metoda, ustalenia, tabela bram: id P6, node OSM, szerokość, promień, data ortofoto, niepewność; braki; samokontrola), manifest.csv (utf-8; id M49-NNN, obiekt, osm_id, lat, lon, wartość, jednostka, metoda, dokument_strona, url_źródła, licencja, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi), sources.md, audit_20_percent.json. Wycinki ortofoto (JPG ≤ 1600 px) NIE do gita: files/ w .gitignore katalogu, ZIP mistral-p6-dojlidy-gates-files.zip — w PR napisz, gdzie leży. PDF urzędowe ≤ 5 MB mogą być w files/docs/ w gicie.
NIE ZMIENIAJ niczego poza research/mistral/p6-dojlidy-gates/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M49 gotowe, PR #<numer>” i koniec.
```

## M50 — meble uliczne Białegostoku: zdjęcia z poziomu kierowcy, skany, latarnie (luki P9)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p9-furniture-3 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Przeczytaj research/g5-street-furniture/README.md i research/gptpro/p9-street-furniture-2/README.md + manifest.csv — NIE powtarzaj pozycji. Piszesz po polsku.

ZADANIE:
1. Zdjęcia z poziomu kierowcy (z jezdni, nie z chodnika) w kaflu wokół 53,152 N 23,168 E (ul. Andersa, Al. Tysiąclecia, Sokólska, Wileńska) dla 11 typów: ławka, kosz, stojak rowerowy, osłona drzewa, bariera U-12/U-12b, słupek blokujący U-5a, sygnalizator na maszcie/wysięgniku, latarnia, żerdź energetyczna, hydrant nadziemny, szafka gazowa/telekom. ≥ 2 kadry na typ, z datą, azymutem i odległością do obiektu.
2. Odczyt (OCR albo ręczny odczyt z obrazu strony, z numerem strony) skanów: OPZ ZMK Białystok DZ.26.2.8.2026.JO (stojaki rowerowe — wymiary), STO ZDM Warszawa TOS_1 (słupy oświetleniowe), Dz.U. 2019 poz. 2311 zał. 4 (sygnalizatory: wysokości montażu, skrajnia — rysunek s. 370).
3. Model ławek i koszy dostarczonych przez Glasdon Europe AB do Białegostoku w 2019 (protokół, umowa, BIP) i ich wymiary z karty produktu (tylko fakty).
4. Wysokości latarni w Białymstoku wg klasy drogi: standard/wytyczne ZDM/ZDiT Białystok lub projekty oświetlenia (BIP) dla Andersa, Al. Tysiąclecia, Sokólskiej — wysokość słupa, wysięgnik, rozstaw.
5. Karta żerdzi wirowanej E-12 (ZPUE lub inny producent): wysokość 12,0 m, średnice podstawy i wierzchołka — potwierdzenie.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła zdjęć: Panoramax (CC BY-SA 4.0, azymut z API), KartaView, Wikimedia Commons, Openverse (CC0/BY/BY-SA). Mapillary — brak tokenu: UNVERIFIED, nie zgaduj kluczy, nie używaj cudzych tokenów.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja, nie pobrano”. CC BY-SA: „referencja, nie tekstura”. Karty producentów: tylko fakty, pliku nie pobieraj.
- Nie zmyślaj: każda liczba ze źródłem albo UNVERIFIED/ESTIMATED z metodą. Pozycje WGS84 (6 miejsc); sezon i pora_dnia obowiązkowe dla zdjęć. JPG ≤ 1600 px.
- Samokontrola 20 % z jawnym seedem — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p9-furniture-3/ z README.md, manifest.csv (id M50-NNN; kolumny: obiekt, model_wzor, wymiary_m, materiał, kolor_ral, dokument_strona, lat, lon, kierunek_deg, data_zdjęcia, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA (files/ w .gitignore, ZIP mistral-p9-furniture-3-files.zip — w PR, gdzie leży); PDF urzędowe ≤ 5 MB mogą być w files/docs/.
NIE ZMIENIAJ niczego poza research/mistral/p9-furniture-3/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M50 gotowe, PR #<numer>” i koniec.
```

## M51 — zieleń przyuliczna: lato osiedla, gatunki żywopłotów, odtwarzalna detekcja koron (luki P10)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p10-greenery-3 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1. Przeczytaj research/g7-street-greenery/README.md i research/gptpro/p10-street-greenery-2/README.md + manifest.csv — nie dubluj. Piszesz po polsku.

ZADANIE:
1. Zdjęcia z LATA (VI–VIII, liście) dla ulic osiedla domów jednorodzinnych: Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska, Racławicka, Łańcucka (Białystok, ok. 53,150–53,158 N, 23,147–23,156 E). ≥ 2 kadry na ulicę, z datą i azymutem. Skidelska i Świsłocka nie mają dziś żadnego zdjęcia.
2. Gatunki i wysokości żywopłotów przy tych ulicach (tuja/żywotnik, ligustr, grab, świerk…) — odczyt ze zdjęć z poziomu ulicy, ≥ 20 odcinków; dla każdego: gatunek albo „iglasty/liściasty”, wysokość ESTIMATED (metoda: odniesienie do ogrodzenia/furtki), id zdjęcia.
3. Odtwarzalna detekcja koron drzew dla kafla EPSG:2180 [776971, 595199, 779019, 597247] (cały kafel, także Andersa na wschód od lon 23,156): plik GeoJSON z koronami (środek, promień, iglaste/liściaste), skrypt albo opis metody krok po kroku, data i GSD ortofoto GUGiK. Porównaj z wartościami P10-201…237 i P10-301…313 i podaj różnice.
4. Projekt zieleni przebudowy Al. Tysiąclecia (Strabag, 2021/22; 74 drzewa, 109 krzewów): gatunki, obwody i rozstaw sadzenia — z BIP/dokumentacji przetargowej ZDM, jeśli dostępne.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: Panoramax (CC BY-SA 4.0), KartaView, Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK ortofoto (dane otwarte), OSM (ODbL), BIP (urzędowe). Mapillary — brak tokenu: UNVERIFIED, nie zgaduj kluczy.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. CC BY-SA: „referencja, nie tekstura”.
- Każda liczba ze źródłem albo UNVERIFIED/ESTIMATED z metodą. Pozycje WGS84 (6 miejsc), sezon i pora_dnia obowiązkowe. JPG ≤ 1600 px.
- Samokontrola 20 % z jawnym seedem — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p10-greenery-3/ z README.md, manifest.csv (id M51-NNN; kolumny jak research/gptpro/p10-street-greenery-2/manifest.csv), crowns.geojson (≤ 5 MB; większy — ZIP), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA (files/ w .gitignore, ZIP mistral-p10-greenery-3-files.zip — w PR, gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p10-greenery-3/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M51 gotowe, PR #<numer>” i koniec.
```

## M52 — nawierzchnie i oznakowanie poziome: rysunki rozporządzenia, kafel startowy, detale (luki P2)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p2-surfaces-2 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1. Przeczytaj research/gptpro/p2-surfaces/README.md i manifest.csv — nie dubluj. Uwaga: w P2 jest błąd — P-11 to PRZEJAZD DLA ROWERZYSTÓW (1,8 m jednokierunkowy / 3,0 m dwukierunkowy), nie „przebieg przejścia/azyl”. Piszesz po polsku.

ZADANIE:
1. Wymiary znaków poziomych z RYSUNKÓW załącznika 2 do rozporządzenia Dz.U. 2019 poz. 2311 (PDF z eli.gov.pl, część c2): P-2a/b, P-3a/b, P-4, P-5, P-6 (szerokości linii, odstęp linii podwójnych, kreska/przerwa), P-12, P-13, P-14, P-21a/b, P-23, P-25. Dla każdej wartości numer rysunku i strona Dz.U. — źródła wtórne (blogi, tioman.pl) NIE potwierdzają.
2. Zdjęcia kafla startowego Jaroszówka (ok. 53,152 N 23,168 E) z poziomu jezdni: nawierzchnia jezdni, chodniki, krawężniki, linie — ≥ 10 kadrów z datą i azymutem.
3. Zdjęcia + wymiary: azyle (wyspy dzielące) na przejściach, płytki dotykowe (układ rzędów), ścieki przykrawężnikowe i wpusty — w Białymstoku.
4. Kolor dróg i pasów rowerowych na trasie startowej (Andersa, Al. Tysiąclecia, Sokólska, Wileńska): gdzie czerwony asfalt (droga dla rowerów), gdzie pas malowany na szarym asfalcie — z pozycjami i zdjęciami.
5. Rynek Kościuszki: rodzaj nawierzchni (kostka granitowa? wymiary, układ) — z dokumentu (projekt rewitalizacji, BIP) albo ESTIMATED ze zdjęcia z metodą.
6. Aktualny katalog standardów/wytycznych ZDM/ZDiT Białystok (nowszy niż „Wytyczne do projektowania” zał. 5, BIP resource 99308) — link, data, zmiany względem starej wersji.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: ELI/Dz.U., BIP Białystok, GDDKiA (urzędowe), Panoramax, KartaView, Commons, Openverse (CC0/BY/BY-SA). Mapillary — brak tokenu: UNVERIFIED.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. CC BY-SA: „referencja, nie tekstura”.
- Każda liczba ze źródłem albo UNVERIFIED/ESTIMATED z metodą. Pozycje WGS84, sezon i pora_dnia dla zdjęć. JPG ≤ 1600 px. PDF urzędowe ≤ 5 MB.
- Samokontrola 20 % z jawnym seedem — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p2-surfaces-2/ z README.md (tabela linii P-* z numerem rysunku i stroną), manifest.csv (id M52-NNN; kolumny jak research/gptpro/p2-surfaces/manifest.csv), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA (files/ w .gitignore, ZIP mistral-p2-surfaces-2-files.zip — w PR, gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p2-surfaces-2/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M52 gotowe, PR #<numer>” i koniec.
```

## M53 — zabudowa: poprawne dopasowanie budynków, systemy wielkiej płyty, kolory elewacji (luki P3)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p3-buildings-2 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK. Przeczytaj research/gptpro/p3-building-typology/README.md, manifest.csv i REVIEW-NOTE.md. W P3 dopasowanie zdjęć do budynków było błędne (brano punkt kamery, nie fotografowany budynek) — 5 z 9 sprawdzonych wysokości dotyczyło innego budynku. Piszesz po polsku.

ZADANIE:
1. ≥ 30 budynków widocznych z Andersa, Sokólskiej, Wileńskiej, Białostoczku, Al. Tysiąclecia: dla każdego budynek FOTOGRAFOWANY (nie najbliższy kamerze) — id obrysu LoD1 GUGiK lub BDOT10k i OSM way, measuredHeight, liczba kondygnacji (policzona na zdjęciu), adres, typ, dach (kształt, kolor), kolor elewacji. Metoda dopasowania: kierunek patrzenia + odległość + porównanie bryły; podaj ją w README.
2. System wielkiej płyty per osiedle (Białostoczek, Bacieczki, Zielone Wzgórza, Wysoki Stoczek, Przydworcowe/Sienkiewicza): monografie, BIP spółdzielni, artykuły naukowe, dokumentacja termomodernizacji — z cytatem. Bez źródła — UNVERIFIED.
3. Kolory elewacji po termomodernizacji 2015–2026 dla bloków w kaflu Andersa/Białostoczek: STWiOR/projekty kolorystyki (BIP, spółdzielnie, TBS), a gdy brak — zdjęcia 2023+ z ESTIMATED sRGB (metoda, balans bieli).
4. Tekst MPZP części os. Białostoczek z warstwą tekstową (uchwała z BIP lub Dziennik Urzędowy Woj. Podlaskiego) — ustalenia o kolorach elewacji, pokryciu i kącie dachów, z paragrafem.
5. Stacja paliw przy Andersa (Circle K): adres, zdjęcie, wysokość wiaty.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: GUGiK (LoD1/LoD2, BDOT10k, ortofoto), OSM (ODbL), BIP/Dz.Urz. (urzędowe), Panoramax, KartaView, Commons, Openverse (CC0/BY/BY-SA). Mapillary — brak tokenu: UNVERIFIED.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. Bez logo i znaków towarowych w opisach do odtworzenia.
- Każda liczba ze źródłem albo UNVERIFIED/ESTIMATED z metodą. JPG ≤ 1600 px; sezon i pora_dnia dla zdjęć.
- Samokontrola 20 % z jawnym seedem — sprawdź też, czy obrys/wysokość należą do budynku ze zdjęcia. Wynik w README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p3-buildings-2/ z README.md, manifest.csv (id M53-NNN; kolumny: typ_budynku, adres, lat, lon, lod1_id, osm_way, measuredHeight_m, kondygnacje_ze_zdjęcia, dach, kolor_elewacji, kolor_srgb, metoda_koloru, system_wp, metoda_dopasowania, zdjęcie_id, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA (files/ w .gitignore, ZIP mistral-p3-buildings-2-files.zip — w PR, gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p3-buildings-2/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M53 gotowe, PR #<numer>” i koniec.
```

## M54 — ograniczenia ciężarówek: skrajnia pod wiaduktami, podstawy zakazów, S19 (luki P8)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p8-restrictions-3 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki z naczepą, Białystok 1:1 z OSM. Przeczytaj research/g10-truck-restrictions/README.md i research/gptpro/p8-truck-restrictions-2/README.md + manifest.csv — nie dubluj. Ustalone: skrajnia ustawowa 5,00 m (A/S) i 4,50 m (pozostałe; § 80 Dz.U. 2022 poz. 1518); e-TOLL od 1.02.2026. Piszesz po polsku.

ZADANIE:
1. Rzeczywista skrajnia / znak B-16 pod wiaduktami: rondo Putry (Maczka, Andersa), Al. Tysiąclecia nad linią kolejową nr 6, ronda Wolnej Ukrainy i Żołnierzy Wyklętych, S8 nad al. Niepodległości — zdjęcia znaku albo dokument (projekt, inwentaryzacja obiektu, GDDKiA/ZDM), wartość w m. Brak znaku na zdjęciu z daty X — zapisz jako obserwację z id zdjęcia.
2. Podstawa prawna (numer zarządzenia/zatwierdzonego projektu organizacji ruchu, data) dla: Bitwy Białostockiej hgv=no+delivery (OSM way 178208423), Sokólska hgv=no (way 188396757), Branickiego i Zwierzyniecka maxweight=8, Warszawska maxweight=12 t przy hgv=no (way 842154286) — rejestr organizacji ruchu ZDM, BIP, komunikaty. Zdjęcia znaków B-5/B-18 z datą.
3. Nowa S19 Krynice–Dobrzyniewo–Białystok Zachód (otwarta 20.10.2026): dopuszczalne naciski osi, wiadukty (liczba, skrajnia), znaki ograniczeń, czy odcinek jest w OSM i z jakimi tagami (maxaxleload, maxheight, toll:hgv).
4. Zmiany po 1.02.2026 w e-TOLL w promieniu 40 km od Białegostoku (DK8, DK19, DK65, S8, S19) — lista MF z datą wersji.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: OSM (API 0.6, ODbL), Dz.U./ELI, MF e-TOLL, GDDKiA, BIP Białystok/ZDM (urzędowe), Panoramax, KartaView, Commons (CC0/BY/BY-SA). Mapillary — brak tokenu: UNVERIFIED, nie zgaduj kluczy, nie używaj cudzych tokenów.
- Każda wartość ze źródłem (link + data dostępu + cytat ≤ 25 słów albo strona) albo UNVERIFIED/ESTIMATED. Źródła wtórne nie potwierdzają przepisu.
- Samokontrola 20 % z jawnym seedem — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p8-restrictions-3/ z README.md, manifest.csv (id M54-NNN; kolumny jak research/gptpro/p8-truck-restrictions-2/manifest.csv, separator „;”), sources.md, audit_20_percent.json. PDF urzędowe ≤ 5 MB w files/ (w gicie); zdjęcia NIE do gita (files/photos/ w .gitignore, ZIP mistral-p8-restrictions-3-files.zip — w PR, gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p8-restrictions-3/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M54 gotowe, PR #<numer>” i koniec.
```

## M55 — audio: retarder, hamulec silnikowy, AMT, R6 12–13 l, osuszacz (luki P5)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p5-audio-3 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, dźwięk silnika sterowany fizyką, gra komercyjna. Przeczytaj research/gptpro/9-audio-refs/ i research/gptpro/p5-audio-refs-2/README.md + manifest.csv — NIE powtarzaj ID Freesound/plików z tych paczek. Piszesz po polsku.

ZADANIE (tylko nagrania z licencją komercyjną):
1. Retarder (hydrokinetyczny lub elektromagnetyczny) w ciężarówce lub autobusie — z kabiny i z zewnątrz; opis autora musi potwierdzać retarder.
2. Hamulec silnikowy (dekompresyjny lub wydechowy) POJEDYNCZEGO pojazdu — z kabiny i z zewnątrz, z prędkością/biegiem, jeśli autor podaje.
3. Zautomatyzowana skrzynia mechaniczna (AMT) z przerwą momentu przy zmianie biegu — ciężarówka lub autobus; wnętrze i zewnątrz.
4. Silnik R6 diesel 12–13 l z NAZWANYM modelem (opis autora lub metadane): rozruch, bieg jałowy, obciążenie, rozpędzanie.
5. Cykliczna regeneracja osuszacza powietrza w POJEŹDZIE („psssst” co kilkadziesiąt sekund) i zawór zabezpieczający / ogranicznik ciśnienia.
Jeśli czegoś nie ma — wynik negatywny z listą przeszukanych źródeł i zapytań (to też jest wynik).

TWARDE ZASADY:
- Źródła: Freesound (licencja ze strony dźwięku), Wikimedia Commons (API), OpenGameArt, Sonniss GDC (licencja: użytek komercyjny bez atrybucji — zacytuj), archive.org (tylko z jawną licencją CC0/BY/BY-SA), Openverse audio. NC/ND/RemArc (BBC) — tylko link „tylko referencja, nie pobrano”.
- Każda pozycja: id źródła, URL, licencja potwierdzona na stronie (data dostępu), autor, długość (pomiar pliku, nie deklaracja), sample rate, bit depth, kabina/zewnątrz, opis autora (≤ 25 słów), status SOURCED/UNVERIFIED (UNVERIFIED, gdy opis nie potwierdza treści).
- Freesound bez logowania daje tylko podgląd MP3 — pobierz podgląd, a oryginały wpisz do download_list.csv (id, url, licencja, autor, plik_docelowy).
- Samokontrola 20 % z jawnym seedem (link, licencja, długość) — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p5-audio-3/ z README.md (ustalenia per kategoria, wyniki negatywne, samokontrola), manifest.csv (id M55-NNN; kolumny jak research/gptpro/p5-audio-refs-2/manifest.csv), download_list.csv, sources.md, audit_20_percent.json. PLIKI AUDIO NIE DO GITA (files/ w .gitignore, ZIP mistral-p5-audio-3-files.zip — w PR, gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p5-audio-3/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M55 gotowe, PR #<numer>” i koniec.
```

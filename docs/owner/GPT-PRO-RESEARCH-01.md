# ChatGPT 6 Pro — 10 zleceń badawczych (s16, 2026-11-13)
Każde zlecenie = osobna rozmowa z ChatGPT 6 Pro. **Skopiuj cały jeden blok i wklej** — zasady są już w środku. Wynik: ZIP (i jeśli się da — gałąź na GitHubie). Lider wrzuca ZIP-y do `research/gptpro/` i przydziela agentom.

---

## G1 — zdjęcia referencyjne trasy w obecnym kaflu

```
ZADANIE G1 (slug: route-photos). Zbierz zdjęcia referencyjne z poziomu kierowcy ciężarówki (wysokość oka ok. 2,5 m, widok wzdłuż jezdni) dla ulic i rond z listy: Generała Władysława Andersa, Generała Stanisława Maczka, Aleja Tysiąclecia Państwa Polskiego, Bitwy Białostockiej, Białostoczek, Kombatantów, Michała Motoszko, Stefana Batorego, Władysława Bełzy, Wileńska, Sokólska, Grodzieńska, Brzeska, Buska, Kowieńska, Lidzka, Olsztyńska, Racławicka, Sitarska, Skidelska, Wołkowyska, Łańcucka, Świsłocka; rondo Krzysztofa Jakuba Putry, rondo Pamięci Bieżeństwa 1915 roku; wiadukty i łącznice S8/DK8 w tym rejonie (Białystok, ok. 53,152 N 23,168 E).
Cel: dla każdej ulicy ≥ 3 ujęcia w obu kierunkach (początek, środek, skrzyżowania), dla rond i wiaduktów ≥ 6 ujęć z każdego wlotu. Źródła: głównie Mapillary (podaj image key, datę wykonania, współrzędne, kierunek), Wikimedia Commons.
Priorytet: zdjęcia najnowsze (2022+), w dzień, bez mocnego rozmycia. Zaznacz sezon (liście / bez liści / śnieg).
manifest.csv — kolumny dodatkowe: ulica, punkt_opis, lat, lon, kierunek_deg, data_zdjęcia, sezon, mapillary_key, jakość_1_5.
W README: mapa pokrycia (lista ulic z liczbą ujęć), luki (gdzie nie ma zdjęć).

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G2 — następny region: gdzie jeżdżą ciężarówki wokół Białegostoku

```
ZADANIE G2 (slug: next-regions). Gra rozszerzy się z obecnego kafla (okolice ronda Putry i ul. Andersa, Białystok, ok. 53,152 N 23,168 E) na obrzeża, potem Podlasie. Ustal, dokąd realnie jeżdżą ciężarówki z naczepą w Białymstoku i okolicy: strefy przemysłowe i aktywności gospodarczej (np. Białostocki Park Naukowo-Technologiczny, SSE), centra logistyczne i magazyny, bazy transportowe, terminale, zakłady produkcyjne, bazy paliw, stacje dla TIR, parkingi dla ciężarówek, MOP-y na S8/S19/DK65/DK19, wagi preselekcyjne, punkty kontroli ITD, przejścia graniczne w regionie (Kuźnica, Bobrowniki, Budzisko — tylko jako cel trasy).
Dla każdego miejsca: nazwa, typ, adres, współrzędne, źródło (BIP, strona firmy, OSM — podaj id obiektu OSM, jeśli jest), czy wjazd naczep 13,6 m jest realny (dowód), trasa dojazdu od S8 (lista ulic).
Na końcu zaproponuj 3–5 kolejnych kafli 2×2 km w kolejności, z uzasadnieniem (ile celów dla ciężarówek, ruch, rozpoznawalność, połączenie z obecnym kaflem).
manifest.csv — kolumny dodatkowe: nazwa, typ, adres, lat, lon, osm_id, dojazd_od_S8, naczepa_13_6_ok (TAK/NIE/UNVERIFIED), dowód.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G3 — treść tablic kierunkowych na S8/DK8 i węzłach Białegostoku

```
ZADANIE G3 (slug: s8-signs). Spisz dokładną treść oznakowania kierunkowego (tablice E-1, E-2a…E-2g, E-3, E-15 i podobne, bramownice, tablice przeddrogowskazowe, numery węzłów, odległości, piktogramy) na drodze ekspresowej S8 i DK8 w granicach Białegostoku i do ok. 15 km od miasta, ze szczególnym uwzględnieniem węzłów w rejonie ronda Putry / ul. Andersa / Al. Tysiąclecia (ok. 53,152 N 23,168 E). Z każdego kierunku jazdy.
Źródła: zdjęcia Mapillary / Wikimedia Commons (podaj key i współrzędne), projekty stałej organizacji ruchu i dokumentacja przetargowa GDDKiA/ZDiT (BIP), OSM (destination:*, ref). Znane z gry: bramownica „Warszawa / Ełk / Augustów” przy łącznicy Putry — potwierdź treść i miejsce.
Dla każdej tablicy: lokalizacja, kierunek jazdy, typ znaku, wiersze tekstu dokładnie jak na tablicy (z wielkością liter i znakami diakrytycznymi), numery dróg (kolor tła), piktogramy, odległości, strzałki; data zdjęcia.
manifest.csv — kolumny dodatkowe: lat, lon, kierunek_deg, droga, typ_znaku, tekst_wiersze (rozdzielone „|”), numery_dróg, piktogramy, data_zdjęcia, mapillary_key.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G4 — typologia zabudowy w kaflu i wokół: parametry z dowodami

```
ZADANIE G4 (slug: building-typology). Dla Białegostoku (najpierw okolice 53,152 N 23,168 E: osiedla przy Andersa, Wileńskiej, Sokólskiej, Białostoczek, Wysoki Stoczek; potem typowe dla miasta) opisz typy zabudowy widoczne z jezdni: bloki z wielkiej płyty (systemy, liczba kondygnacji, wysokość kondygnacji, rytm okien, balkony/loggie, kolory po termomodernizacji), domy jednorodzinne (lata 60–80 „kostki”, nowsze), drewniane domy podlaskie, pawilony handlowe, hale i magazyny, garaże blaszane, stacje paliw, budynki usługowe.
Dla każdego typu: ≥ 5 zdjęć (licencje jak w ZASADACH) z adresem/współrzędnymi, parametry liczbowe z dowodem (dokumentacja termomodernizacji w BIP spółdzielni/miasta, projekty, przetargi, katalogi systemów W-70, OWT-67, Szczecin itp.), typowe materiały i kolory (podaj przybliżone sRGB z opisem metody), dachy (kąt, pokrycie), ogrodzenia przy tych budynkach.
manifest.csv — kolumny dodatkowe: typ_budynku, adres, lat, lon, kondygnacje, wys_kondygnacji_m, rytm_okien_m, kolor_srgb, dach, materiał.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G5 — meble uliczne Białegostoku: wymiary z przetargów

```
ZADANIE G5 (slug: street-furniture). Ustal wygląd i wymiary elementów wyposażenia ulic Białegostoku: latarnie i oprawy (typy, wysokość, wysięgniki, rozstaw), słupy (betonowe wirowane, stalowe), wiaty przystankowe BKM, tablice przystankowe, kosze, ławki, słupki blokujące, barierki U-12a/U-12c i ogrodzenia przy jezdni, osłony drzew, stojaki rowerowe, szafki energetyczne, hydranty, studzienki. Najważniejsze źródło: dokumentacja przetargowa i standardy techniczne miasta (BIP Białystok, ZDiT/ZDM, Białostockie Zakłady Oświetlenia — SIWZ, opisy przedmiotu zamówienia, rysunki, katalogi „standardów elementów małej architektury”), plus zdjęcia z kafla (ok. 53,152 N 23,168 E).
Dla każdego elementu: wymiary (z dokumentu, strona), materiał, kolor (RAL, jeśli podany), gdzie występuje w kaflu (zdjęcia ze współrzędnymi), zdjęcie z bliska.
manifest.csv — kolumny dodatkowe: element, typ_model, wysokość_m, szerokość_m, inne_wymiary, RAL, materiał, dokument_strona, lat, lon.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G6 — nawierzchnie, krawężniki i oznakowanie poziome w praktyce

```
ZADANIE G6 (slug: surfaces). Ustal, jakie nawierzchnie i elementy jezdni występują w Białymstoku (najpierw kafel ok. 53,152 N 23,168 E): asfalt (kolor świeży/stary, łaty, spękania, koleiny na S8 i ulicach), kostka betonowa (typy, kolory, wzory na chodnikach, zatokach, wyspach), płyty, krawężniki (typy 15×30, 20×30, najazdowe, wysokość wystawania), obrzeża, ścieki przykrawężnikowe, pasy rowerowe (czerwony asfalt?), płytki dotykowe, azyle, oznakowanie poziome (stan zużycia, farba/masa grubowarstwowa, profilowane).
Źródła: standardy techniczne ZDiT/miasta (BIP, „katalog standardów”), dokumentacja przetargowa przebudów ulic z kafla, zdjęcia Mapillary/Commons ze współrzędnymi; GDDKiA dla S8.
Dla każdego: zdjęcie z bliska i z poziomu kierowcy, wymiary i materiały z dokumentu (strona), opis wyglądu w czasie (zużycie), przybliżony kolor sRGB z metodą.
manifest.csv — kolumny dodatkowe: element, lokalizacja, lat, lon, materiał, wymiary, kolor_srgb, stan_zużycia, dokument_strona.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G7 — zieleń przy ulicach: gatunki, układ, żywopłoty

```
ZADANIE G7 (slug: street-greenery). Ustal, jaka zieleń rośnie przy ulicach Białegostoku, najpierw w kaflu (ok. 53,152 N 23,168 E: Andersa, Wileńska, Sokólska, ulice domów jednorodzinnych Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka), potem typowo w mieście: gatunki drzew przyulicznych (lipa, klon, jesion, kasztanowiec, brzoza…), wiek/wysokość, rozstaw w szpalerach, pasy zieleni, żywopłoty przy domach (gatunki: tuja, ligustr, grab…, wysokość), drzewa w ogrodach widoczne z ulicy, krzewy na wyspach i rondach, trawniki (koszenie, chwasty, pobocza).
Źródła: miejskie dane o drzewach (BIP / Geoportal Białystok / inwentaryzacje zieleni / projekty nasadzeń w przetargach), OSM (natural=tree, tree_row, hedge — policz w kaflu), zdjęcia Mapillary/Commons ze współrzędnymi i porą roku.
Wynik ma posłużyć generatorowi roślinności: gęstość (drzew/100 m ulicy), proporcje gatunków, wysokości, odsetek posesji z żywopłotem od ulicy — każda liczba z metodą liczenia.
manifest.csv — kolumny dodatkowe: ulica, lat, lon, gatunek, wysokość_m, typ (drzewo/szpaler/żywopłot/krzew), sezon, metoda.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G8 — ciężarówka i naczepa: wymagania przepisów widoczne z zewnątrz i z kabiny

```
ZADANIE G8 (slug: truck-regulations). Gra ma jedną fikcyjną (bez marki) ciężarówkę: ciągnik siodłowy 4×2 + naczepa firanka 13,6 m, trzy osie. Zbierz wymagania przepisów, które wpływają na jej wygląd i widok z kabiny, z cytatami: regulamin EKG ONZ R48 (rozmieszczenie świateł: pozycyjne, obrysowe, boczne, kierunkowskazy, odblaski, wysokości i odległości od krawędzi), R104 i R70 (oznakowanie odblaskowe konturowe), R46 (lusterka: klasy II, IV, V, VI — pola widzenia z wymiarami), R58/R73 (osłony przeciwwjazdowe tylne i boczne — wysokości, prześwity), dyrektywa 96/53/WE (wymiary, masy, w tym aktualizacje 2015/719 i nowsze), tablice rejestracyjne PL (wymiary, położenie), tabliczki znamionowe, tachograf, kliny pod koła, gaśnice, trójkąt — co jest obowiązkowe w PL.
Źródła: EUR-Lex, UNECE (pełne teksty), ISAP; cytaty z numerem punktu. Dodaj rysunki/schematy tylko z licencją pozwalającą (zwykle dokumenty UNECE/EUR-Lex są urzędowe).
manifest.csv — kolumny dodatkowe: element, przepis, punkt, wartość, jednostka, warunek (np. dla N3, dla O4), cytat.

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G9 — dźwięki referencyjne na wolnych licencjach

```
ZADANIE G9 (slug: audio-refs). Znajdź nagrania referencyjne (do porównania widm i do ewentualnego użycia) dźwięków ciężkiej ciężarówki z naczepą i otoczenia miejskiego: silnik diesla R6 ok. 13 l na biegu jałowym i pod obciążeniem (wnętrze kabiny i zewnątrz), hamulec silnikowy, retarder, zautomatyzowana skrzynia (zmiany biegów), hamulce pneumatyczne (spust, „psyknięcie”, osuszacz), sprężarka, kierunkowskaz w kabinie, sygnał cofania, opony na mokrym i suchym, przejazd po dylatacji wiaduktu, ruch miejski i ekspresówka z perspektywy kabiny, deszcz na dachu kabiny.
Źródła: Freesound (TYLKO CC0 i CC BY — podaj id dźwięku, autora, licencję), Wikimedia Commons, BBC Sound Effects tylko jako link (licencja RemArc — nie pobieraj), archiwa na CC0. Bez nagrań z nazwą/marką producenta w opisie, jeśli ma to znaczenie licencyjne — opisz.
Dla każdego: opis, długość, format, częstotliwość próbkowania, jakość 1–5, czy jest w kabinie/zewnątrz, typ silnika jeśli znany.
manifest.csv — kolumny dodatkowe: kategoria, opis, długość_s, format, sample_rate, kabina_zewnątrz, freesound_id, jakość_1_5. W ZIP tylko CC0 i CC BY (oryginalne pliki, bez konwersji).

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

---

## G10 — ograniczenia dla ciężarówek w Białymstoku vs OSM

```
ZADANIE G10 (slug: truck-restrictions). Ustal obowiązujące ograniczenia ruchu ciężarówek w Białymstoku (najpierw w okolicy 53,152 N 23,168 E, potem całe miasto i dojazdy): zakazy wjazdu pojazdów > X t (B-5, B-18, B-19, strefy), ograniczenia wysokości (B-16) pod wiaduktami i kładkami, długości (B-17), szerokości, nacisku osi, zakazy w określonych godzinach, wyznaczone trasy dla ruchu tranzytowego/ciężkiego, strefy dostaw, ulice z zakazem zatrzymywania dla ciężarówek, parkingi dla ciężarówek.
Źródła: uchwały i zarządzenia (BIP Białystok, Dziennik Urzędowy Województwa Podlaskiego), projekty organizacji ruchu, komunikaty ZDiT, zdjęcia znaków z Mapillary (key + współrzędne), dane OSM (maxweight, maxweight:hgv, maxheight, maxlength, hgv=*, access — podaj id drogi OSM).
Najważniejsze: tabela porównania „przepis/znak w terenie” vs „tag w OSM” — gdzie OSM jest niepełny lub błędny (to wpływa na nawigację w grze). Nie edytuj OSM.
manifest.csv — kolumny dodatkowe: ulica, odcinek_od_do, lat, lon, ograniczenie, wartość, godziny, podstawa_prawna, znak_mapillary_key, osm_way_id, osm_tag_obecny, zgodne_z_OSM (TAK/NIE/BRAK).

Pracujesz jako researcher dla projektu Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK, gra komercyjna (budżet 0 zł). Odpowiadasz i piszesz po polsku.

TWARDE ZASADY:
1. ZAKAZ używania Google Maps, Google Street View, Google Earth i Google 3D Tiles — ani jako źródła, ani do sprawdzania. Dozwolone: Mapillary (CC BY-SA 4.0), Wikimedia Commons, OpenStreetMap (ODbL), Geoportal/GUGiK (ortofoto, dane otwarte), BIP i dokumenty urzędowe (przetargi, uchwały, projekty organizacji ruchu), ISAP/ELI, strony GDDKiA, ZDiT Białystok, Freesound (tylko CC0 / CC BY), własne zdjęcia autorów z jawną licencją.
2. Licencje: zapisuj licencję i autora każdego pliku. Do ZIP pobieraj TYLKO pliki z licencją pozwalającą na użytek komercyjny (CC0, domena publiczna, CC BY, CC BY-SA, dokumenty urzędowe — art. 4 ustawy o prawie autorskim). Pliki NC, ND albo bez jasnej licencji — tylko link w manifeście, z dopiskiem „tylko referencja, nie pobrano”. Bez marek i logo producentów ciężarówek.
3. Nie zmyślaj. Każda liczba i każdy fakt ma źródło (link + data dostępu + cytat ≤ 25 słów albo numer strony/tabeli). Czego nie da się potwierdzić — oznacz UNVERIFIED. Wartości szacowane z dowodów (np. wysokość z proporcji na zdjęciu) — oznacz ESTIMATED z metodą.
4. Pozycje: dla każdego zdjęcia/obiektu podaj współrzędne (WGS84, 6 miejsc) i kierunek patrzenia (stopnie od północy), jeśli źródło je ma; inaczej opisz, skąd je ustaliłeś, albo UNVERIFIED.
5. Pracuj długo i dokładnie — to jest zlecenie na wiele godzin; używaj wyszukiwania i agentów, ile potrzebujesz. Przed oddaniem zrób samokontrolę: sprawdź ponownie losowe 20 % pozycji (link działa, licencja się zgadza, współrzędne pasują do opisu) i opisz wynik w README.

WYNIK — jeden plik ZIP o nazwie gptpro-<NR>-<slug>.zip:
- README.md — po polsku: cel, metoda, najważniejsze ustalenia (wypunktowane), braki i niepewności, wynik samokontroli.
- manifest.csv — jeden wiersz na pozycję (kolumny podane w zadaniu; zawsze także: id, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- files/ — pobrane pliki o nazwach <id>.<rozszerzenie>; zdjęcia zmniejszone do maks. 1600 px dłuższego boku, JPG; łącznie ZIP ≤ 80 MB.
- sources.md — lista wszystkich źródeł z datą dostępu.
GITHUB (jeśli masz dostęp z prawem zapisu do repo woogitsugames/kamion): utwórz gałąź gptpro/<NR>-<slug> od main, wrzuć zawartość ZIP do katalogu research/gptpro/<NR>-<slug>/ i zrób commit. NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Jeśli nie masz dostępu — tylko ZIP. Na końcu napisz: „G<NR> gotowe” + co oddałeś (ZIP / gałąź).
```

# RESEARCH-PACK-02 — kolejne zlecenia badawcze dla innego modelu (s16, 2026-11-13)

Każdy blok P1–P10 jest samodzielny: **skopiuj cały blok z ramki ``` i wklej do osobnej rozmowy** (zasady, licencje, format wyniku i samokontrola są w środku, razem z poprawkami z recenzji paczek 01). Wynik: ZIP `gptpro-<NR>-<slug>.zip` (NR = p1…p10, slug z bloku) i opcjonalnie gałąź `research/<NR>-<slug>` bez pushu na main. Lider wrzuca ZIP-y do `research/gptpro/` i przydziela agentom (kontrola jak w `docs/reports/REVIEW-2026-11-13-s16-gptpro-g2-g3.md`).

Kolejność (priorytet): P1 (G1 zdjęcia trasy) → P2 (G6 nawierzchnie) → P3 (G4 zabudowa) → P4 (G8 przepisy ciężarówki) → P5 (G9 uzupełnienie) → P6 (G2 uzupełnienie) → P7 (G3 uzupełnienie) → P8 (G10) → P9 (G5) → P10 (G7).

| Blok | Zlecenie | Powód |
|---|---|---|
| P1 | G1 route-photos | nieoddane; główna luka wizualna |
| P2 | G6 surfaces | nieoddane |
| P3 | G4 building-typology | nieoddane |
| P4 | G8 truck-regulations | nieoddane |
| P5 | G9 audio-refs-2 | braki G9: retarder, hamulec silnikowy, osuszacz, skrzynia, R6 13 l, oryginały zamiast podglądów MP3 |
| P6 | G2 next-regions-2 | kafle Dojlidy/Krywlany, WIM, niesprawdzone źródła, trasy dojazdu |
| P7 | G3 s8-signs-2 | aktualność 2025–2026, DK19/DK65/S19, epoki bramownic, kontrola Mapillary |
| P8 | G10 truck-restrictions-2 | skrajnia Putry, e-TOLL, plan UM 2018 |
| P9 | G5 street-furniture-2 | UNVERIFIED wymiary mebli, przystanki ze współrzędnymi |
| P10 | G7 street-greenery-2 | rejestr drzew, drugi sezon, żywopłoty |

Uwaga dla właściciela: modele z przeglądarką mogą pobrać kadry Mapillary ręcznie (zasada A); bez przeglądarki wynik będzie z oznaczeniami UNVERIFIED zamiast zgadywania. Oryginały audio z Freesound wymagają darmowego konta — pobiera je właściciel z `download_list.csv` (P5).

---

## P1 — zdjęcia referencyjne trasy w obecnym kaflu (G1, nieoddane)

*Dlaczego: G1 nie został oddany. Brakuje ujęć z wysokości oka kierowcy dla ulic, rond i wiaduktów kafla; dotychczasowe zdjęcia (G3, G7) pokrywają głównie Andersa/Putrę i kwiecień 2024.*

```
ZADANIE P1 (NR: p1, slug: route-photos). Zbierz zdjęcia referencyjne z poziomu kierowcy ciężarówki (wysokość oka ok. 2,5 m, widok wzdłuż jezdni, kamera z kabiny lub samochodu dostawczego) dla ulic i rond kafla wokół 53,152 N 23,168 E w Białymstoku: Generała Władysława Andersa, Generała Stanisława Maczka, Aleja Tysiąclecia Państwa Polskiego, Bitwy Białostockiej, Białostoczek, Kombatantów, Michała Motoszko, Stefana Batorego, Władysława Bełzy, Wileńska, Sokólska, Grodzieńska, Brzeska, Buska, Kowieńska, Lidzka, Olsztyńska, Racławicka, Sitarska, Skidelska, Wołkowyska, Łańcucka, Świsłocka; rondo Krzysztofa Jakuba Putry, rondo Pamięci Bieżeństwa 1915 roku; wiadukty i łącznice S8/DK8 w tym rejonie.
Cel: dla każdej ulicy ≥ 3 ujęcia w OBU kierunkach (początek, środek, skrzyżowanie); dla rond i wiaduktów ≥ 6 ujęć, po jednym z każdego wlotu i wylotu. Dla każdej ulicy co najmniej jedno ujęcie z DRUGIEGO sezonu niż pozostałe (jeśli wszystkie dostępne są z jednej pory roku — zapisz to jako lukę).
Źródła: Mapillary (patrz zasada A), Panoramax (panoramax.xyz, CC BY-SA; instancje publiczne), Wikimedia Commons (kategorie Białystok, ulice, rondo Putry), zdjęcia z jawną licencją z BIP/ZDiT (dokumentacja przebudów).
Priorytet: 2023+, dzień, bez mocnego rozmycia, bez dużych pojazdów zasłaniających widok. Odrzucaj kadry kontrasłoneczne i nocne (wpisz je jako odrzucone w manifeście z powodem).
manifest.csv — kolumny dodatkowe: ulica, punkt_opis, lat, lon, kierunek_deg, data_zdjęcia, sezon, pora_dnia, mapillary_key, panoramax_id, jakość_1_5, odrzucone_powód.
W README: tabela pokrycia (ulica × kierunek × liczba ujęć × sezony), lista luk, 10 najlepszych kadrów do kamer kontrolnych gry z uzasadnieniem.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P2 — nawierzchnie, krawężniki i oznakowanie poziome (G6, nieoddane)

*Dlaczego: G6 nie został oddany. Gra ma generyczne materiały asfaltu, kostki i krawężników; brakuje dowodów z dokumentów i zdjęć, jak to wygląda w Białymstoku.*

```
ZADANIE P2 (NR: p2, slug: surfaces). Ustal, jakie nawierzchnie i elementy jezdni występują w Białymstoku (najpierw kafel ok. 53,152 N 23,168 E): asfalt (kolor świeży/stary, łaty, spękania, koleiny na S8 i ulicach), kostka betonowa (typy, kolory, wzory na chodnikach, zatokach, wyspach), płyty, krawężniki (typy 15×30, 20×30, najazdowe, wysokość wystawania), obrzeża, ścieki przykrawężnikowe, pasy rowerowe (kolor nawierzchni), płytki dotykowe, azyle, oznakowanie poziome (stan zużycia, farba/masa grubowarstwowa, profilowane, szerokości linii wg rozporządzenia o znakach i sygnałach drogowych).
Źródła: standardy techniczne ZDiT/miasta (BIP, „katalog standardów”, np. standardy z 2018 r. dla Białegostoku), dokumentacja przetargowa przebudów ulic z kafla (STWiORB, przedmiary: grubości warstw, typy kostki, krawężniki), GDDKiA dla S8 (OST, WT-2 dla nawierzchni asfaltowych), rozporządzenie w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych (ISAP; szerokości linii, odblaskowość), zdjęcia Mapillary/Commons/Panoramax ze współrzędnymi.
Dla każdego elementu: zdjęcie z bliska I z poziomu kierowcy (jeśli się da), wymiary i materiały z dokumentu (numer strony), opis wyglądu w czasie (zużycie: świeże / 3–5 lat / zniszczone), przybliżony kolor sRGB z metodą (np. mediana z wycinka 100×100 px, oświetlenie opisane, ESTIMATED).
Osobno: tabela szerokości linii poziomych (P-1…P-7, P-10, P-12…) z rozporządzenia dla dróg ekspresowych, głównych i lokalnych, z cytatami punktów — wartości, których gra używa jako WORKING_VALUE, mają być potwierdzone albo skorygowane.
manifest.csv — kolumny dodatkowe: element, lokalizacja, lat, lon, materiał, wymiary, kolor_srgb, metoda_koloru, stan_zużycia, sezon, pora_dnia, dokument_strona.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P3 — typologia zabudowy z dowodami (G4, nieoddane)

*Dlaczego: G4 nie został oddany. Zabudowa jest największą częścią obrazu miasta, a gra ma jedną generyczną typologię bloków i domów bez dowodów z dokumentacji.*

```
ZADANIE P3 (NR: p3, slug: building-typology). Dla Białegostoku (najpierw okolice 53,152 N 23,168 E: osiedla przy Andersa, Wileńskiej, Sokólskiej, Białostoczek, Wysoki Stoczek; potem typowe dla miasta) opisz typy zabudowy widoczne z jezdni: bloki z wielkiej płyty (systemy, liczba kondygnacji, wysokość kondygnacji, rytm okien, balkony/loggie, kolory po termomodernizacji), domy jednorodzinne (lata 60–80 „kostki”, nowsze), drewniane domy podlaskie, pawilony handlowe, hale i magazyny, garaże blaszane, stacje paliw, budynki usługowe.
Dla każdego typu: ≥ 5 zdjęć (licencje jak w ZASADACH) z adresem i współrzędnymi, parametry liczbowe z dowodem (dokumentacja termomodernizacji w BIP spółdzielni/miasta — np. audyty energetyczne i projekty ocieplenia; projekty; przetargi; katalogi systemów W-70, OWT-67, Szczecin itp.), typowe materiały i kolory (przybliżone sRGB z metodą), dachy (kąt, pokrycie), ogrodzenia przy tych budynkach.
Pomocniczo wolno użyć danych otwartych GUGiK (LoD1/LoD2 budynków, CC BY 4.0) do sprawdzenia wysokości i liczby kondygnacji dla podanych adresów — podaj identyfikator budynku i wartość `measuredHeight`; porównaj z wysokością z dokumentu i zapisz rozbieżność.
Wprost zaznacz, które typy da się rozpoznać z obrysu i wysokości LoD1 (generator świata), a które wymagają ręcznego przypisania.
manifest.csv — kolumny dodatkowe: typ_budynku, adres, lat, lon, kondygnacje, wys_kondygnacji_m, rytm_okien_m, kolor_srgb, metoda_koloru, dach, materiał, lod1_measuredHeight_m, sezon, pora_dnia.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P4 — ciężarówka i naczepa: wymagania przepisów (G8, nieoddane)

*Dlaczego: G8 nie został oddany. Model fikcyjnej ciężarówki ma światła, odblaski, lusterka i osłony ustawione z pamięci; potrzebne są wartości z numerem punktu przepisu.*

```
ZADANIE P4 (NR: p4, slug: truck-regulations). Gra ma jedną fikcyjną (bez marki) ciężarówkę: ciągnik siodłowy 4×2 + naczepa firanka 13,6 m, trzy osie. Zbierz wymagania przepisów, które wpływają na jej wygląd i widok z kabiny, z cytatami (≤ 25 słów) i numerem punktu: regulamin EKG ONZ R48 (rozmieszczenie świateł: pozycyjne, obrysowe, boczne, kierunkowskazy, odblaski, wysokości i odległości od krawędzi), R104 i R70 (oznakowanie odblaskowe konturowe), R46 (lusterka: klasy II, IV, V, VI — pola widzenia z wymiarami), R58/R73 (osłony przeciwwjazdowe tylne i boczne — wysokości, prześwity), dyrektywa 96/53/WE (wymiary, masy, w tym aktualizacje 2015/719 i nowsze), tablice rejestracyjne PL (wymiary, położenie), tabliczki znamionowe, tachograf, kliny pod koła, gaśnice, trójkąt — co jest obowiązkowe w PL (rozporządzenie o warunkach technicznych pojazdów, ISAP).
Dla każdej wartości podaj kategorię pojazdu (N3, O4), warunek i jednostkę. Dla R48 przygotuj tabelę „element → liczba obowiązkowa → min/max wysokość nad jezdnią → odległość od krawędzi → kolor”, osobno dla ciągnika i naczepy.
Źródła: EUR-Lex, UNECE (pełne teksty regulaminów, wersje z numerem serii poprawek i datą), ISAP. Rysunki/schematy dodaj tylko z licencją pozwalającą (dokumenty UNECE/EUR-Lex są urzędowe — zapisz podstawę).
Dodatkowo (osobna sekcja): tablice kierunkowe i ostrzegawcze na pojeździe wymagane lub spotykane w PL (tablica długiego pojazdu, ADR nie dotyczy, znak ograniczenia 80/90 na naczepie, tablice odblaskowe ostrzegawcze tył) — z podstawą prawną.
manifest.csv — kolumny dodatkowe: element, przepis, punkt, wartość, jednostka, kategoria_pojazdu, warunek, cytat, wersja_przepisu (seria/data).

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P5 — dźwięki referencyjne — uzupełnienie G9 (braki: retarder, hamulec silnikowy, osuszacz, skrzynia, R6 13 l)

*Dlaczego: Przegląd G9 (2026-11-13): 0 pozycji retardera, 0 pewnych hamulca silnikowego, osuszacza i zautomatyzowanej skrzyni, brak potwierdzonego R6 13 l, pobrane tylko podglądy MP3, 3 z 8 pozycji kabiny z samochodów osobowych, G9-C01 ma 8 kHz.*

```
ZADANIE P5 (NR: p5, slug: audio-refs-2). Uzupełnij paczkę G9 (już mamy 72 dźwięków Freesound i 7 z Commons; NIE powtarzaj ich — identyfikatory Freesound z G9: 22877, 22882, 22885, 35051, 49769, 81261, 87076, 118243, 123021, 127244, 128160, 149244, 149429, 155379, 165168, 174820, 176787, 192170, 197166, 207795, 237374, 238760, 241011, 264440, 398859, 400402, 405086, 425839, 433870, 433871, 435656, 438075, 438080, 442766, 450808, 451149, 454420, 455305, 462862, 464988, 477825, 504865, 508058, 511853, 520999, 521766, 521767, 521768, 559375, 563301, 580530, 582529, 583278, 586985, 591079, 591104, 612011, 631966, 637921, 645848, 648786, 650774, 669417, 685074, 699130, 717867, 795866, 829349, 847749, 860718, 866213, 867375). Szukamy WYŁĄCZNIE tego, czego brakuje, i lepszych odpowiedników:
1. retarder hydrokinetyczny / elektromagnetyczny ciężarówki lub autobusu (wycie, narastanie przy włączeniu stopni 1–3, wyłączenie) — priorytet 1;
2. hamulec silnikowy typu dekompresyjnego i wydechowego (klapa wydechowa) z kabiny i z zewnątrz — nagranie pojedynczego pojazdu, nie ruchu ulicznego;
3. osuszacz powietrza ciężarówki (regeneracja, „psssst” co kilkadziesiąt sekund, nie tylko spust przy hamowaniu), zawór ogranicznika ciśnienia, ostrzegacz ciśnienia;
4. zautomatyzowana skrzynia biegów ciężarówki lub autobusu (zmiana biegu z przerwą momentu, sprzęgło) z kabiny i z zewnątrz;
5. silnik rzędowy 6-cylindrowy diesel 12–13 l z NAZWANYM modelem w opisie autora (zapis w manifeście, ale w ZIP bez nazw marek w nazwach plików) — jeśli brak, napisz to wprost;
6. kabina ciężarówki europejskiej (cab-over), jazda miejska i ekspresowa — zamiast aut osobowych;
7. sygnał dźwiękowy cofania i ostrzegawczy wnętrza kabiny (bip, gong), pasy bezpieczeństwa, drzwi kabiny, przełączniki, wycieraczki, nawiew — foley wnętrza.
Źródła: Freesound (TYLKO CC0 i CC BY), Wikimedia Commons (CC0/CC BY), Internet Archive (kolekcje CC0), OpenGameArt (CC0/CC BY), Sonniss GDC (tylko jeśli licencja pozwala na użytek komercyjny; podaj cytat z licencji), BBC Sound Effects tylko link (RemArc, NIE pobieraj).
Jakość: preferuj WAV/FLAC ≥ 44,1 kHz bez kompresji stratnej. Freesound bez logowania daje tylko podgląd MP3; jeśli masz dostęp do oryginałów na własnym koncie (nie koncie właściciela) — pobierz oryginał i zapisz w manifeście `oryginal=TAK`; jeśli nie — wpisz `oryginal=NIE (podgląd MP3)` i podaj w osobnym pliku `download_list.csv` listę id/URL do ręcznego pobrania przez właściciela (kolumny: freesound_id, url, licencja, autor, plik_docelowy).
Dla każdej pozycji sprawdź na żywo stronę dźwięku: tytuł, opis, licencja, długość, częstotliwość — i przepisz je dokładnie; długość z manifestu ma zgadzać się z odtwarzaczem (w G9 pozycja G9-K03 miała 41 s zamiast ok. 82 s). Jeśli opis autora nie potwierdza, co jest na nagraniu — status UNVERIFIED, nie „SOURCED”.
Dla pozycji CC BY podaj gotowy tekst atrybucji (autor, tytuł, URL, licencja) w kolumnie `atrybucja`.
manifest.csv — kolumny dodatkowe: kategoria, opis, długość_s, format, sample_rate, bit_depth, kabina_zewnątrz, freesound_id, jakość_1_5, typ_silnika, oryginal, atrybucja.
Limit ZIP 80 MB: jeśli nie mieści się, priorytet mają kategorie 1–4 w oryginalnej jakości; reszta w download_list.csv.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P6 — regiony — uzupełnienie G2 (Dojlidy/Krywlany, WIM, niesprawdzone źródła, trasy dojazdu)

*Dlaczego: Przegląd G2: rekomendacja 5 kafli na zachód z pierwszym kaflem o 0 celów, a Dojlidy/Krywlany (silniejsze skupisko) bez kafla; waga WIM i kilka źródeł niesprawdzone; trasy dojazdu od S8 nie weryfikowane na grafie.*

```
ZADANIE P6 (NR: p6, slug: next-regions-2). Uzupełnij paczkę G2 (research/gptpro/2-next-regions: 57 miejsc, 5 kafli 2×2 km na zachód od regionu bialystok-industrial-c, bbox EPSG:2180 776971–779019 × 595199–597247). NIE powtarzaj istniejących miejsc; popraw i dopisz:
1. Zaproponuj 3–5 kafli 2×2 km (siatka EPSG:2180, dokładnie przylegająca do obecnego bboxu lub do poprzedniego kafla — podaj współrzędne rogów jako liczby całkowite w metrach) wokół Dojlid, Krywlan i Fabrycznej/Suchowolca na wschodzie/południowym wschodzie oraz na północ (DK8 w stronę Tykocina/Złotorii). Dla każdego kafla: liczba celów dla ciężarówek z oceną TAK/NIE/UNVERIFIED, liczba km dróg klasy ≥ secondary w kaflu, czy kafel łączy się ciągłym korytarzem z obecnym regionem, i czy kafel ma rozpoznawalne punkty orientacyjne. Porównaj z kaflami z G2 w jednej tabeli i wskaż najlepszą kolejność dla gry (zwróć uwagę: cele = konkretne zakłady i ich bramy, nie tagi industrial).
2. Zamknij pozycje UNVERIFIED z G2: RS16 (waga WIM Zabłudowska — współrzędne i dowód), strona Panattoni (była 403), Biazet (błąd certyfikatu), ogłoszenie TED 213042-2026 (PDF nieczytelny), data otwarcia S19 odcinek Krynice–Białystok Zachód (czy 20.10.2026 — podaj komunikat GDDKiA z datą), data otwarcia MOP Haćki (czy 29.10.2026). Każdą oznacz SOURCED z cytatem albo zostaw UNVERIFIED z opisem, co sprawdzono.
3. Dla 10 najważniejszych celów (z G2) zweryfikuj trasę dojazdu od S8 na danych OSM (wycinek pliku z Geofabrik lub Overpass dla małego bboxu — NIE masowe zapytania; podaj wersje way) i zapisz kolejne ulice z `highway`, `maxweight`/`hgv` oraz `maxheight`. Zaznacz, gdzie trasa przechodzi przez ograniczenie dla ciężarówek (patrz research/g10-truck-restrictions).
4. Bramy i place manewrowe: dla ≥ 10 zakładów z TAK podaj z ortofoto GUGiK (Geoportal, WMS/WMTS otwarte dane; bez Google) szerokość bramy i promień łuku wjazdu (ESTIMATED, metoda i niepewność ±).
manifest.csv — kolumny dodatkowe: nazwa, typ, adres, lat, lon, osm_id, osm_wersja, dojazd_od_S8, naczepa_13_6_ok, dowód, kafel_id, bbox_2180.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P7 — tablice kierunkowe — uzupełnienie G3 (aktualność 2025–2026, DK19/DK65/S19, ujednolicenie portali)

*Dlaczego: Przegląd G3: tylko 3 zdjęcia z 2026, 83/152 z 2024; Mapillary nie sprawdzony bezpośrednio; gra ma dwa portale Andersa w różnych epokach (2020 vs 2024); brakuje DK19, DK65 i S19.*

```
ZADANIE P7 (NR: p7, slug: s8-signs-2). Uzupełnij paczkę G3 (research/gptpro/3-s8-signs: 152 pozycje, głównie 2024). NIE powtarzaj istniejących tablic; dopisz i sprawdź:
1. Aktualny stan (zdjęcia 2025–2026; podaj datę) bramownic i tablic w rejonie ronda Putry / Andersa / Al. Tysiąclecia, w obu kierunkach. Dla każdej bramownicy lista paneli (lewy górny, lewy dolny, prawy górny, prawy dolny) z tekstem dokładnie jak na tablicy, numerami dróg (E67, 8, 19, 65, 675 itd.) i strzałkami. Zaznacz, czy treść 2024 jest dalej aktualna.
2. Rozstrzygnij rozbieżność epok: bramownica „andersa-gantry” w grze ma tablicę pasa 2 jako jedną (Augustów / Kuźnica / Centrum, stan 2020), a zdjęcia 2024 mają „Centrum” osobno. Znajdź wszystkie zdjęcia obu bramownic Andersa w latach 2019–2026, ułóż oś czasu zmian treści i wskaż rok zmiany (jeśli ustalisz z dokumentu GDDKiA/ZDiT, podaj numer decyzji; inaczej przedział ze zdjęć).
3. Nowe obszary: DK19 (Białystok – Lublin, 15 km od miasta), DK65 (Białystok – Bobrowniki), DK8 na północ do Tykocina, S19 (nowe odcinki) i S8 do węzła Zawady/Wasilków — tablice E-1, E-2, E-3, E-4, E-14, E-15, przeddrogowskazy, numery węzłów, odległości. Tylko zdjęcia z jawną licencją i danymi (zasada A).
4. Zweryfikuj bezpośrednio na Mapillary (zasada A) 25 pozycji z istniejącego G3 (wybierz losowo, podaj seed): czy klucz, data i współrzędne zgadzają się. Wynik w osobnym pliku `mapillary_recheck.csv`.
5. Dla każdego nowego znaku wypełnij `numery_dróg` jako JSON (numer / kolor tła: zielony, niebieski, żółty / litery), `strzałki`, `grupa_tablic`, `pole_tablicy` w tym samym schemacie co G3, żeby wynik dało się dołączyć do generatora tablic bez konwersji.
manifest.csv — kolumny dodatkowe: lat, lon, kierunek_deg, droga, typ_znaku, tekst_wiersze (rozdzielone „|”), numery_dróg, piktogramy, strzałki, grupa_tablic, pole_tablicy, data_zdjęcia, mapillary_key, sezon, pora_dnia.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P8 — ograniczenia dla ciężarówek — uzupełnienie G10 (e-TOLL, skrajnia Putry, plan UM 2018)

*Dlaczego: G10 (Claude): brak tokenu Mapillary; skrajnia pod wiaduktem Putry UNVERIFIED; lista odcinków e-TOLL DK8/19/65 UNVERIFIED; aktualność klas tonażowych planu UM 2018 UNVERIFIED.*

```
ZADANIE P8 (NR: p8, slug: truck-restrictions-2). Uzupełnij research/g10-truck-restrictions (OSM vs rzeczywistość dla ograniczeń ruchu ciężarówek w Białymstoku i na dojazdach S8/DK8/DK19/DK65). Zamknij pozycje UNVERIFIED:
1. Skrajnia pod wiaduktami: rondo Putry, wiadukty Andersa, wiadukt Al. Tysiąclecia, ronda Wolnej Ukrainy i Żołnierzy Wyklętych, Al. Niepodległości — znak B-16 / tabliczka wysokości, jeśli jest; dokument (projekt wykonawczy, przetarg GDDKiA/ZDiT, dokumentacja przebudowy) z deklarowaną skrajnią w m, strona/cytat; zdjęcia podjazdu z oznakowaniem (zasada A). Jeśli nie ma znaku — napisz to jako fakt i podaj skrajnię ustawową (4,0 m dla dróg publicznych wg prawa — wskaż przepis).
2. e-TOLL: oficjalna lista odcinków dróg płatnych dla pojazdów > 3,5 t w okolicy Białegostoku (S8, DK8, DK19, DK65, S19) wg obwieszczenia/ rozporządzenia lub strony kierowca.e-toll.pl / GDDKiA, z numerem aktu i datą wersji. Mapa lub lista pozwalająca porównać z `toll:hgv=yes` w OSM.
3. Plan transportowy UM Białystok 2018 (uchwała LI/794/18, s. 23): klasy tonażowe 3,5 t / 12 t / 40 t — czy obowiązują, czy zostały zmienione późniejszymi uchwałami lub zarządzeniami (szukaj w BIP i Dzienniku Urzędowym Woj. Podlaskiego; podaj datę najnowszej zmiany). Rozstrzygnij sprzeczne tagi: Bitwy Białostockiej (way 178208423 hgv=no + goods=delivery), Sokólska (188396757), Warszawska (way 842154286 maxweight=12 t razem z hgv=no), Branickiego i Zwierzyniecka (OSM 8 t vs plan 12 t).
4. Znaki B-5, B-18, B-20 (zakaz wjazdu ciężarówek, ograniczenie tonażu) w kaflu i na dojazdach, w pierwszej kolejności zdjęcia znaków przy Bitwy Białostockiej (way 178208423) i Sokólskiej (way 188396757) w obu kierunkach oraz numery zarządzeń/uchwał ustanawiających te zakazy (organizacja ruchu ZDiT, BIP): zdjęcia ze współrzędnymi i datą (zasada A), z rozróżnieniem „wyjątek dostawy / mieszkańcy / strefa”.
5. Wnioski dla pipeline: lista tagów, które powinny trafić do grafu dróg gry (`maxweight`, `maxweight:hgv`, `maxaxleload`, `maxlength`, `hgv:conditional`, `maxheight`, `toll:hgv`), z propozycją reguły rozstrzygania sprzeczności (źródło urzędowe > OSM > domyślne).
manifest.csv — kolumny dodatkowe: ulica_lub_obiekt, osm_way_id, tag_osm, wartość_osm, wartość_urzędowa, dokument_strona, lat, lon, zgodność (ZGODNE/SPRZECZNE/BRAK_ZNAKU/UNVERIFIED), data_zdjęcia, mapillary_key.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P9 — meble uliczne — uzupełnienie G5 (kosze, ławki, szafki, sygnalizatory, żerdzie, hydranty, przystanki)

*Dlaczego: G5 (Claude): 5 pozycji UNVERIFIED i 11 ESTIMATED; brak wymiarów koszy, ławek, szafek, sygnalizatorów i słupów energetycznych w Białymstoku; Mapillary niedostępne bez tokenu; przystanki bez współrzędnych.*

```
ZADANIE P9 (NR: p9, slug: street-furniture-2). Uzupełnij research/g5-street-furniture (wymiary mebli ulicznych Białegostoku z przetargów). Zamknij luki:
1. Kosze na śmieci, ławki, stojaki rowerowe, osłony drzew, bariery U-12/U-12a, słupki: konkretne modele lub wzory z białostockich przetargów ZDiT/BKM/BPBK z wymiarami z karty (strona), kolorem RAL, materiałem. Jeśli ich w Białymstoku nie ma w dokumentach — znajdź miasto o podobnym standardzie, ale oznacz jako proxy z uzasadnieniem.
2. Sygnalizatory świetlne (słupy ø, wysokości, wysięgniki, wysokość główki nad jezdnią): normy/wytyczne (rozporządzenia, katalogi producentów) i dokumentacja przetargowa ZDiT Białystok — wymiary dla signal_pole 4,0 m i signal_mast 6,8 m (obecnie WORKING_VALUE).
3. Słupy energetyczne i oświetleniowe: żerdzie (E-9/E-10/E-12 wg normy PN-EN 12843 / katalogów) — wysokość całkowita, średnica u podstawy i wierzchołku; potwierdź 10 m vs 12 m dla `power_pole`. Rozkład wysokości latarni wg klas dróg w standardzie ZDM (uwaga: poprzednio znaleziono „oprawy do 11 m”).
4. Hydranty nadziemne: wysokość nad gruntem z karty producenta lub normy (zastąp ESTIMATED wartością z dokumentu); skrzynki gazowe i telekomunikacyjne (szafki): wymiary typowych szafek (PFU, Orange/operator — tylko z publicznych kart technicznych, bez marek w nazwach plików).
5. Przystanki: dopasuj numery inwentarzowe przystanków z załącznika 8 (z G5) do współrzędnych — źródła: OSM `highway=bus_stop` w wycinku pliku (nie masowe Overpass) i GTFS Białegostoku/BKM, jeśli ma jawną licencję; podaj tylko pewne dopasowania (nazwa + ulica + odległość ≤ 30 m), pozostałe UNVERIFIED.
6. Zdjęcia z poziomu kierowcy (zasada A) po jednym wzorze każdego mebla w kaflu (53,152 N 23,168 E) z datą i współrzędnymi.
manifest.csv — kolumny dodatkowe: obiekt, model_wzór, wymiary_m, materiał, kolor_ral, dokument_strona, lat, lon, status_poprzedni (z G5), zmiana (potwierdzono/skorygowano/nowe).

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

## P10 — zieleń przyuliczna — uzupełnienie G7 (rejestr drzew, drugi sezon, żywopłoty)

*Dlaczego: G7 (Claude): brak rejestru drzew przyulicznych (proporcje gatunków to WORKING_VALUE z ok. 40 zdjęć); pokrycie ulic Kowieńska/Lidzka/Skidelska/Wołkowyska/Świsłocka wyłącznie z Commons, jeden fotograf, kwiecień 2024; gęstość młodych drzew przy Andersa UNVERIFIED.*

```
ZADANIE P10 (NR: p10, slug: street-greenery-2). Uzupełnij research/g7-street-greenery. Zadania:
1. Rejestr drzew: znajdź w otwartych źródłach jakiekolwiek zestawienie drzew w pasach drogowych Białegostoku (BIP miasta/ZDM/Wydział Ochrony Środowiska, Geoportal Białegostoku warstwy zieleni, dane otwarte miasta, pozwolenia na usunięcie drzew z listą gatunków, inwentaryzacje przy przebudowach ulic w kaflu, programy nasadzeń — np. „Białystok drzewa przyuliczne”, uchwały o nasadzeniach). Wyciągnij liczby gatunków i wieku/obwodu, gdzie są. Jeśli nic nie ma — przygotuj gotowy tekst wniosku o informację publiczną (ustawa o dostępie do informacji publicznej) do ZDM Białystok z dokładnym zakresem danych (gatunek, obwód pnia, współrzędne, ulica); wniosku NIE wysyłaj.
2. Drugi sezon: dla ulic Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska, Racławicka, Łańcucka znajdź zdjęcia z lata (pełna zieleń) i jesieni/zimy (zasada B), ze współrzędnymi i kierunkiem; wskaż, które ulice nadal mają tylko jeden sezon.
3. Żywopłoty i ogrodzenia zielone przy domach jednorodzinnych (Łańcucka i podobne): gatunki rozpoznane ze zdjęć (żywotnik, ligustr, grab, świerk), wysokość w m (ESTIMATED z proporcji do znanego elementu, metoda), gęstość pokrycia odcinka ulicy w % — z min. 20 odcinków po 100 m.
4. Młode drzewa przy Andersa/Al. Tysiąclecia: policz z kolejnych kadrów (2022–2026) liczbę drzew na 100 m odcinka dla ≥ 10 odcinków, wiek sadzenia (z zestawienia dat zdjęć), gatunek jeśli widać. Zamknij status UNVERIFIED liczbą z metodą.
5. Gatunki: katalogi szkółek tylko jako źródło wymiarów dojrzałych drzew (wysokość, korona, kształt) dla 10 najczęstszych gatunków przyulicznych Podlasia (lipa drobnolistna, klon pospolity, klon jawor, brzoza brodawkowata, jesion, topola, dąb szypułkowy, kasztanowiec, jarzębina, świerk pospolity) z cytatem strony.
manifest.csv — kolumny dodatkowe: obiekt, ulica, lat, lon, kierunek_deg, gatunek, wysokość_m, korona_m, gęstość_na_100m, sezon, pora_dnia, data_zdjęcia, metoda, status_poprzedni.

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
DODATKOWE ZASADY PACZKI 02 (wynikają z recenzji paczek 01):
A. Mapillary: API wymaga tokenu, a agenci go nie mieli. Jeśli masz przeglądarkę, otwórz mapillary.com/app ręcznie (bez logowania na konto właściciela; token przeglądarki własny lub publiczny widok), odczytaj image key z adresu (parametr pKey), datę i autora z panelu zdjęcia i pobierz kadr. Jeśli nie masz przeglądarki — nie zgaduj kluczy; oznacz pozycję UNVERIFIED i napisz, czego zabrakło. Klucze zapisuj jako TEKST (są 15–16-cyfrowe).
B. Sezon i pora: zdjęcia z Commons są często z jednej pory roku (kwiecień 2024, jeden fotograf). Szukaj aktywnie drugiego sezonu (pełne liście lipiec–wrzesień, jesień, zima bez liści/śnieg) oraz innej pory dnia i oświetlenia. W manifeście kolumna sezon (liście / bez liści / śnieg) i pora_dnia (rano / południe / wieczór / zmierzch) są obowiązkowe dla każdego zdjęcia.
C. Nie zmniejszaj przeglądu do jednej rodziny źródeł: gdy zdjęcie jest z Mapillary (CC BY-SA 4.0), podaj w uwagach „share-alike: używać jako referencji, nie jako tekstury”. Treści faktograficzne (odczytany tekst, wymiar) są wolne; same wycinki zdjęć traktujemy jako referencję z atrybucją.
D. Format plików: zdjęcia JPG (nie PNG — PNG wymaga w repo Git LFS), dokumenty PDF/XLSX tylko urzędowe (art. 4 prawa autorskiego) i ≤ 5 MB każdy; audio w oryginalnej postaci (WAV/FLAC) tylko jeśli ZIP mieści się w limicie.
E. Identyfikatory: jedna spójna konwencja <PREFIKS>-<numer> (np. P1-001) w CAŁYM manifeście; pole id i klucze zewnętrzne jako tekst.
F. Samokontrola 20 %: losuj z jawnym seedem (podaj go w README), losowanie ma objąć ≥ 20 % wszystkich pozycji, nie tylko pobranych; wynik wpisz do README i do pliku audit_20_percent.json (lista id, co sprawdzono, wynik).
G. GitHub: jeśli masz prawo zapisu do repo woogitsugames/kamion, utwórz gałąź research/<NR>-<slug> od main (ZIP-owa zawartość do research/gptpro/<NR>-<slug>/), commit, NIE pushuj na main, NIE otwieraj PR, nie zmieniaj innych plików. Bez dostępu — tylko ZIP.
```

---

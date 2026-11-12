> Notatka częściowa. Końcowa integracja i globalna samokontrola: README.md oraz audit_20_percent.json. Nazwy roboczych zapytań wymienione w opisie metody nie oznaczają dodatkowych plików w paczce.

# DK8 na północ od Białegostoku — odczyty Mapillary (część MN)

Data dostępu: **2026-11-12**. Zakres: północny odcinek DK8 od granicy Białegostoku przez zjazdy Osowicze i Jurowce, rozdzielenie DK8/DK19 i Katrynkę, z obserwacjami z obu kierunków jazdy. Najdalej na północ położona wybrana tablica oznacza wjazd do Rybnik w kierunku Augustowa. Współrzędne wszystkich wybranych kamer mieszczą się w przybliżonym buforze 15 km od granicy administracyjnej Białegostoku (granica OSM, bufor EPSG:2180; geometria i metoda w `files/G3-OSM004.geojson`). To dobór potwierdzonych obserwacji, a nie deklaracja kompletnej inwentaryzacji każdego fizycznego znaku na tym korytarzu.

## Wynik

- **24 obserwacje, 22 grupy fizycznych tablic lub paneli:** dwie lokalizacje mają oddzielnie zapisane obserwacje historyczne i nowsze. Dwa odrębne panele na tej samej bramownicy zachowano jako dwa rekordy. Liczby wynikają z `records.json (rekordy MN)`, pól `id` i `obiekt_grupa`.
- **18 rekordów SOURCED** ma potwierdzony tekst główny; **6 rekordów UNVERIFIED** zawiera odczyt częściowy. Flaga UNVERIFIED nie neguje czytelnych fragmentów wpisanych w tym samym rekordzie.
- **22 obserwacje z 2024 r.** pochodzą od `kino` (2024-07-26, kierunek północny) i `strudel` (2024-08-15, kierunek południowy). Dwie obserwacje historyczne pochodzą od `szurek` (2017-08-16) i `richlv` (2017-07-15). Daty i autorzy są polami publicznych metadanych Mapillary zapisanych w `files/G3-META001.json`.
- Wszystkie pliki JPG zawierają wycinki rzeczywistych tablic. Nie odtwarzano liter, nie odszumiano generatywnie, nie prostowano perspektywy i nie usuwano zasłaniających obiektów. Zapisano prostokąt kadru w pikselach źródła, rozmiar oryginału i SHA256. Kadry nie zawierają znaków producentów ciężarówek.

## Najważniejsze ustalenia

1. **Zachowano dosłowną sprzeczność odległości do Suwałk.** Na MN004 jest `Suwałki 114`, a na następnym odcinku na północ, MN009, `Suwałki 119`. Jednocześnie Augustów zmienia się z 83 na 80, a Kowno z 239 na 236. Liczby nie zostały „naprawione” według odległości drogowej. Źródła: [MN004](https://www.mapillary.com/app/?pKey=876869244252986), [MN009](https://www.mapillary.com/app/?pKey=1009127457582864), dodatkowa [klatka potwierdzająca 119](https://www.mapillary.com/app/?pKey=8391472337531180); odczyt tablic, dostęp 2026-11-12. Drugi badacz niezależnie potwierdził 119 na ostatniej klatce.
2. **Przy zjeździe Osowicze zapis na tablicach brzmi `Osowicze`.** Muzea podpisano `Muzeum Dziejów Ziemi` oraz `Podlaskie Muzeum Kultury Lud.`. Skrótu `Lud.` nie rozwinięto. Źródła: [MN001](https://www.mapillary.com/app/?pKey=2899614616862562), [MN021](https://www.mapillary.com/app/?pKey=1600170667206591) i jego pomocnicza klatka; odczyt fotografii, dostęp 2026-11-12.
3. **Przed zjazdem na DK19 od północy w 2017 r. tablica pokazywała `Sanktuarium` / `Święta Woda` oraz B-33 z liczbą 40.** W fotografii z 2024 r. mały napis i liczba są zbyt słabe, by przenieść je do nowszego rekordu. Źródła: [MN024, 2017](https://www.mapillary.com/app/?pKey=2940883439528148), [MN014, 2024](https://www.mapillary.com/app/?pKey=1157387411982440); odczyt tablic, dostęp 2026-11-12. Odrębna bramownica dla przeciwnego kierunku ma w 2024 r. czytelny pełny napis, zapisany w MN007.
4. **Historyczna tablica szlaku w kierunku Białegostoku zawiera `Praha CZ 812`.** W MN018 nie ma słowa „Praga” ani nawiasu. W tej samej fotografii są `Warszawa 192`, `Lublin 257`, `Rzeszów 423`; obie pozycje Białystok mają 9. Nowszy MN017 pozostaje częściowy — nie uzupełniono jego treści na podstawie starszej tablicy. Źródła: [MN018, 2017](https://www.mapillary.com/app/?pKey=193638549280421), [MN017, 2024](https://www.mapillary.com/app/?pKey=1622960618287216); odczyt fotografii, dostęp 2026-11-12.
5. **Nazwę Białystok na wlocie od Jurowiec potwierdza mała, wcześniejsza klatka.** W bliższym zdjęciu Mapillary automatycznie rozmyło początek nazwy. Jako źródło główne MN023 wybrano więc klatkę z pełnym tekstem, a bliższą zachowano wyłącznie jako pomocniczą. Źródła: [pełny napis](https://www.mapillary.com/app/?pKey=529998729367213), [zbliżenie z rozmyciem](https://www.mapillary.com/app/?pKey=1179179989800294); odczyt tablicy, dostęp 2026-11-12.

## Metoda i granice pewności

Przejrzano próbki sekwencji z publicznych metadanych Mapillary: początkowo co około piątą klatkę, w uzupełnionym wycinku Katrynki co około trzecią, a następnie sąsiednie zdjęcia wytypowanych tablic. Dla odczytów małych napisów pobierano dostępne źródła o pełnej rozdzielczości. Nie używano Google ani zewnętrznego OCR do uzupełniania nieczytelnych liter. Szerokie zapytanie API miało przerwy przestrzenne mimo braku dalszego stronicowania; uzupełniono je wąskim zapytaniem dla Katrynki. Nie traktowano wyniku zapytania jako dowodu nieistnienia zdjęć lub znaków.

`lat` i `lon` są pozycją **kamery** z pola `geometry` Mapillary. Zapis sześciu miejsc po przecinku zachowuje format danych, lecz nie oznacza dokładności geodezyjnej. Dokładne współrzędne fizycznej tablicy oznaczono UNVERIFIED. W `kierunek_deg` podano źródłowe `compass_angle`; zachowano także `computed_compass_angle` i `computed_geometry` w metadanych. Ogólny zwrot jazdy sprawdzono na obrazach. Nie przeprowadzono niezależnej kalibracji azymutu kamery. Sekwencje z widokiem przez boczne okno nie służyły do tych odczytów.

`tekst_wiersze` zapisuje czytelne wiersze, rozdzielone `|`. Numery dróg i owale krajów wpisane są przy odpowiadającym im wierszu; nie są częścią nazwy miejscowości. Dodatkowo opisano ich kolor i funkcję w polach `numery_dróg` i `piktogramy`. Schemat odgałęzienia, strzałki nad pasami i B-33 wrysowany w tablicę opisano oddzielnie. `UNVERIFIED` w tekście jest znacznikiem badawczym, nie napisem do odtworzenia w grze.

Rozpoznanie symbolu znaku (E-1, E-2a, E-2b, E-4, E-14, E-15a, E-17a, E-18a) to **ESTIMATED — klasyfikacja wizualna** według urzędowych wzorów i opisu w [Dz.U. 2019 poz. 2310, §62–66](https://eli.gov.pl/api/acts/DU/2019/2310/text.html), dostęp 2026-11-12. Nie jest odczytem numeru inwentaryzacyjnego z projektu organizacji ruchu. Przyjęto dokument odpowiadający okresowi wykonania fotografii; brak potwierdzenia aktualności fizycznego oznakowania w 2026 r.

## Braki

Pozostają nieczytelne: białe pole turystyczne MN005, pełna nazwa i ewentualna liczba drogowskazu MN013, drobny napis i B-33 MN014, białe pole MN016, większość szczegółów tablicy szlaku MN017 oraz częściowo przesłonięte pola muzealne MN022. Odczyt MN017 został niezależnie sprawdzony przez drugiego badacza; brak pewności zachowano. Nie ma pełnego katalogu małych numerów dróg, wszystkich wjazdów i wyjazdów miejscowości ani tablic odwróconych od aparatu. Zestaw nie potwierdza aktualnego oznakowania po zmianach układu dróg z 2026 r.

## Licencje i pliki

Mapillary podaje, że obrazy są udostępniane na **CC BY-SA**; odsyłacz licencyjny artykułu prowadzi do **CC BY-SA 4.0**. Źródła: [oficjalny artykuł Mapillary](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data), akapit pod nagłówkiem „CC-BY-SA license for open data”, oraz [tekst licencji CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), sekcje „You are free to” / „Under the following terms”; dostęp 2026-11-12. Autor każdego kadru jest zapisany w manifeście. Kadrowanie opisano jako modyfikację; wycinki pozostają na tej samej licencji. Zestaw zawiera wyłącznie kanoniczne linki Mapillary, bez wygasających adresów CDN i bez tokenów API.

- `records.json (rekordy MN)`, `manifest.csv (rekordy MN)`: pełne rekordy obserwacji.
- `files/G3-META001.json`: jawne metadane zdjęć głównych i pomocniczych; bez podpisanych URL i tokenów.
- `files/MN001.jpg` – `files/MN024.jpg`: 24 wycinki tablic, bez powiększania ponad źródłową liczbę pikseli.
- `sources.md`: źródła wszystkich użytych kadrów.
- `validation.json`: wynik kontroli technicznej po końcowym kadrowaniu.

## Kontrola jakości

Wszystkie 24 gotowe kadry obejrzano ponownie po wycięciu: granice kadru zachowują tablicę; małe lub zasłonięte fragmenty nie zostały syntetycznie poprawione. Kontrola techniczna sprawdziła wszystkie rekordy, zgodność autora i key z metadanymi, SHA256, format JPG, limit boku 1600 px, pozycje w przybliżonym buforze oraz brak tokenów i podpisanych URL w publicznych eksportach. Szczegóły liczbowe: `validation.json`.

Niezależna losowa samokontrola 20% całego projektu jest osobnym etapem opisanym w głównym README. Powyższa kontrola eksportu jej nie zastępuje i nie stanowi deklaracji zakończenia globalnego audytu.

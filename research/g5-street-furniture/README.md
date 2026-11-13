# G5 - meble uliczne Białegostoku: wymiary z dokumentów przetargowych i standardów miasta

Wykonał: Claude (przejęcie zlecenia G5 po ChatGPT Pro), 2026-11-13. Zakres kafla: ok. 53.152 N, 23.168 E.
Zakazane źródła (Google Maps/Street View/Earth/3D Tiles) nie były używane. Mapillary nie było użyte (API wymaga tokenu).

## 1. Cel i metoda

Ustalić z dokumentów (nie z pamięci) wymiary, materiały i kolory (RAL) wyposażenia ulic Białegostoku i porównać je z obecnym generatorem `tools/worldgen/streetscape/{props,furniture}.py` + `roads/standards.py` (stan: HEAD main 222b5e9a7, bez zmian w kodzie).

Metoda: przeszukanie BIP UM Białystok (ZDM, BKM) pod kątem załączników przetargowych z opisami i rysunkami; pobranie PDF/DOC (poza repo), wyciągnięcie tekstu (`pdftotext`/`antiword`) i ręczne odczytanie skanów (renderowane strony). Każdy wiersz `manifest.csv` ma status:

- SOURCED - liczba/zdanie z dokumentu (strona/punkt w kolumnie `dokument_strona`),
- ESTIMATED - proxy z innego miasta, katalogu albo wyliczenie z metodą w `uwagi`,
- UNVERIFIED - brak źródła; wartość z generatora zostaje WORKING_VALUE.

Wynik: 35 pozycji, SOURCED 19, ESTIMATED 11, UNVERIFIED 5 (patrz sekcja 6 - część SOURCED to wymagania jakościowe, nie wymiary).

## 2. Najważniejsze ustalenia (Białystok, SOURCED)

- **Wiata BKM (czerwona)**: konstrukcja modułowa, moduł 2 m, długość zadaszenia 5 m (2 mod.), 7 m (3 mod., standard) lub 9 m; wysokość 2.6 m (wzór plastyczny; projekt 2006: 2.61 m w tekście i 2.778 m na rysunku - rozbieżność w dokumencie); głębokość 1.4 m na rysunku ogólnym, 2.10 m wg projektu z zadaszeniem, ściany boczne 1.07 lub 0.58 m; szyby 0.6 x 0.99 m z dolną krawędzią 0.15 m nad chodnikiem; siedzisko ławki 0.4 m, listwy 45x160 mm (siedzisko) i 30x80 mm (oparcie); gabloty rozkładowe w modułach z lewej, ławka z prawej; **kolor RAL 3020**; dach poliwęglan dymiony; stelaż znaku D-15 nad dachem lub z przodu. Zamówienie 2020: 80 wiat = 44 x 3-mod., 29 x 2-mod., 7 x 4-mod. (Zał. 8, bez współrzędnych).
- **Panele U-12a "olsztyńskie"**: rozstaw słupów 2.0 m, wierzch 1.10 m nad gruntem, pętla przęsła 0.64 m, słupki rura Ø60.3 (2-3.2 mm), przęsło Ø48.3, **żółty RAL 1012**, słup całkowity 1.50 m (0.4 m w gruncie).
- **Przęsła U-12 segmentowe**: 2.50 x 0.83 m (lub 0.63 m), żółte RAL 1012, słupki 60x40 **czerwone RAL 3020**. Wygrodzenie łańcuchowe U-12b: słupki 1.10 m, rozstaw 1.5/1.8 m. Pylon U-5a: 0.90 m, Ø0.20 m, żółty RAL 1012.
- **Słup znakowy**: Ø60.3 mm, ścianka >= 2.9 mm (zgodne z generatorem).
- **Słupy oświetleniowe ZDM**: stal ocynkowana zbieżna S315, oprawy "do 11 m", wnęka drzwiczkowa min 600x130 mm, dolne ok. 0.3 m podstawy malowane na szaro; oprawa LED IP66/IK08, 4000 K. Brak rozkładu wysokości wg klas dróg i wysięgników w znalezionych dokumentach.
- **Krawężnik przystankowy** 16 cm (generator: 13 cm dla krawężnika ulicy); **studnie w jezdni**: właz D400, korpus 150 mm, światło 600 mm.
- Białystok ma w Centrum także starsze wiaty czarne (Commons, ul. Lipowa) - nie wszystkie są czerwone BKM.

## 3. Generator vs źródło

(Generator: `props.py` - półosie w `m.box(hx,hy,hz)`; tabela podaje wymiary pełne.)

| Element | Generator (WORKING_VALUE) | Źródło (status) | Rozbieżność / zalecenie |
|---------|---------------------------|-----------------|-------------------------|
| Wiata (`bus_shelter`) | 4.0 x 1.5 m stopy słupków, dach 4.2 x 1.9 m grubość 0.1, wys. 2.5 m, słupki kwadratowe 8 cm, stal ciemna (`steel_painted` ~0.12), szyby ciemne, ławka 2.4 m na wys. 0.45 | 2.6 m wysokość, dach 5/7(/9) m, głębokość 1.4-2.1 m, zwis dachu >= 0.5 m z każdej strony, **RAL 3020 czerwony**, szyby jasne 0.6 x 0.99, siedzisko 0.4 m (SOURCED) | **Największa rozbieżność**: kolor (czerwony vs czarny), długość (4 vs 7 m standard), zwis dachu (0.1 vs >= 0.5), gabloty z lampami LED i stelaż D-15 nieobecne. Zalecenie: wiata BKM 3-modułowa 7 m jako domyślna, wariant 2-mod. (5 m) poza centrum, wariant czarny tylko Centrum/Lipowa |
| Latarnie `lamp_Nm` (GP/G/Z/L/D) | 12 / 10 / 9 / 8 / 8 m, bracket 1.5-0.5 m; słup stożkowy Ø0.17 -> 0.08 m | ZDM: oprawy "do 11 m" (SOURCED); wnęka 600x130 (SOURCED); dolne 30 cm szare | 12 m (klasa GP) jest powyżej deklarowanego maks. 11 m ulic ZDM - ESTIMATED do obniżenia dla ulic miejskich (drogi krajowe poza zakresem). Brak szarej podstawy 0.3 m i wnęki; dodać drzwiczki 0.60 x 0.13 m na wys. ok. 0.5 m (położenie wnęki UNVERIFIED) |
| `lamp_old_concrete_*` / `power_pole` | Ø0.30 -> 0.14 m, 9 m / 12 m; GROUND_PROP_H power_pole 10 (niezgodne z prototypem 12) | UNVERIFIED (brak tabeli żerdzi E) | Wewnętrzna niespójność 10 vs 12 m w standards.py; zewnętrznego źródła brak |
| Barierka pieszych (RAILING, `lin.posts` + 2 poręcze) | wys. 1.10 m, słupki 0.10x0.10 co 2.0 m, 2 poręcze (1.05 i 0.55), galwaniczne `steel_galv` | Białystok: panel "olsztyński", wys. 1.10, rozstaw 2.0 (zgodne), słupki **rura Ø60.3**, **kolor żółty RAL 1012**, pętla 0.64 m (SOURCED) | Wysokość i rozstaw zgodne. Różni się kształt (pętla zamiast 2 poręczy), przekrój słupka (okrągły) i kolor: Białystok maluje panele na żółto; galwanizowane tylko tam, gdzie nie ma dokumentu |
| Słupek (`bollard`) | Ø0.12, 0.9 m, szary + biały pasek 0.75-0.82 | Białystok: U-5a pylon 0.9 x Ø0.20 **żółty** (SOURCED); U-12c: proxy Poznań Ø76 x 1.50 (z poprzeczką) lub Ø120 x 1.20, RAL 7043/biało-czerwone (ESTIMATED) | Dodać `pylon_u5a` (żółty RAL 1012) jako osobny proto; słupki blokujące wyższe niż 0.9 m z poprzeczką - tylko po potwierdzeniu w Białymstoku |
| Ogrodzenia | FENCE_H 2.03 / panel 2.5, kolory zielony/antracyt/galw. (przemysłowe) | U-12 przy drodze: 0.83 x 2.50, żółty + czerwone słupki (SOURCED); ogrodzeń przemysłowych Białegostoku brak | Różne klasy: nie mylić ogrodzenia przy jezdni (żółte) z ogrodzeniem działki (UNVERIFIED) |
| Słup znaku | Ø0.0603 | Ø60.3, ścianka >= 2.9, kotwa przeciw obrotowi (SOURCED) | Zgodne. Wysokość słupa 3.6 m generatora bez źródła |
| Kosz `waste_bin` | tuba Ø0.40-0.44 x 0.75 m + słupek 0.9 m (ciemna stal) | Płock: 0.80 x Ø0.33 m, RAL 7035 (ESTIMATED proxy); zdjęcie Zwycięstwa: kosz betonowy walcowy | UNVERIFIED dla Białegostoku; prawdopodobnie Ø0.33-0.45 m, ale kolor/materiał (beton) różny od generatora |
| Ławka `bench` | 1.8 x 0.44 m, siedzisko 0.45 m, oparcie 0.24 m | Płock 1.82/3.02 m (proxy); Białystok brak | UNVERIFIED |
| Szafka `street_cabinet` | 0.9 x 0.4 x 1.4 m, szara | PFU: poliester/GRP, IP44 (SOURCED); wymiary brak | UNVERIFIED wymiary; materiał: żywica poliestrowa (nie blacha) |
| Krawężnik | KERB_HEIGHT 0.13 | przystanki 16 cm (SOURCED) | Dla stref przystanków użyć 0.16 m |
| Sygnalizator (`signal_pole` 4.0, `signal_mast` 6.8) | WORKING_VALUE | brak wymiarów w OPZ | UNVERIFIED |
| Brak w generatorze | - | hydranty nadziemne (ok. 0.9 m nad terenem, ESTIMATED z karty producenta), osłony drzew (UNVERIFIED), stojaki rowerowe (poza OSM hoop; Płock 0.75 m, proxy), U-5a, U-12 przęsła, U-12b łańcuchy, stelaż D-15, tablica DIP | Tylko U-5a, U-12 i wiata mają źródło SOURCED; reszta wymaga zdjęć/pomiaru |

## 4. Zalecenia dla generatora (bez zmian w kodzie - ocena właściciela)

1. Wiata: przestawić domyślny model na BKM czerwony RAL 3020, 7 m / 2.6 m; wprowadzić wariant czarny dla Centrum.
2. Barierka U-12a: osobny prototyp "olsztyński" (żółty RAL 1012, rura Ø60.3, pętla 0.64 m, rozstaw 2.0 m); galwaniczną zostawić jako fallback poza ulicami miejskimi.
3. Latarnie ulic miejskich ograniczyć do <= 11 m (do potwierdzenia na zdjęciach), dodać wnękę i szarą podstawę 0.3 m.
4. Pylon U-5a (żółty 0.9 m) jako nowy proto zamiast słupka stalowego na wyspach.
5. Krawężnik przystankowy 0.16 m.

## 5. Braki i niepewności

- RAL 3020/1012/7043: podane jako kody z dokumentów. Wartości sRGB nie pochodzą z dokumentów (konwersja publiczna) - nie wpisano ich do manifestu.
- Wysokość wiaty: 2.6 m (wzór BKM), 2.61 m (tekst projektu) i 2.778 m (rysunek) - nierozstrzygnięte (różne punkty odniesienia?).
- Zał. 7a (rysunki wiaty) objęty zastrzeżeniem praw autorskich projektantów - użyte tylko liczby, pliki nie skopiowane.
- Rozporządzenie (Dz.U. 2019 poz. 2311) - załączniki jako skany, wymiary U-12 z aktu nie zweryfikowane; ESTIMATED z Poznania i oferty sprzedawcy.
- Brak współrzędnych obiektów: Zał. 8 ma nr inwentarzowe przystanków i ulice, nie ma lat/lon; dopasowanie do kafla (OSM `highway=bus_stop`/GTFS) nie wykonano - wymaga osobnego zadania. Mapillary niedostępne bez tokenu. Z Commons tylko jedno zdjęcie z GPS (Zwycięstwa, ok. 3.5 km od środka kafla).
- Nie znaleziono dokumentu Białegostoku z wymiarami koszy, ławek, stojaków rowerowych, osłon drzew i szafek; wartości z Płocka/Poznania to proxy, nie fakty o Białymstoku.
- Strony BIP są wyszukiwane przez WebSearch; mogły istnieć nowsze załączniki (np. "Standardy" po 2018) nieobecne w wynikach.

## 6. Policzenie statusów

Wiersze: 35. SOURCED 19, ESTIMATED 11, UNVERIFIED 5. Uwaga: SOURCED obejmuje także pozycje, gdzie dokument podaje materiały/klasy, ale nie podaje wszystkich wymiarów (np. G5-012 oprawa, G5-041..043); kolumny z "UNVERIFIED" w komórkach wskazują brakujące liczby w obrębie takiego wiersza.

## 7. Samokontrola 20 %

Sprawdzono ponownie 7 z 35 pozycji (20 %) oraz wszystkie 15 adresów URL z manifestu:

- Wszystkie 15 URL odpowiedziały HTTP 200 (curl, 2026-11-13).
- G5-001 (wiata): wartości 2.6 m, 0.15 m, 1.1 m, 0.4 m, 1.07/0.6 m, RAL 3020, szyby 0.6 x 0.99 odczytane ponownie z wyrenderowanego rysunku (files/G5-001).
- G5-004: tekst "Dane powierzchniowe" (2.10 m, 7.04/5.04 m, 2.61 m) odczytany z renderu str. 3; rysunek str. 6 pokazuje 2778 - zapisano jako rozbieżność.
- G5-020: wymiary 2000/1100/1500/640, Ø60.3/Ø48.3 odczytane z rysunku w skanie (files/G5-010).
- G5-010/011: "do 11 m", "600x130", S315 odczytane ponownie z wersji tekstowej PFU.
- G5-049 (hydrant): pobrano kartę ponownie; strona podaje tylko wysokość całkowitą 2150 mm i głębokość 1250 mm - wartość 0.9 m nad terenem to wyliczenie, zmieniono status z UNVERIFIED na ESTIMATED z metodą.
- G5-061 (współrzędne zdjęcia): 53.13707, 23.12235 zgodne z metadanymi Commons; licencja CC BY-SA 3.0 zgodna z metadanymi.
- Poprawka z samokontroli: odległość zdjęcia od środka kafla poprawiona z "ok. 4 km" na "ok. 3.5 km".

## 8. Zawartość katalogu

- `manifest.csv` (UTF-8 z BOM, 35 wierszy), `sources.md`, `files/` (5 stron dokumentów urzędowych + 2 zdjęcia CC BY-SA 3.0, każdy <= 1600 px; razem ok. 1.9 MB).

> Notatka częściowa. Końcowa integracja i globalna samokontrola: README.md oraz audit_20_percent.json. Nazwy roboczych zapytań wymienione w opisie metody nie oznaczają dodatkowych plików w paczce.

# G3 — zachodni odcinek S8 / DK8: odczyty Mapillary

## Wynik i zakres

Zestaw obejmuje **45 rekordów tablic, paneli i jednego zestawu E-15d/T-34**, odczytanych z **31 zdjęć Mapillary**. Wszystkie końcowe pozycje kamer mieszczą się w roboczym buforze 15 km od granicy Białegostoku, obliczonym przez zespół z relacji OSM 2910925 w EPSG:2180. Bufor jest metodą ustalenia przybliżonego zakresu opracowania, nie granicą urzędową PRG.

- **21 rekordów z kierunku ku Warszawie:** zdjęcia d3mol3k, 19.04.2024. Podejścia główne do Choroszczy, Tykocina i Rzędzian; część znaków jezdni zbierającej przy Tykocinie widoczna z jezdni głównej.
- **19 rekordów z kierunku ku Białemustokowi:** zdjęcia kino, 26.07.2024. Podejścia główne do Rzędzian, Tykocina i Choroszczy; dalej tablica czasu oczekiwania na granicy i historyczne oznakowanie DK8 przed Łyskami.
- **5 rekordów łącznic i dróg poprzecznych:** Rzędziany — grobin, 20.09.2020, i picturehoover, 28.06.2020; Choroszcz — picturehoover, 28.06.2020.

Daty i autorów potwierdzają metadane API w `files/G3-META001.json`; powiązanie rekordów ze zdjęciami zawiera `records.json (rekordy G3-MLY-S8)`. Materiał jest historyczny. Nie potwierdza stanu oznakowania po zmianach drogowych w 2026 r.

## Najważniejsze odczyty

- Przy **Choroszczy** w obu kierunkach występuje zjazdowy panel `Choroszcz / Dzikie / Żółtki`. Na kierunku głównym widnieje odpowiednio `Warszawa` lub `Białystok`, symbol drogi ekspresowej i czerwone `S8`. Tablice E-1 mają `500 m`; na schemacie zjazdu od Białegostoku jest miniatura ograniczenia `40`, a od Warszawy `30`. Źródła: G3-MLY-S8-001, 002, 006, 034–036.
- Przy **Tykocinie** panele zjazdowe mają `Tykocin / Złotoria`. W stronę Warszawy widnieje `S8`, natomiast na E-1 i bramownicy ku Białemustokowi czerwone pole zawiera samo **`8`**, bez litery `S`. Tej różnicy nie poprawiono według aktualnej numeracji. Źródła: 003, 004, 010, 028, 030, 031.
- Tablice usług **Złotoria** zawierają paliwo, parking `P` z małym `TIR`, nocleg i gastronomię. Osobne tablice pokazują `5 km`, `2000 m`, `1000 m`, `700 m` lub `1300 m`; nie przeniesiono odległości między sąsiednimi panelami. Źródła: 005, 008, 009, 011, 013, 016, 026, 027, 029, 032.
- Przy **Rzędzianach** panele zjazdowe brzmią `Saniki / Rzędziany`. E-1 ma `500 m`, ograniczenie na miniaturze zjazdu `40` od Białegostoku i `60` od Warszawy. Źródła: 017–019, 022–024.
- E-14 ku Warszawie za Choroszczą: **Zambrów 56; Ostrów Mazowiecka 89; Warszawa 177; Kudowa - Słone 649**. Litery w dwóch owalach są prześwietlone, pozostają `UNVERIFIED`. Za Rzędzianami: **46; 79; 167; 639**, z czytelnymi owalami `PL` i `CZ`. Źródła: 007, 020.
- E-14 ku Białemustokowi za Rzędzianami: **Białystok 20; Augustów 107; Budzisko 165; Bobrowniki 71; Kuźnica 78**. Za Tykocinem: **14; 101; 159; 65; 72**. Na obu tablicach występują `S8`, `E67`, `65`, `19` oraz owale `PL/LT` i `PL/BY`. Źródła: 025, 033.
- Tablica **Radule 5 km** ma sześć pól, w tym `LPG / GAZ` i symbol **D-26 — stacja obsługi technicznej**. Symbol D-26 porównano z urzędowym rysunkiem 5.2.27.1, Dz.U.2019 poz.2311, s.232. Źródło fotograficzne: 021.
- **Rzędziany, łącznice:** E-1 przed południowym rondem wskazuje górą `Złotoria / Babino`, w lewo `Warszawa / Saniki`, w prawo `Jeżewo Stare / Radule`. Na północnym końcu drugiej łącznicy E-2a wskazuje `Saniki` w lewo, `Białystok / Babino` i `Radule` w prawo. Osobny E-3 `S8 Warszawa` ma grot w prawo. Źródła: 041–043.
- **Choroszcz, dojazd od miasta Choroszcz:** przed południowym rondem E-1 wskazuje na wprost `Warszawa / Dzikie / Żółtki`, w lewo `Białystok`. Po przejeździe pod S8, przed północnym rondem, E-1 wskazuje na wprost `Warszawa`, w lewo `Dzikie / Żółtki / Złotoria`. Źródła: 044–045.
- Na odczytywanych tablicach nie stwierdzono wydrukowanych **numerów węzłów**. Nazwy miejscowości zjazdowych nie zostały zamienione na rzekome nazwy lub numery węzłów.

Ukośniki w powyższym opisie są separatorami opisowymi. Dokładne litery, odległości, symbole i układ należy brać z rekordów oraz fotografii, nie kopiować ukośników jako znaków drukowanych na tablicach.

## Metoda

Punktem wyjścia były trzy odpowiedzi oficjalnego publicznego API Mapillary: `s8_choroszcz_recent.json`, `s8_tykocin_recent.json`, `s8_rzedziany_recent.json`. Połączono metadane bez duplikatów, wybrano sekwencje patrzące do przodu, sporządzono arkusze kontaktowe co cztery klatki i pobrano bliższe klatki przy zauważonych tablicach. Dla małych napisów pozyskano pełny wariant oryginalny zdjęcia. Obrazy boczne quickness805 nie posłużyły do odczytów końcowych.

Dodatkowo sprawdzono odpowiedzi ze wszystkich lat dla trzech wąskich bbox:

| Węzeł | Bbox: zachód, południe, wschód, północ | Liczba rekordów API | Wynik dotyczący dojazdów bocznych |
|---|---|---:|---|
| Rzędziany | 22.852, 53.148, 22.871, 53.160 | 720 | Znaleziono przejazdy łącznicami z 2020 r. |
| Tykocin | 22.941, 53.158, 22.959, 53.171 | 475 | W tym wyniku nie znaleziono pełnego przejazdu drogą poprzeczną lub łącznicą; pozostają główne jezdnie. |
| Choroszcz | 22.992, 53.150, 23.008, 53.166 | 598 | Znaleziono przejazd przez oba ronda od strony Choroszczy z 2020 r. |

Wybór kandydatów dojazdów bocznych wsparto odległością ponad 35 m od linii głównych przejazdów S8; następnie sprawdzono obrazy i sąsiednie klatki. Próg 35 m jest techniczną decyzją selekcji, nie ustaleniem terenowym. Wszystkie trzy odpowiedzi zostały zwrócone bez dalszej strony wyników; nie oznacza to gwarancji pełnej inwentaryzacji platformy ani drogi.

Typy E-1, E-2a/E-2b, E-3, E-14 i E-15 przypisano przez porównanie formy tablic z urzędowym wzornikiem historycznym. Dla ujęć 2020/2024 użyto historycznej klasyfikacji E-2b zielonych drogowskazów nad jezdnią. Nie stosowano wstecznie klasyfikacji po nowelizacji z 2026 r. Piktogramy zbiorczych tablic usług opisano dosłownie; nie przypisano niepotwierdzonego jednolitego kodu całej konstrukcji.

## Współrzędne i azymuty

`lat/lon` to **pozycja kamery z pola `geometry`**, w WGS84, zaokrąglona do sześciu miejsc. Nie oznacza pozycji słupa, bramownicy ani środka tablicy. `lat_tablicy/lon_tablicy` pozostają `UNVERIFIED`. Mniejsza liczba cyfr nie podwyższa dokładności oryginalnego GPS.

W `kierunek_deg` zapisano `computed_compass_angle` ze źródła, jeśli nie wystąpiła wyraźna niespójność z przednim widokiem i przebiegiem sekwencji. Jest to kierunek kamery szerokiego kadru, nie azymut promienia do wyciętej tablicy. Metadane surowego `compass_angle` bywają ewidentnie błędne, np. na przejeździe na zachód podają około 150°. Nie zastąpiono ich bez opisu azymutem ruchu.

Dla rekordów **003, 004, 005, 025, 026 i 045** kierunek kamery oznaczono `UNVERIFIED`: różnica `computed_compass_angle` od pomocniczego kierunku ruchu przekracza 40° i nie znajduje uzasadnienia w przednim ujęciu. Surowe wartości zachowano. Pomocniczy azymut ruchu ma osobne pole **ESTIMATED**, metodę geodezyjną WGS84 oraz klucze i geometrie sąsiednich klatek; nie jest pomiarem osi kamery.

W `tekst_wiersze` znak `|` oddziela wiersze tekstu. Przy schematach wielokierunkowych opisano również położenie gałęzi. W rekordzie 041 tabulator oddziela boczne kolumny na tej samej wysokości. Napisy `P`, `TIR` i `LPG/GAZ` w polach piktogramów opisano dodatkowo, ponieważ nie zajmują pełnej szerokości tablicy.

## Licencja i pliki końcowe

Wszystkie 45 plików w `files/` są wycinkami publicznych zdjęć Mapillary na **CC BY-SA 4.0**, z autorami i kluczami przypisanymi indywidualnie w rekordach. Zachowują tę licencję; zmiany to kadrowanie i ewentualne zmniejszenie, bez zmiany treści ani generatywnego przetwarzania. Pliki to JPG, dłuższy bok nie przekracza 1600 px. Razem zajmują około 1,93 MB. W wycinkach nie ma logo producentów ciężarówek.

Oficjalna podstawa licencji: [Mapillary — CC-BY-SA license for open data](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data) i [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), dostęp 12.11.2026. Dane OSM użyte do bufora wymagają odrębnego wskazania © OpenStreetMap contributors, ODbL; źródłem jest pakiet OSM przygotowany przez zespół.

Do końcowego ZIP należy kopiować wyłącznie wycinki `files/`, rekordy/metadane bez tymczasowych URL, niniejsze uwagi, wykaz źródeł i wynik kontroli. Robocze pliki API z podpisanymi URL, pełne pobrania, skrypty i arkusze kontaktowe służyły badaniu.

## Luki

To **udokumentowany zbiór odczytów, a nie pełny spis wszystkich fizycznych tablic**. Brakuje pełnych przejazdów wszystkich łącznic w obu kierunkach, najazdów od Żółtek/Dzikich i od strony Tykocina, a także części dróg poprzecznych przy Rzędzianach. Widoczność tablic jest ograniczona kadrowaniem, pojazdami i światłem. Nie potwierdzono kompletu znaków E-15, tablic F-14 ani wszystkich kolejnych powtórzeń po każdym włączeniu.

Nie przenoszono odczytów OSM na tablice bez fotografii. Nie wywnioskowano bieżącej dostępności przejść granicznych z historycznych nazw na znakach. Na tablicy oczekiwania na granicy sześć wartości elektronicznych jest nieodczytanych. Na E-14 za Choroszczą ku Warszawie nie odczytano liter w prześwietlonych owalach krajów.

## Samokontrola

Losowo ponownie sprawdzono **9 z 45 rekordów, czyli 20%**, bez dobierania wyników: `random.Random(20261112).sample(..., 9)`. Wylosowano 014, 033, 045, 025, 016, 039, 008, 041 i 028. Dla wszystkich:

- ponowny odczyt oficjalnego publicznego API zwrócił ten sam klucz, autora, datę i geometrię;
- ponowne pobranie obrazu zakończyło się HTTP 200, a SHA-256 miniatury był identyczny z wcześniejszym pobraniem;
- kanoniczny link aplikacji Mapillary zwrócił HTTP 200; to kontrola dostępności adresu, nie test pełnego interfejsu JavaScript;
- pozycja kamery mieściła się w przyjętym buforze, a ponowny przegląd pełnego kadru i wycinka był zgodny z opisem;
- zachowano przypisanie autora i CC BY-SA 4.0; globalna podstawa licencji została ponownie odczytana z oficjalnej strony.

Szczegóły w `files/G3-AUD004.json`. W trakcie kontroli wszystkich 45 wycinków poprawiono rozpoznanie symbolu D-26 na Radule, typ E-3 przy Rzędzianach oraz doprecyzowano E-15d/T-34. Nie zmieniono odczytanych nazw i odległości. Nie podniesiono `UNVERIFIED` do `SOURCED` na podstawie sąsiedniej tablicy.

# 02 — Brud tylnych drzwi naczepy — WIP

Cel: ≥ 20 kadrów brudnych dwuskrzydłowych drzwi naczep, w tym ≥ 6 zimowych i ≥ 6 europejskich. **Kryteria niespełnione: 0 / 0 / 0 kwalifikowanych.** W manifeście 6 pobranych i obejrzanych kadrów oraz 1 pomocniczy link-only: 3 odrzucone, 1 wzorzec czysty, 1 rdza/wiek, 1 zimowy kontekst klapy solówki oraz 1 link-only małego zabrudzenia. Dodatkowy screening obejmuje 8 nowych obejrzanych oryginałów (w tym ten 1 kadr rdzy), zapisanych poza gitem; 7 pozostałych odrzucono bez kopiowania miniatur do gita. Nie są dowodem rozkładu brudu. Liczby powyżej to zliczenie wierszy manifestu.

## Wynik przeglądu

- 02-001: SOURCED [obraz, link w manifeście] — zimowy zestaw widoczny z boku, bez widoku tylnych drzwi.
- 02-002: SOURCED [obraz] — załadunek skrzyni od góry; brak widoku tylnych drzwi.
- 02-003: SOURCED [obraz] — solówka ze zbiornikiem; nie jest naczepą ze skrzynią.
- 02-004: SOURCED [obraz] — czyste drzwi, poza statystyką osadu. To znany projektowi kadr P18-107, ponownie obejrzany; nie jest nowym materiałem M61-FIX. Osobno obejrzano wycinek lewej lampy z oryginału; E-numer nieczytelny. Nie kwalifikuje się także jako nowy dowód homologacji.

## Luki

UNVERIFIED: wysokość i intensywność filmu brudnego, położenie i liczba smug, udziały stref, rozkład zimowej soli. Ze zdjęcia śniegu nie wnioskujemy o chemicznym składzie osadu. Nie wyliczono statystyk brudu z odrzuconych kadrów. Poszukiwania trwają.

Openverse API zwróciło HTTP 403 dla pojedynczego zapytania `dirty truck rear`, bez prób obejścia. Commons API zadziałało ponownie; pobrania oryginałów rozdzielono 12 sekundami. Oryginały i metadane poza gitem w `Data/raw/refs/codex-s21/02-brud`. Miniatury ≤ 800 px; licencje i autorzy per kadr w manifeście. Kadry tylko do referencji, nie tekstury.

## Screening dodatkowy 15.11

`screening-2026-11-15.csv`: 8 nowych oryginałów obejrzanych osobno (kandydaci raw5/6/7/8/11/12/13/14). Kadr kontenera 02-005 osobno także na wycinku dolnej części drzwi. Rdzawe plamki rozpoczynają się przy dolnej krawędzi paneli i obrzeżu ramy, a długie cienkie rdzawe ślady przy szczelinie i krawędziach. Brud drogowy/rozbryzg UNVERIFIED, więc nie zwiększa mianownika. Łączna wysokość drzwi na oryginale około 1400 px (ESTIMATED z pełnego kadru), lecz sama duża rozdzielczość nie zmienia kwalifikacji.

Kandydaci9/10 nie pobrani (PD poza filtrem bieżącej serii); kandydat15 Line of trucks zwrócił HTTP429: nie pobrano, nie obejrzano, bez retry. Przerwano pobieranie z Commons. **Nowe kwalifikowane brudne drzwi:0; europejskie0; zimowe0.** Kolejny obieg powinien przejść na inne źródła lub szukać konkretnych tylnych widoków floty z licencją CC. Odrzucenia nie są podstawą statystyki rozkładu brudu.

## Flickr CC — kolejny obieg

Publiczny search Flickr HTTP200 z filtrem licencji 4 (BY) / 5 (BY-SA) / 9 (CC0): cztery zapytania, po 25 metadanych wyników. Czterech wybranych kandydatów nie udało się pobrać (HTTP403). Po zgłoszonym 429 dla static hostu przerwano dalsze próby. Jedną publiczną fotostronę sprawdzono w Chrome przez CUA: metadane i CC BY 2.0 były widoczne, ale właściwy obraz pozostał czarny na zrzucie także po zamknięciu cookies. **Żaden z tych kandydatów nie jest obejrzanym kadrem ani wpisem manifestu zdjęć; wzrost liczników 0.** Log metadanych i testu w `flickr-screening-2026-11-15.json`. Nie zapisano HTML zawierającego zbędne dane runtime ani nie użyto logowania/CAPTCHA.

## Materiały zimowego utrzymania — dane dokumentacyjne

02-D01 (GDDKiA, 02.11.2026): SOURCED [pełny HTML, sekcja planu sezonu 2026/2027] — w skali kraju wymieniono sól drogową, chlorek wapnia i materiały uszorstniające. To kontekst krajowy, bez potwierdzenia składu mieszaniny stosowanej na DK65.

02-D02 (Oddział Białystok, 20.01.2026): SOURCED [pełny tekst jednostronicowej odpowiedzi przetargowej, pkt 1] — uziarnienie piasku 1–2 mm dla dostawy ZUD sezonu 2026. Lokalna kopia i wizualny zrzut PDF nie powstały (timeout); wartość pochodzi z pełnego odczytu tekstowego, nie z obrazu.

**Dawka g/m² na DK65, procent NaCl w dostawie lokalnej, aktualny standard ZUD dawnego odcinka po otwarciu S19 oraz skład i rozkład osadu na drzwiach pozostają UNVERIFIED.** Wielkość ziarna na jezdni nie oznacza tej samej wielkości cząstek przyklejonych do naczepy. Nie wyprowadzono odsetka soli, wysokości filmu, koloru ani smużenia z danych o utrzymaniu drogi. Dwa wiersze dokumentacyjne nie zwiększają liczby kadrów.

## Tabela dawek — odczyt archiwalny oczekuje obrazu

`data/zud2006-table2-PENDING-VISUAL.csv` to robocza transkrypcja tekstowa tablicy 2 z **2006**, s. 36–37. Nie jest wersją 2017 ani aktualnym przepisem. Kod A oznacza prewencję gołoledzi/lodowicy/szronu; B — zapobieganie przywieraniu śniegu; C — likwidację śliskości/cienkich pozostałości po pługu. Wszystkie dawki dotyczą jezdni, g/m².

**NIEGOTOWE do użycia jako pełna tabela**: tekst pominął wiersz A dla −3…−6°C; ten wiersz ma UNVERIFIED. Nie uzupełniono go z innej wersji. PDF 2017, lokalne pobranie 2006 i obraz stron były niedostępne (timeout/blank). Szczegóły w `data/zud-table-access-check.json`. Roboczego pliku nie traktować jako zamknięcia luki dawek ani jako wejścia generatora. Nie ma lokalnego snapshotu PDF/SHA.

## Zimowe kadry stock — obejrzany podgląd, wyłącznie link-only

02-006: SOURCED [fotostrona Getty 2208838382 i obejrzany obraz] — Bośnia i Hercegowina, autor MASTER, kolekcja Moment, widoczna etykieta Non-AI. Data zdjęcia UNVERIFIED; 07.06.2025 to upload. Podgląd pokazuje słabe zabrudzenie jasnych dwuskrzydłowych drzwi: rozproszony szarobeżowy film i cienkie pionowe ślady. Na belce poniżej drzwi zabrudzenie jest mocniejsze. Brak wiarygodnej identyfikacji soli, błota pośniegowego lub składu chemicznego; zimowy kontekst wspierają tytuł oraz białe drzewa. Fizyczna wysokość stref i kierunek geograficzny UNVERIFIED.

Obejrzano osobno także trzy kadry tej serii (log `getty-screening-2026-11-15.json`): dwa powtarzają czerwony zestaw, trzeci pokazuje inny pojazd zbyt daleko do rozkładu osadu. Nie zwiększają liczników. **Kryterium brudnych drzwi >=1000 px na zweryfikowanym obrazie pozostaje niespełnione**: podgląd 02-006 ma drzwi około 320 px wysokości (ESTIMATED); deklarowane 8636 × 5760 dotyczy niedostępnego oryginału, a nie obejrzanej rozdzielczości drzwi. Delta ścisłych kryteriów: 0 / 0 / 0. Link-only obejrzane pomocnicze: 1. Materiałów komercyjnych ani zrzutów obrazu nie pobrano; tylko URL i własny opis. Royalty-free nie oznacza CC ani otrzymanej licencji.


### Kontrola publicznego zoomu Getty

02-006 obejrzano ponownie w zwykłej galerii Zoom: wyrenderowany obraz ma naturalnie 2048 × 1366 px (SOURCED [read-only DOM obrazu galerii]), wyświetlony 1303 × 869 px. Drzwi około 370 px na ekranie i około 580 px w naturalnym podglądzie (ESTIMATED z proporcji, nie pomiar oryginału); nadal poniżej progu 1000 px. Nie powiększano sztucznie miniatury. Dodatkowy kadr 181541451 obejrzany osobno w Zoom odrzucono: jasny prosty tył bez wiarygodnego brudu i bez czytelnej konstrukcji dwuskrzydłowych drzwi.

Łącznie ta seria screeningu obejmuje 5 różnych kadrów, około 3 pojazdów/scen (ESTIMATED z obrazów); trzykrotny czerwony zestaw to jeden pojazd. Ponowny Zoom 02-006 nie jest nowym kadrem. Przyrost kwalifikowanych M61 pozostaje 0. Publiczny PDF gov.pl ze zdjęciem naczepy w zimowym otoczeniu był niedostępny wizualnie (timeout); Shutterstock pokazał Device Check. Nie użyto tych nieobejrzanych kandydatów ani nie obchodzono blokad.


## Lokalny przegląd manifestów i nowy kontekst zimowy

Przejrzano 61 lokalnych manifestów CSV; filtr terminów zimowych i ciężarowych dał 19 wierszy kandydatów (zapis `data/local-winter-manifest-search-2026-11-15.json`). Nie znaleziono lokalnego archiwum fotografii P18 w sprawdzonym głównym katalogu research ani Data/raw; nie zmieniano cudzych danych. Najmocniejszy znany kandydat P18-118 został pobrany ponownie z Commons i obejrzany w oryginale: zamknięte drzwi z prętami są częściowo zasłonięte panelami aerodynamicznymi, dolny pas ma rzadkie szare cętki. To kadr już wykorzystany, więc wzrost liczników nowych zdjęć 0.

Nowy 02-007 (Heavy filthy): SOURCED [opis autora Commons] — Glasgow, 29.01.2010, śnieżyca; CC BY-SA 4.0, Chris McKenna (Thryduulf). Osobno obejrzany oryginał i wycinek pokazują gęsty szarobrązowy film, napis odsłaniający jaśniejszą powierzchnię i ciemne pionowe smugi poniżej. ESTIMATED: ślady spływu głównie w dolnej połowie, sam film niemal na całej widocznej klapie. Fizyczne wysokości i skład białego materiału przy zamknięciu UNVERIFIED. To **solówka z pojedynczą klapą/platformą**, dlatego stanowi tylko jakościowy kontekst zimowego brudu i nie spełnia kryterium dwuskrzydłowych drzwi naczepy. Oryginał 3648 × 2736 poza gitem, miniatury ≤800 px.

Nowy kandydat Old Trailer Abandoned in the Snow (CC BY 2.0, Cindy Shebley) po obejrzeniu miniatury okazał się przyczepą kempingową widzianą z boku — odrzucony, bez miniatury w repo. Wyniki i SHA surowych plików w `data/local-winter-recheck-results-2026-11-15.json`. **Przyrost ścisłych progów M61: 0; nowy pomocniczy kadr zimowy/europejski: 1, jeden pojazd.**

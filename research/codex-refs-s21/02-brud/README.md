# 02 — Brud tylnych drzwi naczepy — WIP

Cel: ≥ 20 kadrów brudnych dwuskrzydłowych drzwi naczep, w tym ≥ 6 zimowych i ≥ 6 europejskich. **Kryteria niespełnione: 0 / 0 / 0 kwalifikowanych.** W manifeście 5 pobranych i obejrzanych kadrów, 0 link-only: 3 odrzucone, 1 wzorzec czysty i 1 rdza/wiek. Dodatkowy screening obejmuje 8 nowych obejrzanych oryginałów (w tym ten 1 kadr rdzy), zapisanych poza gitem; 7 pozostałych odrzucono bez kopiowania miniatur do gita. Nie są dowodem rozkładu brudu. Liczby powyżej to zliczenie wierszy manifestu.

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

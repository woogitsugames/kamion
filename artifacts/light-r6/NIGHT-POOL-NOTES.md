Nocne lampy — ponowny ogląd historycznych danych R5

Dane R5 mają 109 kamer, każda z czterema wybranymi pulami. W 15 kadrach żaden poprawny rzut środka pod lampą nie leży wewnątrz obrazu, a w 94 leży co najmniej jeden. Office_1 ma zero, office_2 dwa, docks zero. Nie oznacza to braku oświetlenia: skończona plama może wchodzić w kadr mimo środka poza nim, a widoczny środek nie wyklucza zasłonięcia ani innego materiału.

Rodzic ponownie obejrzał pełne Low-night office_1 i office_2. Office_1 ma ciemną fasadę i nawierzchnię, z jaśniejszymi skrajami. Office_2 ma wyraźne jasne plamy na chodniku i dolnej fasadzie, więc nie można uznać globalnej siły źródeł za zerową. Głowica pobliskiego prawego słupa wygląda na ciemną sylwetkę. Trzeba odróżnić brak świecącej soczewki od braku halo; samo bloom nie naprawia źle przypiętego lub niewidocznego emitera. To obserwacja, nie diagnoza bindingu lub geometrii.

Zapisana ekspozycja obu kamer wynosi 0.17708923, kompensacja presetu -3 EV, kolor puli około 140.923/131.059/115.557 w jednostkach eksponowanych. Nominalne 31–65 lx to model bez ograniczenia kąta, okna zasięgu i zasłonięć. Nie należy używać go jako zmierzonego oświetlenia pikseli.

Materiał pochodzi z rundy 5; nie jest świeżą bazą rundy 6. Nie zmieniono globalnego EV, lamp, cudzych shaderów lub geometrii. Niezależny przegląd w toku.
Uzupełnienie po porównaniu czterech torów R5

Rodzic obejrzał arkusz night-lens-history/comparison.png; krytyk potwierdził hasze i etykiety. Głowica jest ciemna w Low produkcyjnym, Low native, High legacy i High HDR. Zatem sam eksperyment native ani wyłącznie cel ARGB32 nie wyjaśniają braku czytelnej soczewki. Oba High mają silnie biały trzon i detale budynku, oba Low ciemne. To objaw różnicy tierów, nie ustalona przyczyna.

Faktyczne probe R5 office2: Low ma4 pule i0 świateł punktowych; High ma8 pul i4 światła punktowe. Ekspozycja0.17708923, słońce-8°, skyLux0.38861293 oraz kolor puliR140.923 są zgodne między czterema wariantami. Nie wolno traktować równej krzywej koloru jako wyrównania samego oświetlenia. WorldSurface i sprawdzony WorldPBR dodają pule, ale nie znaleziono w nich pętli GetAdditionalLight; nie przypisujemy więc białego trzonu punktowym światłom bez identyfikacji actual shadera.

night-pool-ablation.json przygotowuje10 przyszłych obrazów po świeżej bazie: office1/2, Low0/4, High0/4/8. Używa istniejącego rq_lamppools, nie dodaje opcji ani pola QualityProfile. Nie podnosi liczby pul Low ponad produkcyjne4. Po każdym jobie trzeba potwierdzić rzeczywistą liczbę w lamp-probes, bo same argumenty nie są dowodem. rq_a8=0 nie jest izolacją streetLights, bo wyłącza też inne efekty. Macierz nie została uruchomiona i nie zastępuje pierwszeństwa triage horyzontu P1.

Kontrola zakresu zmierzchu: historyczne reflection-fix R2 zawiera po5 prób na Low/High dla Dusk i Night. Dusk modelExposure około0.07072972, Night około0.17708923. Przy podstawieniu nominalnych200000cd/m² i lampsOn1 iloczyn przed dalszym tone wynosi odpowiednio około14145.94 i35417.85, poniżej65504. Wszystkie20 wierszy i hasze źródeł zapisano w historical-emission-range.json. To kontrola nominalnego zakresu, nie odczyt actual global exposure/material binding i nie audyt wszystkich operacji half. Nie znaleziono tu podstaw do poprawki emisji lub ogólnego przypisywania braku soczewki overflow.

# 0115 — Zewnętrze TRAKT-a i naczepy

## Runda 1 — lakier, szkło i światła dzienne

Status: runda zakończona z ograniczonymi poprawkami technicznymi; cel wyglądu lakieru i szyby pozostaje otwarty. Start 11 listopada 2026, 21:31 CET. Gałąź `gpt-truck-r1`.

Punktem wyjścia jest main `5f2aa277` oraz recenzja `REVIEW-2026-11-11-s10-gpt-0087-0090.md`. Dawne pomiary 0087 nie stanowią pomiaru tej rundy. Obowiązują D30, D34, D35 i D44, a także budżet Low bez dodatkowych przebiegów i wzrostu liczby wywołań rysowania. Czas GPU na telefonie pozostanie UNVERIFIED, ponieważ telefony należą do zakresu lidera.

Najpierw zapisujemy aktualny baseline Low i High, przy zachmurzeniu i słońcu. Ocenę lamp opieramy na tej samej masce i rozkładzie jasności, ocenę szyby na jej górnej i dolnej części oraz widoczności wnętrza, a lakieru na drzwiach i deflektorze. Zdjęcia Commons są wyłącznie odniesieniem do zachowania materiału, nie projektem do skopiowania. Przesłane obrazy AI nie są zdjęciami ani źródłem tekstur.

Pierwsza uzasadniona poprawka techniczna dotyczy mgły w `FragFast`: szkło używa mieszania premultiplied, więc jego wkład rozproszonego światła atmosfery powinien być pomnożony przez alfę. W szybkim wariancie wierzchołek już oblicza transmitancję atmosfery, dlatego fragment nie może ponownie liczyć wykładnika. Osobno należy zachować zgodność filtrowania capture z pełną ścieżką.

DRL zachowuje kodowanie 1000 nitów na jednostkę RGBAHalf. Luminancja jest WORKING_VALUE i wymaga porównania przed i po. Nie zmieniamy ekspozycji całej sceny ani presetów oświetlenia należących do innej sesji. Lakier wymaga aktualnego dowodu rozdzielającego refleks od jasności białego pigmentu; nie przyjmujemy z góry, że capture nie zawiera podłoża.

Nie ogłaszamy PASS wyglądu. Wyniki i ograniczenia zapisano poniżej oraz w raporcie rundy.

### Decyzje i dotychczasowe dowody r1

Zachowujemy poprawkę mgły w `FragFast`: wkład atmosfery jest pomnożony przez alfę tafli, a transmitancja obliczona w wierzchołku pozostaje bez zmian. Wariant pełny High nie został zmieniony. Niezależny recenzent nie stwierdził regresji w parach widoku kierowcy i zewnętrza. Zmiana jest mała wizualnie: Low `truck-34` ma medianę jasności próbki szyby 19,86 → 19,05% i odchylenie 5,885 → 6,065 punktu. Nie jest to rozwiązanie mleczności ani spełnienie D34.

Stała redukcja surowej luminancji DRL nie dała właściwego kompromisu pogodowego. Wariant 2000 usunął przycięcie, ale recenzent wskazał wygląd jasnego plastiku. Wariant 4000 pozostawił 1209 przyciętych pikseli High-overcast wobec 1214 w bazie. Wariant 3000 usunął clipping, lecz mocno osłabił pasek w słońcu. Te warianty są dowodami porównawczymi, a nie wybranymi ustawieniami kontrolera.

Kandydat końcowy zachowuje surowe ustawienia sterownika 160000/56000 oraz skalę kodowania 1000 nitów na jednostkę. Wyłącznie grupa DRL o identyfikatorze 1 dostaje w `TruckExterior.shader` lokalną kompresję luminancji `E / (1 + Y / k)`. Wspólny mnożnik RGB zachowuje barwę; maska emitera jest stosowana po korekcie. Obliczenie odbywa się w `float` przed konwersją do `half`. Parametr materiału `_DrlHighlightShoulder` ma roboczą wartość 0,8 w odsłoniętych jednostkach sceny, a 0 wyłącza korektę. To jawna kalibracja obrazu dla istniejącej krzywej D23, nie pomiar fizycznej fotometrii lampy.

Nie zmieniamy F0, amplitudy wypukłości drzwi, geometrii, pozostałych grup lamp ani ustawień światła i postprocessingu. Korekta nie dodaje tekstur, próbek, przebiegów ani wariantów shaderowych. Dodatkowa arytmetyka dotyczy fragmentów DRL; jej czas na A16 pozostaje UNVERIFIED. Liczniki wszystkich kamer oraz instancji będą porównane osobno po kanonicznej regeneracji.

W stałym natywnym ROI lewej lampy liczba pikseli z każdym kanałem RGB ≥254 wynosi 1214 → 0 na High-overcast; w pozostałych trzech warunkach kandydat również ma 0. ROI zawiera obudowę i otoczenie lampy. Recenzent rozpoznaje włączone DRL w obu pogodach, nie widzi regresji reflektorów i kierunkowskazu; zaznacza, że gradient pozostaje subtelny. To akceptacja kandydata do walidacji, nie PASS całego truck.

Testy rzeczywistego dekodowania/stanu oraz nowego ograniczenia HDR i bypassu przeszły 11/11, bez pominięć. Nowe próby GPU obejmują zerową i dużą ekspozycję. Wyniki pełnego EditMode i końcowego GIS są poniżej.

Kontrole lakieru zachowały szorstkość i tłumienie podłoża przy wyłączaniu samego wkładu powłoki. High-overcast: wkład powłoki w średnią jasność próbki drzwi wynosi 1,62 punktu na bieli i 4,66 na ciemnym pigmencie. To wyniki po przetwarzaniu obrazu, nie surowe HDR. Potwierdzają obecność odbicia, lecz nie zamykają celu połysku białej kabiny. W tej rundzie nie wzmacniamy sztucznie F0.

Pozostają otwarte: kredowy lakier i dach w słońcu, mleczność szyby oraz D44. Stara baza ma stosunek odchyleń szyby do widoku bez przedniej tafli 0,475 Low i 0,526 High, przy celu 0,7. Końcową próbę bez tafli wykonano na identycznej wersji kandydata. Brak pomiarów telefonów zgodnie z zakresem właściciela.

Po pilnej aktualizacji właściciela wszystkie ciężkie zadania Pythona korzystają z puli `heavy` (max 3), a pełny GIS jest uruchamiany wyłącznie na końcu rundy. Wcześniejszy bazowy GIS, wykonany przed tą aktualizacją i przed zmianami produkcyjnymi, dał 488 passed, 5 failed, 1 xfailed. Pięć błędów dotyczy far-field, wiaduktu, przeterminowanego fidelity, brakującego prototypu i deterministyczności świata; pliki tych dziedzin nie są poprawiane w sesji truck.

### Końcowa kontrola renderowania i EditMode

Po kanonicznym zbudowaniu obu pojazdów i instalacji w scenach zapisano 28 kadrów końcowych, dodatkowo 6 Medium, 6 o zmierzchu i 6 kontrolnych bez przedniej szyby. Pełny EditMode zakończył się kodem 0: 266 passed, zero failed i skipped. Wszystkie 96 wierszy kamer (48 × Low/High, overcast) ma identyczne liczniki rendererów, cieni i instancji oraz raportowane tysiące trójkątów. Dowód: `artifacts/truck-r1/all-cameras-counters.csv`. Trójkąty są zaokrąglone, wywołania rendererów są estymatami przed SRP, a nie pomiarem GPU telefonu.

Końcowy D44 według tej samej próbki i skalowania do 1024 px: 0,490 Low i 0,526 High, nadal poniżej 0,7. Rozrzut profilu drzwi pozostaje identyczny: overcast 3,362 Low i 2,437 High; clear 5,261 Low i 3,661 High. Przy celu 4–10 większość warunków nadal nie przechodzi. Końcowe ROI lewej lampy potwierdza 1214 → 0 przyciętych pikseli High-overcast i 0 → 0 w pozostałych trzech warunkach.

Decyzja o podłodze szorstkości capture w `FragFast`: nie dodajemy nominalnej wartości 0,09 z pełnej ścieżki. Obecne Low i Medium mają capture 64 px; wzór `mip = clamp(log2(max(pr² × size / 2, 1)), ...)` daje mip 0 zarówno przed, jak i po takim ograniczeniu dla pr < 0,09 (największy footprint 0,2592). Dla większego pr ograniczenie nic nie zmienia. Ta równoważność dotyczy aktualnych profili, a nie dowolnej przyszłej rozdzielczości. Medium-overcast i Medium-clear zostały wyrenderowane po zmianie mgły.

Niezależna kontrola po rebuildzie nie wykazała nowej regresji sylwetki, ustawienia pojazdu ani widoku kierowcy w ośmiu arkuszach. Lakier, dach i szyba nadal nie spełniają celu materiałowego. Zmierzch jest kontrolą jakościową bez bazy: Low i High pokazują płaskie jasne moduły reflektorów; nie przypisujemy ich tej rundzie. Pełna ocena jest w `artifacts/truck-r1/FINAL-REVIEW.md`.

Końcowy GIS pod slotem heavy: 488 passed, 5 failed, 1 xfailed w 688,34 s, dokładnie te same pięć testów co w bazie. Porównanie nazw i wyników jest w `gis-comparison.json`. Sześć zmienionych przez test plików generated zachowano w patchu i przywrócono do wersji gałęzi. Nie poprawiano błędów innych dziedzin.

Kompilacja Android z zawartością Low i High zakończyła się powodzeniem: 0 błędów, 12 ostrzeżeń, 289 s. APK ma 375305009 bajtów; log, SHA i metadane w `artifacts/truck-r1/build/`. Wśród ostrzeżeń są potencjalnie niezainicjalizowane wartości w niezmienionym `KamionVehicleEnv.hlsl`; brak błędów shaderów. Nie instalowano ani nie uruchamiano aplikacji na telefonie. Wygenerowane ustawienia przywrócono; tymczasowe Resources usunął sam pipeline Unity. Kod źródłowy builda jest wskazany przez SHA w nazwie APK, późniejsze commity zapisywały jedynie dowody i dokumentację.

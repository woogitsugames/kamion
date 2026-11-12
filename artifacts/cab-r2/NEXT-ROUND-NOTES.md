# Rozpoznanie do rundy nocnej (przed jej baseline)

Istniejący kod CabDisplaySource wybiera Night po wysokości słońca (domyślnie 6 stopni); ClusterLayout i DinLayout mnożą kolory przez 0,62, NavLayout ma ciemną paletę. CabDisplay.shader wylicza clamp(500 * exposure, 0,45, 0,9). Hipoteza do pomiaru: wzrost gain przy nocnej ekspozycji może znosić przyciemnienie kolorów. Nie jest to jeszcze wynik obrazu ani diagnoza błędu. Dusk w bieżącym drzewie ma słońce -5 stopni.

Po merge main w r3: świeży baseline Low/High clear i dusk, widok kierowcy oraz panelu. Zmierzyć obszary znaków i tła, sprawdzić czytelność kontrolki i brak białej plamy ekranu; rozdzielić emisję i odbicie. Zmiany tylko w shaderze/panelach kabiny, bez światła świata, szyb i nowych przebiegów Low. Zachować alarmy i dotychczasową czytelność dzienną. Wyznaczone wartości będą WORKING_VALUE do czasu dowodów.

Recenzja zbiorcza s11 dopisuje okluzję prawego szerokokątnego przez kanał drzwi: pomiar z DriverEyePoint, odróżnić geometrię szkła od obrazu RT. Kremowy przód kabiny w Front należy do zewnętrza, nie zmieniać shaderów ani modelu sesji 6.

Instrukcja producenta Scania potwierdza oddzielne tryby jasności dzień/noc/auto, ale nie jest zdjęciem referencyjnym ani celem liczbowym dla fikcyjnej kabiny:
https://www.scania.com/content/dam/scanianoe/market/master/pdf/SCANIA_AUS4_5inch.pdf
Zdjęcie nocne ciężarówki wymaga jeszcze znalezienia i obejrzenia. Nie używać obrazów z gier jako rzeczywistej referencji. Nie pobierano ani nie kopiowano grafik z instrukcji.
Wstępny render Low dusk na końcu r2: night-preflight/Low-dusk, trzy kamery, Unity exit 0 i slot zwolniony. Obejrzano cab-dash: tryb ciemnej mapy działa, brak dominującej białej płyty; główne cyfry czytelne, drobne napisy miękkie przy rozdzielczości Low. Log potwierdza night=True, clock=20:18. Hipoteza znoszenia dimmingu pozostaje niepotwierdzona — nie zmieniać parametrów tylko na podstawie wzoru. Przed zmianą r3 wymagany baseline po merge main, High i porównanie do zdjęcia.

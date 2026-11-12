# Niezależna ocena bazowego zewnętrza

Recenzent: agent `truck_visual_review`, 11 listopada 2026. Ocena wyłącznie na podstawie odczytu kadrów, zdjęć i kodu; bez uruchamiania Unity, testów ani generatorów. Nie jest to zgoda na scalenie ani PASS całego wyglądu.

1. Na `truck-34r` i `truck-side` przy zachmurzeniu duże białe panele nadal wyglądają kredowo. Odbicie otoczenia na drzwiach jest słabe. Pewność wyglądu jest wysoka, przyczyny średnia; srebrna i czerwona kabina ze zdjęć uwydatniają odbicia bardziej niż biel.
2. Na `truck-front` Low i High szeroka szara zasłona tłumi wnętrze, a różnica między górą i dołem szyby jest słaba. Fotele są widoczne, lecz mało kontrastowe. Inne kąty rzeczywistych tafli nie pozwalają bezpośrednio porównać jasności.
3. Plandeka na `truck-rear34` i `truck-side` ma regularne pionowe pasy i mało lokalnej zmienności połysku lub zużycia. Pewność średnia: czerwona plandeka na zdjęciu i inne światło wzmacniają te cechy. To materiał na rundę 2.
4. Zalecany pierwszy eksperyment to pomnożenie wkładu mgły przez alfę w `FragFast`, zgodnie z `Blend One OneMinusSrcAlpha` i pełną ścieżką. Niespójność kodu jest pewna; skala poprawy wizualnej nie jest znana i może być niewielka z bliska.
5. Eksperyment ocenić na Low-overcast `truck-front` i `cab-driver`, z High-overcast jako kontrolą. D44 porównać z identycznym widokiem bez przedniej tafli. Zachować D29, D30 i D34. Zakres zmiany nie dodaje geometrii ani przebiegów; czas GPU na telefonie pozostaje UNVERIFIED.

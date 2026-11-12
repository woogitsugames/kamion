# Niezależna recenzja kodu B przed renderem

Krytyk wycofał pierwotną propozycję samej zmiany wysokości po odkryciu ośmiu samoprzecinających ringów. Zalecił lokalne offsety Shapely w plantings.py, wspólną orientację i parametr obwodu, odmowę pustych lub rozłącznych offsetów, bez wyboru największego fragmentu i bez naprawiania helpera roads.

Po przeczytaniu B krytyk uznał prawidłowe osiem obrysów i krawędzie poniżej 0,98 m za dowód usunięcia konkretnej przyczyny. Brak punktów wewnętrznych w wąskim capie jest dopuszczalny, jeśli poprawna triangulacja pokrywa go krótkimi trójkątami. Wynik 11 560 zamiast 18 402 tris nie stanowi jednak pomiaru kamer ani GPU i nie daje wizualnego PASS.

Pozostawione warunki do sprawdzenia:

- Poprawny ring sam w sobie nie dowodzi, że rdzeń mieści się w shell. Niezależna redukcja bulge i cięciwy rdzenia próbkowanego co drugi punkt mogą naruszać przynależność.
- Równy parametr obwodu i wspólny anchor nie dowodzą braku globalnych przecięć pasów. Kontrola lokalnych quadów nie wykrywa wszystkich nakładań.
- Polygon z otworami nie może po cichu utracić wnętrz.
- UV i wysokości wykorzystują parametr bazowego obrysu, więc skala liści oraz skośne pasy wymagają oceny na renderze.
- Błąd capa nie może zniknąć w szerokim except, pozostawiając otwarty krzew.

W odpowiedzi dodano test globalnej sumy/union powierzchni quadów i zgodności z pierścieniem między przekrojami, test przynależności sześciu ringów rdzenia oraz rzeczywisty prześwit względem trójkątów góry na czterech obrysach i dwóch nachyleniach gruntu. Kod odmawia offsetu z otworami, a dla berberysu propaguje błąd capa. Testy czekają na heavy w sekwencji 73347; wyniki nie są jeszcze znane. Pozostałe rodziny zachowują wcześniejszy kod. Przed akceptacją potrzebne są także świeże obrazy B i ponowna niezależna ocena.

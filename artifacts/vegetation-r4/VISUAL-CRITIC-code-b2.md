# Niezależna recenzja kodu B2

Krytyk uznał, że triangulacja rzeczywistych pasów usuwa zależność od zgodności indeksów ringów, czyli źródło bow-tie odrzuconego B. Pochwalił zachowane narożniki, odmowę pustych/rozłącznych obszarów i otworów, CDT obszaru z otworem, odzyskane krawędzie i przypisane wysokości. Nie dał wizualnego PASS bez renderów.

Wskazane ryzyka i odpowiedzi:

- Prześwit sprawdzany tylko w wierzchołkach rdzenia nie pokrywa dwóch różnych triangulacji. Test rozszerzono o ich wspólny podział: przecięcia każdego trójkąta rdzenia z sąsiednimi shell, całą pokrytą powierzchnię i różnicę wysokości we wszystkich wierzchołkach przecięć, także na krzyżujących się krawędziach.
- Przyciąganie pędów do wierzchołków co 0,45 m mogło grupować kilka korzeni mimo kroku około 0,13 m. Nowa ścieżka interpoluje XY, Z i normalną na rzeczywistej stacji krawędzi; liczba kart pozostaje taka sama. Dodano test kilku różnych korzeni na jednym odcinku.
- Tolerancja wstawiania punktów cap może objąć oba sąsiednie trójkąty. Oprócz dokładnego trafienia w krawędź test ma dwa przypadki minimalnego przesunięcia obok niej i kontrolę luk, nakładania oraz T-junction.
- Szew UV i różne długości obwodów nadal wymagają oglądania, mimo testu ograniczającego zawinięcie. Brak potwierdzenia skali liści i skośnych smug przed świeżymi obrazami.

20 347 tris nasadzeń to około +10,6% względem 18 402; nie utożsamiać tego z procentem całego kadru. Wymagane są rzeczywiste pomiary każdej kamery Low, +0 draws i ≤+2% tris, oraz osobna informacja o braku pomiaru GPU. Testy 33 przypadków pozostają w kolejce heavy w sekwencji 87809. Żaden z opisanych warunków nie jest jeszcze zielonym wynikiem GIS ani akceptacją wizualną.

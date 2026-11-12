# Notatka do dalszej kalibracji kamer

Kadr 182011943700132 pozostaje C. Obejrzano ponownie zachowany arkusz diagnostic-baseline r1: zdjęcie pokazuje skrzyżowanie na poziomie terenu, a nie dowód jazdy na pomoście. Sama różnica wysokości względem pobliskiej kamery 494288258686575 (136,7608 m wobec 141,888 m) nie uzasadnia podniesienia kamery. Nie wolno używać tej liczby jako potwierdzonego błędu wysokości.

Następna próba powinna rozdzielać położenie w planie, kurs oraz możliwą różnicę epok danych. Pozycja 182011943700132 leży blisko środka ronda w obecnych danych; wcześniejsza próba oryginalnego GPS trafiała pod pomost. Potrzebne są 2–3 jednoznaczne kotwice geometryczne, najlepiej elementy skrzyżowania, a nie samo dopasowanie horyzontu. Nie zmieniono pozy, klasy, wysokości ani recenzji D51.

D51 wyróżnia ponadto B: 177786140912399 (odległość do C-9), 3281350541967811 (jezdnia), 275528677534382 (stacja kamery samochodowej) i 494288258686575 (kurs). Te cztery zastrzeżenia pozostają widoczne w raporcie obok negatywnych ocen świata. Nie usuwamy ich z historycznej kohorty recenzji.

## Kamera 326 — rozdzielenie orientacji i perspektywy
Obejrzano natywny obraz porównawczy 326454015490067 (1280×960). Metadane źródłowe: perspective, parametry [0,422982514161; -0,0508463849748; 0,0031409695342], rozmiar aparatu 4000×3000. Piony i krawędzie są silnie ukośne, a zdjęcie obejmuje dużo nieba. Sam wygląd ukośnych linii nie rozstrzyga roll, ponieważ duży pitch także powoduje zbieżność pionów. Potrzebne są pewne, wyprostowane optycznie linie i ich wspólny punkt zbiegu.

Odczytano bez edycji game/Assets/_Project/Gameplay/Gate3Cameras.cs: Entry ma pos/look_at/fov, a ustawienie kamery używa Quaternion.LookRotation(look - pos, Vector3.up), bez wejściowego pola roll. To ograniczenie reprezentacji należy uwzględnić przy dalszej kalibracji. Nie zmieniono C# ani produkcyjnych plików SBS. Ewentualna przyszła normalizacja źródła musi być jawnym przekształceniem projekcyjnym z nowym comparison_sha256 i poprawną projekcją/FOV, z zachowaniem surowego zdjęcia; nie może służyć ukrywaniu niezgodności świata. Na razie pozostaje to hipotezą do kolejnej pracy, nie korektą ani zatwierdzeniem pozy.

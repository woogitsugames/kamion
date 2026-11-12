# Korekta pomiaru kontrastu z rundy 1

Podczas przygotowania rundy 2 wykryto błąd odtwarzania układu współrzędnych w narzędziu `wheel_contrast.py`. Narzędzie wyznaczało wysokość początku regionu jako różnicę wysokości wejściowej kamery i jej rzeczywistej pozycji w Unity. Kamera z `seat: road` jest jednak automatycznie przestawiana na powierzchnię kolizji. Przesunięcie kamery nie jest przesunięciem regionu.

Przykład `d_wear_lane_old`: wejściowe U wynosi 133,334 m, a zarejestrowane Y kamery w Low overcast wynosi około 1,393314 m. Narzędzie wywnioskowało z tego początek 131,940686 m. Skonfigurowany początek regionu ma 131,14 m. Różnica około 0,80 m przesuwała projektowane pola UV względem obrazu. Macierze widoku i projekcji były rzeczywiste, ale brakowało rzeczywistej macierzy regionu.

Wycofujemy wszystkie proporcje ślad/środek i statystyki pól pochodzące z `wheel-contrast-candidate2.json/csv` oraz zatwierdzenie masek `wheel-mask-candidate2-*.jpg`. Pliki pozostają jako zapis diagnostyczny i otrzymują oznaczenie nieważności. Nie są dowodem osiągnięcia kontrastu ani wielkości jego poprawy. Pomiary pól na samej fotografii pozostają oddzielnymi, poprawnymi pomiarami obrazu, a nie albedo fizycznego.

Korekta dotyczy narzędzia pomiarowego. Zachowane obrazy przed/po, liczniki 312 ujęć, raport pamięci importera i wyniki testów nie korzystają z tego odtwarzania współrzędnych. Ich zapis pozostaje aktualny. Niezależna ocena wizualna była warunkowa i nie opierała się na wycofanych proporcjach; nie zgłaszamy pełnego wizualnego PASS ani pomiaru A16.

Naprawa narzędzia wymaga zapisanej podczas renderowania macierzy `rootToWorld` obiektu `WorldRegionRoot`, obok rzeczywistych macierzy kamery. Brak tej macierzy powoduje teraz błąd zamiast wnioskowania z wejściowej kamery. Własne zbliżenia materiałów z wysokością zmierzoną w meshu używają `seat: file`. Pliki kodu kamer i geometrii innych dziedzin nie zostały zmienione.

Historia gałęzi `gpt-asphalt-r1` pozostaje zachowana. Korekta jest zapisana w kolejnej gałęzi `gpt-asphalt-r2` i przekazana do tego samego katalogu artefaktów w main. Ponowny wiarygodny pomiar wymaga zgodnych danych geometrii i nowych zapisów rzeczywistej macierzy regionu; nie zastępujemy brakującego dowodu pomiarem na innym wariancie świata.

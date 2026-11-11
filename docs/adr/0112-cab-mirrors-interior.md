# ADR 0112 — Kabina: lusterka i wnętrze

## r1 — Lusterka V/VI i mocowanie ramion

Stan: w toku, bez zgłoszenia przejścia bramki wizualnej. Gałąź `gpt-cab-r1`, baza `main` `4c9905b1`.

Recenzja `REVIEW-2026-11-11-s10-gpt-JK.md` wykryła wnętrze kabiny w odbiciach lusterek przedniego i krawężnikowego oraz ramię przed lewym szkłem szerokokątnym. ADR 0104 mylił odsłonięcie powierzchni szkła z poprawnością odbijanego obrazu; sprostowano ten zapis.

Zmierzone w prefabie odległości przycinania kamer przedniej i krawężnikowej wynoszą odpowiednio 1,881 i 1,973 m. Kamery leżą nad kabiną, więc tak odległa płaszczyzna może odcinać dach i odsłaniać wnętrze. Kod dodatkowo celowo pozostawia wnętrze widoczne dla klas V/VI. Hipoteza poprawki: bliższa płaszczyzna oraz wyłączenie wnętrza wyłącznie na czas renderowania lustra; potwierdzenie wymaga natywnych RT i kontroli przywrócenia stanu rendererów.

Audyt `CabMirrorAudit` zapisuje zwykły obraz oraz osobne przejście z wnętrzem oznaczonym magenta. Liczba pikseli identyfikatora pozwala wykryć fotele i deskę niezależnie od oświetlenia. To diagnostyka edytora, bez dodatkowego przebiegu w grze.

Próby źródłowej geometrii ramion: siatka 40 × 60 promieni na szkło, osobno identyfikowane obiekty podpór. Cofnięcie końca mocowania przy głowicy o 80 mm usuwa trafienia w ramiona w tym pomiarze. Wartość przesunięcia jest WORKING_VALUE; eksport, widok kierowcy i budżety po zmianie pozostają UNVERIFIED.

Nie zwiększamy rozdzielczości RT, liczby renderów na klatkę ani częstotliwości odświeżania. Pozycje, orientacje i pola widzenia pozostają przedmiotem dotychczasowych testów R46. Telefon i niezależną recenzję wykonuje lider. Dowody nowej rundy znajdują się w `artifacts/cab-r1/baseline`; starsze katalogi `before/after` należą do ADR 0104.

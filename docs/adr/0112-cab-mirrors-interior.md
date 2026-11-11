# ADR 0112 — Kabina: lusterka i wnętrze

## r1 — Lusterka V/VI i mocowanie ramion

Stan: w toku, bez zgłoszenia przejścia bramki wizualnej. Gałąź `gpt-cab-r1`, baza `main` `4c9905b1`.

Recenzja `REVIEW-2026-11-11-s10-gpt-JK.md` wykryła wnętrze kabiny w odbiciach lusterek przedniego i krawężnikowego oraz ramię przed lewym szkłem szerokokątnym. ADR 0104 mylił odsłonięcie powierzchni szkła z poprawnością odbijanego obrazu; sprostowano ten zapis.

Zmierzone w prefabie odległości przycinania kamer przedniej i krawężnikowej wynoszą odpowiednio 1,881 i 1,973 m. Kamery leżą nad kabiną, więc tak odległa płaszczyzna może odcinać dach i odsłaniać wnętrze. Kod dodatkowo celowo pozostawia wnętrze widoczne dla klas V/VI. Hipoteza poprawki: bliższa płaszczyzna oraz wyłączenie wnętrza wyłącznie na czas renderowania lustra; potwierdzenie wymaga natywnych RT i kontroli przywrócenia stanu rendererów.

Audyt `CabMirrorAudit` zapisuje zwykły obraz oraz osobne przejście z wnętrzem oznaczonym magenta. Liczba pikseli identyfikatora pozwala wykryć fotele i deskę niezależnie od oświetlenia. To diagnostyka edytora, bez dodatkowego przebiegu w grze.

Próby źródłowej geometrii ramion: siatka 40 × 60 promieni na szkło, osobno identyfikowane obiekty podpór. Cofnięcie końca mocowania przy głowicy o 80 mm usuwa trafienia w ramiona w tym pomiarze. Wartość przesunięcia jest WORKING_VALUE; eksport, widok kierowcy i budżety po zmianie pozostają UNVERIFIED.

Nie zwiększamy rozdzielczości RT, liczby renderów na klatkę ani częstotliwości odświeżania. Pozycje, orientacje i pola widzenia pozostają przedmiotem dotychczasowych testów R46. Telefon i niezależną recenzję wykonuje lider. Dowody nowej rundy znajdują się w `artifacts/cab-r1/baseline`; starsze katalogi `before/after` należą do ADR 0104.

### Zweryfikowany etap K1–K3

Checkpoint K1/K2 `1284e35e`: test identyfikatora wnętrza daje zero pikseli w sześciu lustrach dla Low/High × clear/overcast. Low clear: Kerb 3366→0, Front 5364→0; zwykłe draws odpowiednio 83→77 i 120→100, instancje 79/102 bez zmian. Sześć kamer zachowuje RT/FOV/cadence/far. Odległość near V/VI wynosi 0,1 m, pozostałe klasy i Legacy zachowują dawną regułę. Przywracane są wcześniejsze flagi rendererów. Przebudowa prefabów potwierdziła cofnięcie podpór we wszystkich trzech LOD bez zmiany bounds i liczby trójkątów.

K3: `MirrorGlassBezel` dokłada do istniejącego submeshu Trim cztery zaokrąglone obrzeża szkieł bocznych. Nie zmienia szkła ani UV odbicia. Koszt siatki +480 trójkątów na LOD, bez dodatkowych materiałów, rendererów i przebiegów; bounds niezmienione. Wymiary obrzeża pozostają WORKING_VALUE. Obejrzano pełne obudowy A/B z oka kierowcy (`bezel-inspection/High-clear`), w tym odsłonięte wcześniej ostre rogi.

`comparison-0112-p2.json`: PASS czterech stanów kabiny, sześciu natywnych RT i pełnych 78 kamer Low/Gate3. Zwykłe draws i instancje są raportowane oddzielnie. Testy lusterek 36/36, XML `editmode-20261111-233900.xml`. To estymaty widoczności CPU w edytorze, nie pomiary GPU telefonu ani niezależna akceptacja wizualna. K4–K6 pozostają w pracy; nie zgłoszono końca rundy.

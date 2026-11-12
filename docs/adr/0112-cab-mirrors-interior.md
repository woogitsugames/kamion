# ADR 0112 — Kabina: lusterka i wnętrze

## r1 — Lusterka V/VI i mocowanie ramion

Stan: r1 zakończona w zakresie K1–K3, bez zgłoszenia przejścia bramki wizualnej. K4–K6 przechodzą do rundy materiałów r2. Gałąź `gpt-cab-r1`, baza `main` `4c9905b1`.

Recenzja `REVIEW-2026-11-11-s10-gpt-JK.md` wykryła wnętrze kabiny w odbiciach lusterek przedniego i krawężnikowego oraz ramię przed lewym szkłem szerokokątnym. ADR 0104 mylił odsłonięcie powierzchni szkła z poprawnością odbijanego obrazu; sprostowano ten zapis.

Zmierzone w prefabie odległości przycinania kamer przedniej i krawężnikowej wynoszą odpowiednio 1,881 i 1,973 m. Kamery leżą nad kabiną, więc tak odległa płaszczyzna może odcinać dach i odsłaniać wnętrze. Kod dodatkowo celowo pozostawia wnętrze widoczne dla klas V/VI. Hipoteza poprawki: bliższa płaszczyzna oraz wyłączenie wnętrza wyłącznie na czas renderowania lustra; potwierdzenie wymaga natywnych RT i kontroli przywrócenia stanu rendererów.

Audyt `CabMirrorAudit` zapisuje zwykły obraz oraz osobne przejście z wnętrzem oznaczonym magenta. Liczba pikseli identyfikatora pozwala wykryć fotele i deskę niezależnie od oświetlenia. To diagnostyka edytora, bez dodatkowego przebiegu w grze.

Próby źródłowej geometrii ramion: siatka 40 × 60 promieni na szkło, osobno identyfikowane obiekty podpór. Cofnięcie końca mocowania przy głowicy o 80 mm usuwa trafienia w ramiona w tym pomiarze. Wartość przesunięcia jest WORKING_VALUE; sprawdzono następnie eksport, widok kierowcy i budżety opisane poniżej.

Nie zwiększamy rozdzielczości RT, liczby renderów na klatkę ani częstotliwości odświeżania. Pozycje, orientacje i pola widzenia pozostają przedmiotem dotychczasowych testów R46. Telefon i niezależną recenzję wykonuje lider. Dowody nowej rundy znajdują się w `artifacts/cab-r1/baseline`; starsze katalogi `before/after` należą do ADR 0104.

### Zweryfikowany etap K1–K3

Checkpoint K1/K2 `1284e35e`: test identyfikatora wnętrza daje zero pikseli w sześciu lustrach dla Low/High × clear/overcast. Low clear: Kerb 3366→0, Front 5364→0; zwykłe draws odpowiednio 83→77 i 120→100, instancje 79/102 bez zmian. Sześć kamer zachowuje RT/FOV/cadence/far. Odległość near V/VI wynosi 0,1 m, pozostałe klasy i Legacy zachowują dawną regułę. Przywracane są wcześniejsze flagi rendererów. Przebudowa prefabów potwierdziła cofnięcie podpór we wszystkich trzech LOD bez zmiany bounds i liczby trójkątów.

K3: `MirrorGlassBezel` dokłada do istniejącego submeshu Trim cztery zaokrąglone obrzeża szkieł bocznych. Nie zmienia szkła ani UV odbicia. Koszt siatki +480 trójkątów na LOD, bez dodatkowych materiałów, rendererów i przebiegów; bounds niezmienione. Wymiary obrzeża pozostają WORKING_VALUE. Obejrzano pełne obudowy A/B z oka kierowcy (`bezel-inspection/High-clear`), w tym odsłonięte wcześniej ostre rogi.

`comparison-0112-p2.json`: PASS czterech stanów kabiny, sześciu natywnych RT i pełnych 78 kamer Low/Gate3. Zwykłe draws i instancje są raportowane oddzielnie: wzrost drawów +0, maksymalny wzrost sumy tris 0,498%. Testy lusterek 36/36, XML `editmode-20261111-233900.xml`; pełne EditMode 276/276, XML `editmode-20261111-234613.xml`. To estymaty widoczności CPU w edytorze, nie pomiary GPU telefonu ani niezależna akceptacja wizualna.

Końcowy GIS r1 pod heavy: 491 pass, 2 fail, 1 xfailed, 673,09 s. Nieaktualny raport fidelity i hash eksportu chunk 0_0 zawodziły również w pomiarze bazowym; brak zmian naprawczych poza cab. Produkty testów cofnięte, slot zwolniony. K4–K6 przechodzą do r2 z audytem UV i wariantami kanałów materiału; r1 nie zgłasza ich naprawy.

## r2 — Materiały ze skanów CC0 i czytelność zużycia

Stan: r2 zakończona, z otwartymi ograniczeniami K4–K6. Gałąź `gpt-cab-r2` od r1, następnie scalono aktualny main bez konfliktów. Baseline obejmuje poprawki K1–K3; budżety kolejnych wariantów liczymy względem nowego baseline, bez przypisywania zmian main materiałom kabiny. Pozostają własność plików cab oraz zakaz zmian szyb i zewnętrza.

Przed obróbką skanów poprawiono sprzątanie audytu powierzchni: oryginalne referencje MeshFilter są przywracane przed zniszczeniem tymczasowych kopii. Nie zakłada to, że poprzednia awaria D3D12 była spowodowana tym błędem. Przygotowanie skanów i eksport obejmujemy heavy, owner `gpt-cab-r2`; Unity nadal pod owner `gpt-cab` zgodnie z poleceniem sesji.

Końcowy wariant scan2 wykorzystuje Brown Leather Roba Tuytela z Poly Haven (CC0, pole 40 cm). FAQ dostawcy potwierdza fotograficzne metody tworzenia tekstur; konkretna metoda tego zasobu pozostaje UNVERIFIED. Skóra: crop około 12 cm; Plastic: pochodna tłoczenia ze skóry, crop 20 cm na kafel 10 cm, nie skan tworzywa deski. Amplitudy profilu są WORKING_VALUE. Kontrakt kanałów, rozdzielczości i perforacja pozostają zachowane. Obręcz ma korektę UV 5/12, piasta i atlas AO bez zmian. Nie zmienia się geometria.

Tryb eksportera --textures-only odtwarza wyłącznie Plastic/Leather. Reprodukcja 12/12 SHA256 zgodna, pełne EditMode 279/279. World exit 0, 416,4 s, bez fallback=True. comparison-0112-scan2.json: PASS 28 kadrów kabiny, sześciu natywnych RT w czterech stanach i 78 kamer Low; maksymalne delty regular/instanced draws i tris wynoszą 0. To estymaty CPU edytora, nie wynik GPU telefonu. Końcowy GIS pod heavy: 521 pass, 2 fail, 1 xfailed w 663,06 s; te same dwie porażki fidelity stale i deterministyczność chunk 0_0 co w r1. Slot zwolniony, własne produkty spoza cab cofnięte.

K4: UV centralnej deski bez potwierdzonego szerokiego rozciągnięcia, wariant AO bez mipów i eksperyment diffuse fill nie usunęły pasma. Eksperyment shaderowy wycofany. K5 nie odtworzono w poprawionych przekrojach zaimportowanego modelu; bez przesuwania geometrii. K6 poprawia mikroziarno, nie dodaje zużycia kontaktowego. Materiał Plastic nie zastępuje brakującego skanu konkretnego tworzywa. Otwarte ograniczenia i arkusze opisuje REPORT r2; następny backlog to nocne zegary.


## r3 — Nocne legendy przycisków

Stan: wariant night1 wdrożony i zweryfikowany w Unity; końcowa walidacja GIS/Fidelity oczekuje na heavy. Od r2 d04feba0, merge main bez konfliktów. Nocne palety ekranów istniały już wcześniej; nowe podświetlenie dotyczy legend przycisków. Zdjęcie Volvo Trucks (Jonatan Fernström, 2017) jest odniesieniem jakościowym, nie CC0 ani pomiarem intensywności. Zmiana ogranicza się do wnętrza, za flagą danych, bez nowych draw/pass i bez zmiany świata. Baseline wykonano po merge; zachowano palety ekranów i alarmy zegarów.

Wariant night1: flaga danych cab_backlight.json i lokalny keyword tylko w istniejącym paśmie ikon Decal. 8 cd/m2, cap 0,06 i fade 6→0 stopni to WORKING_VALUE. Brak nowych pass/fetch/draw, bez zmian QualityProfile. Stan środowiska zerowany bez modelu i po OnDisable; emisja dodana po cab-view lift. Trzy testy celowane i pełne EditMode 301/301 zaliczone. comparison-0112-night1 PASS sześciu stanów, 36 RT i 78 kamer Low; wszystkie maksymalne delty regular/instanced draws/tris 0. To CPU visibility, GPU A16 UNVERIFIED. World zakończony exit 0 w 436,8 s, brak fallback=True; obejrzano wszystkie 15 arkuszy do 960 px. Fidelity i końcowy GIS pozostają otwarte. REPORT r3 opisuje miejscowy efekt, różnice hashów dnia i ograniczenia referencji. Po dodaniu odczytowego audytu geometrii powtórzono pełne EditMode: nadal 301/301, XML 033834.

Dodatkowy pomiar prawego szerokokątnego z DriverEyePoint rozdzielił geometrię od treści odbicia. Raycast przednich stron: centralnie 0/1944 trafień, 127/2400 na brzegach. Maska GPU szkła obejmuje szeroki ciemny obszar widoczny w normalnym renderze: w tej pozycji jest to treść RT, nie szerokie zasłonięcie kanałem drzwi. Low exit 0; High ma komplet PNG i marker OK, ale proces zamknął się kodem -1073741819, więc dodatkowy High opisano z ograniczeniem. Nie zmieniono geometrii, oka ani optyki.


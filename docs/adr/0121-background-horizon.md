# ADR 0121 — Tło i ciągłość horyzontu

## Runda r1 — 11 listopada 2026

Recenzja HIL wskazała brak widocznej kontynuacji jezdni w tle wschodnim i południowym. Istniejące przedłużenia mają 420 m i są częścią tej samej siatki apron, bez dodatkowych rendererów.

Audyt modelu wysokości wykazał, że ukośne przedłużenie używało profilu wysokości przy początku drogi na całej długości. Rzeczywisty apron pod dalszym odcinkiem pochodzi z innych punktów granicy. Dla południowego wyjazdu Tysiąclecia model wskazał różnicę do około 4,75 m poniżej terenu; jest to diagnoza modelowa, nie pomiar renderu ani gotowej siatki.

WorldEdgeBuilder próbkuje teraz wysokość istniejących trójkątów apron pod obiema krawędziami pasa asfaltu. Wyższa z wysokości wyznacza koronę przedłużenia. Pozostaje łagodne połączenie z poziomem jezdni przy granicy, a każde przedłużenie nadal ma 12 segmentów. Podział na dwa submeshe, liczba rendererów, materiały i przebiegi pozostają takie same. Bariery, geometria dróg regionu i ustawienia mgły pozostają własnością innych sesji.

Pomiar bezpośrednio z zapisanej siatki Unity potwierdził minimum −4,6413 m dla południowego przedłużenia Tysiąclecia w środkach trójkątów asfaltu. Siatka bazowa ma 6000 wierzchołków i 576 trójkątów asfaltu w 24 przedłużeniach. Kontrola obejmuje wszystkie ich środki względem oryginalnych trójkątów apron, bez poboczy. Dane: `artifacts/edge-r1/mesh-clearance-before.json`.

Samo dopasowanie stacji nie wystarczyło: kontrola prototypu wykazała resztkowe zakrywanie w początkowym przejściu i przy zmianach nachylenia pomiędzy stacjami. Korona otrzymuje więc minimum 0,04 m nad podłożem (WORKING_VALUE), a segment jest sprawdzany w ośmiu odstępach na trzech śladach poprzecznych. Wymagane podniesienie obu końców zachowuje topologię. Zmieniana jest wysokość istniejących wierzchołków; kontrola odbywa się wyłącznie podczas importu. Prototyp na zapisanej siatce nie wykazał zakrywania poniżej tolerancji −0,02 m w środkach trójkątów. Jest to sprawdzenie geometrii proponowanej poprawki, nie dowód wykonania kodu C# ani ocena wizualna.

### Oddzielne jezdnie przy granicy

Po pierwszym cyklu renderów znaleziono drugi błąd: promień deduplikacji 30 m usuwał przedłużenie osobnej jezdni. W grafie Tysiąclecia na południu osie są oddalone o 14,557 m, a Andersa na wschodzie o 14,406 m. Scalane są teraz jedynie końce oddalone o mniej niż 3 m i ze zgodnym kierunkiem (iloczyn skalarny znormalizowanych kierunków >0,95; tolerancje WORKING_VALUE). Geometria i kolizje zamknięć pozostają bez zmian. Rzeczywista liczba przedłużeń wzrosła z 24 do 35.

### Walidacja r1

Siatka przekazuje także TEXCOORD_1 = (−1, 5), czyli istniejący w WorldPBR znacznik braku danych o zużyciu drogi. Poprzedni brak kanału dawał (0, 0) i uruchamiał warstwę zabrudzonego brzegu na całej szerokości kontynuacji. To poprawka danych własnej siatki, bez zmiany shadera czy materiałów. Stride wierzchołka wzrósł z 52 do 60 bajtów; liczba trójkątów nie zmieniła się przez dodanie kanału. Dwa testy stoków sprawdzają również ten kontrakt.

Po drugiej przebudowie siatka ma 6572 wierzchołki zamiast 6000 oraz 10968 trójkątów zamiast 10176 (+792). W 840 środkach trójkątów asfaltu najmniejszy prześwit względem apron wynosi 0,0403 m; w bazie minimum 576 próbek wynosiło −8,8035 m. To pomiar gotowej siatki wygenerowanej przez C#, nie wyłącznie prototypu Python. `mesh-audit-summary.json` zawiera podsumowanie.

EditMode: 267/267, w tym dwa przypadki stoków poprzecznych i cztery przypadki deduplikacji. Cztery konfiguracje Low/High × clear/overcast: 356 par kamer, z tego 178 Low; w każdej Low suma draw calls statycznych i instancji ma deltę 0. Największa zmiana sumy zaokrąglonych trójkątów wynosi +1,1765%, poniżej +2%. Wszystkie kamery i obie składowe instancji są zapisane w `all-cameras.csv` / `measurements.json`. To estymaty edytora, nie liczniki GPU telefonu. Są także 136 par zdjęcie–render do 960 px z atrybucją i ograniczeniami pozy.

Ocena obrazu: efekt w standardowych kadrach jest subtelny. Maska Apron:road_asphalt dopasowała jeden materiał na jednym rendererze i potwierdziła widoczność kontynuacji w kadrach east/south. Usunięto konkretne błędy geometrii tła; ogólny cel fotograficznej jakości H1 nie jest jeszcze zamknięty, a masa zabudowy pozostaje rzadka. Ujęcie w osi DK8 jest z wysokości kabiny; nazwa lasu wymaga osobnego potwierdzenia źródłowego. Telefon i niezależna recenzja należą do lidera.

Pełny GIS przy zamknięciu rundy, pod pulą heavy: 492 passed, 1 failed, 1 xfailed (658,63 s). Jedyna porażka to test_report_not_stale: istniejący fidelity_qa jest nieaktualny dla overrides.yaml oraz sześciu plików roads. Wszystkie siedem plików i sam raport pozostają bez zmian względem bazy rundy. Nie naprawiano dziedziny Claude. Po odtworzeniu ubocznych metadanych innych dziedzin i zachowaniu tylko pól far_field w world_manifest, własny test_far_field.py przeszedł 5/5, a oba SHA siatek są zgodne z QA. W world_manifest zmieniono wyłącznie dwa skróty far-field; źródła dróg, budynków i roślinności są nietknięte.

### Kolejna runda

Audyt przypiętego archiwum LoD1 potwierdził 31 plików GML, które dotychczasowy parser pomija (czyta wyłącznie XML i oczekuje innego zapisu buildingId). Produkcyjny parser zwraca 0 wysokości. Prototyp do odczytu odzyskał 36971 wysokości, z czego 5390 pasuje bezpośrednio do identyfikatorów pierścienia. Naprawa produkcyjnego odczytu i pochodzenie wysokości należą do rundy r2; r1 nie zmienia far_field.py.

## Runda r2 — odczyt wysokości LoD1

Archiwum GUGiK 2061 zawiera kafle GML. Odczyt pojedynczego XML przez wyrażenie regularne nie obsługiwał użytego zapisu identyfikatora w gen:stringAttribute. Parser strumieniowy przechodzi przez wszystkie GML/XML i wiąże buildingId oraz measuredHeight wyłącznie w obrębie jednego Building, niezależnie od prefiksu i kolejności pól. Zachowuje obsługę starszego elementu buildingId. Wartości niefinitywne, niepozytywne, brakujące oraz jednostki inne niż metry są odrzucane. Sprzeczne powtórzenia tego samego ID są wykluczane, zamiast uzależniać wynik od kolejności plików.

Cache ma wersję /11. Każdy budynek zapisuje height_source: pomiar GUGiK, szacunek WORKING_VALUE z kondygnacji/typologii albo niezweryfikowany tag OSM. Manifest i QA zapisują liczniki tych źródeł oraz audyt odczytu archiwum. Jest to pochodzenie wysokości źródłowej; dotychczasowa kompresja odległości i wysokości dalekiego planu pozostaje aktywna. Nie oznacza to modelu tła o pełnej skali pionowej.

Baza r2 obejmuje 364 PNG (91 kamer w czterech konfiguracjach), aktualne klasy pozy i SHA wejść. Porównania fotograficzne dopuszczają A/B, odrzucają C; fotometria i pozy B pozostają niezweryfikowane. Testy parsera: 11/11. Walidacja regeneracji, sylwetki, wszystkich kamer Low i końcowy GIS pozostają w toku.

### Wyniki regeneracji i zakres r2

Produkcja odczytała 36971 wysokości z 31 GML, bez duplikatów i konfliktów. W pierścieniu 5390 z 8447 budynków ma measuredHeight; 97 zachowuje szacunek BDOT, 2921 szacunek OSM, 39 tag height OSM pozostaje UNVERIFIED. Różnicę wysokości względem bazy ma 5384 obiektów: 2253 bloki, 1564 biurowe, 1065 hal i 502 domy. Wszystkie obrysy oraz lasy, kominy, maszty i linie zachowały dane z bazy. Audyt dotyczy danych źródłowych przed kompresją perspektywy.

Pełny build_world zakończył się po 459,9 s, bez fallback=True. Far-field Low: 24508 → 24500 trójkątów; High: 118524 → 118524. Import edge potwierdził te liczby i nie zmienił 35 kontynuacji ani 36 zamknięć dróg. Uboczne metadane dróg, props, wiaduktu i streetscape odtworzono; w world_manifest zachowano wyłącznie aktualizację własnego far-field. Test parsera po sprawdzeniu rzeczywistej jednostki meter: 15/15; pojedynczy far-field: 5/5; EditMode: 267/267, bez pominięć.

Macierz po zmianie obejmuje kolejne 364 PNG. W obejrzanym edge-south High clear zmieniła się wysokość hali w panoramie; na wschodzie efekt jest subtelny. Nie ogłaszamy zamknięcia jakości fotograficznej miasta. Weryfikacja wszystkich kamer Low i końcowy GIS pozostają do dopisania po zakończeniu ich zadań.

### Budżet i dalsza diagnostyka r2

Compare zakończyło 364 porównania kamer. Wszystkie 182 Low mają deltę sumy drawsEst statycznych i instancji równą 0; delta zaokrąglonej sumy trójkątów wynosi od −1k do 0k. To estymaty edytora, bez pomiaru GPU telefonu. Zapisano 100 par zdjęcie–render dla 25 pozy B; 17 C wykluczono z oceny fotograficznej. W obejrzanej dziennej parze 150280503737744 kominy i tło nadal nie uzasadniają ogólnego PASS jakości. Pozy B pozostają przybliżone, fotometria UNVERIFIED.

Kontrola SHA obu siatek apron i zamknięć potwierdza zgodność bajt w bajt z bazą r2. Diagnostyka na potrzeby r3 porównała 5676 punktów modelu Python z trójkątami Unity. Python minus Unity: od −0,3726 do +1,4267 m, p95 wartości bezwzględnej 0,1717 m; 40 punktów przekracza +0,8 m. Największe różnice są przy północno-zachodnim narożniku. To pomiar rozbieżności modeli, nie dowód widocznego szwu ani liczba wiszących budynków. R2 nie zmienia podłoża ani ustawień mgły; r3 sprawdzi źródło różnicy i obraz.

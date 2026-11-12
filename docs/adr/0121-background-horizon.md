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

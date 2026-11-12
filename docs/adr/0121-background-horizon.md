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

### Końcowy GIS r2 i granica odpowiedzialności

Pełny zestaw pod heavy na koniec rundy: 536 passed, 2 failed, 1 xfailed w 749,35 s. Zestaw nie jest zielony. Pierwsza porażka to istniejący stale fidelity dla siedmiu niezmienionych plików roads/overrides. Druga, test_export_is_deterministic, porównuje świeżą budowę z zachowanymi metadanymi chunków bazowej, importowanej sceny. Ograniczenie world_manifest do własnych pól zachowuje te wpisy i ujawnia ten rozjazd.

Aby rozdzielić metadane od stabilności generatora, sprawdzono fizyczne pliki: wszystkie 64 chunki z wcześniejszej budowy CLI są bajtowo identyczne z niezależną budową pytest i pasują do świeżego manifestu. 54 wpisy bazowego manifestu są inne. To dodatkowy audyt, nie zmiana porażki testu w PASS. Plik chunk-manifest-drift.json zapisuje każdy SHA; świeży pełny manifest zachowano w artifacts. Nie naprawiano ani nie zatwierdzano cudzych chunków lub generatorów. Integracja wymaga pełnej regeneracji manifestu w stanie lidera.

Po testach ponownie sprawdzono oba SHA źródłowych far GLB i niezmienność własnych QA/manifesta; odtworzono uboczne metadane innych dziedzin. Źródła GLB i cache przed/po zachowano w edge-r2, aby następne rundy nie nadpisały dowodów. Runda 2 przekazuje poprawę danych wysokości i poprawny budżet własnej zmiany, z częściową jakością obrazu i dwiema jawnymi porażkami pełnego zestawu.

## Runda r3 — wspólny profil wysokości apron

Baza r3 obejmuje main 2c3939b2 (life/vegetation/cab/edge r1) scalony do gałęzi przez 45c1921b. Po odtworzeniu materiałów i pełnego świata wykonano import Low/High oraz standardowe odtworzenie generowanych prefabów pojazdów. Brakujące niezmienne wejścia cache (fotografia warstwy asfaltu i wnętrze LOD0) skopiowano z main z kontrolą SHA, bez edycji cudzych źródeł. 368 PNG Before i 368 After obejmują po 92 kamery w Low/High clear/overcast; kontrola wymaga obrazu i statystyki każdego ID. 25 fotografii B zamrożono z przypiętymi SHA, 17 C pozostaje poza oceną fotograficzną.

C# wygładzał 528 wpisów obwodu, w tym kopie narożników potrzebne do wachlarzy trójkątów. Python BorderElevation używa 512 unikalnych próbek. W rezultacie ta sama lokalizacja narożnika otrzymywała dodatkową wagę, a okno ±6 wpisów obejmowało mniej rzeczywistych sąsiadów. Średnia i wygładzanie są teraz liczone po uporządkowanych, unikalnych pozycjach; wyniki trafiają z powrotem do wszystkich kopii wachlarza. Okno jest zgodne z Python: do ±6 unikalnych próbek. Surowe wysokości przy brzegu i topologia pozostają takie same.

Dwa testy rzeczywistego BuildApron wykorzystują płaski stok N ±0,025. Niezależna średnia trzynastu próbek przy NW wynosi 13066/13 m we współrzędnej N (z odsunięciem 0,75 m do wnętrza regionu). Stary kod dał dwie porażki właściwej asercji: błędy około +0,4248 i −0,4248 m. Po poprawce oba przypadki spełniają tolerancję 0,01 m; plik testu ma identyczny SHA w Red i Green. Pełne EditMode: 297/297, bez pominięć. Nowy helper działa tylko przy imporcie, bez nowej pracy C# podczas jazdy.

Pomiar nowej bazy Before potwierdził w 5676 punktach różnicę Python−Unity do +1,4267 m; p95 abs 0,1733 m, 40 punktów >+0,8 m. Source Before jest zamrożony w artifacts/edge-r3/before-source. Wynik After, kontakt rzeczywistych dolnych wierzchołków kurtyn, prześwit asfaltu, wszystkie budżety kamer i końcowy GIS są jeszcze do uzupełnienia.

Obejrzane zwykłe ujęcia north Low-overcast i east High-clear są wizualnie bliskie bazie. Statyw NW w regionie zasłania płot/roślinność, a dodatkowy statyw poza regionem znalazł się wewnątrz HLOD; żaden nie uzasadnia wizualnego PASS szwu. Nie zmieniono zamrożonej pozy z podstawowej macierzy ani nie przedstawiono kalibracyjnego statywu jako zdjęcia lub widoku gracza. Rozpoznawalność miasta i widoczne zamknięcia mapy pozostają osobnymi otwartymi problemami.

### Wyniki geometrii i budżetu r3

Po zmianie pomiar 5676 punktów daje maksimum Python−Unity +0,8907 m (było +1,4267 m), p95 abs 0,1413 m (było 0,1733 m), a liczba próbek >+0,8 m spadła z 40 do 1. Pozostaje różnica między źródłowym NPY a próbkami rzeczywistego collidera oraz interpolacją trójkątów; poprawka wagi narożników nie rozwiązuje jej w całości. To nie jest liczba wiszących budynków.

Niezależny audyt dolnych wierzchołków kurtyn używa V=1 w surowym glTF, bo eksporter zapisuje 1−V. Pierwszy wynik z V=0 mierzył wierzchołki koron i jest jawnie unieważniony w forest-TOP-clearance-INVALID.json. Powtórzenie audytu jest objęte pulą heavy; końcowe potwierdzenie w corrected-forest-receipt.json. Wstępny poprawiony pomiar: Low 137→1 podstaw powyżej +0,05 m, max +0,9182→+0,2053 m; High 777→7, max +0,9267→+0,3774 m. Próg 0,05 m jest WORKING_VALUE; alfa tekstur i widoczność szwu nie są ocenione przez ten pomiar. Wszystkie 3761 Low / 17821 High punktów mają pokrycie siatki apron, źródłowe GLB zachowały SHA.

368 porównań obejmuje wszystkie 92 kamery każdej konfiguracji. We wszystkich 184 Low suma draws statycznych i instancji ma deltę 0, a suma zaokrąglonych trisK również 0. Osobne składowe instancji są w all-cameras.csv / measurements.json. Nie zmieniono shaderów, przebiegów, profili jakości ani mgły. Siatka apron nadal ma 6572 wierzchołki, 10128 trójkątów trawy i 840 asfaltu, 35 kontynuacji. Minimalny prześwit w środkach asfaltu wynosi 0,0403 m. Zmiana Y może zmienić wyliczane normalne i tangenty; nie twierdzimy, że cały pozostały bufor jest bajtowo identyczny.

### Wskazana ściana lasu — diagnostyka kolejnej rundy

Zachowano trzy pary G3-A 303305/320215/454716 w next-round-review/blocks-vs-forest.jpg. Fotografie pokazują wyraźniej panoramę bloków niż obecny render. Maska całego FarField_far_west wybrała dwa sloty, a wszystkich FarField_far osiem slotów czterech rendererów. Ciemna ściana lasu nadal nie otrzymała magenty; maska oznaczyła jedynie niewielkie fragmenty własnego tła. Nie przypisujemy więc automatycznie problemu dziewięciu własnym pasom drzew ani ich nie usuwamy. Low far clip 900 m i odległość przeciwległej granicy od tych kamer wymagają dalszego rozdzielenia widoczności tła od roślinności regionu. Klasa pozy B pozostaje przybliżona. Cudzej roślinności, kamer sbs oraz geometrii barier nie zmieniano.

Dalszy odczyt źródeł doprecyzował limit fotografii High: QualityProfile.asset ma 2500 m, ale Gate3Cameras.cs:90 ustawia 1400 m, a VisualQaRunner zachowuje min(authored, tier). Własne zdjęciowe rendery High z tej rundy są więc ograniczone do 1400 m; nie reprezentują pełnego zasięgu normalnej kamery High. Low pozostaje 900 m. Nie zmieniono kamer ani SBS. W audycie środków bloków h≥20 m w poziomym FOV 67/104/104 kandydatów jest poza 900 m; poza 1400 m odpowiednio 67/100/102. Najbliższe środki mają odległość osiową 1422/1361/1384 m. To kandydaci źródłowi, bez obrysu, pruningu Low, pionowego FOV i okluzji. Maska High wybrała cztery materiały budynków na czterech sektorach; w kadrze 303305 oznacza jedynie małe fragmenty przy lewej krawędzi. Normalne fotografie i maski zachowano osobno. Dalsze usuwanie mgły lub lasu bez rozdzielenia tych limitów nie ma podstaw.

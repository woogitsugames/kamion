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

Baza rundy: main 2c3939b2 scalony przez 45c1921b. Po odtworzeniu materiałów i świata wykonano pełny import Low/High oraz standardowe odtworzenie generowanych prefabów pojazdów. Brakujące niezmienne wejścia cache skopiowano z main z kontrolą SHA, bez edycji cudzych źródeł. Build_world po poprawce zakończył się po 424,4 s, bez fallback=True.

C# wygładzał 528 wpisów obwodu, w tym kopie narożników potrzebne do wachlarzy trójkątów. Python BorderElevation używa 512 unikalnych próbek. Ta sama pozycja narożnika otrzymywała więc dodatkową wagę, a okno ±6 obejmowało mniej rzeczywistych sąsiadów. Średnia i wygładzanie są teraz liczone po uporządkowanych unikalnych pozycjach; wynik trafia także do kopii wachlarzy. Surowe wysokości brzegu, topologia, UV, kolory i podział submesh pozostają takie same. Zmiana Y może zmienić wyliczane normalne i tangenty. Helper działa tylko przy imporcie, bez dodatkowej pracy podczas jazdy.

Dwa testy rzeczywistego BuildApron wykorzystują płaski stok N ±0,025 i niezależną średnią trzynastu próbek przy NW: 13066/13 m we współrzędnej N, z odsunięciem 0,75 m do wnętrza. Stary kod dał dwie porażki właściwej asercji, z błędami około ±0,4248 m. Po poprawce oba przypadki spełniają tolerancję 0,01 m; SHA testu Red/Green jest identyczny. Pełne EditMode: 297/297, bez pominięć. Kod poprawki: 16199d31a2b2fe38889cd15338fa4f79f22dd8c4.

Pomiar 5676 punktów modelu Python względem rzeczywistych trójkątów Unity: maksimum +1,4267→+0,8907 m, p95 abs 0,1733→0,1413 m; próbek >+0,8 m jest 1 zamiast 40. Pozostaje różnica między źródłowym NPY, próbkami collidera i interpolacją trójkątów. Nie jest to liczba wiszących budynków. Before i After siatki zachowano w before-source / after-source.

Audyt podstaw kurtyn używa V=1 w surowym glTF, ponieważ eksporter zapisuje 1−V. Pierwszy wynik z V=0 mierzył korony; jest jawnie unieważniony w forest-TOP-clearance-INVALID.json. Poprawiony audyt powtórzono pod heavy, exit_code=0 w corrected-forest-receipt.json. Low: 3761 podstaw, liczba ponad +0,05 m spadła 137→1, maksimum +0,9182→+0,2053 m. High: 17821 podstaw, 777→7, +0,9267→+0,3774 m. Wszystkie punkty mają pokrycie apron. Próg jest WORKING_VALUE; alfa tekstury i widoczność szwu pozostają UNVERIFIED. Oba źródłowe GLB zachowały SHA.

Siatka apron nadal ma 6572 wierzchołki, 10128 trójkątów trawy i 840 asfaltu oraz 35 kontynuacji. Minimum prześwitu środków trójkątów asfaltu wynosi 0,0403 m. Nie dodano materiałów, rendererów, przebiegów ani pól profilu; shadery i mgła są bez zmian.

Macierz obejmuje 368 PNG Before i 368 After: po 92 kamery w Low/High clear/overcast. Wymagano obrazu i statystyki każdego ID oraz niezmiennych SHA wejść podczas przechwycenia. Wszystkie 184 Low mają deltę draws 0, również osobno dla statycznych, instancji i cieni; delta sumy zaokrąglonych trisK wynosi 0. Osobne liczniki każdej kamery są w all-cameras.csv / measurements.json. Są to estymaty edytora, bez pomiaru GPU telefonu. 25 fotografii B zamrożono z SHA i atrybucją; 100 par ma szerokość do 960 px. 17 C wykluczono z oceny fotograficznej. Pozy B i fotometria pozostają niezweryfikowane.

Obejrzane zwykłe north Low-overcast i east High-clear są wizualnie bliskie bazie. Statyw NW zasłania regionalny płot/roślinność, dodatkowy statyw poza regionem trafił wewnątrz HLOD; żaden nie dowodzi zamknięcia widocznego szwu. Nie zmieniano zamrożonej pozy z macierzy. Jakość fotograficzna pozostaje PARTIAL.

### Końcowe testy i zakres r3

Pierwszy pełny GIS urwał restart komputera; log kończy się na 85%, bez wyniku końcowego. Po wznowieniu sprawdzono brak procesu, zwolniono tylko własny osierocony slot i zachowano nieukończony log. Pełne powtórzenie na końcu rundy, pod heavy i z ograniczeniem bibliotek numerycznych do jednego wątku: 591 passed, 1 xfailed, 0 failed w 797,91 s. Nie selekcjonowano zaliczonych fragmentów przerwanego przebiegu.

GIS uruchomiono wobec świeżego manifestu pełnej regeneracji, zgodnego z fizycznymi GLB. Dopiero po teście sprawdzono SHA obu własnych GLB, QA i manifestu źródłowego, po czym odtworzono uboczne metadane dróg, wiaduktu, props i world_manifest. Własne pola far_field i materials.far_field_buildings są identyczne z bazą r3, więc nie wymagają zmiany w commicie. Audyt 64 plików po teście odczytuje ścieżki CLI, nie niezależną kopię temp pytest (independent_pytest_paths=0); niezależność eksportu jest sprawdzona przez zaliczony test_export_is_deterministic. Nie przedstawiamy audytu CLI jako drugiego dowodu plików pytest.

### Rozdzielenie panoramy i własności geometrii

Wskazane pary 303305/320215/454716 pokazują bardziej rozpoznawalne bloki na fotografii niż w renderze. Maska zachodniego far-field wybrała dwa sloty, a wszystkich sektorów osiem slotów czterech rendererów; ciemna ściana lasu nie otrzymała magenty. Nie ma podstaw do automatycznego usunięcia własnych pasów drzew. W next-round-review zachowano obrazy i maski.

QualityProfile Low ma 900 m, High 2500 m, lecz Gate3Cameras ustawia authored far=1400 m, a runner stosuje min(authored,tier). Zdjęciowe High tej rundy jest więc ograniczone do 1400 m. Odczytowy audyt środków bloków far-field ≥20 m w poziomym FOV znalazł 67/104/104 kandydatów poza 900 m, z czego 67/100/102 także poza 1400 m. Najbliższe środki mają odległość osiową 1422/1361/1384 m. To kandydaci źródłowi, bez pruningu Low, obrysu, pionowego FOV, mgły i okluzji; nie jest to pomiar widoczności całych brył.

Osobny odczyt buildings.geojson wskazuje po dziesięć regionalnych bloków mieszkalnych ≥25 m w poziomym FOV tych trzech kadrów, wewnątrz tile i 900 m. Dla 303305 najwyższe źródłowe budynki 37,59–56 m leżą około 574–680 m w osi widoku. ID, wysokości i pozycje są w near-city-ownership.json. Nie jest to dowód brakującej siatki, złej wysokości ani identyfikacji fotografii. Tych budynków nie wolno dublować w far-field lub rysować przed bliższą roślinnością. Schemat 64 dalekich brył bez far clip/mgły/okluzji jest wyłącznie studium, nie assetem gry; koszt 768 trójkątów jest obliczony, nie zmierzony w Unity. Hipotezę masowego pomijania pomierzonych wysokich offices odrzucono: tylko jeden office ≥16 m poza360m w cache.

Następny priorytet po merge main: szary klin nad halami na nowych chmurach, wskazany przez recenzję light-r1 batch2 i HANDOVER s12. Obejrzano archiwalny artefakt light-r1 2948, nie świeży main. Najpierw odtworzenie aktualnego stanu i maski Apron/FarField; nie zmieniać wysokości lub mgły na podstawie samej etykiety recenzenta. 2948 ma klasę C i służy wyłącznie diagnozie artefaktu. Cudze źródła budynków, roślinności, barier, kamer SBS i światła pozostały nietknięte.

## Runda r4 — diagnoza szarego klina po integracji chmur

Baza: merge432d5675 z main c882f81c, bez nowej edycji produkcji edge. Pełne materiały486s i świat503s zbudowano pod osobnymi slotami heavy, bez fallback=True. Wykonano pełny importLow/High i odtworzenie generowanych prefabów, bez zmiany źródeł innych dziedzin. Pełne EditMode319/319,0failed/skip; XML z SHA w artifacts/edge-r4/tests.

Baza dowodowa: 368PNG w formacie telefonu2340×1080 oraz104PNG native, 26kamer w4konfiguracjach (25zaakceptowanych fotografiiB oraz diagnostycznaC2948). Każdy nativePNG ma kontrolowane wymiary1280×720 lub1280×960. Kanoniczne pozy/FOV/seat są zgodne z sbs_cameras.json; fotografie, kamery i ich przypisania są zamrożone przez SHA. Nie zmieniono kalibracji, klasy pozy ani fotometrii.

Errata do r3: 100par zdjęcie–render r3 używało ogólnego renderu2340×1080, natomiast fotografie mają10×16:9 i15×4:3. Pary są poglądowe, nie dowodzą identycznego kadru ani zgodności fotograficznej. Budżet przed/po r3 pozostaje ważny, bo obie strony miały te same kamery i proporcje. Odczytowe audytyFOV r3 zakładały jawnie16:9 i nie są pełnym licznikiem pola widzenia formatu telefonu. R4 rozdziela te zastosowania; ERRATA-R3-PHOTO-ASPECT.md dostarczono do artifacts main. Ocena jakości r3 pozostajePARTIAL.

Klin odtworzono w clear2948/303305 na bieżącej bazie. Maska Apron i wszystkich nieprzezroczystych sektorów far-field wybrała6slotów5rendererów, nie oznaczając klina. Oddzielna maska kurtyn forest_edge_mixed wybrała4sloty4rendererów i również go nie oznaczyła. Użyto osobnej maski kurtyn, żeby pełna magenta zastępująca alfę nie ukryła geometrii ocenianej w pierwszym kroku. Wszystkie normalne obrazy i maski zachowano osobno.

Odczyt źródeł wskazał możliwą granicę dolnej półsfery fotografii chmur: metadane mówią opacity=0 poniżej źródłowego horyzontu, a SourceRotation obraca fotografię do innej wysokości słońca. Przed dodatkową ablacją zapisano obliczenie tej granicy dla obu kamer, bez dopasowania do pikseli. Słońce źródła47,856°, preset42°; obliczona linia pokrywa się wizualnie z ukośną krawędzią klina. Oryginalny Sky i WorldAtmosphere pozostają nietknięte.

Dodatkowy render z istniejącym rq_clearcover=0 usuwa klin wraz z fotografią chmur, bez zmiany geometrii, mgły czy ekspozycji. To wyłącznie ablacja diagnostyczna, nie proponowane rozwiązanie produkcyjne; podstawowe Before pozostaje z chmurami. Dostępne dowody wiążą artefakt z granicą obróconej fotografii, nie z geometrią edge. Pakiet wedge-diagnosis z maskami, SHA i predykcją skopiowano do własnych artifacts main. Dalsza naprawa należy do light; nie schowano problemu zmianą wysokości lub koloru terenu. Kamera2948 ma klasęC i nie służy zaliczeniu podobieństwa fotograficznego.

R4 nie tworzy fikcyjnego After ani deklaracji poprawy budżetu dla samej ablacji. Ogólny cel obrazu nadalPARTIAL; klin pozostaje w produkcyjnej bazie. Końcowy GIS i odtworzenie obcych metadanych są w toku. Następna runda edge sprawdzi pozostały odstęp dolnych końców własnych kurtyn względem rzeczywistych trójkątów apron, bez zmiany koron, regionalnej roślinności i shaderów.
Pomiar10z góry określonych kolumn w obu1280×720 wiąże krawędź z predykcją do1,46px. W9kolumnach największy sąsiedni skok szarości zmniejsza się z6–10/255 do1/255 po ablacji. Kolumna303305,x1020 przecina dach(17→14/255), więc nie jest czystym pomiarem nieba; nie usunięto jej z danych. Pełne27wartości na pas i reguła pomiaru są w cloud-cutoff-measurement.json. Wynik nie mierzy fotografii.

### Końcowa walidacja r4

Pełny GIS pod heavy: 632 passed, 1 failed, 1 xfailed w 752,59 s. Jedyna porażka test_report_not_stale wskazuje fidelity_qa nieaktualne dla overrides.yaml i tools/worldgen/roads/meshing.py. Oba pliki i raport pozostają niezmienione od bazy 432d5675; audyt SHA w fidelity-staleness.json. Nie naprawiano obcej domeny i nie zamieniono porażki w PASS. Po teście kontrola obu GLB far-field, QA i manifestu źródłowego potwierdziła niezmienne SHA. Przywrócono obce generated, props_meta i street_props.glb; diff produkcji r4 jest pusty. Dodatkowy odczyt64GLB dotyczy ścieżekCLI (independent_pytest_paths=0), nie niezależnej kopii testowej; zaliczony test deterministyczności pozostaje właściwym dowodem tej części zestawu.

Przeczytano nową recenzję s12 batchA: po diagnozie klina ważniejszą poprawką obrazu edge jest płaska, brązowo-pomarańczowa wysoka hala panoramy południowej (P1). Bieżące edge-south High-clear potwierdza artefakt. Własny far_field.py traktuje każdą halęh≥22m jak elektrociepłownię niezależnie od funkcji, nadając brąz, a losowy pas zajmuje16%wysokości. Kandydat C061 o measuredHeight23,91m ma funkcję produkcyjny; projekcja jest zgodna z ogólnym położeniem bryły, ale wymaga potwierdzenia przez rzeczywistą geometrię i nie jest identyfikacją fotograficzną. R5 nada mu priorytet przed resztkowym stykiem kurtyn; źródeł budynków regionu nie zmieniamy.

## Runda r5 — przemysłowa hala południowej panoramy (walidacja w toku)

Baza main 889201d5, merge cc53055a. Pełna budowa bazowa trwała 515,4 s, bez fallback=True. Materiały ponownie wykorzystano po sprawdzeniu niezmiennych wejść, kompletu plików i cache; szczegóły w material-baseline-reuse.json. Ukończono Before: 368 ujęć telefonu i 104 native z proporcjami 25 fotografii B oraz diagnostycznej C2948. Nie zmieniano kamer ani referencji.

Potwierdzono tożsamość źródłowej bryły 2BE4B431-C061-1BF0-E053-CC2BA8C0D140 z rzeczywistą geometrią: 18/18 trójkątów High i 16/16 Low. Nakładka trafia w krytykowaną halę. Dane podają funkcję produkcyjną i wysokość LoD1 23,91 m, bez liczby kondygnacji. To identyfikacja geometryczna, nie fotograficzna; kolor, podziały okładziny, szkło i obróbka pozostają WORKING_VALUE.

Poprawka klasyfikuje wygląd energetyczny wyłącznie z jawnej funkcji, zamiast samego progu wysokości. Jawnie przemysłowe hale otrzymują stonowaną paletę i cienką obróbkę. Szacowany wariant wysokiej hali używa istniejącego COLOR.a=0,25 dla paneli i 0,65 dla paneli z górnym pasmem szkła. Nowa addytywna ścieżka WorldSurface działa tylko w _FAR_FACADE dla tych zakresów danych; nie dodaje kanału, varying, tekstury, słowa kluczowego ani przebiegu. Podziały są filtrowane pochodnymi i przechodzą do średniego pokrycia przy rozstawie mniejszym od piksela. Nie jest to dowód braku kosztu GPU.

Red rzeczywistego _add_building: 20 przypadków, 18 passed i dwie oczekiwane porażki Low/High przy braku znacznika przemysłowego. Ten sam plik testów jest zamrożony dla Green; SHA zapisano w facade-red-result.json. Kod zastosowano dopiero po identyfikacji i Red. Green, pełna regeneracja After, kompilacja shadera, obraz, budżet i testy końcowe są jeszcze niezaliczone; tej sekcji nie traktować jako raportu przyjęcia zmiany.

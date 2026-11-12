# SBS r3 — ranking i kalibracja G3-B

Start 12.11.2026 około 02:42 Europe/Warsaw. Ten sam worktree .claude/worktrees/gpt-sbs. Gałąź gpt-sbs-r3 utworzona od zamkniętej gpt-sbs-r2 962ad111; merge main 9874d98c zakończony bez konfliktów jako 31988772. Main zawiera ADR 0125 i rundy r1 innych dziedzin. Nie scalano do main i nie pushowano.

R2: 561 passed, 1 xfailed; EditMode 261; 168 raw, 100 B, 168 diagnostycznych arkuszy; dostawa do main potwierdzona receipt. Nie jest obrazem nowych scaleń. R3 odtwarza materiały i świat, potem importuje przed renderami. Wszystkie ciężkie zadania w heavy gpt-sbs-r3 (max 3), Unity w gpt-sbs. Pełny GIS dopiero na końcu rundy, podczas pracy pojedyncze pliki.

Zakres: docs/refs/sbs-priorities.md dla wszystkich sesji oraz własne narzędzia/dane SBS. Priorytet wskazany przez recenzję 0125: 275528/837235 cofnięcie 12–20 m, 328135/297817 wspólna próba około 45 m, 180137 pozycja, 494288 kurs. Liczby to hipotezy. Zanim zmieni się produkcyjne pozy, diagnostyka C, porównanie co najmniej dwóch niezależnych trwałych kotwic i niezależny krytyk. Nie ukrywać negatywnych kadrów ani nie przenosić starego D51 na nowe SHA.

Obejrzany materiał wstępny jest zapisany w r2/PRE-R3-VISUAL.md. 297817 ma portal daleko w tle; porządek zdjęć 297817 przed 328135 o 2678 ms jest zgodny ze zbliżaniem do portalu. Nie znaleziono dowodu zamiany ID. Świat, znaki, runtime i pliki Claude są poza zakresem edycji. Pochodne generatorów po walidacji ponownie przywrócić, zachowując wejścia dowodów.

Zapisano wejściowy ranking docs/refs/sbs-priorities.md: 10 tematów rozpoznawalności i zadania dla wszystkich 10 dziedzin, ze źródłem i stanem potwierdzenia. Ranking odróżnia r1/r2, recenzję 0125 i oczekujący render r3; nie sumuje ocen z różnych epok. Generator bazowy czeka na heavy, uchwyt 1171.

Przygotowano make-gantry-probes.py, jeszcze bez uruchomienia: 18 hipotez C dla czterech kamer naziemnych. Grobin: 0/-12/-16/-20/-28 m, zsolt: 0/-30/-45/-60 m wzdłuż własnego kursu siatki. Wariant 0 zachowuje dokładną kamerę; przesunięte użyją NMT+2,2 m, stałych yaw/FOV/pitch i dwóch natywnych proporcji 16:9/4:3. Skrypt wymaga zgodnej ukończonej migawki świata r3 i sprawdza SHA zdjęć oraz niezmienność produkcyjnych źródeł. Nie obejmuje kamer na wiadukcie, gdzie NMT nie jest wysokością pokładu.

Przygotowano wrapper importu (kopię sprawdzonego r2) i render-gantry-probes.ps1: dwie natywne proporcje, osobne Acquire/Release Unity przed każdym uruchomieniem, wymagany receipt poprawnego importu, migawka pięciu wejść i kontrola SHA/HEAD przed i po. Parser PowerShell bez błędów. Żaden z tych wrapperów nie został jeszcze uruchomiony; bazowa generacja nadal czeka na heavy.

Przed użyciem uzupełniono wrapper importu o wymagany zgodny baseline-completed.json, SHA świata i materiałów oraz zapis własnego import-completed.json tylko po kodzie 0. Render wymaga teraz również zgodnej migawki materiałów z importu. Oba parsery PowerShell poprawne. To zapobiega użyciu starych lokalnych siatek przed generacją r3.

Niezależny przegląd przygotowania wykrył i po poprawkach zamknął dwie luki związania epoki. REVIEW-PREPARATION.md zapisuje zakres PASS kodu, bez oceny świata. Wykonano lekki PS check-provenance: zgodne wejścia przyjęte, osiem podmian odrzuconych właściwym powodem, fixture przywracany po każdym przypadku. Bez Unity, Pythona i dodatkowej dzierżawy; wynik w provenance-contract-results.json. Poprawione skrypty nadal czekają na rzeczywiste wykonanie po bazowej generacji.

Sprawdzono metadata 494288/180137 i źródłowy graf bez ciężkiego Pythona. bridge-topology.json oraz BRIDGE-POSE-NOTES.md: kurs 494288309,37 jest blisko osi wiaduktu304–307, nie należy zastępować go kierunkiem sąsiedniej kamery180137. Obejrzano wcześniejszy wykres topologii r2. Zachowano dawne trafienia wysokości jako jawnie historyczne, bez uznania ich za pomiar nowego r3. Następna partia wiaduktowa wymaga kontroli wygenerowanej powierzchni i stacji, nie tylko yaw.

Około 02:59 generacja bazowa uzyskała heavy gpt-sbs-r3 (3/3) i rozpoczęła build_all.py; log pokazuje pierwszy zestaw asphalt_sma_fresh. Następnie ten sam wrapper wykona build_world i zwolni slot w finally. Nie uruchomiono obok drugiego ciężkiego Pythona tej gałęzi.

Przygotowano read-only sample-bridge-surfaces.py (jeszcze nie uruchomiono). Korzysta z read_glb/node_triangles/ray_heights istniejącego tests/gis/route_corridor.py, sprawdzi SHA nowych Low GLB wobec ukończonego baseline. 21 punktów dla stacji/bocznych przesunięć494288 i stacji180137 oraz oryginalnego GPS494288; zachowuje wszystkie poziomy asfaltu zamiast automatycznie wybierać NMT lub najwyższy pokład. Wynik będzie diagnostyką rzeczywistych trójkątów, nie akceptacją kamery.

Po niezależnym odczycie dopracowano proweniencję narzędzia powierzchni: SHA helpera/intrinsics zapisane przed użyciem i sprawdzone na końcu, ponownie kontrolowane bajty odczytanych GLB; usunięto zaszyte U141,888 dla oryginalnego GPS. Algorytm znaków/poziomów nie wymagał korekty. To nadal przygotowanie, bez uruchomienia obok build_all.

Przygotowano compose-gantry-probes.py do późniejszej dzierżawy heavy: galeria 18 par960px, źródła/licencje, offsety, C i brak D51; kontroluje dwie grupy capture, wszystkie siedem migawek wejść, oba SHA obrazu i jeden HEAD. Kopiuje cztery natywne zdjęcia do lokalnej galerii dla przenośności, bez zapisu produkcyjnych źródeł. Skrypt jeszcze nie wykonany; build_all nadal postępuje.

Materiały zakończone: build_all total456s, kod0 potwierdzony przejściem sekwencyjnego wrappera do build_world. Receipt materials-completed.json zapisuje SHA logu i materials_spec. Świat ruszył w tej samej dzierżawie; pierwszy log pass1:16261węzłówpokładu. To licznik generatora, nie ocena obrazu ani nowy wynik bramki.

Przygotowano własny run-heavy.ps1 r3: sekwencyjne PrepareDiagnostics (dwa narzędzia, bez równoległego Pythona), kompozycja, pojedynczy plik testu, fidelity i końcowy GIS wymagający EndOfRound. Każda ścieżka Acquire/Release heavy w finally; parser poprawny. Nie uruchomiono go podczas bieżącej generacji, aby nie odświeżyć tej samej dzierżawy i nie dopuścić drugiego zadania.

Bazowa generacja zakończona kodem 0 i zwolniła heavy: materiały 456 s, świat 413,7 s, brak fallback=True. baseline-completed.json wiąże SHA świata i materiałów; potwierdzono zgodność bieżącego manifestu. Następne niezależne odczyty tej samej migawki: PrepareDiagnostics w heavy oraz import w osobnej puli Unity. Nie ma drugiej generacji ani dwóch ciężkich Pythonów naszej gałęzi.

Import uzyskał Unity gpt-sbs (2/4). PBR preflight: 0 brakujących, 0 przestarzałych; CC0: 13 zasobów, 65 plików, 0 problemów. RegionImporter nadal pracuje. Metadane baseline-vs-r2.json: wszystkie 64 High i 64 Low mają inne SHA w manifestach niż r2; produkcyjne kamery i referencje bez zmian. To porównanie manifestów, nie niezależny audyt wszystkich bajtów. Zmiany świata po merge innych dziedzin nie są efektem SBS. PrepareDiagnostics nadal czeka na heavy (54688); import osobno12781.

Import zakończony kodem 0 i slot Unity zwolniony. import-completed.json potwierdza zgodną migawkę świata i materiałów. Dane WORLD_MEMORY to księgowanie siatek/instancji/źródeł kolizji, nie pamięć procesu ani pomiar urządzenia. Przygotowano i uruchamiamy EditMode r3 przez osobne Acquire/Release gpt-sbs; bez telefonów.

EditMode r3 zakończony kodem 0: 317/317, bez błędów i pominięć, slot Unity zwolniony. XML sprawdzono bezpośrednio; editmode-completed.json zachowuje SHA i liczby. Nie zakładano dawnego wyniku 261, ponieważ nowy main ma więcej testów. Diagnostyka nadal czeka na heavy; nie ma aktywnego Unity naszej sesji.

Dane wygenerowanego portalu zapisano w gantry-model-anchor.json: środek około (-260,771;-208,292), prototyp sign_gantry_16_74 oznacza rozpiętość16m i wysokość7,4m powyżej bazy. To wymiary modelu WORKING_VALUE, nie pomiar realnego obiektu. Aby nie ograniczać prób do szacunku12–20m recenzji, dodano -8m dla obu kamer grobina: partia obejmuje teraz20 hipotez (wcześniej18). Generator i galeria mają zgodne kontrole20; wrapper renderu grupuje plan dynamicznie. Skrypty nie były jeszcze wykonane, PrepareDiagnostics nadal czeka na heavy.

Korekta poprzedniego wpisu: PrepareDiagnostics w międzyczasie uzyskało heavy i zakończyło się kodem 0 na wcześniejszej siatce18, przed edycją do20. Faktyczny wynik sprawdzono: 18 kamer, zgodny SHA planu, 21 punktów powierzchni w3 Low chunkach. Przywrócono oba własne skrypty do zgodnej wersji18; nic nie renderowano ani nie opisano fałszywie jako20. Możliwe -8m pozostaje refinacją po oglądzie pierwszej partii. Receipt diagnostics-prepared.json, slot heavy zwolniony.

Kontrola rzeczywistego planu przed renderem ujawniła natywne separatory Windows w kluczach SHA. Wrapper normalizuje je przed porównaniem z dwoma dozwolonymi plikami, odrzuca też zduplikowane związanie. Rozszerzony check-provenance przyjął oba formaty separatorów i odrzucił osiem podmian. Plan/kamery nie zmieniły się, nadal18hipotez; Unity diagnostyczne jeszcze nie uruchomione.

Render gantry-probes zakończony kodem 0: 18 raw, dwie grupy1280x720/1280x960, jeden HEAD01b4d215, wszystkie SHA PNG zweryfikowane i roster zgodny z planem. Każda grupa miała osobny Acquire/Release Unity; slot zwolniony. To wyłącznie hipotezy C, bez zmiany produkcji i bez oceny D51. Następna kompozycja18 par przez heavy; odczyt powierzchni pokazał różne poziomy przy494288, brak asfaltu przy jego oryginalnym GPS i niższą jezdnię przy180137.

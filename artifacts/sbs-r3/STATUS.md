# SBS r3 — ranking i kalibracja G3-B

Stan 12.11.2026 około 03:34 Europe/Warsaw. Worktree .claude/worktrees/gpt-sbs, gałąź gpt-sbs-r3. Runda zaczęła od zamkniętej r2 962ad111 i merge main 9874d98c jako 31988772. R2 jest dostarczona do main, z końcowym GIS 561 passed, 1 xfailed. Nie scalano naszych gałęzi do main i nie pushowano. Sesja 24 h trwa do około 12.11, 21:31.

## Zakończone

Materiały: kod 0, 456 s. Świat: kod 0, 413,7 s, brak fallback=True. baseline-completed.json wiąże oba SHA; generowany kod świata pochodzi z ff308ea6, późniejsze kroki zmieniały własne artefakty i dokumentację. Import: kod 0, zgodna migawka świata i materiałów; PBR 0 brakujących i 0 przestarzałych, CC0 13 zasobów i 65 plików bez problemów. EditMode: 317/317, brak błędów i pominięć, XML i receipt zapisane.

Wszystkie 64 High i 64 Low mają inne SHA w manifestach niż r2. To porównanie metadanych, nie ukończony audyt bajtów wszystkich 128 siatek. Źródłowe kamery i referencje pozostają identyczne z r2. Zmiany świata po merge innych dziedzin nie są efektem SBS; nie przypisujemy im zerowego kosztu ani poprawy na podstawie samych liczników.

Ranking docs/refs/sbs-priorities.md obejmuje tematy dla wszystkich dziesięciu dziedzin. Rozdziela historyczną pełną ocenę D51 r1, nowszą częściową recenzję 0125 i oczekujący pełny render r3. Nie sumuje ocen z różnych epok. Wstępna kontrola niezależna zaakceptowała ten zakres.

PrepareDiagnostics zakończone kodem 0: 18 hipotez C dla czterech kamer naziemnych oraz odczyt 21 punktów powierzchni w trzech rzeczywistych Low chunkach. Skrypt powierzchni zachowuje wszystkie poziomy asfaltu, wiąże SHA helpera przed importem, intrinsics przed odczytem i sprawdza niezmienność wejść oraz GLB na końcu. Przy oryginalnym GPS 494288 brak trafienia w asfalt; inne przesunięcia trafiają w teren pod mostem albo w pokład około U140 m. Nie jest to akceptacja żadnej nowej pozy.

Render prób: kod 0, 18 raw, dwie grupy 1280×720 i 1280×960, jeden HEAD 01b4d215. Każda grupa miała osobny slot Unity. Wszystkie SHA raw sprawdzone. Kompozycja: kod 0, 18 par po 960 px, pełne źródła i licencje, lokalna galeria gantry-probes/pairs/index.html. Migawka siedmiu wejść, plan i receipt importu są związane z capture. Żadna hipoteza nie zmieniła produkcji.

Obejrzano wszystkie 18 pojedynczych arkuszy, nie tylko overview; gantry-visual-inspection.json zachowuje ich SHA. Dodatkowo obejrzano cztery natywne rendery. Cofnięcie poprawia portal, ale sam przesuw nie wystarcza. W grobinie pozostaje różnica pionowego kadru. Długie przesunięcia zsolta wzdłuż spojrzenia wyprowadzają kamerę ku krawężnikowi; kolejne próby powinny rozdzielić oś przesuwu od kierunku patrzenia. Nie awansowano żadnej klasy. Niezależny sbs_visual_review ogląda obecnie komplet 18 par.

## Poprawki i ograniczenia dowodu

Przegląd przygotowania znalazł dwie luki: kontrolę importu przed czekaniem na slot i brak związania planu z wejściami. Poprawiono je przed Unity. Wrapper kontroluje stan także po Acquire oraz po renderze, plan, receipt, zdjęcia, produkcyjne źródła i wspólny HEAD. Lekki check-provenance zaakceptował zgodne wejścia z oboma separatorami ścieżek Windows i odrzucił osiem podmian. Rzeczywisty render potwierdził działanie wrappera na natywnych kluczach Windows.

Próba rozszerzenia siatki o −8 m nastąpiła, gdy oczekujące przygotowanie zdążyło już skończyć na 18 wariantach. Sprawdzono rzeczywisty wynik i przywrócono zgodną wersję skryptów. Nie opisywano 18 klatek jako 20. Wariant −8 m pozostaje do ewentualnej następnej próby. gantry-model-anchor.json zawiera faktyczny model sign_gantry_16_74: rozpiętość 16 m, wysokość 7,4 m nad bazą. To wymiary modelu WORKING_VALUE, nie pomiar realnego obiektu.

Poprawiona projekcja na graf: najbliższa oś wiaduktu przy 494288 ma około 306,99°, blisko zapisanego kursu 309,37°. Nie przenosić kursu kamery 180137 z innej drogi. Stare raycasty zachowano jako historyczną wskazówkę; nowy bridge-surface-survey.json jest osobnym wynikiem z aktualnych bajtów siatek. Kamery na pokładzie nie mogą używać w ciemno NMT.

## Dalej

Po niezależnym przeglądzie: kolejna ograniczona partia prób, przegląd własny i niezależny, dopiero potem uzasadnione zmiany własnych danych SBS. Następnie pełne odświeżenie 42 par Low/High × clear/overcast na tej bazie, metryki, liczniki geometrii i instancji osobno, aktualizacja rankingu i latest. Ostatnia pełna seria r2 jest z około 00:19; kolejne pełne odświeżenie zaplanować najpóźniej około 06:19.

Fidelity, pełny GIS r3 i końcowy audyt 128 siatek/całej serii nie są jeszcze wykonane. Pełny GIS tylko na końcu rundy, w trakcie pojedyncze pliki. Potem ADR 0111 r3, REPORT normalnym polskim tekstem, robocopy artefaktów do main i od razu r4 z merge main.

Nie ma aktywnego Unity ani ciężkiego Pythona naszej sesji. Ostatnie uchwyty zakończone: baseline 1171, przygotowanie 54688, import 12781, EditMode 62910, render 40279, kompozycja 33915 — wszystkie kod 0. Każdy proces miał właściwy slot i Release. Ciężki Python: heavy gpt-sbs-r3, Unity: gpt-sbs; cudzych slotów i PHONE_RUN nie ruszamy.

Pozostają niezatwierdzone pochodne generatora poza SBS: far_field_qa.json, viaduct_putry_underdeck.spec.json, streetscape_qa.json, world_manifest.json, far-field manifest, props_meta.json i street_props.glb. Przywrócić dokładne pliki po końcowej walidacji, zachowując migawki dowodów. Świat, runtime, shadery, znaki i pliki Claude są poza zakresem edycji SBS.


Niezależny przegląd18/18 zapisany w REVIEW-GANTRY-INITIAL.md: wszystkie C. Wskazuje grobin275528 −8…−12m i kontrolę pionowego kadru,837235 −16…−20m z bocznym położeniem, zsolt po właściwej osi jezdni. Naprawiono pomocniczą projekcję PowerShell na odcinki: pierwotna mogła zaokrąglać do końców. Sanity (u=0,25, odległość3m) poprawne; nowe odległości:4942881,69m od osi wiaduktu,3281352,90m od osi trunk,2978170,50m. Kamery i18raw nie korzystały z błędnego pomocnika; własne skrypty NumPy były niezależne. Nowy inspect-road-topology.ps1 i poprawiony JSON są dowodem do kolejnej rodziny prób.

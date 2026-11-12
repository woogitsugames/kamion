# SBS r3 — ranking i kalibracja G3-B

Stan 12.11.2026 około 09:17 Europe/Warsaw. Worktree .claude/worktrees/gpt-sbs, gałąź gpt-sbs-r3. Runda zaczęła od zamkniętej r2 962ad111 i merge main 9874d98c jako 31988772. R2 jest dostarczona do main, z końcowym GIS 561 passed, 1 xfailed. Nie scalano naszych gałęzi do main i nie pushowano. Sesja 24 h trwa do około 12.11, 21:31.

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


Niezależny przegląd 18/18 zapisany w REVIEW-GANTRY-INITIAL.md: wszystkie C. Wskazuje grobin 275528 −8…−12 m i kontrolę pionowego kadru,837235 −16…−20 m z bocznym położeniem, zsolt po właściwej osi jezdni. Naprawiono pomocniczą projekcję PowerShell na odcinki: pierwotna mogła zaokrąglać do końców. Sanity (u=0,25, odległość 3 m) poprawne; nowe odległości:494288 — 1,69 m od osi wiaduktu,328135 — 2,90 m od osi trunk,297817 — 0,50 m. Kamery i 18 raw nie korzystały z błędnego pomocnika; własne skrypty NumPy były niezależne. Nowy inspect-road-topology.ps1 i poprawiony JSON są dowodem do kolejnej rodziny prób.

Wznowienie 12.11 o 09:04: od ostatniego zapisu około 03:42 nie ma nowych wykonanych zadań w repo; przyczyna przerwy nieustalona. Pełne odświeżenie nie odbyło się w planowanym terminie około 06:19. Main przeszedł z9874d98c do14ccbaf1 tylko przez obsługę priorytetowych slotów, integracyjne wrappery i handover, bez zmiany źródeł świata/materialów. Merge do r3 jako0c4afdaa. Aktualna wygenerowana i zaimportowana migawka nadal odpowiada źródłom świata main. Najpierw pełne168raw w czterech stanach, potem dalsza kalibracja. Nie usuwamy cudzych slotów ani rezerwacji, używamy canonical slot script z main.

Pełne odświeżenie około 09:06–09:09 zakończone kodem 0: wszystkie168 PNG sprawdzone po SHA,8grup,42klatki w każdym z4stanów, jeden HEAD62d45b92. full-capture-audit.json i full-render-completed.json zachowują dane. Produkcyjne kamery bez zmian, świat odpowiada aktualnemu main14ccbaf1 (od poprzedniej generacji tylko zmiany ops). Następnie pełna kompozycja przez jedną dzierżawę heavy, z diagnostyką C i jawną kwalifikacją starych masek.

Druga rodzina przygotowana jako osobne artefakty make-refinement1.py, render-refinement1.ps1 i compose-refinement1.py. Maksymalnie 30 prób: 12 dla 275528 (−8/−10/−12 m, h 0,52/0,55, oko 1,7/2,2 m), 6 dla 837235 (−16/−20 m, lewo −2/0/+2 m, h 0,52), po 6 dla obu kamer zsolta na osi właściwej jezdni. Kamera 328135: −60/−75 m i lewo −2/0/+2 m; 297817: −60/−75/−90 m i lewo 0/+2 m. Wysokość z rzeczywistego road_asphalt i ciągłego profilu; brak trafienia lub skok ponad 1 m powoduje jawne odrzucenie. Rzeczywista liczba klatek może być mniejsza niż 30. Wszystkie C, bez zapisu produkcyjnych kamer. Składnia dwóch Pythonów i wrapperów PS sprawdzona; niezależny przegląd kodu w toku. Nie uruchamiać PrepareRefinement, dopóki ComposeOnly 95614 nie skończy, ponieważ używają tej samej nazwy dzierżawy heavy.

Lekkie parsowanie tekstowych statystyk dało 168 wierszy liczników z oddzielnymi instancjami w counters/. Nie jest to ciężka generacja ani wynik GPU. Pełna kompozycja 100 B i diagnostyki nadal czeka na heavy. Pełny render 41521 zakończony kodem 0, slot Unity zwolniony.


Niezależny odczyt drugiej rodziny potwierdził kierunki i poziomy; uzupełniono guard kodów zakończenia baseline. summary.json w counters/ opisuje wszystkie 168 wierszy, osobne statyczne i instancje oraz zakres delty wobec r2. Nie jest to izolowany koszt SBS ani wynik telefonu. Nowe przygotowanie nadal nie zostało uruchomione, ponieważ pełna kompozycja czeka na tę samą pulę heavy.

Obejrzano cztery natywne raw świeżej serii i trzy odpowiadające zdjęcia: A201270/A139889 Low-overcast oraz A303305 Low/High-clear. Zapisano FRESH-SPOT-REVIEW.md i ledger SHA. Potwierdzono brak najbliższych podpór i bariery/nasypu; tablica z nazwą ronda już jest. Klin nad halami i brak grupy bloków po lewej nadal widać w A303305 w obu tierach. Zaktualizowano tylko te wiersze rankingu; bez nowego formalnego D51 i bez twierdzenia o obejrzeniu całej serii.

Przygotowano wstępne udostępnienie świeżej serii: cztery podstawowe migawki wejść w prestage-source-bindings mają SHA zgodne z capture. Kopia raw, liczników i przeglądu czterech klatek do main będzie oznaczona jako częściowa, bez REPORT i bez ukończonego GIS r3. Pełna kompozycja nadal czeka na heavy; nie uruchamiamy drugiej dzierżawy o tej samej nazwie.

Wstępna kopia do main zakończona: raw, liczniki i cztery migawki wejść, trzy kody robocopy 1. Sprawdzono SHA wszystkich 168 PNG w docelowym main oraz siedmiu kluczowych plików. prestage-receipt.json ma jawny stan PRESTAGE_NOT_FINAL_DELIVERY; brak REPORT i końcowego GIS r3. Bieżący STATUS skopiowano jako informację o postępie.

Pełna kompozycja zakończona kodem 0: 100 arkuszy B i 168 diagnostycznych, bez brakujących renderów. Każdy stan ma 25 B i 42 diagnostyczne. Migawka inputs i ZIP zapisane, slot heavy zwolniony. Podczas sprawdzania odpytywania kolejka sama uzyskała slot; nie zatrzymano żadnego procesu i nie zmieniono interwału. Teraz można uruchomić PrepareRefinement w nowej, osobnej dzierżawie tej samej gałęzi.

Raport latest przebudowany: 3 rundy i 8 porównań stanów. Kontrola Playwright 1280×960 oraz 390×844 przeszła; szerokość dokumentu odpowiednio 1280/390, przełączniki rund i stanów, C 42 karty, skrót trendu, załadowane obrazy bez braków, konsola 0 błędów i 0 ostrzeżeń. R2 Low-clear zachowuje 3 sprawdzone próbki; R3 ma 0 i jawny brak porównywalnych danych. D51 nadal jawnie odnosi się do r1. Zrzuty obejrzano i zapisano w ui-review; przeglądarka oraz serwer zamknięte. Nie oznacza to końcowego GIS ani zaliczenia świata. PrepareRefinement 40244 nadal czeka na heavy.

PrepareRefinement zakończone kodem 0 i zwolniło heavy: 28/30 prób, dwie 328135 odrzucone za brak asfaltu na profilu. To oba warianty boczne +2 m, przy −60 i −75 m. Nie zastąpiono wysokości NMT ani krańcowym punktem ścieżki. Rzeczywisty roster: 275528 — 12, 837235 — 6, 328135 — 4, 297817 — 6. Plan i SHA kamer sprawdzone, wszystkie C. Galeria jasno rozróżnia oś jezdni i kierunek spojrzenia. Następnie render dwóch proporcji obrazu, bez zmian produkcyjnych kamer.

Render drugiej rodziny zakończony kodem 0: 28/28 przygotowanych raw, dwie grupy proporcji, jeden HEAD dd92f5c7. Wszystkie SHA PNG i roster sprawdzone; dwa wcześniejsze odrzucenia pozostają jawne w planie i galerii. Slot Unity zwolniony. Niezależny przegląd pełnej bazowej kohorty 25 B (przed nowymi korektami) dał 13 rozpoznawalnych, 11 częściowych i 1 nierozpoznawalny, nadal FAIL. Nie jest to akceptacja 28 prób C ani wynik telefonu.

Zapisano kompletną niezależną ocenę baseline w REVIEW-D51-BASELINE.md: G3-A 11/4/0, G3-B 2/7/1, razem 13/11/1, nadal FAIL. Kandydat recognition-r3-baseline.json wiąże wszystkie 25 ocen z SHA zdjęcia, raw i arkusza oraz zachowuje r1 w historii. Nie nadpisano jeszcze Data/sbs_recognition.json: raport musi najpierw wybierać właściwą ocenę historyczną według obu SHA, aby nowa opinia r3 nie zastąpiła treści przy starych r1/r2. Nowe próby pozostają osobnymi C. Obejrzano dodatkowo cztery natywne raw drugiej rodziny; nie jest to jeszcze przegląd wszystkich 28 par.

12 listopada, 10:12: dodałem wybór wersji oceny D51 według obu skrótów obrazu (zdjęcie i render). Starsze rundy mogą korzystać z historycznej oceny; przy braku zgodnych pikseli raport pokazuje ocenę ze snapshotu danej rundy i jawne zastrzeżenie. Przygotowałem testy historii, pierwszeństwa najnowszej oceny, snapshotu oraz błędnych danych. Testy pojedynczego pliku czekają na zakończenie bieżącego składania porównań; nie uruchamiam drugiego ciężkiego zadania z tym samym właścicielem slotu.

10:13: niezależny recenzent wskazał lukę przy braku snapshotu lub kamery w snapshocie: wtedy raport mógł jeszcze pokazać przyszłe uzasadnienie z ostrzeżeniem. Usunąłem ten fallback; bez zgodności pikseli i bez oceny w snapshocie karta pokazuje brak oceny. Dodałem dwa przypadki testowe i zachowanie daty źródłowego przeglądu. Testy nadal nieuruchomione, czekam na zakończenie jedynego własnego zadania heavy.


2026-11-12T10:14:53.4571183+01:00: obejrzałem wszystkie 25 arkuszy Low-clear; zapisałem przegląd i SHA. Ranking odstępstw uwzględnia teraz pełny niezależny Low-overcast i własny pełny Low-clear. Podgląd historii raportu: 25/25 zgodnych ocen r1, 19/25 r2, 25/25 r3 w Low-overcast. To kontrola danych, nie wynik pytest ani QA nowego HTML.

2026-11-12T10:17:06.5989862+01:00: zakończyłem własny przegląd obu stanów High po 25 arkuszy. Własne pokrycie bazowe: 75 B (Low-clear + oba High); niezależny recenzent: 25 B Low-overcast. Łącznie obejrzano 100 unikalnych B. Różnicę kratownicy B297817 Low/High zapisałem jako osobny problem LOD, bez przypisywania go wyłącznie pozie. Kolejka kompozycji nadal oczekuje na heavy, bez uruchamiania następnego ciężkiego procesu.

2026-11-12T10:20:53.9967717+01:00: niezależny przegląd kodu historii ocen PASS (bafa7544), testy nadal oczekują. Podgląd HTML z kandydatem przeszedł 12 przełączeń runda/stan, C=42 oraz 1280/390 px bez poziomego przepełnienia. Obejrzałem dwa aktualne screenshoty; konsola 0 błędów i ostrzeżeń. Zapisałem ui-history-review/RESULT.json ze skrótami. Pierwszy selektor etykiety nie zadziałał; poprawiona kontrola przez istniejące identyfikatory zakończona. Przeglądarka i serwer zamknięte. Data i latest nadal bez tej publikacji.

2026-11-12T10:22:10.6670075+01:00: przygotowałem audyt r3 bazujący na sprawdzonym audycie r2, bez ponownego składania galerii. Sprawdzi docelowo 168 raw, 100 B, 168 diagnostycznych, ZIP wejść, 128 rzeczywistych GLB i powiązanie nowego D51 z parami. To na razie skrypt, nie wynik uruchomienia; task Audit będzie pod heavy po zakończeniu obecnej kompozycji.

2026-11-12T10:22:51.0994521+01:00: drugie prestage do main/artifacts/sbs-r3: komplet 100 arkuszy B i 168 diagnostycznych oraz wejścia ZIP i nowe recenzje. Zweryfikowano SHA wszystkich 268 skopiowanych PNG. To nie końcowy raport ani zgoda na zamknięcie rundy; latest bez zmian. Nie wykonano merge/push. Kompozycja i późniejsze testy nadal czekają na heavy.

2026-11-12T10:27:11.5515251+01:00: kompozycja 28 par zakończyła się exit0 i zwolniła heavy. Obejrzałem wszystkie 28 par; niezależny recenzent obejrzał wszystkie 28 raw i cztery zdjęcia z kontrolą SHA. Najlepsze C: 275528 warianty 02/04 bez rozstrzygnięcia, 837235-12, 328135-21, 297817-26. Brak dwóch jednoznacznych kotwic oznacza zero promocji do produkcji. Wynik i następne minimalne kroki zapisane w REVIEW-REFINEMENT1.md. Teraz jedyny własny ciężki task to pojedynczy pytest raportu, sesja 55346, nadal czeka na slot.

2026-11-12T10:31:09.6211459+01:00: natywna kontrola dwóch najlepszych prób po osi drogi potwierdziła konflikt pionowej projekcji dalszej jezdni i portalu. Zapisałem szerokie, jawnie robocze pasma y, SHA obrazów i minimalną następną próbę pitch przy stałym XY do r4. Nie zmieniam produkcyjnych kamer bez dwóch kotwic. R3 przechodzi do końcowej walidacji po obecnym pojedynczym teście raportu; nie dodaję kolejnej szerokiej siatki.

2026-11-12T10:33:00.3547736+01:00: dodałem sekcję r3 do ADR 0111 z jawnym statusem trwającej walidacji. Wymienia wykonane dowody, brak awansu C, nową ocenę bazową, ograniczenie trendu i pozostałe testy. Nie oznacza zamknięcia rundy.

2026-11-12T10:33:35.8799391+01:00: pojedynczy pytest tests/gis/test_sbs_report.py zakończony exit0, 34 passed in0.31s, heavy zwolniony. Następny task Audit (sesja75884) czeka na heavy. Po testach wprowadziłem wersjonowany rejestr ocen do Data/sbs_recognition.json i odbudowałem własny latest z trzech rund; historyczne wejścia renderów pozostały bez zmian. Wynik r3 FAIL13/11/1, brak akceptacji C.

2026-11-12T10:33:55.7096293+01:00: własny latest porównałem strukturalnie z podglądem faktycznie sprawdzonym w przeglądarce. Jedynymi różnicami są czas generacji i niewyświetlana notatka rejestru; rundy, oceny par, trendy i werdykt identyczne. Zapisałem SHA latest i wynik równoważności, bez sugerowania ponownego renderu świata.

2026-11-12T10:37:00.2741809+01:00: do przyszłego tasku Fidelity dopisałem uzupełniający audyt 268 arkuszy: dekodowanie i szerokość960, wszystkie tożsamości diagnostyczne oraz zgodność bieżącego rejestru z ocenionym kandydatem. Obecnego audit_final.py nie zmieniałem; nadal czeka w sesji75884. Nowy skrypt będzie wykonany przed fidelity w tej samej przyszłej dzierżawie heavy, bez równoległych właścicieli.

2026-11-12T10:37:55.5661695+01:00: niezależny przegląd audytu wskazał dodatkowo brak jawnej unikalności rosterów, liczników, chunków i ocen oraz rozróżnienia oceny archiwalnej od bieżącej. Uzupełniłem audit_sheets.py o te kontrole, zgodność diagnostyki z raw/zdjęciami i manifestami metryk, kompletność wykluczeń oraz przeliczenie counts. To nadal przygotowany skrypt do uruchomienia pod heavy po obecnym audycie; brak nowego wyniku wykonania.

2026-11-12T10:39:36.2720646+01:00: sprawdziłem aktualny main f560cbd19362d32f5916a988436145efa580c435 i nowe recenzje s12. Main ma już kolejne domeny i regenerację; r3 ich nie przedstawia. Zapisany jawny zakres dowodów oraz plan odświeżenia r4. Nie mieszam nowych wejść z capture r3 podczas końcowej walidacji. Testy raportu34PASS, audyt nadal ta sama żywa sesja75884 w kolejce heavy.

2026-11-12T10:42:00.9307748+01:00: audyt główny zakończony exit0, 168 raw, 100 B, 168 diagnostycznych, 128 rzeczywistych GLB i168 liczników zweryfikowane. Heavy oddany. Uruchomiłem następny task Fidelity, który najpierw wykona uzupełniony audyt arkuszy, następnie fidelity w jednej dzierżawie; nie uruchamiam równoległego zadania heavy.

2026-11-12T10:42:33.1801662+01:00: audyt pokazał 38/84 Low ze wzrostem draws i22/84 z delta tris>2% versus r2. Zapisałem BUDGET-LIMITATIONS.md; r3 nie deklaruje PASS budżetu wspólnego świata. Kamer produkcyjnych ani runtime SBS nie zmieniono, wzrost dotyczy nowej zintegrowanej bazy. Nie przypisuję go bez analizy konkretnej domenie ani nie poprawiam cudzych plików.

2026-11-12T10:44:15.4802484+01:00: przygotowałem REPORT-DRAFT.md jako konkretny projekt do kontroli przed zamknięciem. Wprost oznacza brak wyników fidelity/końcowego GIS i niewykonaną końcową dostawę, więc nie zastępuje REPORT.md. Utrwala koszty, porównania, zero akceptacji C oraz brak pokrycia pierwszych300m.

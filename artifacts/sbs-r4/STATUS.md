# SBS r4 — stan pracy

Start: 12 listopada 2026, około 11:58. Gałąź gpt-sbs-r4, ten sam worktree gpt-sbs. R3 zamknięta i dostarczona: bd5edafb, GIS665+1xfail, EditMode317, D51 nadal FAIL13/11/1, zero awansów C.

R4 zaczęła się od poprzedniej rundy i merge aktualnego main 0023f39d, commit scalenia664fd272, bez konfliktów. Main zawiera już pakiety A+B+C, w tym poprawkę klina nieba light r3 i edge r4. Dowody r3 nie są dowodami tej nowej bazy. Nowa runda wymaga materiałów, świata, importu i pełnej świeżej serii przed oceną zmian.

Nowe zasady zasobów przeczytane w skrypcie main i GPT-FEEDBACK-S10: FIFO, bez -Priority dla GPT; heavy oddawany po każdym kroku. Unity nadal właściciel gpt-sbs zgodnie z poleceniem użytkownika, ciężki Python właściciel gpt-sbs-r4. Nie usuwamy cudzych slotów ani PHONE_RUN.

Zakres: pozy297817/328135 jako pierwsze, potem mała próba275528 i osobne kadrowanie494288/180137 z ponownym rozróżnieniem widocznej powierzchni od kolizji. Wszystkie nowe próby C do niezależnej kontroli dwóch kotwic. Dodatkowo poprawić wskazane przez lidera składanie z historycznymi wejściami i jawne zachowanie zagnieżdżonej dzierżawy heavy, zachowując kontrolę SHA.

Nowszy HANDOVER opisuje restart komputera03:44 i start hosta09:01 jako przyczynę przerwy. To informacja z dziennika lidera, odczytana dopiero po zamknięciu r3; własny raport r3 wcześniej nie przypisywał nieznanej przyczyny.

Nie wykonano merge do main, push, telefonu ani edycji innych dziedzin. Odświeżenie prywatnych kopii cache i git lfs checkout poprzedza generację, aby nie dopuścić do fallbacków.

2026-11-12T12:00:00.6770175+01:00: pięć prywatnych cache odświeżonych, robocopy bez błędów, LFScheckout0. Poprawiłem wyłącznie pole pochodzenia w receipcie: helper błędnie pytał o drugiego rodzica późniejszego WIP, zamiast commitu scalenia664fd272. Potwierdzony rodzic main0023f39d. Kopii nie powtarzano; żaden generator jeszcze nie ruszył.

2026-11-12T12:00:39.2839154+01:00: przygotowany i uruchamiany build-baseline.ps1: materiały i świat mają osobneAcquire/Release w FIFO, bez Priority. Zapisze dwa receipty i po zgodności SHA specyfikacji wspólny baseline. Nie wykonuje Unity ani pełnego GIS; te etapy dopiero po generacji.

2026-11-12T12:06:21.3396005+01:00: zaimplementowałem strict compose z wybranej migawki bez osłabiania trybu provenance. RenderOnly zapisuje wejścia bez starych metryk; ComposeOnly domyślnie czyta OutputRoot/inputs. Heavy zwalniany po każdym stanie; zagnieżdżenie bez jawnego HeavyLeaseOwner kończy się od razu błędem. Jawna pożyczona dzierżawa obejmuje jeden stan i wiąże niezmienny rekord właściciel+czas przed/po, bez Release przez borrower. Niezależny przegląd planu wskazał ten warunek tożsamości, uwzględniony. ParserPSprzeszedł; testy nowych zachowań są jeszcze do przygotowania i wykonania po terminalu generatora77049, żeby nie uruchamiać dwóch zadań z tym samym ownerem.

2026-11-12T12:09:01.9222708+01:00: przygotowałem11 nowych przypadków w pojedynczym pliku test_sbs_gate3.py: strict snapshot mimo nieczytelnego live, cztery zmienione źródła, cztery brakujące źródła, brak capture i mieszane epoki. Strict snapshot wymaga wszystkich4 plików wejściowych. Testów jeszcze nie uruchomiono; baseline77049 w kolejceFIFO. Kolejny krok to izolowane testy PowerShell dzierżawy i publikacji wejść.

2026-11-12T12:11:01.7574500+01:00: przygotowałem6 izolowanych testów orkiestracjiPowerShell w test_sbs_evidence_script.py. Używają tymczasowego repo i atrap slotu/kompozytora, bez Unity i globalnych locków. Pokrywają dwa osobne stany z Release, zachowanie migawki mimo dirtylive, jawnyborrow, odrzucenieukrytegoborrow, podmianęrekordu tego samego ownera i brak obowiązkowego wejścia. Testy jeszcze niewykonane; realnybaseline77049 pozostaje jedynym własnym zadaniem heavy.

2026-11-12T12:18:27.4313599+01:00: zamknąłem dwa blockery przeglądu: ComposeOnly nie ma fallbacku do live przy braku katalogu migawki; sealing wymaga pełnych grup aspektów, unikalnego rosteru kamer i hashy, właściwego stanu i epoki oraz zgodnych SHA i wymiarów PNGraw, bez czytania starych metryk. Rozszerzyłem izolowane testy do12 przypadków, w tym faktyczna ścieżka RenderOnly z atrapą renderera oraz podmiana raw/stanu, duplikat i brakcapture. Bez prawdziwego Unity i globalnych locków. Testy jeszcze niewykonane; generator77049 nadal w FIFO.

2026-11-12T12:20:39.4069548+01:00: sealing sprawdza także roster hashy i jednolitą bazę main całej serii. Izolowane testyPSobejmują teraz15 przypadków, w tym błędne wymiaryPNG przy zgodnym SHA, zduplikowane kamery i mieszane main_sha między stanami. ASTPython i parserPSbez błędów; nadal nie wykonano pytest. Generator77049 pozostaje jedynym własnym taskiemheavy.

2026-11-12T12:24:26.6507474+01:00: niezależny recenzent potwierdził zamknięcie obu blockerów(strict ComposeOnlybezlivefallback i pełny sealingcapture/raw). Warunkowy PASS kodu, bez deklaracji wyniku testów lub jakości świata. FIFO generacji spadło do jednego wcześniejszego zgłoszenia; monitoruję tę samą sesję77049, bez dodatkowych heavyjobów.

2026-11-12T12:30:55.3660397+01:00: przygotowałem make-controlled-probes.py z15 próbami C i kontrolami. Czyta widoczną jezdnię z road ORAZ bridge i rozdziela kolizje; source meshing.py:133 jawnie eksportuje nawierzchnię pomostu do bridge, którego stary sampler nie badał. Wszystkie poziomy i odrzucone hipotezy zostaną zapisane. Bez NMT/topmostfallback i bez zapisów produkcyjnych. Skrypt jeszcze niewykonany: wymaga zakończonej nowej bazy i osobnego heavy po terminalu77049.

2026-11-12T12:32:58.2020705+01:00: Potwierdzono SHA produkcyjnych kamer/referencji nadal zgodne z bazą hipotez r3. Nowy sampler ma poprawną składnięAST; zachowa plan odrzuceń także przy zerze kandydatów i wymaga jawnego braku fallbacków bazy. Dodałem źródłowe powiązanie eksportu nawierzchni bridge. Żaden nowy ray ani render jeszcze nie wykonany.


2026-11-12T12:35:49.6345987+01:00: materiały uzyskały heavy FIFO, generator pracuje. Przygotowałem prywatne wrappery importu i kontrolowanych renderów r4; delta przesunięcia jest jawnie względem odziedziczonej kontroli, a poziom oka będzie ponownie osadzony na świeżej widocznej jezdni. Bez uruchomienia drugiego zadania heavy ani Unity.

2026-11-12T12:36:16.6686306+01:00: niezależny przegląd samplera PASS w zakresie kodu, bez uruchomienia. Przygotowane również wrappery pełnej serii i EditMode. ComposeOnly będzie korzystać wyłącznie z zapisanych wejść, bez podmiany adnotacji na pliki live. Nowe helpery dodaję jawnie force, ponieważ artifacts jest ignorowane; poprzedni commit45396e97 zapisał tylko śledzony STATUS.

2026-11-12T12:36:49.5422890+01:00: przygotowany run-heavy.ps1 r4, bez Priority, z ochroną przed już zajętym slotem lub własnym biletem kolejki. Każde wywołanie obejmuje jeden testplik lub jeden etap i zapisuje exitcode przed Release. Nie uruchamiano go równolegle z baseline77049.

2026-11-12T12:39:26.9379522+01:00: generator Materials zakończony exit0; osobny heavy zwolniony. Szczegóły i SHA w receipcie kroku.

2026-11-12T12:39:35.4060595+01:00: prywatne próby wiążą teraz także materials_spec z planem i importem, zachowują main_sha i sprawdzają pełny unikalny roster raw przy składaniu. Jest to przygotowanie kodu, nie wynik renderu. W chwili zapisu zakończenie materiałów już nastąpiło; poniższy receipt potwierdza wynik.


2026-11-12T12:39:50.3809308+01:00: potwierdzono Materials exit0, 505 s w logu, spec SHA c552a473. Source HEAD3a1e398c; późniejsze commity dotyczyły jedynie SBS i helperów, nie źródeł materiałów. Heavy zwolniony12:39:26, World ma nowy bilet FIFO (6 wcześniejszych). Ten sam proces orkiestracji77049, bez nowego heavyjobu.

2026-11-12T12:40:28.0841969+01:00: zapisałem protokół kontroli 15 prób: oddzielna ocena zbiegu jezdni i portalu/ekranu, historyczne regiony tylko WORKING_VALUE. Pitch poprawiający jezdnię kosztem ekranu nie oznacza zaliczenia. Nowe obrazy r4 jeszcze nie powstały; World nadal w FIFO.

2026-11-12T12:44:49.3771232+01:00: zapisano migawkę recenzji pakietu C i SHA. W sbs-priorities jawnie rozdzielono historyczny ostry klin r3 od poprawki light i pozostałego miękkiego pasa nieba. Nowy wspólny dowód SBS pozostaje pending; bez przenoszenia werdyktu z cudzych kadrów. World nadal kolejkaFIFO.

2026-11-12T12:48:56.8311771+01:00: wszystkie prywatne wrapperyPSr4 bez błędów parsera; oba nowe skrypty kontrolowanych prób bez błędówAST. To wyłącznie lekka kontrola składni, bez wykonania generatora, rayów, pytest ani Unity. World77049 pozostaje aktywny i czeka w FIFO, obecnie2 zgłoszenia przed nim.

2026-11-12T12:51:59.5366756+01:00: świeże pojedyncze zapytanie Commons zwróciło16 rekordów metadanych;7 nie było w lokalnym manifeście. Lekka projekcja współrzędnych na G3-A wykazała, że wszystkie7 leży przy stacjach317–437 m lub dalej od korytarza. W pierwszych300 m i do35 m od osi pozostają wyłącznie dwa znane źródła229,676 i248,704 m. Nie pobrano nowych zdjęć, nie zmieniono produkcyjnych referencji ani oceny pokrycia0–200 m. Zapisano odpowiedźAPI i źródłowe SHA klasyfikacji.

2026-11-12T12:54:22.6491094+01:00: API oryginałów obu Commons ujawniło EXIF:27 mm eq,3,6 mm,4608×2592,Orientation1,bez kierunku. Dla109685822 geotagCommons różni się odGPSoryginału; wysokości172/0m nie używamy do oka. Pełna odpowiedź i ograniczenia zapisane. Brak automatycznej zmiany FOV/pozy lub awansu C; miniatury nadal bezEXIF. World77049 aktywny wFIFO.

2026-11-12T12:54:49.3682273+01:00: doprecyzowano ograniczenie EXIF: metadane aktualnej wersji Commons nie są jeszcze związane bajtowo z lokalną miniaturą. Przed wykorzystaniem do kalibracji potrzebna kontrola wersji obrazu i SHA. Odczyt metadanych sam tego nie dowodzi.

2026-11-12T12:58:13.4233885+01:00: zamknięto ograniczenie powiązania EXIF z obrazem: obie aktualne miniatury3840×2160 mają identyczne SHA256 jak lokalne referencje, metadataAPI przed/po identyczne i niezmienne SHA1oryginałów. Odrzucenia preflight(host i rozmiar) zachowane; jedno udane pobranie każdej miniatury,3 686 648B łącznie, bez dekodowania lub nowych obrazów wgit. Nie potwierdza to GPS ani poza/FOV; brak zmian produkcyjnych. World ma1 zgłoszenie przed sobą.

2026-11-12T13:00:40.7790198+01:00: osiem odpowiedzi/receiptów metadanych zamknięto w reference-metadata-evidence.zip z SHA każdego wpisu. Archiwum nie zawiera obrazów i zachowuje dokładne bajty mimo normalizacji końców linii przez Git. To dowód źródłowy, nie ocena pozy lub D51.

2026-11-12T13:02:29.3985455+01:00: nagłówki przyszłych arkuszy rozróżniają KONTROLĘ od PRÓBY, a stopka pokazuje widoczny node/material i zmianęU od źródła. Dzięki temu ponowne osadzenie oka nie jest ukryte za etykietą kontroli. Obrazów r4 nadal nie oceniano; World osiągnął planowanie98 posesji i28 obniżeń krawężnika.

2026-11-12T13:06:15.5316847+01:00: generator World zakończony exit0; osobny heavy zwolniony. Szczegóły i SHA w receipcie kroku.

2026-11-12T13:07:38.6749324+01:00: baseline77049 terminal exit0, świat505,9s,64chunkiHigh+Low,bezfallbackTrue; pełny receipt5f90bdb1/c552a473. Pojedynczy testcore uruchomiono przez FIFOheavy w sesji55690, obecnie8 wcześniejszych zgłoszeń. Import świeżego świata uruchamiam niezależnie przez Unitygpt-sbs; testcore pisze wyłącznie do tmp i czyta repo, nie zmienia świata. Nie uruchamiam drugiego heavy z tym ownerem.

2026-11-12T13:09:35.9178668+01:00: importUnity79443 zakończony exit0, źródła5f90bdb1/c552a473 zachowane; slotgpt-sbs zwolniony, efekty Rendering/Settings iProjectSettings cofnięte. Uruchamiam pełne168raw Low/High×overcast/clear na jednymHEAD, bez commitów w trakcie capture. Nowe testycore iPSpozostają do wykonania; same raw nie oznaczają akceptacji narzędzia ani świata.

2026-11-12T13:13:24.4180197+01:00: pełnyRender42988 terminalexit0. Wszystkie168 raw naHEAD80159a70, świat5f90bdb1 i materiałyc552a473; Save-EvidenceInputs zapisał i sprawdził kompletcapture/raw/roster/SHA oraz inputs.zip. Unityslotzwolniony, efekty ustawieńcofnięte. Końcowy audyt nadal do wykonania, D51 nieocenione. Testcore55690 nadalFIFO(przed7, rezerwacjalead-s12-e), bez drugiegoheavy.

2026-11-12T13:14:26.5189107+01:00: po zakończeniu pełnego capture zamknąłem potwierdzony przez recenzenta przypadek istniejącego biletuFIFO: wspólny guard sprawdza slot i wait przy starcie oraz bezpośrednio przed każdym własnym Acquire. RenderOnly nie dotykaheavy; borrowed zachowuje swoje warunki. Dodałem5 izolowanych przypadków: istniejącybilet, slot/bilet pojawiający się podczasUnity, bilet między stanami, RenderOnly obok kolejki. ParserPS/ASTOK; pytest jeszcze niewykonane. Guard nie jest atomową blokadą wszystkich klientów canonical; własne orchestration pozostają sekwencyjne.

2026-11-12T13:14:58.5839031+01:00: kolejny niezależny etap to EditMode na świeżo zaimportowanym świecie, z osobnym Unityslotgpt-sbs i przywróceniem efektów ustawień. Nie uruchamiam dodatkowegoheavy; testcore55690 nadal jedyny własny wFIFO. Fullraw pozostają zamrożone na80159a70; późniejszy guard dotyczy wyłącznie orchestration SBS.

2026-11-12T13:17:33.7543210+01:00: własny przegląd4 świeżych nativeclear(294859/303305×Low/High) potwierdził brak ostrego klina i pozostały miękki szary pas; w303305 nadal brak właściwej panoramy bloków.294859C,303305B; brak nowegoD51. SHA obejrzanychraw i zdjęć sprawdzone zcapture. Niezależny przegląd actualguardcc23f5f4 PASS w zakresie kodu/fixture, nie wyniku testów; PSma20przypadków i nadal niewykonane. Aktualizacja priorytetów jawnie ograniczona do4klatek.

2026-11-12T13:19:24.9772670+01:00: EditMode 366/366 Passed, bez błędów i pominięć. Sesja 67651 zakończona kodem 0; slot Unity zwolniony, śledzone pliki game czyste, świat zachował SHA bazy. Źródła runtime nie zmieniły się od startu testów c29c873d; kolejne commity dotyczyły dokumentacji SBS. XML i receipt zapisane. Pojedynczy test core 55690 nadal czeka w FIFO, sześć wcześniejszych zgłoszeń.

2026-11-12T13:22:58.8893913+01:00: komplet 168 liczników odczytany z 40 388 B tekstu, bez ciężkiej analizy obrazów/siatek. Kamery mają identyczne SHA r2/r3/r4. Względem r3 draws +0 na wszystkich ujęciach, tris Low 0…+9 tys., High +1…+19 tys., bez przekroczeń 2%. Skumulowane Low względem r2: 38/84 wzrostów draws i 34/84 tris ponad 2% (r3 miało22/84). Zapisano pełne tabele z oddzielnymi instancjami i ograniczenia budżetu; telefonu/GPU nie mierzono. Test core nadal jedyny własny heavy w kolejce.

2026-11-12T13:25:02.6318241+01:00: przygotowano pełny request niezależnego D51: 25 B Low-overcast, ścieżki natywnego raw i zdjęcia, sprawdzone rzeczywiste SHA obu plików i capture. Recenzent pracuje bez ciężkiego Pythona/Unity; oceni wszystkie pary, C17 wykluczone. Dopuszczone tylko dwa własne artefakty recenzji, bez commitów lub edycji źródeł. Arkusze 960 px i ich SHA zostaną związane po późniejszym składaniu. Nie ma jeszcze wyniku D51 r4.

2026-11-12T13:31:51.0540842+01:00: niezależna ocena 25/25 par natywnych (50 obrazów) zakończona. D51 r4 FAIL: 13 rozpoznawalnych, 11 częściowych, 1 nierozpoznawalna. Lekki binder ponownie sprawdził rzeczywiste SHA wszystkich zdjęć/raw, pełny roster i wyniki. Rejestr Data otrzymał świeżą ocenę z historią r3 i r1; żadnej pozy C nie promowano, arkuszy 960 px recenzent jeszcze nie oglądał. Priorytety zaktualizowano z nowej oceny oraz kosztu skumulowanego. Test core nadal czeka w tym samym FIFO, obecnie dwa wcześniejsze zgłoszenia.

2026-11-12T13:32:30.0945752+01:00: sześć plików świeżej oceny natywnej i rejestru zapisano w native-review-evidence.zip. Po zamknięciu archiwum ponownie sprawdzono roster, rozmiary i SHA każdego wpisu. To zachowuje dokładne bajty recenzji mimo normalizacji końców linii Git; nie zawiera obrazów ani deklaracji obejrzenia przyszłych arkuszy.

2026-11-12T13:38:07.9717987+01:00: wyodrębniono 12 nowych przekroczeń skumulowanego Low, sześć kamer G3-B w dwóch stanach. Arytmetyka r2→r3→r4 zgodna dla wszystkich 84 rekordów Low. Nowe przypadki mają +3…+8 tys. trójkątów od r3 i około 2,18…3,39% skumulowanego wzrostu od r2. Pełne ID i wartości w new-low-threshold-crossings.json oraz tabeli budżetu, bez przypisywania kosztu konkretnej dziedzinie.

2026-11-12T13:44:00.6571581+01:00: zweryfikowano wszystkie osiem wpisów wcześniejszego archiwum metadanych referencji: SHA ZIP, roster, rozmiary i SHA rozpakowanych strumieni zgodne. Początek układu współrzędnych użyty do klasyfikacji Commons jest identyczny z początkiem świeżego świata capture. Nie potwierdza to poprawności geotagów ani pozy. Test core nadal aktywnie czeka w FIFO.

2026-11-12T13:47:21.3050350+01:00: preflight JSON nowego GLB przy 494288 potwierdził węzły road, bridge i road_collision bez transformacji. Widoczny road_asphalt występuje także w bridge, a collision_asphalt pozostaje osobną klasą. Odczytano tylko 81 848 B nagłówka JSON i sprawdzono hash pliku z manifestem; nie wykonywano raycastów ani dekodowania geometrii. Nie dowodzi to jeszcze wysokości powierzchni dokładnie pod kamerą. Przygotowany sampler jest zgodny z metadanymi eksportu.

2026-11-12T13:53:20.5143944+01:00: ADR 0111 otrzymał sekcję r4 oznaczoną jako runda w toku. Opisuje faktycznie wdrożony kontrakt migawek, odrębne lease dla stanów i guard istniejącego biletu; jawnie wymienia testy nadal oczekujące, brak nowych raycastów i brak końcowego GIS. Zapisano także świeży D51 oraz skumulowany budżet, bez deklaracji zamknięcia rundy.

2026-11-12T13:54:37.6582499+01:00: sesja core 55690 zakończona kodem 0: 51 passed w 1,87 s. Heavy zwolniony. Zapisuję log i receipt faktycznego przebiegu; uruchamiam oddzielny plik test_sbs_evidence_script.py przez nowy Acquire FIFO. ADR zaktualizowany o zmierzony wynik core, bez przypisywania wyniku niewykonanym jeszcze testom PS.

2026-11-12T14:02:51.8456522+01:00: przygotowano jeden audyt całej bazy r4: 168 raw i 268 arkuszy z pełnym dekodowaniem PNG, 128 hashy GLB, ZIP wejść, liczniki i rejestr oceny natywnej. Pochodne arkusze otrzymają osobne mechaniczne powiązanie SHA bez przypisywania ich oglądu recenzentowi. Audyt dopuszcza ocenę bazową w historii rejestru, jeśli później pojawi się inna faza. Dodano osobny task Audit w helperze heavy. AST i parser PS poprawne; audytu nie uruchomiono, bo arkusze jeszcze nie powstały, a test PS pozostaje jedynym własnym zadaniem w kolejce.

2026-11-12T14:07:34.1911951+01:00: zamknięto blocker przeglądu audytu: każda z 25 ocen candidate musi odpowiadać niezależnemu JSON w wyniku, uzasadnieniu, zastrzeżeniu i obu SHA. Sprawdzane są też COMPLETE, count, run/state, gate oraz pełny unikalny roster requestu i jego konkretne ścieżki względne/bezwzględne. Sumy ocen nie zastępują już tożsamości poszczególnych par. Dodano odmowę ostrzeżeń provenance. AST poprawny; audyt nadal niewykonany.

2026-11-12T14:14:59.9423276+01:00: lekka analiza 20 zapisanych metadanych uwzględniła też widoczność ku początkowi spoza stacji 300 m. Z siedmiu kierunkowych kandydatów pobrano i obejrzano trzy miniatury, łącznie 437 690 B, bez ciężkiego przetwarzania. Wszystkie są nocne z odblaskami/rozmyciem; nie kwalifikują dziennych par ani pokrycia 0–200 m. SHA sprawdzone, autor grobin i CC BY-SA 4.0 zapisane; podpisane URL i tokeny pozostały wyłącznie w pamięci. Produkcyjne kamery i 42 referencje bez zmian. Poprawka audytu 72585415 otrzymała scoped PASS niezależnego recenzenta, bez wykonania audytu.

2026-11-12T14:25:12.9510070+01:00: sesja 28476 ponownie potwierdzona jako żywa. Ostatni log: dwa zgłoszenia przed nami, PHONE_RUN obecny. Własny slot heavy i Unity nie są zajęte; własny bilet FIFO pozostaje obecny. To oczekiwanie, nie uruchomiony pytest. Nie zmieniano blokady, kolejności ani cudzych slotów; brak operacji na telefonie. Szczegóły obserwacji w heavy-wait-observation.json.

2026-11-12T14:42:07.0742791+01:00: odczytano optykę sześciu źródeł z migawki. Wszystkie mają intrinsics SfM i rektyfikację, pionowy FOV od 31,97862 do 58,71551 stopnia. Plan zachowuje te parametry; nie są nowym pomiarem lub potwierdzeniem SfM. Protokół wyjaśnia znaczenie natywnego zdjęcia porównawczego, a podpis przyszłych arkuszy jawnie wskazuje rektyfikację. Produkcyjne kamery i referencje bez zmian; AST kompozytora poprawny, nie wykonano kompozycji.

2026-11-12T14:55:47.2780059+01:00: bieżący main wprowadził f7d0e5a0: PHONE_RUN blokuje tylko Unity, ciężki Python może pracować w puli heavy. Zweryfikowano stary Acquire PID 3200 i jego rodzica 9972: wyłącznie oczekiwanie sprzed tej zmiany, bez slotu i bez pytest/uv. Zatrzymano tylko własny stary Acquire; parent i sesja zakończyły się przed pracą. Log oczekiwania zachowano. Receipt przejścia i jawne wznowienie zachowują oryginalne ticki biletu FIFO; brak restartu testów, bo nie były uruchomione. Nie zmieniano wspólnego skryptu, PHONE_RUN ani cudzych slotów.

2026-11-12T15:02:06.5364910+01:00: rzeczywisty test PS zakończony 20/20 PASS w 28,43 s, sesja 67981 terminal 0, heavy zwolniony. Przejście ze starego oczekiwania nie było ponowieniem pytest; receipt wznowienia oznaczono zużytym. Bieżący main zawiera scalone ADR 0130 (abf15f9e), zmieniające sześć spornych póz; jego recenzję zachowano. Przepis 15 prób starej bazy oznaczono jako zastąpiony przed wykonaniem (0 przygotowanych/renderowanych), nie jako nieudaną kalibrację. Nie nadpisujemy danych Claude. R4 domyka pełne arkusze i walidację istniejącej bazy; r5 ma od razu scalić aktualny main i wykonać świeżą pełną serię. Oceny części G3-B z innej epoki nie są dodawane do r4 D51.

2026-11-12T15:11:08.0105544+01:00: ADR i priorytety uzupełniono o rzeczywiste 51+20 testów, aktualną politykę f7d0e5a0 oraz scalone pozy ADR 0130. Rozdzielono ocenę starej pełnej bazy r4 od nowej częściowej oceny G3-B z main. Jednorazowy przepis 15 prób pozostaje zachowany jako historia, ale helper odmawia jego uruchomienia po zastąpieniu przez upstream. Składanie 31378 jest aktywnym oczekiwaniem na nowe lease per stan, bez obchodzenia FIFO.

2026-11-12T15:17:12.2561792+01:00: read-only porównanie kamery z migawki r4 i konkretnego main potwierdza przesunięcia sześciu póz: około 10/16/73/85/20/3 m, przy zachowanym FOV. Tylko 297817 ma istotną zmianę kursu, około +1,15 stopnia. Początek układu zgodny. Pełne wektory i identyfikatory blobów w upstream-pose-comparison.json; opis nie jest nowym pomiarem ani renderem i nie zmienia r4 rejestru. Utrwalono podstawę do weryfikacji po merge następnej rundy.

2026-11-12T15:23:16.3807572+01:00: zapisano REPORT-DRAFT.md normalnym polskim tekstem, wyłącznie z potwierdzonymi wynikami i jawnymi brakami. Nie jest to raport końcowy ani dostawa; brak arkuszy, audytu i pełnego GIS pozostaje wymieniony. Składanie 31378 nadal jest tym samym żywym oczekiwaniem na FIFO, bez nowego procesu lub zmiany kolejności.

2026-11-12T15:27:46.5230953+01:00: przygotowano składanie raportu historii r1–r4 z kontrolą kompletu metryk czterech stanów, 25 B/17 C i zgodności wszystkich 25 natywnych ocen Low-overcast z pikselami r4. Generator nie renderuje ani nie dekoduje obrazów; używa istniejącego narzędzia raportu i kopiuje gotowe arkusze. AST poprawny, nie uruchomiono go przed powstaniem metryk. Składanie 31378 nadal oczekuje na FIFO.

2026-11-12T15:29:02.9712608+01:00: generator historii r4 zapisze rzeczywisty HEAD, kod wyjścia i SHA generatora/szablonu, zamiast pustego pola pochodzenia. Odmawia pracy na późniejszej gałęzi, aby stary skrypt nie nadpisał nowszej historii. To nadal przygotowanie kodu, bez zbudowania brakujących metryk lub raportu.

2026-11-12T15:35:14.6669400+01:00: rzeczywiście obejrzano osobno natywne zdjęcie i raw B150280 Low-overcast. Zapisano oba SHA i ręczne przybliżenia zbiegu jezdni około 340/720 wobec 430/720; to nie pomiar segmentacji. Hipoteza pitch pozostaje prywatna i czeka na świeży main r5, bez produkcyjnej zmiany XYZ/kursu/FOV lub D51. Składanie 31378 nadal czeka w dotychczasowym FIFO.

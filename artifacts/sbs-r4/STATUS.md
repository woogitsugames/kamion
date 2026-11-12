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

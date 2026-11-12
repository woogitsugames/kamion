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

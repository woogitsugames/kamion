# Wznowienie końcowej walidacji po awarii hosta

Stan odczytany 2026-11-12 około11:14: branch gpt-asphalt-r2, uchwyt17097 potwierdzony aktywny. Nie uruchamiać ponownie end-validation.ps1, dopóki ten proces działa. Brak nowego tekstu i timeout obserwacji nie są zakończeniem procesu.

Jeśli narzędzie zgłosi brak uchwytu, najpierw sprawdzić w Win32_Process własne end-validation.ps1/run-heavy.ps1/run-gis.ps1/run-unity-stage.ps1 i ich potomków. Nie uruchamiać drugiego procesu, jeżeli poprzedni nadal istnieje. Nie usuwać cudzych slotów. Oba runnery używają aktualnego skryptu slotów z main; heavy Owner to gpt-asphalt-r2, Unity Owner gpt-asphalt.

Zakończone etapy nie wymagają ponowienia przy niezmienionych źródłach produktu:

- GIS: candidate2-final-gis.log/xml, 604 passed,1 xfailed,exit0; metadane producenta odtworzone, audyt196 SHA bez rozbieżności.
- Physics/gate3: candidate2-final-PhysicsGate3.log,47 passed,1 znana porażka top_speed_flat_comb.json,exit1. physics-result.json potwierdza brak zmian testów/scenariuszy i dims.json względem bazy4992c434. Wynik nie jest zielony i musi pozostać ujawniony w REPORT.
- Capture, Compare, geometria, macierze i wszystkie60 obejrzanych arkuszy są ukończone. Integralność sprawdza handoff-preflight.ps1; obecnie celowo zwraca niezero, bo brakuje fidelity/EditMode.

Dopiero po potwierdzeniu braku żywych własnych procesów odczytać validation-progress.json i logi. Jeżeli fidelity rzeczywiście jeszcze nie ruszyło albo nie ma wyniku końcowego, wznowić ten etap przez pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage Fidelity -Label candidate2-final. Jego exit i raport trzeba odczytać i zachować; samo exit0 nie oznacza zaliczenia Gate3. Potem pwsh artifacts/asphalt-r2/run-unity-stage.ps1 -Stage Test -Label candidate2-final z logiem candidate2-final-editmode.log; zachować konkretny XML tej próby, nie cudzy ani historyczny. Po każdym kroku STATUS i WIP.

Nie omijać końcowego audytu odwołań/SHA, przywrócenia ustawień Unity i kontroli źródeł przed końcowym REPORT/end-round-checks.json/robocopy. Brak pola finished nie uprawnia do ponowienia całego pełnego GIS. Nie tworzyć finalnego REPORT ani następnej gałęzi przed zakończeniem bieżącej rundy. Powyższe jest instrukcją odzyskania po awarii; aktualny proces17097 pozostaje jedynym wykonawcą sekwencji.

## Aktualizacja po świadomym przeplanowaniu kolejki

Uchwyt17097 został celowo zakończony po sprawdzeniu, że jego drzewo zawiera tylko trzy oczekujące pwsh, bez Pythona i bez własnego slotu. Dowód w rescheduled-waiter-tree.json. Stary end-validation-recovered.log jest historią, nie aktualnym procesem. Nowy wykonawca: finish-remaining.ps1, log remaining-validation.log. Odczytać aktualny uchwyt i proces przed wznowieniem; nie uruchamiać obu naraz. Ten runner wznawia tylko fidelity z istniejącą funkcją rezerwacji slotu, potem EditMode, zachowując GIS/physics i blokując powtórzenie już zakończonego etapu. Pula nadal max3; cudzych rezerwacji nie usuwa ani nie nadpisuje.

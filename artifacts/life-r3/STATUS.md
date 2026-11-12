# Life r3 — kontynuacja doby
Start 12.11 około 03:43, gałąź gpt-life-r3 od life-r2 bd6f6b96; main 14ccbaf1 dołączane tylko do własnej gałęzi. Jedyny integrator main: Claude S11. Bez push/telefonu.
R2 przekazane do main artifacts; kod i testy zamrożone, ocena PARTIAL. Następny priorytet z recenzji lidera: tył osobówek i wachlarze brudu, felgi, czerń w słońcu, sheet_far. Palety później.
Konflikt fidelity_qa rozwiązano wersją main; world_manifest/props_meta też z main do regeneracji. Wspólne źródła połączyły się automatycznie, wymagają kontroli opt-in. Nie rozpoczęto zmiany wyglądu r3.
Następny krok: sprawdź git diff HEAD^ w blokach CARPAINT/fabryce i nowe life.py; odśwież dane CC0/Megascans, potem World przez unity-slot -Pool heavy -Owner gpt-life-r3. Nowy baseline na scalonych źródłach, nie obrazach r2.
Pierwotny termin doby około 12.11 21:31 Warszawa. Unity Owner gpt-life, heavy Owner gpt-life-r3; -StaleHours 1000000, respektuj rezerwacje lidera i PHONE_RUN.

Krok 1: merge zakończony. Skorygowano ścieżki dwóch obrazów w raporcie r2 (są w refs/), a osiem krytycznych SHA sprawdzono ponownie z błędami kończącymi walidację. Następny krok: przygotowanie i kontrola nowego baseline.

Krok 2: odświeżono lokalne CC0/_raw/Megascans z main (bez derived/World i bez cudzych blokad). Przeniesiono pomocniki QA do r3 i dotychczasowe kamery jako punkt wyjścia. Heavy helper zawiera już respektowanie rezerwacji lidera przez nowy unity-slot. Następny krok: baseline-gen.ps1 wykona materiały, World i source-proof sekwencyjnie w jednym heavy; następnie nowe kamery i import.

Krok 3: baseline-gen zapisany; tylko sekwencyjna generacja materiałów/świata/proof pod jednym heavy, checkpoint po każdym etapie. Nie zmieniać produkcji do ukończenia baseline capture. Następny krok: pwsh -NoProfile -File artifacts/life-r3/baseline-gen.ps1.

Krok 4 (09:06): po przerwie środowiska stary proces baseline nie istniał; brak logów i własnego slotu potwierdzony. Wznowiono baseline-gen raz: nabył heavy gpt-life-r3, materiały w toku (handle 2467). Obejrzano dwie nowe referencje CC BY; ograniczenia pogody/licencji zapisane. Przygotowano dodatkowe kamery z rzeczywistych instancji; skrypt nie został jeszcze wykonany. Następny krok: zakończenie 2467, następnie heavy prepare-cameras.py i import/capture bez zmiany produkcji.

Krok 5: rozszerzono wyłącznie opt-in LifeExactStats o rzeczywistą pozycję/rotację i typ projekcji kamery; porównanie r3 będzie wymagało ich równości. Inwentarz oczekiwanych kamer pochodzi z ControlCamera w natywnych scenach plus packet, zamiast historycznej liczby 114. Poprawka przed baseline capture, bez ingerencji w runtime. Następny krok: dokończyć baseline-gen (2467), potem przygotować kamery, import i capture.

Krok 6: zapisano projekt r3 bez zmiany produkcji. Audyt GLB będzie chronił wszystkie węzły poza car_/van_ i 192 produkty raw względem nowego baseline; budżet wymaga osobno worldDraws i instanceDraws +0. Skorygowano kontrolę kamer: packet jest dodatkiem, część trasy istnieje w scenach. Następny krok: 2467, kamery, PreparedImport i przed-zmianą capture.

Krok 7: pomocniki PS/Python parsują się poprawnie; inwentarz aktualnej sceny odnajduje 48 kamer bazowych. Zapisano post-baseline.ps1: czeka na JEDEN istniejący generator, potem heavy-kamery, guarded import i cztery capture. Brak automatycznej zmiany produkcji bez oględzin. Następny krok: uruchomić raz pwsh -NoProfile -File artifacts/life-r3/post-baseline.ps1 (2467 pozostaje generatorem).

Baseline (2026-11-12T09:13:02.3950166+01:00): odtwórz materiały świeżego baseline r3. Następny etap w baseline-gen.ps1; po generacji nowe kamery i PreparedImport.

Krok 8: materiały ukończone w 519 s, checkpoint cdc1e6b5; generator World nadal w tym samym heavy 2467. Audyt przyszłego kandydata sprawdzi też .col/.contact i każdą podsiatkę osobówki; pozwala jedynie rim/rim_dark/rim_dusty przy zachowanym układzie grup. Następny krok: ukończenie World → post-baseline 46468 automatycznie przygotuje kamery i capture.

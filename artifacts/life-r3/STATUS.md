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

Krok 9: obejrzano zimową miniaturę PD (250 px); opisano zakres informacji i brak dopasowania fotometrycznego. Kamery zapiszą też rzeczywistą odległość pos→look_at, aby przybliżone nazwy rear5/wheel2 nie zastępowały pomiaru. World ma aktywny proces 35436 i narastający CPU, log na tym etapie jeszcze pusty; nie uruchamiać duplikatu. Następny krok: istniejący 2467 → 46468.

Krok 10: przeniesiono generator arkuszy porównawczych do r3 z nowymi life3_/sheet_far_ i oddzielną kontrolą obu draws. Nie został jeszcze uruchomiony, baseline nadal w budowie. Następny krok: terminalny wynik 2467 i post-baseline 46468; po capture miniatury ≤960 px i oględziny.

Krok 11: inspekcja eksportera wykazała próg creasing 38°; zapisano hipotezę wygładzania płytkich grzbietów felgi. Nie zmieniono globalnego eksportera ani produkcji. World przeszedł planowanie działek/placu/furniture; trwa jedna instancja. Następny krok: istniejące 2467 i 46468, potem oględziny baseline.

Baseline (2026-11-12T09:22:19.5697821+01:00): wygeneruj i potwierdź świeży baseline r3. Następny etap w baseline-gen.ps1; po generacji nowe kamery i PreparedImport.

Krok 12: World ukończony 0 (552,1 s), raw 192/192 zgodne, 15 Fab ready, 151 map. Zapisano lekki odczyt nagłówka GLB baseline (liczby trójkątów/grup aut) bez budowania modeli. Następny krok: istniejący post-baseline 46468 czeka na heavy dla wyboru kamer; nie duplikować pracy, później guarded import/capture.

Krok 13: odczyt bazowego GLB pokazuje maksimum LOD0 4170 (biały kombi na stalowych kołach). Roboczy rachunek dodania drugiej powierzchni tylko cienkich ramion daje maks. 4150 dla zmienianych aut i 4170 ogółem, nadal pod istniejącym 4200; to prognoza topologii, NIE wynik wygenerowanego kandydata. Dane w rim-topology-plan.json. Następny krok: czekający 46468, baseline capture i oględziny; nie zmieniać limitu testu 4200.

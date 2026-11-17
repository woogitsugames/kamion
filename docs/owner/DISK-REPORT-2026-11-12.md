# Raport dysku C: — 12 listopada 2026

Pomiar wykonany bez uprawnień administratora. Raport nie został commitowany. Wszystkie rozmiary oznaczone jako GB są GiB (bajty / 1024³), tak jak w PowerShell.

## Wolne miejsce

- Początek tej sesji (2026-11-12T20:01:51.7929949+01:00): **473,17 GB wolnego**, 1388,76 GB zajętego.
- Bezpośrednio przed czyszczeniem (2026-11-12T20:11:03.8997705+01:00): **487,36 GB wolnego**.
- Koniec (2026-11-12T21:12:03.4250738+01:00): **773,45 GB wolnego**.
- Zmiana od początku tej sesji: **+300,28 GB**; od chwili rozpoczęcia czyszczenia: **+286,09 GB**.
- Wartości 0,9 GB oraz około 446 GB po wcześniejszym sprzątaniu pochodzą od właściciela; nie są pomiarami wykonanymi w tej sesji.
- Agenci pracowali w tle. Wolne miejsce spadało również podczas samego skanowania; suma logicznych rozmiarów usuniętych plików nie jest tym samym co przyrost wolnego miejsca.
- Równoległe sesje utworzyły m.in. audio-idle, gps-map, mistral-r3-int i steer-r2. Chroniony mistral-r2-int przestał istnieć poza operacjami tego sprzątania: jego pierwotny HEAD 1e9a56786bac4a79a8c613f6dbd4a5429f42ca56 jest przodkiem main, a w main znajduje się merge fc5000837. W tej sesji usuwano wyłącznie 16 worktree GPT wyszczególnionych niżej.

## Co zajmowało około 1,36 TiB

Skan odczytał 10,422,553 plików i wykazał **1341,32 GB logicznej wielkości dostępnych plików**. Początkowe zajęcie woluminu wynosiło 1388,76 GB, czyli 1.356 TiB.

Arytmetyczna różnica między początkowym zajęciem woluminu a sumą dostępną dla skanera to 47,43 GB. Nie przypisano jej automatycznie kopiom cieni: zamknięte katalogi systemowe oraz różnica między logiczną wielkością plików i alokacją NTFS uniemożliwiają taki wniosek.

Największą przyczyną były kopie projektów, obrazy z testów i renderów, środowiska narzędziowe oraz kosz. Sam Kamion zajmował 544,61 GB: 293,47 GB w worktree i 226,37 GB w głównym artifacts. W artifacts około 200,13 GB stanowiły PNG. Dodatkowo .codex zajmował 139,33 GB, a 33 katalogi lw-wt-* — 101,74 GB. Dane źródłowe Kamiona były znacznie mniejsze: Data około 4,05 GB, art-source 2,25 GB.

Ograniczenia: pominięto 2208 punktów reparse i odnotowano 329 błędów dostępu/odczytu. Nie podążano za junctionami ani nie skanowano G:. Rozmiary są logiczne; twarde dowiązania, kompresja, pliki rzadkie, metadane NTFS i praca procesów w tle wpływają na porównanie z fizycznym zajęciem woluminu. Wynik dla niedostępnego katalogu nie oznacza, że jest pusty.

Niedostępne były m.in. C:\Program Files\WindowsApps i C:\System Volume Information. vssadmin list shadowstorage odmówił dostępu z powodu braku podwyższonych uprawnień. Wielkości punktów przywracania/kopii cieni nie ustalono; niczego w nich nie zmieniano.

## Top 30 przed usuwaniem

Tabela została pokazana właścicielowi przed pierwszym usuwaniem. To rozłączne grupy katalogów, bez ponownego doliczania ich rodziców.

| GB (GiB) | Ścieżka |
|---:|---|
| 293,47 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees` |
| 226,37 | `C:\Users\matma\Documents\Claude\kamion\artifacts` |
| 97,45 | `C:\$Recycle.Bin` |
| 84,22 | `C:\Users\matma\AppData\Local\Temp` |
| 51,02 | `C:\Users\matma\.codex\worktrees` |
| 45,07 | `C:\Users\matma\AppData\Local\uv` |
| 43,35 | `C:\Windows` |
| 33,35 | `C:\Program Files\Unity` |
| 30,68 | `C:\Users\matma\.gradle` |
| 29,75 | `C:\Users\matma\.codex\archived_sessions` |
| 22,20 | `C:\Users\matma\.codex\visualizations` |
| 21,06 | `C:\Users\matma\AppData\Local\Google` |
| 19,19 | `C:\Users\matma\tools` |
| 12,98 | `C:\Program Files\Adobe` |
| 10,20 | `C:\Users\matma\lockwright` |
| 9,86 | `C:\Users\matma\Documents\Claude\kamion\game` |
| 9,74 | `C:\tools` |
| 9,55 | `C:\ProgramData` |
| 8,88 | `C:\Users\matma\Documents\Claude\kamion$W` |
| 7,72 | `C:\Users\matma\Documents\Claude\kamion\.git` |
| 7,57 | `C:\Users\matma\.codex\sessions` |
| 6,23 | `C:\Users\matma\AppData\Local\Microsoft` |
| 5,81 | `C:\Users\matma\AppData\Roaming` |
| 5,31 | `C:\Users\matma\lw-wt-perf` |
| 5,20 | `C:\Users\matma\lw-wt-icon` |
| 5,04 | `C:\Users\matma\lw-wt-release` |
| 4,94 | `C:\Users\matma\AppData\Local\Packages` |
| 4,85 | `C:\Program Files\Microsoft Office` |
| 4,79 | `C:\Users\matma\lw-wt-a11y2` |
| 4,77 | `C:\Users\matma\.cache` |

## Wykonane czyszczenie

Najpierw uruchomiono oryginalny cleanup-disk.ps1 -WhatIf. Zablokowano w tym podglądzie git worktree prune, ponieważ oryginalny skrypt wywołuje go także przy WhatIf. Podgląd nie wskazał kolejnych nieaktywnych Library ani nadmiarowych APK. Pozostałe Library należały do chronionych aktywnych worktree; zachowano sześć APK w artifacts/apk.

Po pokazaniu top 30 właściciel potwierdził sprzątanie, a następnie rozszerzył je na Kamiona i inne projekty. W rozszerzonym zakresie usuwano wyłącznie zweryfikowane pozostałości z zabezpieczeniem pracy oraz odtwarzalne cache/wyniki kompilacji.

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 49,51 | `C:\Users\matma\AppData\Local\Temp — stare, niezablokowane pliki; z pominięciem claude, reparse i ścieżek procesów` |
| 97,45 | `C:\$Recycle.Bin — dostępne dane przed → po: Clear-RecycleBin i usunięcie osieroconych pozostałości` |
| 23,30 | `C:\Users\matma\.gradle\caches — starsze pliki, brak procesów używających wskazanych ścieżek` |
| 0,11 | `C:\Users\matma\AppData\Local\pip\cache — pip cache purge` |
| 1,39 | `C:\Users\matma\AppData\Local\npm-cache — npm cache clean --force (ubytek rozmiaru katalogu)` |
| 7,81 | `C:\Users\matma\Documents\Claude\kamion$W\game\Library — osierocony cache Unity, bez ProjectSettings i bez procesu używającego tej ścieżki` |

Temp: usunięto 329,245 plików; pominięto 3 używanych ścieżek; 4 błędów/blokad. Cache Gradle: 32,112 plików, 0 błędów. Resztki kosza: 1,277,470 plików, 23 błędów. Nie usuwano rekurencyjnie przez junctiony. Pierwsze Clear-RecycleBin również usunęło część kosza; jego efekt ujęto w końcowym pomiarze, bez przypisywania mu osobnego dokładnego rozmiaru.

Dodatkowe usuwanie resztek kosza objęło 68,08 GB po standardowym Clear-RecycleBin. Zastosowano natywne DeleteFileW; Windows odmawia usuwania plików zablokowanych. 23 przejściowe błędy wynikały ze współbieżnego zakończenia usuwania tych samych pozycji lub chwilowego otwarcia przez drugi własny proces sprzątania. Końcowa kontrola wykazała 0 dostępnych zwykłych plików, 0 bajtów i 0 reparse. Usunięto też 24 dowiązania (lokalne junctiony i dowiązania linuksowe rozpoznane po tagu) oraz 126 426 pustych katalogów, bez podążania za celami dowiązań. Pozostałych kont SID, do których brakowało dostępu, nie dotykano.

Temp po czyszczeniu: 34,57 GB; npm-cache: 0,03 GB. Temp/claude i bieżące pliki zachowano. Cztery zablokowane pliki Temp: baza .db, lockfile qtsingleapp-DPMLau i dwa pliki wct*.tmp — bez zatrzymywania aplikacji.

Wyniki kompilacji innych projektów: sprawdzono brak śledzonych plików w usuwanym katalogu, objęcie go gitignore, brak reparse, brak procesu wskazującego worktree i commit starszy niż dwie godziny.

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 0,18 | `C:\Users\matma\lw-wt-a11y2\game\build` |
| 1,46 | `C:\Users\matma\lw-wt-a11y2\game\android\build` |
| 0,31 | `C:\Users\matma\lw-wt-icon\game\build` |
| 1,51 | `C:\Users\matma\lw-wt-icon\game\android\build` |
| 0,36 | `C:\Users\matma\lw-wt-perf\game\build` |
| 1,50 | `C:\Users\matma\lw-wt-perf\game\android\build` |
| 0,29 | `C:\Users\matma\lw-wt-release\game\build` |
| 1,46 | `C:\Users\matma\lw-wt-release\game\android\build` |
| 0,24 | `C:\Users\matma\lw-wt-win\game\build` |
| 1,32 | `C:\Users\matma\lw-wt-win\game\android\build` |

### Worktree Kamiona

Przed usunięciem sprawdzono git status oraz git log main..gałąź. Wypchnięto 16 gałęzi na origin bez force; oba pushe zakończyły się powodzeniem, łącznie z obiektami LFS. Przy każdym usuwaniu ponownie sprawdzano HEAD, status, zgodność zdalnego HEAD i procesy. Zachowano lokalne gałęzie.

Pliki ignorowane przez Git i nieśledzone porównywano z main bajtowo przez SHA-256. Identyczne kopie pozostają w main. Pliki unikatowe zabezpieczono w artifacts\_disk-rescue-2026-11-12, tworząc twarde dowiązanie na tym samym woluminie przed usunięciem starej nazwy; po usunięciu worktree dane pozostają w katalogu ratunkowym. Lokalne modyfikacje zachowano również w LOCAL-CHANGES.patch. Główne artifacts pozostawiono jako źródło zachowanych identycznych kopii.

Kontrola po zabezpieczeniu: 264,075 wpisów manifestu ma istniejącą kopię o oczekiwanej wielkości; błędów: 0. Porównanie SHA-256 wykonywano przed usuwaniem; kontrola końcowa potwierdzała dostępność i wielkość kopii. Zdalne HEAD wszystkich 16 gałęzi zweryfikowano ponownie. Zachowano też obiekty LFS wskazane w patchach lokalnych zmian.

Junctiony pięciu katalogów Data/raw odpinano w PowerShell natywnym Directory.Delete(path, false), bez rekursji. Sprawdzano ich typ i dokładny cel w main, a potem brak reparse w Data/raw. Dopiero po tym wywoływano git worktree remove --force --force.

Rozmiary poniżej są pomiarem katalogu przed sprzątaniem; nie należy utożsamiać ich z odzyskanym miejscem, ponieważ zachowano unikatowe dane w rescue.

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 11,81 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-asphalt` |
| 8,58 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-cab` |
| 12,24 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-car-paint` |
| 15,98 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-edge` |
| 5,37 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-firestation-r7` |
| 18,01 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-furniture` |
| 12,93 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-landmarks` |
| 20,23 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light` |
| 6,08 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light-r12` |
| 0,93 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-s10-coordination` |
| 7,88 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-sbs` |
| 7,49 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-tint-gamma` |
| 11,76 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-truck` |
| 6,38 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-truck-paint` |
| 9,54 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation` |
| 7,33 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation-r2` |

Usunięte worktree: 16. Rozmiar logiczny zabezpieczonych plików w przygotowanych kopiach: 22,50 GB. Dokładny wykaz źródło → zachowana kopia znajduje się w worktree-rescue-files.jsonl w katalogu ratunkowym.

Pomiar kontrolny Kamiona po usunięciu 16 worktree: **437,53 GB** wobec 544,61 GB na początku. Obecne worktree: 163,67 GB. Główne artifacts: 249,09 GB, w tym 22,63 GB danych ratunkowych. W tym samym czasie inne sesje tworzyły nowe worktree i cache.

Odtworzenie: utworzyć worktree z zachowanej zdalnej gałęzi, odtworzyć junctiony do main, zastosować LOCAL-CHANGES.patch (jeżeli istnieje), a następnie odtworzyć pliki wskazane w manifeście z rescue i main. Obiekty LFS wskazane w patchach zachowano dodatkowo w rescue/_lfs, jeśli były wymagane. Nie usuwać katalogu rescue ani głównego artifacts przed przeglądem lidera.

## Pozostawione i dalsze decyzje

| Ścieżka | GB przed | Powód / ryzyko |
|---|---:|---|
| `C:\Users\matma\Documents\Claude\kamion\artifacts` | 226,37 | Unikatowe obrazy i dowody QA; część plików służy jako zachowana kopia po usunięciu worktree. Do uzgodnienia retencja/archiwizacja, bez kasowania całości. |
| `C:\Users\matma\AppData\Local\uv\cache` | 45,07 | uv cache prune zgłosił używany cache. Przerwano wyłącznie własny oczekujący uv prune; nie użyto force. Ponowić po zakończeniu sesji korzystających z cache. |
| `C:\Users\matma\AppData\Local\Temp\claude` | 32,52 | Katalog wyłączony z czyszczenia przez polecenie właściciela; aktywne i historyczne materiały agentów. |
| `C:\Users\matma\.codex\worktrees` | 51,02 | Osobne projekty i potencjalnie niezintegrowana praca; nie usuwano całych katalogów. |
| `C:\Users\matma\.codex\archived_sessions` | 29,75 | Historia czatów; usunięcie powoduje utratę historii. |
| `C:\Users\matma\.codex\visualizations` | 22,20 | Artefakty i kopie projektów; nie traktować całości jako odtwarzalnego cache. |
| `C:\Users\matma\lw-wt-*` (33 katalogi) | 101,74 | Zachowano źródła i zmiany; usunięto tylko 8,64 GB zweryfikowanych wyników kompilacji. Pełne usuwanie wymaga osobnego zabezpieczenia gałęzi i plików. |
| `C:\Users\matma\Documents\Claude\kamion$W\Data` | 1,07 | Po identyfikacji osieroconego Library usunięto z tej kopii 7,81 GB cache. Osobnego Data nie usuwano: wymaga porównania z głównymi danymi. |
| `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-life` | 32,60 | Worktree zablokowany jako trwająca sesja; zachowano go mimo braku procesu wskazującego ścieżkę w początkowym odczycie. |
| `C:\Users\matma\Documents\Claude\kamion\.git\lfs` | 7,33 | Nie wykonywano git lfs prune. Obiekty mogą być potrzebne lokalnym gałęziom i odtworzeniu pracy; ewentualny prune wymaga osobnej decyzji. |
| `C:\Program Files\Unity\Hub\Editor\6000.6.8f1` | 15,11 | Potencjalna deinstalacja przez Hub po potwierdzeniu zależności innych projektów i dostępu administratora. Zachować 6000.3.28f1 (18,24 GB). |
| `C:\hiberfil.sys`, `C:\pagefile.sys` | 57,03 łącznie w pomiarze kontrolnym | Zmiana konfiguracji systemu; nie wykonywano. |
| `C:\System Volume Information` / kopie cieni | nieustalone | Brak uprawnień administratora do vssadmin. Wymaga pomiaru w podwyższonej sesji. |

Chronione: a16-perf, buildings-r9, edge-r6c, junctions-r7, putry-andersa, mistral-r2-int oraz każdy worktree wskazywany przez proces. Dodatkowo zachowano gpt-life: git worktree locked, opis sesji do 12 listopada 21:31. Nie usuwano Data/raw w main ani art-source, nie zmieniano chmury, hibernacji, pagefile, punktów przywracania ani ustawień systemu. Nie zatrzymywano agentów, Unity, Python, pwsh ani bash.

## Wymagane pomiary szczegółowe

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 1,59 | `C:\Users\matma\Downloads — przed sprzątaniem` |
| 0,00 | `C:\Users\matma\Videos — pomiar uzupełniający` |
| 2,85 | `C:\Users\matma\AppData\LocalLow — przed sprzątaniem` |
| 84,22 | `C:\Users\matma\AppData\Local\Temp — przed sprzątaniem` |
| 45,07 | `C:\Users\matma\AppData\Local\uv — przed sprzątaniem` |
| 0,20 | `C:\Users\matma\AppData\Local\Unity — przed sprzątaniem` |
| 0,16 | `C:\Users\matma\AppData\Local\Google\DriveFS — przed sprzątaniem` |
| 4,94 | `C:\Users\matma\AppData\Local\Packages — przed sprzątaniem` |
| 0,11 | `C:\Users\matma\AppData\Local\pip — przed sprzątaniem` |
| 1,42 | `C:\Users\matma\AppData\Local\npm-cache — przed sprzątaniem` |
| 0,00 | `C:\Users\matma\AppData\Local\Microsoft\WindowsApps — przed sprzątaniem` |
| 5,81 | `C:\Users\matma\AppData\Roaming — przed sprzątaniem` |
| 9,55 | `C:\ProgramData — przed sprzątaniem` |
| 33,35 | `C:\Program Files\Unity — przed sprzątaniem` |
| 0,16 | `C:\Windows\SoftwareDistribution — przed sprzątaniem` |
| 97,45 | `C:\$Recycle.Bin — przed sprzątaniem` |

Docker w AppData/Local: katalog nie istnieje. WindowsApps: rozmiar dostępnych aliasów po pominięciu reparse, nie pełnych instalacji aplikacji.

### Kamion i każdy worktree — stan przed sprzątaniem

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 544,61 | `C:\Users\matma\Documents\Claude\kamion` |
| 7,72 | `C:\Users\matma\Documents\Claude\kamion\.git` |
| 7,33 | `C:\Users\matma\Documents\Claude\kamion\.git\lfs` |
| 4,05 | `C:\Users\matma\Documents\Claude\kamion\Data` |
| 1,80 | `C:\Users\matma\Documents\Claude\kamion\Data\raw\fab` |
| 226,37 | `C:\Users\matma\Documents\Claude\kamion\artifacts` |
| 9,86 | `C:\Users\matma\Documents\Claude\kamion\game` |
| 2,25 | `C:\Users\matma\Documents\Claude\kamion\art-source` |
| 17,34 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\a16-perf` |
| 3,36 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\argon-edge` |
| 16,47 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\buildings-r9` |
| 15,91 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\edge-r6c` |
| 11,81 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-asphalt` |
| 8,58 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-cab` |
| 12,24 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-car-paint` |
| 15,98 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-edge` |
| 0,00 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-edge-r2` |
| 5,37 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-firestation-r7` |
| 18,01 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-furniture` |
| 12,93 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-landmarks` |
| 32,60 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-life` |
| 20,23 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light` |
| 6,08 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light-r12` |
| 0,93 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-s10-coordination` |
| 7,88 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-sbs` |
| 7,49 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-tint-gamma` |
| 11,76 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-truck` |
| 6,38 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-truck-paint` |
| 9,54 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation` |
| 7,33 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation-r2` |
| 14,11 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\junctions-r7` |
| 16,81 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\mistral-r2-int` |
| 14,36 | `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\putry-andersa` |

### Pliki systemowe i VHDX

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 25,49 | `C:\hiberfil.sys` |
| 31,53 | `C:\pagefile.sys` |
| 0,02 | `C:\swapfile.sys` |

Są to rozmiary z pomiaru kontrolnego. Na początku pagefile.sys miał 24,74 GB, a później 31,53 GB. Nie zmieniano jego konfiguracji.

| GB (GiB) | Ścieżka / opis |
|---:|---|
| 0,08 | `C:\ProgramData\BlueStacks_polar\Engine\Baklava64\Data.vhdx` |
| 0,08 | `C:\ProgramData\BlueStacks_polar\Engine\Baklava64\Data_orig.vhdx` |
| 3,55 | `C:\Users\matma\AppData\Local\BlueStacks_polar\instances\Baklava64_u1\Data.vhdx` |

Wśród dostępnych ścieżek znaleziono VHDX BlueStacks, bez VHDX WSL/Dockera. Nie kompaktowano ani nie usuwano żadnego VHDX.

## Jak zapobiec nawrotowi

1. Ograniczyć równocześnie utrzymywane worktree i zamykać je po integracji. Przed usuwaniem zachowywać gałąź, lokalne zmiany i unikatowe pliki ignorowane przez Git.
2. Ustalić retencję artifacts: raport + wybrany komplet dowodów dla zaakceptowanej rundy; pełne macierze PNG trzymać tylko do zakończenia przeglądu. Obecne 200 GB PNG jest większym problemem niż surowe dane świata.
3. Poprawić cleanup-disk.ps1: stała lista chronionych worktree, respektowanie git worktree locked, kontrola wieku także w ścieżce merged, brak jakichkolwiek mutacji przy WhatIf, natywne usuwanie cache bez przechodzenia przez reparse.
4. Czyścić uv/cache oraz Temp między sesjami agentów, gdy cache nie jest używany. Nie wymuszać prunowania aktywnych środowisk MCP.
5. Dodać limit/alert budżetu dysku w istniejącym watchdogu (propozycja: ostrzeżenie przy 250 GB wolnego); nie wdrażano automatyzacji ani zmian ustawień.
6. Nie współdzielić Unity Library przez junction pomiędzy równocześnie otwartymi projektami. Dla narzędzi stosować wspólne kontrolowane cache i ograniczać niepotrzebne kopie wyników kompilacji.

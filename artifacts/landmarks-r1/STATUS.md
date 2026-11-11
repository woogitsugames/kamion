# Stan sesji landmarks, runda 1

Przeczytano zadanie 05, HANDOVER s10, zasady, budżety, decyzje D48–D50 i recenzje remizy oraz wiaduktu. Worktree gpt-landmarks, gałąź gpt-landmarks-r1 utworzone z main 5f2aa277.
Zakres: wyłącznie remiza, podpomostowa część wiaduktu i kominy. Bez push, scalania do main i telefonów. Unity wyłącznie przez slot Owner gpt-landmarks, zwalniany po każdym uruchomieniu.
Krok 1: przygotowanie danych i audyt bieżącej remizy. Historyczne artifacts/firestation-r10 zawierają obce aktualizacje i nie są stanem tej sesji.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/bootstrap.ps1

Krok 2: prywatne kopie derived, CC0, Megascans i _Generated wykonane; Library w kopiowaniu. Przygotowano wrapper unity-step.ps1: Acquire/Release Owner gpt-landmarks osobno wokół każdego importu, renderu i testu, restore efektów ubocznych w finally. Zachowano zdjęcie referencyjne Commons 7197, Rakoon, CC0. Uruchomiono świeży generator bazowy; wynik jeszcze niezweryfikowany.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-world.log -Tail 20

Krok 3: bootstrap zakończony, git lfs checkout OK, wszystkie pięć junctionów wejściowych gotowe. Trwa świeża regeneracja świata i pełnych materiałów, testy GIS rozpoczęte. Przygotowano ADR 0116 oraz helper porównania wszystkich kamer z osobnym raportowaniem siatek i instancji. Baseline wizualny i wartości barw UNVERIFIED.
NASTĘPNA KOMENDA: po zakończeniu generatorów: pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import

Krok 4: zapisano SHA źródeł baseline i termin pracy do 12.11.2026 21:31 CET. Bazowy GIS przerwany na etapie 14%: uruchamiał trzy dodatkowe generatory przy ~1,6 GB wolnego RAM. Nie jest zaliczony; pełny GIS zostanie wykonany po zmianach. Świat i materiały dalej w regeneracji, bez startu Unity i bez zmian modelu.
NASTĘPNA KOMENDA: po zakończeniu generatorów: pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import

Krok 5: źródłowy audyt tui wykazał rozdzielone narożniki ścian bez radialnych normalnych; samo use_smooth nie wygładzi Low. Przygotowano plan korekty bez nowych trójkątów. Oba wejścia igliwia CC0 zgodne z SHA. Regenerację PBR ograniczono do Medium, faktycznie importowanego zestawu (Low/High to osobne geometrie, nie wymagają trzech rozdzielczości PBR). Produkcja bez zmian.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-materials-medium.log -Tail 12

Krok 6: świat zakończył wszystkie etapy po 1082,1 s, 64 pary GLB; remiza applied, bez stale, tris 9344/2828/164. Brak fallback=True w logu. Powłoka zwróciła 1 po potraktowaniu komunikatów instalacji uv na stderr jako błędu; sam log generatora kończy się done, bez traceback, eksport obecny. Materiały Medium zakończone exit 0, 694 s. Rozpoczynam import przez slot.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Capture -Phase before -Cameras ''

Krok 7: import oczekuje na cztery zajęte sloty, bez startu Unity. W tym czasie odczytano rzeczywisty street_props.glb: osie obu kominów EC i ich LOD1 mają poziomy dryf 0 m, znaleziono dwie instancje. To dowód CPU, nie runtime Unity; pozorne pochylenie wymaga sprawdzenia kadru, nie zgadywania rotacji. Dopisano jawne -Cameras all do wrappera pełnego baseline.
NASTĘPNA KOMENDA: po imporcie pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Capture -Phase before -Cameras all

Krok 8: zachowano prywatną kopię bazowego GLB i wszystkich map atlasu remizy Medium oraz alfa, z SHA-256. Uzupełniono audyt r2/r3 na podstawie obejrzanych zdjęć lokalnych, bez zmian produkcyjnych w innych dziedzinach. Import nadal oczekuje na slot.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-import-wrapper.log -Tail 10

Krok 9: oczekiwanie na slot trwało kilkanaście minut, podczas gdy inni właściciele wymieniali sloty. Zatrzymano wyłącznie własny proces Acquire bez posiadanego slotu i skrócono odpytywanie z 60 do 10 s. Limit czterech slotów, blokada PHONE_RUN i wymagany Owner pozostają zachowane. Żadna Unity jeszcze nie wystartowała.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import

Krok 10: przygotowano warunkową kontynuację po imporcie: sprawdzenie tożsamości własnego procesu, IMPORT_RESULT OK i zwolnienia slotu, następnie pełny baseline Low/High clear/overcast. Wrapper przyszłych uruchomień nie usuwa cudzych starych slotów. Wszystkie uruchomienia nadal korzystają z oficjalnego Acquire/Release i Owner gpt-landmarks.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-capture-wrapper.log -Tail 10

Krok 11: artifact-only kandydat wygładzenia tui przeszedł porównanie 26 rzeczywistych krzewów. Geometria, UV i materiały identyczne; High 4576 tris/0 nowych normalnych, Low 552 tris/1104 zgodne normalne narożników. Współdzielone pozycje mają identyczne normalne. Nie wdrożono do produkcji; brak renderu oznacza brak visual PASS. Import nadal w kolejce.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-import-wrapper.log -Tail 10

Krok 12: slot gpt-landmarks przyznany, import Unity rozpoczęty 22:15:29. CC0 fetch: 13 zasobów, 65 plików, 0 problemów. Artifact-only próba gradientu hali: 15664 zmienione piksele atlasu 512, wszystkie piksele poza prostokątami okien hali identyczne. Obejrzano arkusz CPU; nie jest to dowód wyglądu Unity. Produkcja nadal bez zmian, baseline w toku.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-capture-wrapper.log -Tail 10

Krok 13: zastosowano pilną zmianę protokołu: każde ciężkie zadanie Python przez pulę heavy, maksymalnie 3, Owner równy bieżącej gałęzi. Pełny GIS wyłącznie na końcu rundy; w trakcie pojedyncze pliki. Nie działa żaden ciężki Python tej sesji. Dodano heavy-step.ps1 z Release w finally i limitem wątków bibliotek numerycznych. Nowe importy używają import-prepared.ps1, bez ukrytego automatycznego build_all poza pulą heavy. Skryptów współdzielonych nie zmieniano; heavy korzysta z aktualnej infrastruktury main przez ścieżkę bezwzględną.
Import baseline OK: 64 kafle, Low 117,0 MB, High 259,1 MB łącznie z instancjami i kolizją. Slot zwolniony; pełny capture czeka na slot. Naprawiono warunkową kontynuację: uchwyt procesu zamiast powtarzanego WMI, które raz anulowało zapytanie. Syntax check trzech helperów OK.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/baseline-capture-wrapper.log -Tail 12

Krok 14: pełny baseline zakończony: 48 kamer × cztery warunki = 192 PNG, wszystkie cztery uruchomienia zwolniły slot. Obejrzano Low/High kadr referencyjny i natywne cropy. Iglaki za wąskie i szkło prawie płaskie potwierdzone; plama przy maszcie istnieje na High, nie Low. Trwa pojedyncza ablacja cieni (Unity slot) w celu ustalenia przyczyny, bez zmiany ustawień produkcyjnych.
Wdrożono w źródłach sprawdzony kandydat normalnych tui Low oraz lokalny gradient i albedo szkła hali. Test istniejącego budżetu roślin utrzymano, rozszerzając sprawdzenie zgodnych normalnych. Jeszcze bez regeneracji, testów i oceny wyglądu po zmianie.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step Materials -Log artifacts/landmarks-r1/round1-materials.log

Krok 15: przygotowano pierwszy pełny kandydat remizy. Iglaki: szersze dwie korony, rdzeń 0,95 R zamiast 0,55 R, ciemniejsza lokalna paleta w wolnej komórce tego samego atlasu; liczby kart i materiałów bez zmian. Zacieki szczytu przeniesiono na pas podążający za łukowym dachem zamiast poziomej linii korony; pigment tynku D48 bez zmiany. Dodano kontrolę kotwienia pasa do krzywizny i braku dodatkowego materiału. Python/JSON syntax OK, wyniki wyglądu i budżetu po zmianie jeszcze niezweryfikowane.
Zachowano świeże JSON baseline do oddzielenia zmian tej sesji od wcześniejszego dryfu produktów wygenerowanych na main. Następny etap kolejno przez heavy: Materials, World, pojedynczy test_fire_station_r7.py; potem import i 16 fokusowych renderów przez unity.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/round1-build.ps1

Krok 16: Materials ukończone pod heavy, exit 0, 32 s. Slot heavy zwolniony i osobno ponownie zajęty przez World. Rzeczywista mapa alfa ma identyczny kanał A na każdym pikselu i identyczne RGBA poza komórką igliwia; pozostałe napisy, płot i brama nie otrzymały zmian alfa. World w toku; test pojedynczego pliku nastąpi po nim.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round1-world.log -Tail 10

Krok 17: World ukończony w 480,5 s w heavy; remiza przebudowana Blenderem, brak fallback=True, hero applied. Zapisano własny GLB, meta i spec oraz pomiar liczby trójkątów/prymitywów przed i po. Produkty pozostałych dziedzin są wyłącznie wynikami wymaganego generatora i nie zostały wystawione jako zmiany ich źródeł.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round1-build-wrapper.log -Tail 10

Krok 18: pojedynczy test remizy w heavy zakończony 6/6 w 3,74 s; slot zwolniony. GLB 9344→9392 / 2828→2860 / 164→164 tris, prymitywy 3/2/1 bez zmiany. Import nowego wariantu w toku. Diagnostyki baseline zakończone i zwolniły slot; własny znacznik ich trwania usunięty. Plama: High Y114,83, bez cieni 131,12 przy sąsiednim tynku131,19; GI-off i SSAO-off pozostawiają114,83. To cień, prawdopodobnie flagi, a nie powód do dodawania kompensacji do albedo. CPU ray/UV probe potwierdził te same UV i kolor atlasu dla LOD0/1 w badanym miejscu.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round1-build-wrapper.log -Tail 10

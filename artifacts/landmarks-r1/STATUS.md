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

Krok 19: obejrzano wszystkie 16 par fokusowych (cztery kamery × cztery warunki) i zestawienie ze zdjęciem. Budżet Low w tym podzbiorze PASS, ale pełna trasa jeszcze niezweryfikowana. Wszystkie 64 wpisy kafli i roads_qa są identyczne ze świeżym baseline; w world_manifest zmienił się wyłącznie materiał fire_station. Inne źródła i geometria pozostają bez zmian.
Wygląd PARTIAL: iglaki są szersze i ciemniejsze, lecz rdzeń czyta się jak zbyt gładki stożek. Gradient szkła odwrócony poprawnie, ale za słaby w overcast: High lewa góra/dół 66,65/63,43 (przed71,93/74,65). Następna iteracja: piętrowa sylwetka z zamianą niewidocznych kart Low na geometrię rdzenia w tym samym budżecie oraz lokalna maska wnętrza dolnych tafli, bez zmiany shaderów.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/round1-build.ps1 -Phase round2

Krok 20: wariant 2 w źródłach. Profil ośmiu poziomów korony zastępuje gładki stożek. Low zamienia 24 karty na cztery dodatkowe segmenty rdzenia na drzewo, zachowując pierwotny budżet trójkątów; High zachowuje karty. Rdzeń otrzymuje detal RGB rzeczywistych igieł CC0 zamiast samego szumu. Dolne tafle otrzymują maskę widoczności wnętrza w istniejącym kanale AO, bez zmian PVC, niebieskiej ramy i shaderów. Dodano test ochrony ram. Syntax OK; wyniki obrazu i budżetu wariantu 2 UNVERIFIED.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/round1-build.ps1 -Phase round2

Krok 21: materiały wariantu 2 ukończone pod heavy, exit 0, 31 s. Slot zwolniony; World osobno zajął heavy i działa. Przygotowano końcowe zachowanie wszystkich wpisów wspólnego materials_spec poza fire_station; przed końcowym commitem remiza będzie wygenerowana we wszystkich trzech rozdzielczościach, aby nie usuwać cudzych opisów High/Low. Pełny GIS nadal nie był uruchamiany w trakcie strojenia.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round2-world.log -Tail 10

Krok 22: źródło plamy rozpoznane jednoznacznie. Promień CPU z ciemnego ROI ku słońcu LP_Overcast trafia po 6,76 m w flagę; promienie z jasnych miejsc nad i obok nie mają przeszkody. W połączeniu z ablacją Unity potwierdza to cień flagi, nie wadę atlasu. Nie zmieniano z tego powodu światła ani albedo. World wariantu 2 przebudowuje teraz hero pod aktualne dane korony.
NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round2-build-wrapper.log -Tail 10

Krok 23: World wariantu 2 ukończony w 479,0 s, hero applied, bez fallback=True. Model: 9584/2860/164 tris; Low zachował budżet poprzedniego wariantu. Pojedynczy zestaw testów zatrzymał pipeline przed importem: 6 PASS, 1 FAIL. Nowa kontrola maski wykryła przyciemnienie białego poprzecznika i parapetu rysowanych po funkcji glazing; pozostałe kontrole geometrii i materiałów przeszły. Poprawka będzie ograniczona do AO tych białych detali. Pełnego GIS nie uruchamiano.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/round2-resume.ps1

Krok 24: poprawiono wyłącznie maskę AO parapetu i poprzecznika rysowanych po glazing. Geometria wariantu 2 pozostaje ta sama, dlatego wznowienie obejmuje generator materiału i pojedynczy test, następnie import oraz render. Zachowano mapy sprzed poprawki do porównania kanałów. Materiał zostanie teraz wygenerowany High/Medium/Low i wpisany do wspólnego spec wyłącznie jako fire_station, z zachowaniem pozostałych zestawów.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/round2-resume.ps1

Krok 25: materiał z poprawką białych detali wygenerowany we wszystkich trzech rozdzielczościach pod heavy. Wspólny spec zachowuje wszystkie pozostałe wpisy z HEAD. Następnie pojedynczy test remizy; bez pełnego GIS.

Krok 26: pojedynczy plik testów remizy po poprawce zakończony exit 0 pod heavy. Pipeline przechodzi do importu i 16 renderów fokusowych wariantu 2 przez oddzielne sloty Unity. NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round2-resume-wrapper.log -Tail 10

Krok 27: wariant 2 obejrzany we wszystkich 16 parach. Profil iglaków jest piętrowy, lecz nadal stylizowany względem zdjęcia; zostaje do dalszej rundy jakości po backlogu. Low w podzbiorze czterech kamer mieści budżet. Szkło High-overcast ma teraz góra/dół 64,93/59,00 (lewy łuk); dół pozostaje za jasny względem fotografii, więc ostatnia korekta tej rundy dotyczy tylko maski wnętrza tafli. Wspólny materials_spec przywrócono do pierwotnej kolejności kluczy: końcowy diff względem bazy to wyłącznie 13 zmienionych wierszy w fire_station, bez przestawiania innych zestawów.
NASTĘPNA KOMENDA: końcowa generacja materiału, pojedynczy test i szybki render samych łuków, następnie pełny komplet kamer i testy końca rundy.

Krok 28: końcowa korekta szkła wzmacnia dolne wnętrze tafli i pozostawia górne odbicie nieba. Maska ma własny przedział wysokości 0,25–0,70; ramy nadal chronione testem. To wyłącznie materiał, bez kolejnej zmiany geometrii. Doprecyzowano opis fallbacku igliwia, aby nie przypisywać skanowi niezweryfikowanych map.
NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/final-glass.ps1

Zapis pośredni: STATUS, fokusowe porównania i pomiary wariantu 2 skopiowano robocopy do głównego artifacts/landmarks-r1. REPORT jeszcze nie jest gotowy; trwa oczekiwanie na heavy dla końcowego materiału szkła. Wrapper Unity korzysta z własnej nazwy katalogu rundy i obsługuje osobny zestaw kamer, aby kolejne rundy nie nadpisywały tych dowodów.

Krok 29: końcowy materiał szkła wygenerowany w High/Medium/Low pod heavy i ograniczony do własnego wpisu spec. Następnie pojedynczy test remizy.

Krok 30: pojedynczy test remizy po końcowej korekcie zakończony exit 0 pod heavy. Import i szybkie cztery rendery łuków przed walidacją całej trasy.


Krok 31: cztery końcowe rendery szkła zakończone poprawnie. Low overcast: lewa góra/dół Y 59,93/48,86, prawa 62,65/48,86; High overcast 66,65/54,86 i 68,72/54,86. Gradient jest poprawny, High pozostaje nieco jaśniejszy od celu fotografii. Korony nadal proceduralne i wymagają następnej rundy po backlogu. Rozpoczynam pełne 192 kadry oraz końcowy GIS pod osobnymi pulami.

Krok 32: pełne 192 rendery końcowe zapisane (48 kamer x 4 warunki), 112 plików pikselowo identycznych. Budżet wszystkich 96 warunków Low: delta draws siatek 0, instancji 0, maksymalna delta trójkątów 0,0% przy kwantyzacji statystyk do tysiąca. Model: 9344/2828/164 -> 9584/2860/164. Wszystkie 64 wpisy chunków i roads_qa identyczne względem świeżego baseline, brak fallback=True. EditMode 261/261. Trwa pełny GIS.

Krok 33: obejrzano wszystkie 24 arkusze przed/po (192 pary). Wcześniej podejrzane cienie na dachach High-above mają ten sam wzór w pełnym przebiegu baseline i after. ADR opisuje końcowego kandydata jako PARTIAL: iglaki nadal proceduralne, High szkło trochę za jasne. Pełny GIS na 14%, brak końcowego wyniku.

Krok 34: końcowe świeżo wygenerowane world_manifest, streetscape_qa i roads_qa zachowane w final-generated jako dowód stanu renderów; nie włączam szumu regeneracji innych dziedzin do zmian źródłowych remizy. Potwierdzono z binarnego GLB 3/2/1 prymitywy. Pełny GIS przeszedł do 87%; czekam na szczegóły dwóch porażek. NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/final-gis.log -Tail 80

Krok 35: pełny GIS 493 passed, 2 failed, 1 xfailed (662 s). Własna porażka: twardy limit całego LOD1 2828, przekroczony o 32 trójkąty pasem zacieków. Zmieniam wyłącznie przekrój rdzenia trzech iglaków Low z 6 na 5 gładko cieniowanych boków: oszczędność 42 trójkąty, wszystkie 12 kart i 8 poziomów korony pozostają. Dopisano kontrolę całego budynku do testu remizy. Druga porażka to zastany stale fidelity dróg. NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step FocusedGIS -Log artifacts/landmarks-r1/budget-fix-focusedgis.log

Krok 36: domyślny przekrój rdzenia Low również 5 boków dla speców sprzed nowego pola. Przygotowano kontrolowaną regenerację i walidację całego modelu; kolejne rendery w osobnym after-budget. NASTĘPNA KOMENDA po oczekującym pojedynczym teście: pwsh artifacts/landmarks-r1/budget-fix.ps1

Krok 36a: dowód stale-fidelity-proof.json potwierdza, że wszystkie 7 niezgodnych wejść raportu dróg jest nietkniętych od bazy rundy. Nie zmieniam cudzych źródeł ani raportu fidelity. Pipeline czeka na zakończenie i zwolnienie slotu przez już oczekujący pojedynczy test; nie ma dwóch ciężkich zadań tej sesji pod jedną tożsamością.

Krok 36b: test remizy z kontrolą całego LOD1 przeszedł: 7/7 w 4,88 s pod heavy. Slot zwolniono przed uruchomieniem generatora, który teraz działa pod własnym kolejnym przydziałem. NASTĘPNY KROK: pipeline budget-fix.ps1 sam wykona test_hero_building.py, import i pełne rendery po regeneracji.

Krok 36c: zapisano NEXT-R2.md z analizą ścieżki PBR i kontraktów UV oraz planem wyłączenia niepotwierdzonych schodów. Źródła wiaduktu nadal nietknięte. NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/budget-fix-world.log -Tail 8

Krok 36d: ustalono przyczynę braku postępu generatora: liderowy ops-watchdog zapisał SUSPEND własnego launchera Python PID 107876 o 00:07:38; jego rzeczywisty proces 111836 ma wszystkie wątki Suspended. Pula heavy jest poprawnie zajęta. Nie wznawiam procesu poza nadzorem i nie uruchamiam duplikatu. Pipeline pozostaje aktywny i po automatycznym RESUME będzie kontynuował. NASTĘPNY KROK: analiza referencji bez ciężkiego Pythona; monitor budget-fix-world.log.

Krok 36e: przygotowano NEXT-R3.md z konkretną różnicą schematu pasów kominów oraz ograniczeniami własności pliku life_props.py. Nadal brak zmian źródłowych poza remizą. Generator pozostaje zawieszony przez watchdog; nie duplikuję go i nie zwalniam slotu, dopóki proces istnieje.

Krok 36f: natywne wycinki kominów ujawniły trzy wyloty na głowicy lewego i jeden na prawym. Zidentyfikowano istniejący przepływ własnych GLB przez hero_building/InstanceImporter, pozwalający przyszłą rundę wykonać bez edycji plików life i roads. Zapisane w NEXT-R3.md; implementacji r3 jeszcze nie rozpoczęto.

Krok 36g: watchdog wznowił własny generator o 00:20:32 i 00:20:33 (dwa uruchomione nadzory). CPU procesu ponownie rośnie. Zapisano ograniczenie identyfikacji zdjęć kominów: referencja pierwotnych override wspomina szachownicę, nieobecną na analizowanym 073128; przed zmianą trzeba potwierdzić przypisanie do OSM. NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/budget-fix-world.log -Tail 8

Krok 36h: odnaleziono pierwotną referencję EC_Białystok (Hiuppo, CC BY-SA 2.5). EXIF DateTime wskazuje 2007-03-06; ma szachownicę i pasy tylko u góry, a referencja CC0 z 2020 pokazuje inny stan malowania. Dane i podglądy zapisane z atrybucją. To istotna różnica epok referencji przed r3; nie przenoszę starego malowania do modelu na ślepo. Generator zakończył pierwszy etap dróg po wznowieniu.

Krok 37: regeneracja modelu i świata po naprawie budżetu: trójkąty 9584/2818/164, brak fallback=True. Następnie pojedyncze testy remizy i hero building.

Krok 37a: model po regeneracji ma potwierdzone 9584/2818/164 trójkąty. Generator zakończony w 1260,6 s czasu ściennego, w tym 775 s udokumentowanego zawieszenia przez watchdog (zdarzenia tylko własnego PID zachowane). Nie jest to pomiar CPU ani regresji wydajności. Oba pliki testów czekają w pipeline na pulę heavy; następnie import i nowe rendery.

Krok 37b: pobrano zweryfikowany SHA-1 oryginał CC0 zdjęcia wiaduktu 7204 (5520x3680, 10468810 B) do własnych artifacts, bez zapisu w junctionie refs. Wcześniejsza kopia miała 960x640. Natywne detale ujawniają pionowe szare ścięcia naroży przy ochrowych ścianach — ważniejsza wskazówka dla r2 niż zwiększanie szumu materiału. NEXT-R2.md uzupełniono; źródła wiaduktu nietknięte.

Krok 37c: mierzone wąskie ROI na natywnych płaszczyznach filarów mają Y sd 6,60–10,02, znacznie mniej niż mieszane ROI z recenzji. Ich mediany różnią się z oświetleniem: ciemna ściana 37/31/16, jaśniejszy dalszy filar 109/92/51. Zapisano dokładne boksy, aby w r2 nie zastąpić błędu powierzchni/światła nadmiernym szumem farby. Pipeline remizy nadal czeka na heavy dla pojedynczych testów.

Krok 37d: pełne dotychczasowe artifacts/landmarks-r1 skopiowano robocopy do głównego repo (kopia pośrednia, brak końcowego REPORT). Zachowano rendery, porażki testów i natywne referencje z metadanymi. Testy po naprawie budżetu wciąż oczekują na slot heavy. Po ich zakończeniu pipeline przejdzie do importu i after-budget; końcowa kopia zostanie powtórzona.

# Status sesji truck — runda 1
Start: 11 listopada 2026, 21:31 CET. Planowany koniec: 12 listopada 2026, 21:31 CET.
Przeczytano instrukcje właściciela, zasady projektu i recenzję 0087/0090. Worktree utworzono z main 5f2aa277.
Zakres: zewnętrze ciągnika TRAKT i naczepy. Bez scalania do main, pushowania i telefonów. Właściciel slotu Unity: gpt-truck.
Następny krok: skopiować lokalne zasoby według protokołu, wykonać git lfs checkout i zapisać baseline Low/High.

Krok 2: skopiowano derived, CC0, Megascans i _Generated; robocopy bez błędów, LFS 777/777. Junctiony surowych danych wskazują na main i są używane wyłącznie do odczytu. Kopiowanie Library trwa. Następny krok: pwsh artifacts/truck-r1/baseline.ps1 (każdy start Unity osobno pod slotem gpt-truck).

Krok 3: przygotowano procedurę baseline i ADR 0115. Obejrzano zdjęcia Commons: ciągnik użytkowy oraz lakier z odbiciami otoczenia. Library nadal się kopiuje; Unity jeszcze nie uruchamiano. Następny krok: pwsh artifacts/truck-r1/baseline.ps1.

Krok 4: Library skopiowano bez błędów (53144 pliki). Baseline czeka na slot 4/4; równolegle uruchomiono wymagane testy GIS. Przygotowano jawne prostokątne ROI oraz arkusze przed/po do 960 px. Następny krok: uv run --project tools/worldgen python artifacts/truck-r1/measure.py before (po renderze).

Krok 5: zapisano SHA-256 shaderów, TruckLights i wszystkich źródłowych FBX zewnętrza/naczepy przed zmianami. Baseline nadal w kolejce Unity, bez uruchomienia poza blokadą. Następny krok: po zapisaniu baseline zmierzyć ROI i poprawić zgodność FragFast.

Krok 6: przed pierwszym startem Unity poprawiono wybór sceny: High używa WorldC_High, Low WorldC. Zatrzymano wyłącznie własny proces czekający na slot i wznowiono kolejkę. Następny krok: pwsh artifacts/truck-r1/baseline.ps1.

Krok 7: przygotowano adapter diagnostyczny w art-source/truck/exterior/qa. Generuje tylko ignorowany kod edytora, zachowuje przywracanie materiałów i dodaje tymczasowy ciemny pigment oraz osobny katalog wyników. Jeszcze go nie aktywowano. Następny krok: po baseline uruchomić prepare_round_0115.py i cztery kontrole pigment/refleks.

Krok 8: zapisano procedurę czterech kontroli lakieru: biały/ciemny × odbicie włączone/wyłączone radiancyjnie, bez zmiany szorstkości podłoża. Adapter zachowuje kontrolę SHA produkcji i przywraca materiały w finally. Następny krok: pwsh artifacts/truck-r1/paint-controls.ps1 po baseline.

Krok 9: testy GIS bazowego worktree wykazały już niepowodzenia przed jakąkolwiek zmianą produkcyjnego kodu truck. Czekamy na pełne tracebacki, aby oddzielić stan wejściowy od regresji. Baseline graficzny nadal oczekuje na slot Unity. Następny krok: odczytać artifacts/truck-r1/gis.log po zakończeniu testów.

Krok 10: dodano atrybucję i licencje obu pomniejszonych zdjęć Commons. Jawnie opisano, że są odniesieniem do materiałów, nie tym samym pojazdem i kadrem. Pierwszy render nadal odtwarza cache/kompiluje skrypty. Następny krok: obejrzeć wynik Low-overcast.
Baseline Low overcast zapisany. Następny krok: obejrzeć PNG i zmierzyć lakier, szybę oraz DRL.

Krok 11: GIS zakończone: 488 passed, 5 failed, 1 xfailed w 1297,55 s. Błędy bazowe: far-field SHA, wiadukt różnica 3 mm przy tolerancji 2 mm, przeterminowany fidelity, brak prototypu plot_drive_gravel, deterministyczność chunk 0_0. Zapisano JSON-owy patch efektów ubocznych testów i przywrócono sześć wygenerowanych plików innych dziedzin. Obejrzano arkusz Low-overcast oraz ROI: górna szyba 21,46%, dolna 19,13%, profil drzwi 3,49 punktu. Następny krok: dokończyć baseline i uruchomić kontrole pigmentu.

Krok 12: przygotowano dodatkowy pełny zestaw wszystkich kamer Low/High overcast przed i po zmianie. Będzie służył do jawnego zestawienia rendererów i instancji każdej kamery, obok kadrów zbliżeń truck w obu pogodach. Następny krok: po baseline pwsh artifacts/truck-r1/all-cameras.ps1 -Stage before-all.

Krok 13: gotowe porównanie wszystkich liczników do CSV/JSON. Skrócono odpytywanie kolejki Unity do 5 s, aby wychwytywać krótkie wolne okna. Zakończone kadry baseline są chronione znacznikiem po potwierdzeniu VISUALQA_RESULT; wznowienie pomija je. Zatrzymano wyłącznie własny oczekujący helper, bez Unity i bez cudzych slotów. Następny krok: wznowić baseline, potem all-cameras before-all.

Krok 14 — pilna aktualizacja właściciela: każde ciężkie zadanie Pythona wymaga puli heavy (max 3), pełny GIS wyłącznie na końcu rundy, w trakcie pojedyncze pliki. Przeczytano aktualny pkt 3 i skrypt z main. Nie działa żaden nasz ciężki Python; wcześniejszy GIS zakończył się przed tą instrukcją. Nowy gis-final.ps1 korzysta z aktualnego centralnego skryptu, właściciel heavy gpt-truck-r1, zwolnienie w finally. Następny krok: dokończyć baseline; gis-final.ps1 dopiero po walidacji rundy.

Krok 15: procedury korzystają teraz z aktualnego unity-slot.ps1 w main, bez edycji infrastruktury w worktree. Końcowy GIS ma lokalny limit jednego wątku BLAS/OMP/MKL. Low-clear rozpoczął render pod własnym slotem; ciężki Python nie jest uruchomiony. Następny krok: ukończyć baseline High i zestawy kontrolne.
Baseline Low clear zapisany. Następny krok: obejrzeć PNG i zmierzyć lakier, szybę oraz DRL.

Krok 16: pomiary zapisują także historyczną metodę po zmniejszeniu do 1024 px oraz dotychczasowe ROI szyby w truck-34, obok pomiaru natywnego. Dodano kontrolę bez samej przedniej tafli dla D44 przy zachmurzeniu; nie usuwa soczewek lamp ani pozostałego szkła. Następny krok: po baseline wykonać zestawy kontrolne, porównywać te same ROI i metodę.
Baseline High overcast zapisany. Następny krok: obejrzeć PNG i zmierzyć lakier, szybę oraz DRL.
Baseline High clear zapisany. Następny krok: obejrzeć PNG i zmierzyć lakier, szybę oraz DRL.
Zapisano wszystkie kamery: before-all Low overcast. Następny krok: zestawić liczniki rendererów i instancji osobno dla każdej kamery.
Zapisano wszystkie kamery: before-all High overcast. Następny krok: zestawić liczniki rendererów i instancji osobno dla każdej kamery.

Krok 17: pełne zestawy baseline: 48 kamer Low i 48 High, oba VISUALQA_RESULT OK. Kontrola white-on zapisała 12 świeżych obrazów i TRUCK_ABLATION_CLEANUP, ale proces zakończył się -1073741819 bez wymaganej sygnatury SaveCache; nie zaliczono. Zachowano log próby 1. Procedura ma unikalne logi, sprawdzenie świeżości wszystkich kadrów, fingerprint trzech źródeł i wznawianie wyłącznie zaliczonych kontroli. Generator adaptera nie nadpisuje identycznego C#, aby uniknąć zbędnych kompilacji. Następny krok: ponowić paint-controls.ps1.

Krok 18: po dodaniu wznawiania poprawiono położenie znacznika ukończenia względem try/finally; parser sprawdził wszystkie procedury PowerShell w pakiecie. Nieudana próba składniowa nie uruchomiła Unity ani nie zajęła slotu. Następny krok: wznowić kontrole pigmentu.

Krok 19: druga próba white-on spełnia dokładną regułę ADR 0083: wynik linia 681, Cleanup mono 696, abort_threads 698, brak stosu/znaczników awarii, 12 świeżych PNG po utworzeniu logu, potwierdzone przywrócenie i niezmienione trzy źródła. Dodano brakującą obsługę tej znanej sygnatury z visual-qa.ps1, zapisano klasyfikację. Próba uznana zgodnie z regułą projektu, bez nowego renderu. Następny krok: wznowić pozostałe cztery kontrole.
Zapisano kontrolę pigmentu white-off. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku.

Krok 20: niezależny recenzent potwierdził kredowy lakier, szarą szybę i równą plandekę; zalecił jako pierwszy eksperyment poprawkę premultiplied mgły w FragFast. Ocena w BASELINE-REVIEW.md, bez PASS. Białe kontrole ON/OFF są zaliczone. Wykryto, że nadrzędny Windows PowerShell przerywał długą procedurę na ostrzeżeniu Gita o końcach linii; kolejne uruchomienie ma jawne Continue na zewnętrznej powłoce, przy zachowaniu Stop i finally wewnątrz procedury. Następny krok: dokończyć ciemny pigment i brak przedniej tafli, następnie zmiana FragFast.
Zapisano kontrolę pigmentu dark-on. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku.
Zapisano kontrolę pigmentu dark-off. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku.
Zapisano kontrolę pigmentu no-pane. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku.

Krok 21: pierwsza zmiana produkcyjna — FragFast waży kolor mgły alfą tafli, tak jak pełna ścieżka. Bez zmiany wykładnika transmitancji, próbek, przebiegów i geometrii. Białe/ciemne kontrole oraz brak przedniej tafli zakończone, źródła wejściowe zachowane w markerach. High jest niezmienioną kontrolą wariantu pełnego. Następny krok: pwsh -ExecutionPolicy Bypass -File artifacts/truck-r1/render-phase.ps1 -Stage fog-only.
Zapisano fog-only Low overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano fog-only High overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.

Krok 22: kontrole radiancyjne potwierdzają obecność odbicia lakieru. High-overcast: wkład w średnią jasność drzwi 1,62 punktu na bieli i 4,66 na ciemnym pigmencie; są to wartości obrazu po przetwarzaniu, nie surowego HDR. D44 w bazie FAIL: sigma szyby/bez tafli 0,475 Low i 0,526 High. Fog-only ma 14 poprawnych kadrów. Low glass p50 19,86→19,05%, sigma 5,885→6,065; High truck-34 identyczny pikselowo, pozostałe kontrolne różnice RMSE do 0,024%. Poprawka techniczna jest mała wizualnie; mleczność nie jest zamknięta. Następny krok: obejrzeć pary review-*.jpg, niezależna ocena i umiarkowana emisja DRL.

Krok 23: niezależna ocena fog-only: zachować jako poprawkę kontraktu, brak widocznej regresji w sześciu parach, bez PASS materiału. Pierwsza ograniczona kalibracja DRL: 160000→2000 cd/m² jako WORKING_VALUE obrazu, nie pomiar fotometrii; stosunek noc/dzień 0,35 bez zmian, kodowanie RGBAHalf 1000 nitów/jednostkę zachowane. Zaktualizowano oczekiwania istniejących testów stanu i rzeczywistego dekodowania GPU. Geometria, przebiegi, keywordy i pozostałe lampy bez zmian. Następny krok: render drl-power-2000 Low/High overcast i oględziny paska.
Zapisano drl-power-2000 Low overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-2000 High overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.

Krok 24: DRL 2000 dał 1214→0 przyciętych pikseli High-overcast i 0→0 Low, lecz niezależna ocena wskazała zbyt słaby sygnał światła dziennego oraz miejscami wygląd jasnego plastiku. Nie uznano go za wariant docelowy. Kolejny ograniczony wariant roboczy: 4000 dzień / 1400 noc, bez dodawania profilu lub efektu shaderowego. Następny krok: drl-power-4000 Low/High overcast i clear; potem ocena całego frontu oraz paska.

Krok 25: procedura renderowania normalizuje listy profili i świateł przekazywane przez natywne pwsh -File oraz sprawdza komplet wskazanych kamer przy wznawianiu. Pierwsze wywołanie overcast,clear zostało zatrzymane przez walidację argumentów przed zajęciem slotu i startem Unity. Następny krok: ponowić drl-power-4000 w obu pogodach.
Zapisano drl-power-4000 Low overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-4000 Low clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-4000 High overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-4000 High clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.

Krok 26: wariant 4000 przywrócił rozległe przycięcie na High-overcast: 1209 pikseli wobec 1214 w bazie. Pozostałe trzy warunki bez pikseli RGB ≥254. W słońcu pasek przy 4000 jest wyraźnie ciemniejszy niż w bazie. Odrzucono 4000 jako rozwiązanie problemu High-overcast. Sprawdzany jest pojedynczy środkowy wariant 3000/1050, nadal WORKING_VALUE bez dodatkowych mechanizmów i kosztu renderowania. Następny krok: drl-power-3000 w czterech warunkach i ocena niezależna.
Zapisano drl-power-3000 Low overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-3000 Low clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-3000 High overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano drl-power-3000 High clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.

Krok 27: 3000 usuwa clipping w badanym ROI we wszystkich czterech warunkach, ale w słońcu pasek nadal wygląda na mocno osłabiony. Nowy ograniczony eksperyment: przywrócono surowe 160000/56000 i dotychczasowy stan sterownika; w TruckExterior dodano lokalny luminancyjny shoulder 0,8 (WORKING_VALUE odsłoniętych jednostek sceny), wyłącznie dla grupy DRL=1, przed konwersją half i maską emitera. Parametr 0 wyłącza korektę. Pozostałe lampy, hue, F0, przebiegi, próbki i geometria bez zmian. Dodano pięć rzeczywistych prób GPU dla skończoności/bound i bypassu. Następny krok: hdr-shoulder-080 w Low/High, overcast/clear; potem testy GPU i oględziny.
Zapisano hdr-shoulder-080 Low overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano hdr-shoulder-080 Low clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano hdr-shoulder-080 High overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano hdr-shoulder-080 High clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.

Krok 28: HDR shoulder 0,8: clipping w stałym ROI 0 we wszystkich czterech warunkach. High-overcast p99 ROI 96,44%, Low 89,18%; ROI zawiera otoczenie. Niezależna ocena: zachować do walidacji, DRL czytelny także w clear, bez widocznych zmian reflektorów/kierunkowskazu/obudowy; gradient w overcast nadal subtelny. Nie ma PASS całości truck ani pomiaru GPU telefonu. Następny krok: 11 testów TruckLampEncodingTests pod slotem Unity, następnie kanoniczna regeneracja truck/trailer i końcowe kamery.
EditMode lamp-focused: 11/11, failed 0, skipped 0, exit 0. XML i JSON w pakiecie. Następny krok: przy błędzie odczytać konkretny test; przy powodzeniu kontynuować walidację rundy.

Krok 29: skupione EditMode/GPU TruckLampEncodingTests: 11/11 passed, 0 failed, 0 skipped, exit 0. Zapisano XML/JSON. Przygotowano odtwarzalny kanoniczny TruckAssetBuilder, TrailerAssetBuilder, WorldTruckInstaller i migawki hashy oraz semantycznych pozycji/rendererów prefabów. Migawki Pythona również korzystają z puli heavy, Unity z oddzielnego slotu. Następny krok: canonical.ps1, porównanie geometrii/pozycji, potem końcowe kadry i pełne testy rundy.
Krok 30: kanoniczny builder zatrzymał się na brakującym, ignorowanym źródle wnętrza LOD0. Skopiowano istniejący FBX z main bez zmiany źródeł kabiny; zapisano porównanie SHA. Slot zwolniony po błędzie. Następny krok: ponowić kanoniczną regenerację.
Krok 31: przygotowano arkusze zdjęcie | render o szerokości 960 px, jawnie oznaczające różne pojazdy, pozy i światło. Regeneracja czeka na limit heavy; nie uruchomiono równoległych ciężkich procesów.
Krok 32: przygotowano końcowe zestawienie dopasowanych metryk przed/po, w tym D44 względem kontrolnego kadru bez szyby. Skupione testy GPU obejmują stan dzień/noc, kodowanie half, dodatnią i zerową ekspozycję oraz wyłączenie shoulder. Wszystkie 11 przypadków passed. Oczekiwanie na heavy trwa; brak dodatkowych ciężkich zadań.
Kanoniczny truck zakończony poprawnie. Następny krok: dokończyć instalację i porównać migawkę wygenerowanych zasobów.
Kanoniczny trailer zakończony poprawnie. Następny krok: dokończyć instalację i porównać migawkę wygenerowanych zasobów.
Kanoniczny install zakończony poprawnie. Następny krok: dokończyć instalację i porównać migawkę wygenerowanych zasobów.
Zapisano final-candidate Low overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano final-candidate Low clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano final-candidate High overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano final-candidate High clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Krok 33: końcowy kandydat po kanonicznym builderze ma komplet 28 kadrów, 7 kamer × Low/High × overcast/clear. Przygotowano sekwencję końcowej kontroli Medium, zmierzchu, kadru bez szyby, wszystkich kamer i pełnego EditMode. Każde Unity ma własny acquire/finally release; końcowy GIS pozostaje oddzielnym ostatnim krokiem rundy.
Zapisano final-medium Medium overcast, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.
Zapisano final-medium Medium clear, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po.

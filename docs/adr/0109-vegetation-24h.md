# ADR 0109 — Roślinność w cyklu 24 h

## Runda r1

Stan: ograniczona korekta edytorowa B oceniona PASS przez niezależnego krytyka. Ogólny realizm pozostaje FAIL. Wydajność i bramka telefonu pozostają UNVERIFIED.

Recenzja 0088 wskazała trawę bez wariacji w skali metrów, prześwietlone korony Putry, walcowate żywopłoty i uproszczone sosny. Punktem odniesienia jest aktualny main 4c9905b1, nie dawna macierz 0088.

Najpierw odtwarzamy baseline Low/High w clear/overcast. Maska B opisuje stan koszenia i suchości, a nie zinwentaryzowane uszkodzenia. Zmiana nie może tworzyć jednolitej piaskowej obwódki wokół każdego trawnika. Pola mają skalę metrów i są zakotwiczone w świecie. Zachowujemy R (odległość), G (las) i A (zmapowane odsłonięte podłoże).

Budżet Low: brak dodatkowych draw calls, trójkąty do +2 procent względem tej samej kamery. Zmiany podłoża wykorzystają istniejące maski i próbki tekstur. Szybka ścieżka lasu pozostaje aktywna. Wartości artystyczne są WORKING_VALUE; wyniki telefonu są UNVERIFIED, ponieważ telefony należą do lidera.

Dowody i kolejne kroki: artifacts/vegetation-r1/STATUS.md. Raport rundy powstanie po kontroli obrazów i testach.

### Doprecyzowanie po baseline r1

Baseline z własnej regeneracji main 4c9905b1 obejmuje 268 obrazów kontrolnych (67 kamer razy Low/High i clear/overcast) oraz 54 kadry fotograficzne. Zdjęcia zachowują proporcje, źródło i licencję. Pozy pozostają UNVERIFIED.

W masce B rozdzielono jawne trawniki OSM od poboczy; pole 8 m i 2,5 m opisuje wyłącznie roboczą suchość i koszenie. Sucha materia w VegetationGround.hlsl korzysta z istniejących sampli i jest dodana za istniejącymi flagami gruntu w WorldPBR oraz WorldSurface. Wariant B mnoży istniejące fotograficzne albedo, które zawiera już liniowe _Tint i _AlbedoScale. Nie nakłada stałej barwy w miejsce detalu. Parametry pigmentu i amplitudy są WORKING_VALUE. Bez nowych próbek, przebiegów, wariantów i pól QualityProfile.

Lokalna wysokość pokrywy i rdzenia jest włączona flagą danych wyłącznie dla aktywnych berberysów rond. Inne prototypy żywopłotu zachowują wcześniejsze wzory. Syntetyczne narożniki ligustru i tui ujawniły osobne defekty; nie deklarujemy ich naprawy. Liczba trójkątów czterech aktywnych żywopłotów: 18402 przed i po generacji.

Eksperyment samocienia kart liściastych wycofano: w próbie A nie poprawił Putry, a przyciemnił DK8. Vegetation.shader zachowuje baseline, w tym VEG_FAST i ForestFastPath. Korony Putry oraz sylwetki sosen pozostają otwarte; nie deklarujemy ich naprawy. Koszt GPU A16 pozostaje UNVERIFIED.

Stary ROI koron Putry zawierał również zielony słup i fasadę. Nowy stały ROI to (0.80,0.32,0.96,0.42); baseline p50 wynosi Low 58,106 i High 76,567. Obszar trawy pomiędzy chodnikiem a jezdnią opisuje stały wielokąt w review_images.py; Low-overcast ma odchylenie średnich pełnych bloków 32 px 3,614 (18 bloków). Starszy mieszany ROI zostaje w danych audytowych, bez utożsamiania go z samą trawą.

Zgodnie z pilną aktualizacją właściciela wszystkie dalsze ciężkie generacje i testy Pythona wymagają puli heavy (3 zadania), a pełny GIS uruchamia się dopiero na końcu rundy. import-safe.ps1 blokuje niegotowe wejścia, aby importer nie uruchamiał ukrytego build_all poza tą pulą.

### Odrzucony wariant A

Pełne 322 obrazy po zmianie zachowano w artifacts/vegetation-r1/candidate-a-rejected. Mieszanie albedo ze stałym suchym kolorem spłaszczało detal: grass-only Low-overcast std bloków 3,614 → 1,841, High 2,981 → 1,066. Wariant B zachowuje detal mnożeniem; Low-overcast daje 5,170 w tym samym obszarze (18 bloków). To wskaźnik wariacji sRGB, nie pomiar wilgotności ani samodzielny dowód realizmu.

Surowe hashe 64 assetów kolizji różnią się po imporcie. Importer usuwa i tworzy zasoby z nowymi identyfikatorami podzasobów; hash pliku nie weryfikuje więc równości geometrii. Kod dróg i fizyki nie jest zmieniany. Nie deklarujemy bitowej identyczności kolizji.

### Wynik pełnej oceny B

Zapisano 322 obrazy przed i 322 po: 67 kamer Low/High razy clear/overcast oraz 27 kadrów fotograficznych w dwóch profilach. Każde z 322 porównań ma delta draws 0 i delta triangles 0%; wywołania instancji podano osobno w all-camera-costs.csv. Metryki trawy grass-only przed/po: Low-overcast 3,614/5,170; Low-clear 4,416/5,476; High-overcast 2,981/3,900; High-clear 3,179/3,495. Mediana sRGB wzrosła też o około 18–19 jednostek, więc poprawka rozjaśnia i osusza wygląd, nie tylko zwiększa wariację.

Niezależna recenzja: docs/reports/visual/2026-11-11-vegetation-0109-r1.md. Brak nowej regresji B blokującej ograniczoną korektę. Sosny, tuje, skład nasadzeń Putry i dalszy realizm berberysu pozostają backlogiem. EditMode 261/261; testy celowane 12/12. Pełny GIS na końcu rundy: 495 passed, 1 xfailed, 1 failed w 612,15 s. Jedyny błąd to test_road_fidelity.py::test_report_not_stale: siedem hashy raportu drogowego nie odpowiada źródłom. fidelity-stale-baseline-proof.json potwierdza nieaktualność także względem blobów bazowego 4c9905b1 oraz brak zmian tych źródeł. Raportu cudzej dziedziny nie regenerowano. Audyt posttests-audit.json: brak zmian źródeł po renderach i brak zmian wyjść kanonicznych po testach.

Do integracji dostarczamy kod i pełne migawki wyników w artefaktach. Wspólne metadane po własnej regeneracji, zawierające też różnice bazowe spoza vegetation, przywracamy w indeksie roboczym przed kolejną rundą; lider musi regenerować świat na swoim aktualnym main. Nie przenosimy do commita cudzych zmian dróg ani budynków. Potencjalne konflikty: addytywne wywołania w WorldPBR/WorldSurface oraz dane generowane, dla których obowiązuje main i regeneracja.

## Runda r3 — rozpoznawalność zieleni G3-B, D51 B8

Druga runda bieżącego cyklu używa gpt-vegetation-r3, ponieważ dawna r2 jest zajęta przez inny worktree. Po merge main bez konfliktów nowy HANDOVER skierował do vegetation bloker B8 z recenzji D51: brak dużych drzew w kadrze sbs-g3-b-297817221966185. Ten priorytet poprzedza dalszą kalibrację palet.

Ortofoto GUGiK 2024, pin 19d7c3ca5d2192b1d0367c8d039e41aa60221927755b45c6a6763e933d96258b z ortho.json, potwierdza cztery odczytane korony przy Andersa. Zdjęcie zsolt z 2017-07-29 (CC BY-SA 4.0) pokazuje charakter tej zieleni. Punkty są środkami koron, nie pomierzonymi pniami: niepewność około 3 m, WORKING_VALUE. Wysokość 12,5–15 m i lipa jako zastępnik liściastego również pozostają WORKING_VALUE, bez deklaracji gatunku botanicznego.

Dane umieszczono w posiadanym vegetation.py, bez zmiany overrides.yaml, geometrii dróg ani landmarku JRG2. Wariant A zaakceptował dwa z czterech punktów, dwa odrzucił blocked. Pozostałe instancje i 130 GLB były identyczne z bazą. Próba B/120 Low dodała jednak 4 wywołania instancji (205 do 209), więc A odrzucono. Ablacja bez nowych drzew po świeżym imporcie dała ponownie 205 wywołań, 129 instancji oraz PNG identyczny z pierwotnym baseline. Przyrost A pochodzi z danych drzew, nie z samego importu.

B jest próbą zastąpienia pobliskiego, losowego samosiewu dojrzałym drzewem w potwierdzonej koronie. Zachowuje jego prototyp, wariant, yaw/lean, liczbę rekordów i komórkę 64 m zgodną z InstanceImporter.CellM. Donorem może być wyłącznie syntetyczny liściasty z końcówką źródła :self, w roboczym promieniu 10 m; nigdy mapowane OSM/BDOT, sosna ani krzew. Korzeń musi przejść blocked/zc, pozostać do 3 m od niepewnego środka korony i co najmniej 1,8 m od innych pni. Brak dawcy odkłada punkt zamiast tworzyć nowy bank. Liczba zaakceptowanych zamian i koszt B wymagają aktualnej generacji oraz renderów.

Baseline: 268 kontrolnych obrazów z r1 B ponownie wykorzystanych po zgodności siedmiu hashy źródeł/kamer i 130 GLB; nie opisujemy ich jako świeże. Dodatkowo wyrenderowano 100 nowych obrazów dla 25 póz B w Low/High clear/overcast. Klasy C są pominięte. Metadane kanoniczne przed rundą oraz metadane wcześniejszego importu B są zapisane osobno: snapshot-baseline i snapshot-baseline/imported-world. Korektę błędu separatorów Windows w pierwszym helperze ujawnia STATUS i baseline-provenance.json; nie dotyczy zgodności kodu, GLB ani PNG.

Test przed funkcją A: 3 failed i 1 passed; po A: 16/16 testów celowanych. Przejście testów nie uchroniło A przed odrzuceniem wizualnym/budżetowym. Testy zmienionej polityki B czekają na heavy; wynik jest w STATUS. Pełny GIS i EditMode będą dopiero na końcu rundy. Stan wizualny B, budżet i D51 pozostają niepotwierdzone do aktualnych renderów i niezależnego krytyka. Telefony są poza zakresem tej sesji.

### R3 — decyzja o odrzuceniu prób, walidacja przywrócenia w toku

Wcześniejszy opis A i B jest dziennikiem eksperymentów, nie przyjętą decyzją produkcyjną. A odrzucono po wzroście łącznych wywołań Low 665 do 669. B1 przeszedł pełny generator i 22 testy celowane, zastąpił jeden samosiew, odłożył trzy punkty i nie dodał rekordów. Próba Low zachowała 460 wywołań statycznych i 205 instancji, ale nie zmieniła żadnego piksela w stałym obszarze koron. Różnice 5307 pikseli leżą w niższym pasie obrazu. Nie certyfikowano B1 na pełnej macierzy kamer.

Diagnostyka wysokości istniejącego klonu 8 do 13,8 m była tylko zmianą wejścia renderera. Nie nazywamy jej wyprodukowanym B2. Powiększyła rzadką sylwetkę, bez odtworzenia zespołu gęstych koron. Odrzucono ją wraz z B1; niezależny krytyk potwierdził oba werdykty. Dowody są w rejected-comparison.jpg oraz VISUAL-CRITIC-B.md.

Produkcję vegetation.py i testy przywrócono do r1 w f5f60b64. Generator przywróconego kodu zakończył się w 455,7 s. Kontrola restored-world-proof.json potwierdziła 130 zgodnych GLB, 64 pliki instancji i siedem pinów źródeł względem baseline; 15 Megascans, fallback false. Końcowy GIS, import, probe i EditMode są nadal w sekwencji walidacji. Nie jest to jeszcze zamknięta runda.

Dodatkowe ograniczenie: cztery odczytane korony leżą przed JRG2; nie dowiedziono, że są tymi samymi drzewami pasa dzielącego, których dotyczy B8. Nowy feedback lidera wskazuje korekty pozy G3-B jako główny bloker. Przed następnym przypisaniem nasadzeń potrzebna jest poprawiona poza SBS. B8 pozostaje otwarte, a odrzuconych punktów nie należy integrować jako jego naprawy.

Następna próba po zakończeniu walidacji i merge main będzie dotyczyć berberysu wyglądającego jak bordowe bale, zgodnie z feedbackiem s11 i recenzją zbiorczą r1. Hipoteza rdzenia i kontrakt materiałów są zapisane w CLOSING-NOTES.md; nie zmieniono ich podczas bieżącej walidacji. Nie edytowano dróg, landmarków ani overrides.yaml.

### R3 — końcowe dowody i zamknięcie

Pełny GIS: 525 passed, 1 xfailed, 1 failed w 1390,34 s (wliczone wstrzymanie watchdog). Jedyna porażka to test_road_fidelity::test_report_not_stale: raport i siedem jego źródeł są niezmienione względem bazy, raport był nieaktualny już tam. Nie traktujemy tego jako zielonego GIS i nie regenerujemy cudzej dziedziny.

Import przywróconego świata przeszedł. Probe B/120 Low-overcast ma SHA identyczny z baseline, co potwierdził niezależny krytyk po obejrzeniu obu PNG. EditMode 261/261. Po GIS i Unity nadal zgodne 130 GLB, 64 pliki instancji i siedem pinów źródeł; posttests-audit nie wykazał driftu. Krytyk akceptuje tylko przywrócenie obrazu. B8 pozostaje otwarte, bez pełnej macierzy after i bez akceptowanej zmiany produkcyjnej r3.

Siedem wspólnych skutków ubocznych generatora zachowano w artefaktach, po czym przywrócono z HEAD. Snapshot-restored oraz generator-side-effects opisują wynik użyty do importu; kanoniczne metadane wróciły do stanu sprzed rundy. Lider musi regenerować po integracji. REPORT oraz docs/reports/visual/2026-11-12-vegetation-0109-r3.md podają pełny zakres dowodów. Następna runda: berberys, z odizolowaną propozycją, która nie została jeszcze wdrożona ani wyrenderowana.

## Runda r4 — berberys, w toku; brak decyzji o integracji

Gałąź gpt-vegetation-r4, baza po merge main c3cf303d (pierwotnie 7c9b4ca6). Po zmianach światła i innych dziedzin wykonano całkowicie świeży baseline: 368 obrazów, 67 kamer kontrolnych i 25 fotograficznych B w Low/High clear/overcast. Autor obejrzał wszystkie 40 arkuszy. Nie wykorzystano PNG z r1 ani r3. Materiały wygenerowano raz, 446 s; World baseline 614,8 s. Piny obejmują 130 GLB, 64 pliki instancji, 617 wejść produkcji i dekodowane wejścia kolizji 64 Low chunków. Megascans: 15 dostępnych, fallback false.

### R4 A — odrzucony materiał warstwy wewnętrznej

Berberys otrzymał na istniejącym rdzeniu ten sam materiał alpha liści co shell, UV w skali HEDGE_TILE_M i osobną fazę. Pozostałe rodziny nie zmieniły tej ścieżki. Oczekiwany test RED: 1 failed, 4 passed; po dostosowaniu dawnych selektorów materiałów zachowano testy geometrii, a 18 celowanych testów przeszło w 3,27 s. Pierwsza próba GREEN dała 16 passed i 2 failed; zachowano ją osobno, a generator nie został wtedy uruchomiony.

World A zakończył się poprawnie w 538,6 s. Jedyną zmianą źródłową był plantings.py; wszystkie 64 pliki instancji, dane kolizji i far_field GLB pozostały identyczne. Zmieniły się tylko chunk_6_6 Low/High i metadane świata. Nasadzenia: cztery, 94,3 m², 18 402 trójkąty przed i po. Import oraz 16 próbnych ujęć zakończono. W dwóch kadrach berberysu wywołania spadły o jeden, w pozostałych bez zmian; raportowane trisK bez zmian. Osiem kontroli fence_2/remiza ma identyczne bajtowo PNG.

Autor i niezależny krytyk obejrzeli wszystkie osiem porównań ze zdjęciem Rakoon, CC0, 2020-11-02. Boki stały się drobniejsze, ale duży płaski wierzch nadal wygląda jak pełna bryła. A odrzucono jako wersję końcową. Nie ma pełnej macierzy after A ani końcowego GIS dla A. Dowody: artifacts/vegetation-r4/SELF-REVIEW-probe-a.md, VISUAL-CRITIC-probe-a.md, probe-a-comparison.json i osiem arkuszy berberis-review-probe-a o szerokości 960 px. Zdjęcie jest odniesieniem wyglądu, poza i sezon nie są kalibracją wymiarów. Koszt GPU i migotanie w ruchu pozostają UNVERIFIED.

### R4 B — naprawa obrysów, jeszcze bez wyniku testów i renderów

Mała analiza czterech rzeczywistych obrysów na płaskim gruncie ujawniła osiem samoprzecinających ringów core/shell. _delaunay_fill prawidłowo je odrzucał, po czym _fill przechodził do awaryjnego ear_clip: zero punktów wewnętrznych, maksymalne krawędzie 16,2–19,7 m. To konkretna przyczyna dużych płaszczyzn i niewykonywania kodu reliefu oraz pędów wewnątrz góry. Wycofano pierwotną hipotezę zmiany samych wysokości istniejących punktów.

B, za flagą offset_rings wyłącznie berberysu, tworzy prawidłowe offsety Shapely z orientacją CCW i stabilnym początkiem. Nie edytuje triangulatora roads ani override. Odmawia pustych, rozłącznych obszarów i otworów, nie wybiera największego fragmentu po cichu. Drobna wariacja ringa jest ograniczana, jeśli narusza jego poprawność. Cap berberysu propaguje błąd zamiast znikać po wyjątku. Tekstury A pozostają bez zmian.

Analiza B: osiem poprawnych capów, maksymalna krawędź poniżej 0,98 m. Wąski cap może poprawnie nie mieć punktów wewnętrznych. Łącznie 11 560 tris w analizie płaskich obrysów wobec 18 402 w A. Równomierne próbkowanie aproksymuje wejściowy band: różnica powierzchni −0,159 do −0,224%, Hausdorff brzegu 0,060–0,0851 m. To zmiana siatki, nie globalnej skali świata ani danych źródłowych; nie deklarujemy zachowania każdego dawnego wierzchołka.

Niezależna recenzja kodu wymaga testów globalnego nakładania pasów, przynależności core do shell i rzeczywistego prześwitu względem triangulowanej góry. Dodano te kontrole na czterech obrysach, na płaskim i nachylonym gruncie, oraz kontrolę braku awaryjnego ear_clip. W momencie tego zapisu 27 celowanych testów B czeka na heavy w sekwencji 73347; World, import i probe-b jeszcze nie wykonane. Nie ma PASS geometrii, budżetu ani wyglądu. Przy akceptacji obowiązuje +0 draws i ≤+2% tris w każdej kamerze Low, pełna macierz i niezależny krytyk, potem końcowy GIS/EditMode. Runda pozostaje otwarta.

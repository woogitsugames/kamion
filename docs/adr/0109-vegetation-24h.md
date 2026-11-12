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

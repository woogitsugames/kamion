# Audyt mapy r9 — lista błędów (pisana przyrostowo)

Audytor: agent map-audit-r9 (gałąź `worktree-agent-a059a8b723e8c235e`). Stan: main `ac2b673`, `_Generated` skopiowany z main (import 2026-11-10 17:00).
Kamery: `scripts/map-audit-cameras.py` -> `artifacts/map-audit-r9/cameras/audit_cameras.json` (403: przód prawy pas co 20 m = 121, tył prawy 147, lewe pasy co 40 m na jezdniach jednokierunkowych wielopasowych 112, z góry 23).
Oko 2,5 m nad kolizją drogi (Gate3Cameras.HeightAboveRoad), FOV 55 (CameraRig.cabFov), patrzy 30 m do przodu. Render: WorldC, High, overcast, 1600x738.
Kierunek "r" (powrót) = najkrótsza ścieżka DK8/DK19 -> Kwadrat Park po grafie (2,94 km, inna niż odwrócona trasa startowa, bo jednokierunkowe).
Indeks kamer (id -> E,N, lat/lon, kurs, krawędź OSM, pasy, szerokość, turn:lanes): `cameras/audit_cameras.index.csv`.
Priorytety: P0 blokuje jazdę / oczywisty dla gracza, P1 wyraźny, P2 kosmetyka. Status: OPEN dopóki naprawiacz nie zmieni.

## Błędy

### MA-001 · P0 · krawężnik/obstacle · krawężnik w poprzek jezdni w miejscu włączenia łącznicy do Andersy
- Kadr: `renders_960/au_f_s0640.jpg` (też `au_fl_s0640`), montaż `montage/au_f_s0640.jpg`
- Pozycja: E 315.6, N -574.0 (lat 53.153238, lon 23.164086), kurs 296°; krawędzie OSM w606396458 (trunk_link 1 pas) -> w536419675 (trunk_link 2 pasy, węzeł n3341716400)
- Opis: na całej szerokości lewego pasa leży poziomy pas krawężnika (podniesiony beton) prostopadle do kierunku jazdy; dodatkowo krawężnik podłużny biegnie środkiem asfaltu (x≈545 px) i urywa się w jezdni. Ciężarówka najedzie na krawężnik na pasie ruchu.
- Rzeczywistość: ortofoto GUGiK 2024 (`Data/raw/derived/bialystok-industrial-c/ortho_0p25m.tif`, montaż): łącznica gładko przechodzi w pas jezdni Andersy, żadnych krawężników na jezdni.
- Przyczyna (przypuszczenie): `tools/worldgen/roads` — zamknięcia (end-caps) krawężników łańcuchów na styku dwóch jednokierunkowych krawędzi z różną liczbą pasów (1 -> 2) generowane jako krawężnik w poprzek; brak scalenia łańcuchów w węźle stopnia 2 (zmiana `lanes`).

### MA-002 · P0 · krawężnik/wysepka · pas wjeżdża w krawędź wysepki i płyta krawężnika leży na jezdni przed włączeniem do Andersy
- Kadr: `renders_960/au_f_s0620.jpg`, montaż `montage/au_f_s0620.jpg`
- Pozycja: E 331.8, N -582.9 (lat 53.15315, lon 23.164321), kurs 296°; w606396458 (trunk_link, lanes=1, width 8)
- Opis: łukowy krawężnik (biała krawędź) przecina lewą część jezdni od pasa dzielącego w stronę osi, lewy pas (przerywana) kończy się na nim; po prawej na asfalcie leży betonowa płyta/krawężnik (ok. 0,3 m) jak resztka wysepki; ciemna łata asfaltu w prostokącie.
- Rzeczywistość: ortofoto: łącznica z ronda Bieżeństwa włącza się prostym klinem, jezdnia ciągła, malowany klin (powierzchnia wyłączona), bez wysepki z krawężnikiem.
- Przyczyna: `roads` — geometria klina (gore) / wysepki rozdzielającej w węźle n3341716400; ta sama klasa co zgłoszenie właściciela (pas w wysepkę).

### MA-003 · P1 · obiekt na pasie · zamknięte szlabany w poprzek pasów bramy Kwadrat Park, bez kolizji (ciężarówka przejeżdża przez ramię)
- Kadr: `renders_960/au_f_s0240.jpg`, montaż `montage/au_f_s0240.jpg`; widać też w kierunku powrotnym przy bramie
- Pozycja: E 620.6, N -594.0 (lat 53.152899, lon 23.168619), kurs 215°; w194536287 (service, 1 pas)
- Opis: oba ramiona szlabanu (czerwone i białe) opuszczone w poprzek obu pasów. `InstanceImporter.cs:123` celowo nie daje im kolizji („open in gameplay”), więc gracz przejeżdża przez ramię — oczywiste dla gracza.
- Rzeczywistość: ortofoto: brama z wysepką i budką, szlabany otwierane; w grze powinny być podniesione (albo otwierać się przed ciężarówką).
- Przyczyna: `tools/worldgen/streetscape/gate.py` (boom „closed position”), `InstanceImporter` bez kolizji/animacji.

### MA-004 · P2 · nawierzchnia · ostre poprzeczne szwy tonu asfaltu między łatą skrzyżowania a odcinkiem drogi
- Kadry: `renders_960/au_f_s0920.jpg` (wyraźna poprzeczna krawędź jaśniejszy/ciemniejszy asfalt), `au_f_s0900`, `au_f_s1040`, `au_f_s1060`, `au_f_s1100` (ciemny prostokąt na pasie), `au_f_s0620` (ciemna łata)
- Pozycja (przykład s0920): E 69.6, N -446.0 (lat 53.154514, lon 23.160528), Andersa w560802657
- Opis: powierzchnie skrzyżowań (junction patch) mają inny ton/UV niż łańcuchy drogi, granica prosta i ostra w poprzek pasów; przy s1100 prostokątna łata w środku pasa. Wygląda jak błąd, nie jak łata remontowa.
- Rzeczywistość: ortofoto: jednolity asfalt Andersy w tych miejscach.
- Przyczyna: `roads` mesh skrzyżowań — osobny materiał/UV world-space bez wyrównania tonu, brak blendu szwu.

### MA-005 · P1 · sygnalizacja · sygnalizator obrócony bokiem (o ~90°) przy wjeździe na łącznicę do ronda Putry
- Kadr: `renders_960/au_f_s1420.jpg` (sygnalizator po prawej, daszki komór skierowane w bok, nie do kierowcy)
- Pozycja kamery: E -331.2, N -151.4 (lat 53.157365, lon 23.154803), kurs 321°; obiekt ok. 12 m przed, 5 m w prawo
- Opis: głowica sygnalizatora na słupie przy krawężniku stoi lica w poprzek drogi; dla żadnego kierunku nie jest czytelna. Do tego stoi za skrzyżowaniem, na początku łącznicy, gdzie nie ma linii zatrzymania.
- Rzeczywistość: na tym odcinku łącznicy (ortofoto, Mapillary do weryfikacji) brak sygnalizatora; sygnalizatory są przy liniach zatrzymania skrzyżowania Andersa (s≈1340).
- Przyczyna: `tools/worldgen/streetscape/furniture.py` — umieszczanie `highway=traffic_signals` z OSM: obrót wg stycznej złej krawędzi (węzeł na styku łańcuchów), brak powiązania z kierunkiem `traffic_signals:direction`.

### MA-006 · P1 · oznakowanie (przepisy) · linia zatrzymania przed sygnalizacją jako P-13 (prostokąty) zamiast P-14 (ciągła)
- Kadr: `renders_960/au_f_s1340.jpg` (też tył: kadry `au_r_*` przy tym skrzyżowaniu)
- Pozycja: E -269.0, N -200.7 (lat 53.156891, lon 23.155689), kurs 309°; Andersa w1093579589, skrzyżowanie z sygnalizacją
- Opis: w poprzek trzech pasów przed sygnalizatorami namalowana linia z prostokątów (P-13 „linia warunkowego zatrzymania” — do znaku A-7). Przy sygnalizacji obowiązuje P-14 „linia zatrzymania” (ciągła, szer. 0,5 m) — rozporządzenie w sprawie znaków i sygnałów drogowych, zał. 2 (UNVERIFIED numer paragrafu).
- Rzeczywistość: ortofoto: linia ciągła przed skrzyżowaniem (sprawdzić na montażu).
- Przyczyna: `tools/worldgen/roads` marking — wybór typu linii zatrzymania nie uwzględnia `highway=traffic_signals` w węźle/na podejściu.

Uzupełnienie MA-005: Mapillary 1424981177846267 (2018-07-21, 17 m od kamery, `Data/raw/mapillary/bialystok-industrial-c/1424981177846267.jpg`, montaż `montage/au_f_s1420.jpg`) — na tym odcinku nie ma żadnego sygnalizatora.
Uzupełnienie MA-006: ortofoto (montaż `montage/au_f_s1340.jpg`) pokazuje na tym skrzyżowaniu **przejście dla pieszych (zebra P-10) w poprzek jezdni Andersy** — w grze go nie ma (brak zebry i znaków D-6). Mapillary 749579949015677 (2 m od kamery): sygnalizatory na słupach po obu stronach, bez wysięgnika nad jezdnią.

### MA-007 · P1 · znak · „90” zasłonięty ścianą i niezgodny z rzeczywistością (tam 70 + zakaz wyprzedzania dla ciężarówek)
- Kadr: `renders_960/au_f_s1820.jpg`, montaż `montage/au_f_s1820.jpg`
- Pozycja: E -544.1, N 150.1 (lat 53.16018, lon 23.151888), kurs 1°; al. Tysiąclecia w882366267 (OSM maxspeed=70)
- Opis: tarcza B-33 „90” stoi wewnątrz/za niższą brązową ścianą ekranu — prawa połowa tarczy przecięta przez panel. Wartość 90 kłóci się z OSM (70 na tej krawędzi; 90 dopiero od w238861874, s≈1996).
- Rzeczywistość: Mapillary 312705613662497 (2017-07-29, 37 m, kurs zgodny): B-26 (zakaz wyprzedzania przez ciężarowe) nad B-33 „70”, na słupie przed ekranem, w pasie zieleni.
- Przyczyna: `streetscape/furniture.py` — znak prędkości z przejścia `maxspeed` umieszczony na złej krawędzi (wartość następnej krawędzi), offset boczny nie omija ekranów (`barrier=noise_barrier`).

### MA-008 · P1 · ekrany akustyczne · nieprzezroczyste szare panele + zdublowana druga (brązowa) ściana zamiast przezroczystych ekranów na zielonych słupach
- Kadry: `au_f_s1420`, `au_f_s1440`..`au_f_s1680`, `au_f_s1800`..`au_f_s1900` (i odpowiedniki `au_r_*`); montaże `montage/au_f_s1420.jpg`, `montage/au_f_s1480.jpg`, `montage/au_f_s1820.jpg`
- Pozycja: łącznica Andersa->Putry i al. Tysiąclecia, E -330..-545, N -150..+200
- Opis: (a) ekrany w grze to pełne szare panele betonowe; (b) przed nimi, kilka dm bliżej jezdni, druga ściana brązowych paneli o innej wysokości — dwie ściany nachodzą na siebie (podwójna geometria), znaki wchodzą w panele (MA-007).
- Rzeczywistość: Mapillary 1424981177846267, 995780104564541, 312705613662497: ekrany **przezroczyste** (szkło/PMMA) na **zielonych** słupach, z niskim pełnym cokołem; jedna linia ekranu. Gate3 notes też mówią „transparent noise screens”.
- Przyczyna: `streetscape` — dwa źródła tej samej bariery (OSM `barrier=noise_barrier` + BDOT10k/ogrodzenie) bez deduplikacji; brak materiału „transparent screen” z typologii (docs/06).

### MA-009 · P1 · geometria jezdni · nadmiarowa powierzchnia asfaltu na rozwidleniu łącznicy do ronda Putry + wysepka ze schodami i barierką na środku asfaltu
- Kadry: `renders_960/au_f_s1440.jpg`, `au_f_s1460.jpg`, `au_f_s1480.jpg`; montaż `montage/au_f_s1480.jpg`
- Pozycja: E -367.6, N -111.9 (lat 53.157738, lon 23.154294), kurs 317°; w606396463 (trunk_link, 1 pas, width 6)
- Opis: na lewo od pasa łącznicy ciągnie się szerokie pole asfaltu (kilkanaście m) bez oznakowania, w nim wysepka z krawężnikiem, schodkami i białą barierką (wygląda jak element chodnika/podpory wiaduktu zatopiony w jezdni).
- Rzeczywistość: ortofoto: wąska łącznica (1 pas) oddzielona pasem zieleni od jezdni głównej; Mapillary 995780104564541: obok łącznicy powierzchnia wyłączona z ruchu (P-21) i bariera ochronna, ekran przezroczysty na czerwonym wiadukcie, nad łącznicą bramownica z tablicami Augustów/Kuźnica.
- Przyczyna: `roads` — wypełnienie skrzyżowania/klina (junction polygon) między rozchodzącymi się łańcuchami trunk / trunk_link zbyt daleko; schody/barierka ze `streetscape` (steps/handrail z OSM) postawione na wypełnionym asfalcie.

### MA-010 · P0 · wysepka na pasie · prawy pas (powrót, wylot z ronda Putry pod wiaduktem) wjeżdża w trójkątną wysepkę z trawą i krawężnikiem
- Kadr: `renders_960/au_r_s1160.jpg`, montaż `montage/au_r_s1160.jpg`
- Pozycja: E -562.2, N -7.7 (lat 53.158774, lon 23.151481), kurs 127°; w180144451 (trunk, 2 pasy, turn:lanes left|through;left), pod wiaduktem Andersy
- Opis: przerywana linia prowadzi dwa pasy prosto, a dokładnie na osi prawego pasa zaczyna się trójkątna wysepka (trawa + pas żwiru + krawężnik). Pas nie ma oznakowania kończenia (brak P-21/strzałek P-8 skrętu, brak przejścia w klin). Ta sama klasa co zgłoszenie właściciela 2026-11-10 (pas „na wprost” w wysepkę).
- Rzeczywistość: ortofoto GUGiK 2024: oba pasy ciągną się prosto pod wiaduktem do skrzyżowania z zebrami; wysepki są z boku (rozdzielenie skrętu w prawo). Mapillary 987194858750300 (2020-08-23, 2 m od kamery, kurs zgodny): prosta wielopasowa jezdnia pod wiaduktem, nic na pasie.
- Przyczyna: `roads` — wypełnienie/wysepka skrzyżowania (junction island polygon) budowane z obrysu między krawędziami OSM bez sprawdzenia, czy przecina pasy ciągłej krawędzi; brak walidatora „wysepka ∩ pas ruchu = ∅” w `roads_qa`.

### MA-011 · P1 · pasy/oznakowanie · zwężenie do 1 pasa i linia ciągła przez zebrę na łączniku przy rondzie Putry (powrót)
- Kadr: `renders_960/au_r_s1200.jpg`, montaż `montage/au_r_s1200.jpg`
- Pozycja: E -531.3, N -30.3 (lat 53.158556, lon 23.151923), kurs 132°; w1360055407 (trunk_link, lanes 1/2, width 5,5/7,5)
- Opis: jezdnia w grze ma ~1 pas z linią ciągłą przechodzącą przez środek przejścia dla pieszych (linia P-4 namalowana przez pasy zebry).
- Rzeczywistość: ortofoto: w tym miejscu szeroka jezdnia (2+ pasy z przerywanymi), zebra przez całą szerokość; Mapillary 284801706686982 (3 m): zebra na całą szerokość, linie przerwane na przejściu.
- Przyczyna: `roads` — szerokość z BDOT10k „clamped 3.50-5.50” dla odcinka `lanes=1` (roads_qa: w1360055407 width [5.5, 7.5]) zaniża jezdnię vs ortofoto; markings: linie podłużne nie są przerywane na `crossing`.

### MA-012 · P0 · nawierzchnia/teren · garb (wybrzuszenie ~0,5–1 m) w asfalcie i nieoznakowane pole asfaltu na włączeniu łącznicy od ronda Putry do Andersy (powrót)
- Kadry: `renders_960/au_r_s1380.jpg`, `au_r_s1400.jpg`, `au_r_s1420.jpg`; montaż `montage/au_r_s1380.jpg`, `montage/au_r_s1400.jpg`
- Pozycja: E -395.3, N -142.3 (lat 53.15748, lon 23.153855), kurs 121°; w268473388 (trunk_link, 2 pasy, turn:lanes merge_to_right|)
- Opis: jezdnia zamienia się w szerokie pole asfaltu bez żadnych linii, z wyraźnym garbem/falą (nawierzchnia „zaciągnięta” do NMT lub do skarpy wiaduktu). Ciężarówka podskoczy/zawiśnie. Po prawej sygnalizator z MA-005 widoczny bokiem.
- Rzeczywistość: ortofoto: dwa pasy łącznicy z liniami, równoległe do jezdni Andersy, klin włączenia; Mapillary 514863372844360 (1 m od kamery): gładka jezdnia z liniami i powierzchnią wyłączoną (P-21) przy ekranie.
- Przyczyna: `roads` — junction patch między trunk / trunk_link zszyty z profilem terenu (heightfield NMT) zamiast z profili osi dróg; ta sama strefa co MA-009 (kierunek przeciwny). Sprawdzić `roads_qa` profile_rms w tym węźle.

### MA-013 · P2 · teren · pionowa ścianka terenu (~1,5 m) między lasem a placem przy al. Tysiąclecia
- Kadr: `renders_960/au_r_s0720.jpg`, montaż `montage/au_r_s0720.jpg`
- Pozycja: E -574.5, N 417.8 (lat 53.162597, lon 23.151667), kurs 166°; obiekt ok. 30 m przed, 12 m w prawo
- Opis: grunt leśny kończy się pionową szarą ścianą nad niżej położonym placem (asfalt), bez skarpy.
- Rzeczywistość: Mapillary 797573504490006 (2 m od kamery) / ortofoto: łagodna skarpa/trawnik.
- Przyczyna: `terrain` — skirt placu (`terrain_walls_qa`: skirt:yard_*) lub cięcie terenu pod plac BDOT bez łagodnego przejścia.

### MA-014 · P2 · oznakowanie · linia podłużna nie przerwana na przejściu dla pieszych
- Kadry: `renders_960/au_r_s1200.jpg` (linia ciągła przez zebrę), `au_f_s0340.jpg` (linia na zebrze przed rondem Bieżeństwa)
- Rzeczywistość: rozporządzenie o znakach poziomych — linie segregacyjne przerywa się na P-10 (UNVERIFIED nr §); Mapillary 284801706686982: przerwane.
- Przyczyna: `roads` markings — brak odcinania linii w strefie `crossing`.

### MA-015 · P1 · krawężnik/wjazd · krawężnik w poprzek wylotu bocznej drogi przy Andersie + wysepka ucięta prostą krawędzią (powrót)
- Kadr: `renders_960/au_r_s1720.jpg`, montaż `montage/au_r_s1720.jpg`
- Pozycja: E -125.0, N -338.9 (lat 53.155577, lon 23.157717), kurs 129°; Andersa w266084694/w266084684, węzeł z drogą boczną po prawej (n1881569071/n131612943)
- Opis: na wylocie drogi bocznej leży poprzeczny krawężnik (ta sama klasa co MA-001: zamknięcie łańcucha w poprzek jezdni); wysepka trawiasta kończy się prostym cięciem zamiast łuku; wjazd/wyjazd z drogi bocznej zablokowany krawężnikiem.
- Rzeczywistość: ortofoto: wlot drogi bocznej z kroplową wysepką dzielącą i dwoma łukami (wjazd i wyjazd), bez krawężnika na jezdni; Mapillary 862904321239283 (2 m): gładki wlot, linia krawędziowa przerwana.
- Przyczyna: `roads` — end-caps krawężników łańcuchów w węźle T + brak fillet (junction_notes „no fillet fits -> sharp” / „kerb line continued to the emerging lane edge”).

### MA-016 · P1 · pasy/oznakowanie · linie pasów kończą się ślepo, za nimi nieoznakowane pole asfaltu z uskokiem krawężnika (Andersa przy zjeździe w stronę ronda Bieżeństwa, powrót)
- Kadry: `renders_960/au_rl_s2200.jpg`, `au_r_s2200.jpg`, `au_r_s2220.jpg`; montaż `montage/au_rl_s2200.jpg`
- Pozycja: E 288.9, N -576.1 (lat 53.153233, lon 23.163687), kurs 132°; w266084694 (trunk 3 pasy, turn:lanes through|through|slight_right) -> rozwidlenie n1882690750
- Opis: trzy linie pasów urywają się w jednej poprzecznej linii, dalej szerokie pole asfaltu bez linii, prawa krawędź robi schodek (krawężnik pod kątem prostym). Gracz nie wie, który pas gdzie prowadzi.
- Rzeczywistość: ortofoto: ciągłe 2 pasy jezdni głównej + osobny pas zjazdu rozdzielony klinem, rząd drzew w pasie zieleni; Mapillary 520711125974721 (2017-07-29, 2 m): linie ciągłe, klin zjazdu.
- Przyczyna: `roads` — junction patch rozwidlenia (diverge) bez oznakowania i z prostokątnym obrysem; ta sama klasa co MA-009/MA-012 (patrz też top `montage/au_top_n2840742308.jpg`: nieoznakowany trójkąt asfaltu tam, gdzie w ortofoto jest pas zieleni/klin).

### MA-017 · P1 · oznakowanie · strzałka P-8 „w lewo” na lewym pasie Andersy, gdzie nie ma skrętu w lewo; dziwny kształt strzałki „łukiem w prawo”
- Kadr: `renders_960/au_r_s2180.jpg`, montaż `montage/au_r_s2180.jpg` (też `au_r_s1680`, `au_r_s1700`, `au_f_s1340` — strzałki skośne na pasach na wprost)
- Pozycja: E 268.3, N -571.6 (lat 53.153284, lon 23.163382), kurs 117°; w266084694 (turn:lanes through|through|slight_right)
- Opis: lewy pas ma strzałkę skośną w lewo (P-8 „w lewo/na ukos”), środkowy prosto, prawy strzałkę zakrzywioną w prawo. OSM mówi through|through|slight_right — lewy pas powinien mieć strzałkę na wprost.
- Rzeczywistość: Mapillary 878632792689769 (4 m): brak strzałek w lewo; nad jezdnią bramownica z tablicami kierunkowymi (w grze jej tu nie ma).
- Przyczyna: `roads` markings — mapowanie `turn:lanes` na decale: indeksacja pasów od złej strony albo `merge_to_left` / `slight_*` mapowane na skośną strzałkę; dodać test „liczba strzałek = lanes i zgodna kolejność”.

### MA-018 · P1 · pasy · łącznica do ronda Bieżeństwa ma w grze 1 pas, w rzeczywistości 2
- Kadr: `renders_960/au_r_s2240.jpg`, montaż `montage/au_r_s2240.jpg`
- Pozycja: E 317.1, N -600.3 (lat 53.153002, lon 23.164087), kurs 124°; w177876102 (trunk_link, OSM lanes=1, width 8; roads_qa lanes [1,2] w [5.5, 8.0])
- Opis: szeroka jezdnia (~5,5 m) z jedną krawędzią, bez podziału na pasy.
- Rzeczywistość: ortofoto: 2 pasy z przerywaną; Mapillary 1377086612666076 (1 m): dwa pasy ruchu.
- Przyczyna: dane OSM `lanes=1` na części łańcucha + clamp szerokości BDOT „3.50-5.50” — potrzebny `authored_override` lanes=2 (Data/Regions/.../overrides.yaml) lub reguła „width>=7 -> 2 pasy”.

### MA-019 · P2 · roślinność · brak szpaleru drzew między Andersą a ścieżką rowerową
- Kadry: `au_r_s2240`, `au_rl_s2200`, `au_r_s2180` (trawa bez drzew)
- Rzeczywistość: ortofoto (montaże jw.): gęsty rząd drzew w pasie zieleni po prawej; Mapillary 520711125974721: drzewa przy jezdni.
- Przyczyna: `streetscape` vegetation — brak `natural=tree_row` w OSM lub nie wykrywane z ortofoto/LoD; do authored_overrides.

### MA-020 · P2 · obiekty · zadaszenie (wiata) bez stacji/budynku przy Andersie; rzeczywiście budynek handlowy/myjnia
- Kadry: `au_r_s1920`, `au_r_s1940`, `au_r_s1960` (dwie wiaty po obu stronach: słupy + cienki dach widziany krawędzią), montaż `montage/au_r_s1940.jpg`, `montage/au_r_s1920.jpg`
- Pozycja: E 57.3, N -459.3 (lat 53.154401, lon 23.160332), kurs 117°
- Rzeczywistość: ortofoto: długi budynek z beżowym dachem przy jezdni; Mapillary 307728661020603 (4 m): oświetlony obiekt przy drodze (sprawdzić w dzień).
- Przyczyna: `buildings` — `building=roof` z BDOT/OSM generowany jako sama wiata; typologia nie rozpoznaje pawilonu.

### MA-021 · P1 · ekran/znak · drugi przypadek: znak „70” wewnątrz ekranu i krótki ciemny panel na krawędzi jezdni (al. Tysiąclecia, powrót)
- Kadr: `renders_960/au_r_s0920.jpg`, montaż `montage/au_r_s0920.jpg`
- Pozycja: E -559.4, N 221.6 (lat 53.160829, lon 23.151722), kurs 182°; w266084696
- Opis: tarcza B-33 przenika panel ekranu; ekran zaczyna się pionowym, ciemnym, niższym panelem stojącym tuż przy linii krawędziowej (ok. 0,5 m od pasu). Ekrany pełne zamiast przezroczystych (MA-008).
- Rzeczywistość: Mapillary 1340597302993462 (2017-07-15, 5 m): ekrany przezroczyste na całej długości, odsunięte za barierą, bez znaku w ekranie.
- Przyczyna: jak MA-007/MA-008 (`streetscape/furniture.py` offset znaków nie omija `noise_barrier`; dwa źródła ekranu).

## Kadry wykluczone (artefakt kamery audytu, nie błąd gry)
- `au_fl_s2360`, `au_rl_s0480`: kamery przy wiadukcie al. Tysiąclecia z `seat=file` (NMT + 2,5 m) wylądowały w nasypie pod pomostem. Nie oceniać.
- Montaże z widokiem z góry (`montage/au_top_*`): ortofoto ma okno 90 m, kadr gry ok. 57 m wysokości — skale różne (ok. 1,6x); porównanie jakościowe.

## Podsumowanie (stan 2026-11-10, 403 kadry obejrzane w arkuszach `sheets/`, 21 błędów)

| Kategoria | P0 | P1 | P2 | Razem |
|---|---|---|---|---|
| Przeszkoda na pasie (krawężnik/wysepka/szlaban) | 3 (MA-001, 002, 010) | 2 (MA-003, 015) | – | 5 |
| Nawierzchnia/geometria jezdni (garb, pola asfaltu, szwy) | 1 (MA-012) | 2 (MA-009, 016) | 1 (MA-004) | 4 |
| Liczba/szerokość pasów vs ortofoto | – | 2 (MA-011, 018) | – | 2 |
| Oznakowanie poziome (strzałki, P-13/P-14, linie na zebrze) | – | 2 (MA-006, 017) | 1 (MA-014) | 3 |
| Znaki/sygnalizacja | – | 2 (MA-005, 007) | – | 2 |
| Ekrany akustyczne | – | 2 (MA-008, 021) | – | 2 |
| Teren | – | – | 1 (MA-013) | 1 |
| Roślinność / obiekty | – | – | 2 (MA-019, 020) | 2 |
| **Razem** | **4** | **12** | **5** | **21** |

Top 10 (kolejność naprawy):
1. MA-010 P0 — wysepka z trawą na osi prawego pasu pod wiaduktem przy rondzie Putry (klasa zgłoszenia właściciela).
2. MA-001 P0 — krawężnik w poprzek jezdni na włączeniu łącznicy do Andersy.
3. MA-002 P0 — pas wjeżdża w łuk krawężnika/płytę na łącznicy przed Andersą.
4. MA-012 P0 — garb i nieoznakowane pole asfaltu na włączeniu od ronda Putry.
5. MA-009/MA-016 P1 — nadmiarowe, nieoznakowane pola asfaltu na rozwidleniach (junction patch) + schody/barierka na jezdni.
6. MA-015 P1 — krawężnik w poprzek wylotu drogi bocznej przy Andersie.
7. MA-017 P1 — strzałki P-8 niezgodne z `turn:lanes`.
8. MA-003 P1 — opuszczone szlabany bez kolizji na bramie Kwadrat Park.
9. MA-008/MA-021/MA-007 P1 — pełne, zdublowane ekrany zamiast przezroczystych; znaki wewnątrz ekranów.
10. MA-005 P1 — sygnalizator bokiem na łącznicy (w rzeczywistości go tam nie ma).

Wspólne przyczyny w generatorze (`tools/worldgen/roads`): (a) zamknięcia krawężników łańcuchów w węzłach stopnia 2–3 rysowane w poprzek jezdni, (b) junction patch/wysepki z obrysu krawędzi OSM bez testu „wysepka ∩ pas = ∅” i bez oznakowania, (c) profil wysokości łaty skrzyżowania z NMT zamiast z osi dróg. Proponowany walidator w `roads_qa`: przecięcie poligonów kerb/island z korytarzem pasów (każda krawędź, oba kierunki) = 0 m², ciągłość linii pasów przez węzeł, zgodność liczby strzałek z `turn:lanes`.

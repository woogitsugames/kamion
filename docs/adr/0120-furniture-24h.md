# ADR 0120 — Meble uliczne, sesja 8

Data rozpoczęcia: 2026-11-11. Status: praca w toku, bez zgody na integrację.

## r1 — Podmurówki, betonowe latarnie i tyły znaków

Źródło problemów: `docs/reports/visual/REVIEW-2026-11-11-s10-gpt-HIL.md`, I1–I5.
Punktem odniesienia jest main `5f2aa277`, a nie stare rendery ADR 0102.
Czysty poprzedni worktree przeniesiono do `.claude/worktrees/gpt-furniture`;
istniejąca gałąź `gpt-furniture-r1` została przesunięta fast-forward do main.
Dowody tej sesji są w `artifacts/furniture-r1/24h`, wcześniejsze ADR 0102 w katalogu nadrzędnym.

Zakres obejmuje wyłącznie ogrodzenia posesji, prototypy lamp i znaki.
Funkcje barier, ekranów, mostów, drogi oraz cudze pliki pozostają poza zakresem.

Plan sprawdzenia: baseline generatora i importu, wszystkie kamery Low/High przy słońcu
i zachmurzeniu, zmiana, ponowna generacja/import, porównanie każdej kamery.
Draws instancji należy raportować osobno. Liczniki edytora nie są pomiarem telefonu.
Budżet Low: draws +0, trójkąty do +2%; wynik wymaga pomiaru.

Podmurówka ma otrzymać krótsze poziome przęsła tam, gdzie skarpa powoduje
nadmierną odsłoniętą wysokość. Detal betonowych żerdzi powinien wynikać
z istniejącej bazy skanu CC0 i masek zależnych od wysokości oraz okuć.
Aluminiowa tarcza znaku nie otrzymuje korozji żelaza na całej powierzchni:
rdza może spływać od stalowych mocowań, a blacha ma utlenienie i brud.
Wymiary i zasięgi zużycia pozostają WORKING_VALUE do porównania ze zdjęciami.

Referencje lokalne: Mapillary p12/p15/p20/p26/p30 (ADR 0069/0102),
`docs/refs/posesje-bialystok.md` oraz Commons z istniejących manifestów.
Dotychczasowe klatki nie potwierdzają rodziny każdej lampy bocznej ulicy:
mapowanie pozostaje UNVERIFIED. Piksele referencji nie wchodzą do builda.

Przed każdym procesem Unity `unity-slot.ps1 -Acquire -Owner gpt-furniture`,
po nim `-Release`; bardzo wysoki próg StaleHours zapobiega usuwaniu cudzych slotów.
Telefony, push i scalanie do main nie są częścią tej sesji.

## Aktualizacja protokołu obciążenia, 2026-11-11 wieczorem

Po pilnym poleceniu właściciela także build_world, build_all, pełny GIS,
physics/gate3 i fidelity wymagają puli `heavy`, maksymalnie trzy zadania na maszynie.
`artifacts/furniture-r1/24h/heavy-step.ps1` pobiera tę pulę dla aktualnej gałęzi
i zwalnia ją w `finally`. Pełny GIS jest uruchamiany wyłącznie na końcu rundy.
W trakcie stosujemy pojedyncze pliki testów. Bieżący import ma już gotowe produkty
świata i PBR; następne importy sprawdzają ich kompletność przed slotem Unity,
aby skrypt importu nie uruchomił ciężkiego generatora poza pulą.
Gate jest wywoływany z aktualnego main; nie zmieniono wspólnego skryptu w gałęzi.

## Stan przed renderami r1

Baseline generatora: exit 0, 64 chunki, brak `fallback=True` w logu.
Przygotowanie cache PBR: exit 0; wersjonowana specyfikacja materiałów bez zmian.
19 testów mebli przechodzi, w tym krótka stroma skarpa, zakres UV pięciu kształtów
oraz rejestracja maski rdzy pod rzeczywistymi mocowaniami A-7 i C-12.
Niezależne ustalenia kodowe zapisano w `24h/REVIEW-CODE.md` i uwzględniono
w geometrii oraz UV. Nie jest to jeszcze zatwierdzenie wyglądu ani budżetu.

Koszt prototypów lamp i znaków pozostaje bez zmian; stara betonowa lampa Low
ma 91 trójkątów i 4 sloty. Lokalny koszt ogrodzeń wzrasta i wymaga pomiaru
na wszystkich kamerach. Przygotowano 6833 hashe chronionych prymitywów baseline.
Jaśniejszy cokół ma oddzielną teksturę; dane zmieniono addytywnie wyłącznie
w aliasie `furniture_footing` w `materials.py`. Nie dodano slotów prototypu.

Cztery dzienne źródła i atrybucje są w `24h/reference-selection.json`.
Zdjęcie SBS 297817221966185 nie pokazuje czytelnej rdzy; wzór zużycia w modelu
pozostaje propozycją do oceny, nie pomiarem tego konkretnego znaku.
Brak pewnego zbliżenia dokładnie tej okrągłej betonowej latarni nadal pozostaje luką.

## r1 — Detal podmurówki bez dodatkowego materiału

Obejrzany baseline potwierdził płaskie deski. Rozważono osobny materiał PBR
z połączeniem materiałów słupków i siatki. Niezależny recenzent wskazał jednak
chunk z bramą: stary materiał pozostałby potrzebny, a nowy zwiększyłby draws.
Tego wariantu nie zastosowano.

Podmurówki z `panel_fence` zachowują nazwę `concrete_plinth` i dostają dane
`COLOR_0`: B=64/255, A=128/255 to zastrzeżony znacznik; R jest fazą detalu,
G to wysokość wierzchołka ponad lokalnym gruntem +0,25 m. Ten kontrakt przetrwa
pakowanie UNorm8. Bramy i ekrany nie dostają tych danych; helpery `Lin`
i ich geometria pozostają bez zmian. Wariant z dużą ujemną współrzędną UV
odrzucono, ponieważ importer pakuje UV do Float16.

Addytywna flaga `furniture_plinth_detail` w `materials.py` uruchamia ograniczoną
ścieżkę w `WorldPbrMaterials.cs`. Używa ona tej samej fabryki World Surface,
tych samych pigmentów i tożsamości materiału; jawnie zachowuje `_GroundMasks=0`.
`Has` oraz reguły `_Tile` i `_Tint` pozostają bez zmian. Lokalny keyword
`_FURNITURE_PLINTH` w WorldSurface modyfikuje wyłącznie oznaczone fragmenty,
korzystając z istniejącego interpolatora masek. Brak nowego pasa renderowania.
Materiał z keywordem jest zapisywany w wygenerowanej scenie; test edytorowy
nie jest jednak dowodem działania na urządzeniu ani wyniku strippingu gotowego APK.

Mikrostruktura pochodzi z istniejącego `brushed_concrete` (CC0, Dario Barresi /
Dimitrios Savva; źródło i hash w LICENSES/manifest). Nowy PNG ma 256×256 i 52 958 bajtów.
Jest to modulacja o średniej 0,5 liniowo, zakodowana do sRGB; pigment mnożony raz.
Rozmiar przetworzonego kafla 1 m, pas brudu 0,25 m i siła 0,55 to WORKING_VALUE,
a nie pomiar deski ze zdjęcia. Oryginalny skan opisano w LICENSES jako 2,5×2,5 m.

Test GPU/fabryki: 7/7 passed, bez pominięć. Porównano keyword off/on na
nieoznaczonym betonie, mnożenie detalu w przestrzeni liniowej, zanik brudu,
zachowanie kanałów i czyszczenie keywordu/samplera po usunięciu flagi danych.
Koszt GPU i ocena materiału pozostają do kontroli w renderach i późniejszym
pomiarze lidera na urządzeniu. Same identyczne próbki nie dowodzą zerowego kosztu.

### r1, korekta po niezależnym przeglądzie iteracji 1

Krótkie stopnie desek na skarpie nie wyznaczają już słupków. Podpory zachowują
moduł do 2,5 m i narożniki linii, a siatka podąża za spadkiem między nimi.
Podział betonu pozostaje niezależny; deski mają zamknięte końce i małe szczeliny.
Poprzedni wymóg poziomego wierzchu siatki zastąpiono kontrolą wysokości nad
pochyłym gruntem. To usuwa przyczynę błędnego rytmu gęstych pionowych podpór.
Ocena wizualna tej korekty i końcowy budżet nadal oczekują na przebudowę/render.

### r1, iteracja 3 i przygotowana iteracja 4

Rendery iteracji 3 potwierdziły naprawę gęstych słupków. Chronione payloady
geometrii: 6833 przed i po, bez różnic. Import zapisał Low 120,0 MB i High
262,1 MB danych mesh/instancji/kolizji; nie jest to pomiar PSS urządzenia.
W 220 kombinacjach kamer delta draws mesh i instancji wynosi zero.
Konserwatywna granica tris nadal nie potwierdza limitu +2% w kilku kadrach
trasy. Pełne dane i ograniczenia są w artifacts/furniture-r1/24h/iteration3/.

Niezależny przegląd zbliżeń wykazał włóknisty odczyt betonowego trzonu.
Przygotowana iteracja 4 zachowuje źródło CC0 brushed_concrete, ale pobiera
je w skali metrycznej zamiast rozciągać kwadratowy skan przez całe 9 m.
Kafel źródłowy ma 2,5 m; obwód atlasu odpowiada średniemu obwodowi obecnego
modelu roboczego. Mniejszy kontrast ziarna i półprzezroczysty pas brudu są
WORKING_VALUE do oceny obrazów, nie pomiarem konkretnej latarni.

Druga zmiana przygotowana do iteracji 4 ogranicza podziały siatki renderowanej
za krótkimi stopniami desek. Kolizja zachowuje poprzednie stacje. Minimum
terenu sprawdzane jest także wzdłuż uproszczonego wygięcia co najwyżej 0,25 m;
na nietypowym spadku poprzecznym pozostaje poprzednia geometria. Nowa dolna
krawędź nie schodzi poniżej istniejących desek. Ostateczne granice rendererów,
cienie, wygląd i budżet wymagają ponownej kontroli po eksporcie.

Doprecyzowanie po przeglądzie kodu iteracji 4: warunek zachowania górnej
krawędzi kontroluje wysokość. Aproksymacja bocznego wygięcia może zmienić XY
około 5 mm; wymaga porównania obrazów. Skala skanu odpowiada średniemu obwodowi
modelu, a nie dokładnie całemu stożkowi. Próbki terenu nie dowodzą braku każdej
szczeliny względem uproszczonego Low. Dodano przypadek ostrego poprzecznego
uskoku oraz porównanie hashy rzeczywistych accessorów kolizji GLB przed/po
iteracji 4 (w slocie heavy przed generatorem i po kontroli eksportu).

### r1, zamknięcie

Zweryfikowany kod i zasoby: 7adbe982. Iteracja 4 poprawiła odczyt betonu;
niezależnie obejrzano 40 arkuszy, 220 par, bez nowej istotnej regresji.
DrawEst mesh i instancji osobno +0 we wszystkich 220 wariantach.
Dokładne liczniki Low potwierdziły górną granicę tris ≤+2% w 102/110 wariantach;
8 wariantów diagnostycznych above/edge pozostaje nierozstrzygniętych.
Chroniona geometria 6833→6833 bez różnic; kolizje ogrodzeń 80→80 bez różnic
wyłącznie między iteracją 3 i 4. Import Low 120,0 MB, High 262,1 MB, nie PSS.
EditMode 268/268; własne Python 17/17 i 9/9. Pełny GIS: 509 passed,
1 xfailed, 1 failed (zastane niezgodności siedmiu hashy fidelity).
Physics/gate3: 47 passed, 1 failed (znana niezgodność top_speed_flat_comb).
Niezmienność odpowiednich wejść od bazy sesji potwierdzają audyty w artefaktach.
Nie zmieniano cudzych źródeł w celu uzyskania PASS. Otwarte I3/I5, aliasing Low,
rodzina słupa i konstrukcja sztywnego panelu są opisane w REPORT i PACKET.
Brak pomiaru telefonu/GPU/PSS; obrazy statyczne nie potwierdzają zachowania w ruchu.

### r2, znaki pionowe

Gałąź gpt-furniture-r2 powstała z r1, następnie scalono main 522361aa.
Generated i street_props.glb przyjęto z main do regeneracji, wspólne dopiski
materiałów/licencji połączono. Kod i shadery zachowują flagę podmurówki r1.
Cel: miejscowe zużycie lica, mocowania także w Low i odblask sterowany rzeczywistym
stanem świateł. Siłę efektu należy oznaczać WORKING_VALUE, dopóki nie ma
kalibracji zdjęcia nocnego. Bez nowych świateł URP/przebiegów ani zmian TruckLights.
Przed zmianą: spójny generator i import oraz komplet bazowych kamer po scaleniu.

### r2, kontrakt odblasku i próby GPU

Przygotowany wariant Kamion/Furniture Sign zachowuje funkcje URP Lit,
stały układ UnityPerMaterial oraz dziewięć przebiegów (pozostałe przez UsePass).
Nie dodaje światła URP. Tylko jawna flaga plate_back.furniture_sign_fronts
uruchomi rejestrację rzeczywistych lic z aktualnego props_meta.json, w tym
kierunkowych; fasadowe etykiety są wykluczone, cudze jawne definicje pozostają.
RegionImporter iteruje kopię ToList definicji przed importem prototypów;
nowe definicje zapewniają im UV0 bez zmiany plików ogólnego importera.
Ta flaga nie jest jeszcze włączona w świecie: trwa baseline po scaleniu main.

Publisher czyta istniejący TruckLights i cztery prawdziwe sockety mijania/drogowe.
Brak aktywnej pary/socketów zeruje stan. Pozycje są z riggu, nie przy kamerze.
Siła i loby kątowe są WORKING_VALUE; formuła nie jest tabelą RA konkretnej folii
ani kalibracją lokalnej referencji. Brakuje cienia od reflektora/przesłaniania
na drodze światła: to jawny limit analitycznego modelu wymagający oceny obrazu.

13/13 prób EditMode przeszło bez pominięć: GPU off/no-source versus URP Lit,
alpha, strony, kąt, dystans, współczynnik HDR 1/800, 9→9 przebiegów,
stan/sockety high-only, trwały GUID i wycofanie fabryki do Lit oraz komplet
36 aktualnych lic w bibliotece. Dotychczasowe porażki fixture zachowano w artefaktach.
HDR _EmissionColor wymaga wartości liniowej bez gamma, co potwierdził odczyt GPU;
kontrakt zwykłego _Tint i SetLinearTint pozostaje bez zmian.
Dusk ma słońce -5 stopni; sam ten preset nie dowodzi efektu w pełnej nocy.

### r2, bieżący kandydat i diagnostyka po korektach

Włączono flagę danych w materials.py, wygenerowano świat i zaimportowano
Biblioteka ma36 lic, a odczyt przypisanych materiałów sceny potwierdził35
lic z aktywnym shaderem. Zużycie jest deterministyczne dla klucza znaku,
zachowuje alfę i wyłącza się przy sile zero. Low otrzymało dwa dystanse
uchwytów w istniejącym slocie plate_back; brak nowego draw i zmian kolizji.
To zastępuje wcześniejszą informację o niewłączonej fladze.

Najnowsza seria FurnitureSignTests: 16/16 bez pominięć. Obejmuje dodatkowo
liniowe skalowanie ekspozycją, asymetryczne prawe odcięcie mijania i wykrycie
socketów dobudowanych po pierwszej próbie znalezienia źródła. Usunięto błędne
robocze wzmocnienie 512, po sprawdzeniu rzeczywistej ekspozycji sceny.

Kontrolowany night-rig after3 Low i High zapisał po 24 obrazy: 25/50/100 m,
mijania, drogowe, wyłączona odpowiedź materiału oraz wyłączony komponent
źródła. Każdy wariant ma cztery próbki rzeczywistego stanu przed kamerą.
Fixture używa socketów ciężarówki i oka kierowcy; nie publikuje sztucznych
pozycji reflektorów. Tryb świateł utrzymuje własny callback editorowy podczas
ponownego ładowania kopii sceny, bez zmian TruckLights i scen gry.

Diagnostyczne EV100=5, siła 800, loby i prawe wzniesienie są WORKING_VALUE.
Model nieba kończy się na -8 stopniach; brak dowodu głębokiej nocy,
kalibracji fotograficznej i przesłaniania ścieżki światła. Obejrzane obrazy
25 m Low pokazują zmianę czytelności lica, lecz nie dowodzą zgodności fotometrycznej.
Pierwszą serię 330 obrazów i dokładne liczniki Low zachowano w iteration1;
po korekcie shadera i cache konieczny jest nowy komplet standardowych kadrów.
Kontrola chronionej geometrii nadal czeka na heavy, więc nie ma jeszcze wyniku.


### r2, pełny przegląd i chroniona geometria

Kod i zasoby zamrożone w52668015; późniejsze commity dotyczą dowodów.
Obejrzano330/330 par na60 arkuszach≤960px, także niezależnie, bez nowego
widocznego blokera furniture. Nie dowodzi to wierności drobnych mocowań
ani kalibracji folii. Bezpośrednia para SBS ma istotne rozbieżności pozy/sceny,
więc zgodność konstrukcyjna ze zdjęciem pozostaje UNVERIFIED.
DrawEst mesh/instancji/cieni wszędzie+0; dokładne165Low max tris+0,18997983%.
Chronione payloady geometrii6833→6833,0 różnic. Końcowe EditMode340/340,
bez pominięć. GIS iphysics/gate3 są osobnymi kontrolami końcowymi w heavy,
aktualnie oczekującymi; nie przypisano im wyniku na podstawie audytu wejść.

Zamknięcie r2:GIS644passed,1xfailed,1failed (zastane dwa hashe fidelity, niezmienione wejścia względem3fe0c97f); physics/gate3 48passed. EditMode340passed. REPORT iPACKET zachowują ograniczenia nocnej aproksymacji i niepotwierdzone detale konstrukcyjne. Następna runda dotyczy przystanków według Mapillary.

### r3, przygotowanie
Gałąźgpt-furniture-r3 od zamkniętej r2, merge main889201d5. Produkty generatora z main do regeneracji; dopiski materiałów/licencji zachowano addytywnie. Cel:wiaty/przystanki/kosze/słupki według Mapillary, bez barier. Baseline po merge przed zmianą geometrii.

### r3, kandydat 1 po baseline

Baseline162214c3:236PNG(59×Low/High×clear/overcast),importOK,6833 chronione
payloady. Niezależny przegląd4zbliżeń wskazał ciemne panele i dach jakoP1.
Kandydat6a50ee4c dodaje wariant tylko dla dwóch referencjiOSM, pozostawiając
pozostałe prototypy i pozycje. Zachowano source seed i kotwicefab/litter.
Rama/dach mają jeden slot,cienkie szkło drugi,ławka trzeci. Low ma mniej
segmentów dachu odHigh. Kolizja zachowuje poprzedni pełnybox; nie deklarować
nowej fizycznej dostępności wejścia. Obrys4×1,5×2,5m zachowuje wartość zastaną,
nie jest pomiarem zdjęcia. Barwa,alpha i profil dachu WORKING_VALUE.

Trzy sloty nowej rodziny nie dowodzą braku wzrostu draws po podziale instancji;
pełna kontrola236kadrów obowiązkowa. Przed generatorem pojedynczy własny
plik testów w heavy; pełnyGIS dopiero przy zamknięciu rundy.

### r3, poprawka podpór i wczesny przegląd

Kod kandydata po poprawce dachu: `973a50be`. Niezależna kontrola kodu
wykryła pierwotną szczelinę podpór oraz za wysoki dach. Poprawiono profil
do maksymalnej wysokości 2,60 m i długości wszystkich pięciu podpór do
interpolowanej spodniej powierzchni segmentów. Wymiary nominalne nadal
są wartością zastaną WORKING_VALUE, a nie pomiarem fotograficznym.

Pojedynczy własny plik testów przeszedł 10/10 w 0,27 s w slocie heavy.
Generator after1 trwał 546,9 s, zapisał 64 GLB, bez `fallback=True`.
Audyt pełnych multizbiorów instancji w 64 plikach JSON potwierdził
23 wiaty i dokładnie dwa nowe warianty: wszystkie inne pola i dane
instancji są identyczne z bazą. Nie jest to dowód niezmienności geometrii;
odpowiednia kontrola payloadów nadal oczekuje na slot heavy.

Podczas tej kolejki wykonano dodatkowy import i cztery kamery Low-clear,
z wymaganymi slotami Unity i markerem zatrzymującym wyłącznie własny
standardowy pipeline. Root i niezależny recenzent obejrzeli 4/4 podglądy
o szerokości 960 px. Czerwona rama, widoczność przez szkło oraz lżejsza
ławka poprawiają odczyt. Nie widać wcześniejszej szczeliny ani rażącego
sortowania z tych stron. Pozostaje słaby odczyt powierzchni dachu od frontu
i niemal niewidoczne szkło; nie zmieniać alpha przed sprawdzeniem High.

Te cztery kadry mają DrawEst mesh i cieni +0, instancji Anders −1,
Factory 0. Nie zastępuje to pełnego budżetu 236 kadrów ani 118 dokładnych
liczników Low. W Factory licznik renderowanych instancji wzrósł o jeden;
przyczyny nie zweryfikowano oddzielnie. High, overcast i drugi narożnik
pozostają nieocenione. Kamera diagnostyczna nie jest dopasowana do zdjęcia.

Oryginały trzech zdjęć Mapillary mają ponownie sprawdzone SHA256;
autorstwo, CC BY-SA 4.0, adresy źródeł i osobny hash wycinka zapisano
w `artifacts/furniture-r3/24h/reference/provenance.json`. Bieżący pakiet
zachowuje pozycje OCZEKUJĄCE dla pełnych renderów, geometrii i końcowych
testów; wyników r2 nie przedstawiono jako wyników r3.

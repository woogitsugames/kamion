# 04 — DK65: datowany stan inwestycji i organizacja ruchu — WIP

Stan ewidencji głównej na 16.11.2026: **31 rekordów** (SOURCED: lokalny `manifest.csv`). Rekordy obejmują także dokumenty, AUX i odrzucenia; nie są licznikiem zaakceptowanych fotografii. Bieżące kwalifikacje i ograniczenia: [STATUS](../STATUS.md). Starsze opisy poniżej są datowanymi etapami pracy.

Wcześniejszy etap manifestu:8 rekordów —6 dokumentacyjnych i2 ponownie obejrzane orto. Brak nowych fotografii naziemnych i brak pobranych obrazów firmowych. Normy i prywatne obserwacje tekstowe opisano osobno.

Cel: oddzielić otwartą S19 od aktualnej budowy S16 i archiwalnych zwężeń DK65. Pakiet zawiera 4 rekordy dokumentacyjne, **0 kadrów pobranych / 0 kadrów link-only**. Nie opisuje zdjęć na stronach GDDKiA, których nie oglądano.

## Ustalenia

- 04-D01/02: SOURCED [komunikat GDDKiA z 20.10.2026, źródło i sekcje w manifeście]. Odcinek S19 otwarty. To pierwotne urzędowe potwierdzenie dla luki K1, gdzie dostępne były tylko źródła wtórne.
- 04-D03: SOURCED [komunikat GDDKiA z 18.05.2026]. Dane o Fastach mają datę historyczną i zapowiadany koniec; nie stanowią potwierdzenia organizacji w listopadzie.
- 04-D04: UNVERIFIED — nie odczytano pełnego rekordu aktualnych utrudnień. Nie przeniesiono do generatora samych fragmentów indeksu wyszukiwarki.

## Wnioski i luki

Otwarcie S19 nie oznacza automatycznie końca robót S16 ani likwidacji każdego ograniczenia na DK65. Lokalny stan dojazdów, żółte oznakowanie, zapory, bariery i ich rozmieszczenie na 15.11.2026 pozostają UNVERIFIED. Nie wyprowadzono z komunikatu wymiarów jezdni DK65. Brak nowych pomiarów rozstawu/gatunków drzew, zatok i rowów. Trwa szukanie urzędowych rekordów oraz otwartych kadrów.

Teksty gov.pl: CC BY-SA 4.0 według stopki odczytanych stron. Zdjęcia w stopce mają inną licencję (domyślnie CC BY-NC-ND 4.0), dlatego żadnej fotografii GDDKiA nie pobrano ani nie skopiowano. Do gita trafiają parafrazy i odnośniki.

## Ortofoto — nieregularność drzew

04-O01: ponownie obejrzany K1-132, bez nowego pobrania ortofoto; 1 miniatura ≤800 px. SOURCED [obraz]: po zachodniej stronie pojedyncze korony na pasie trawy, po wschodniej nieregularne grupy z przerwami. ESTIMATED: ręcznie wskazano 6 większych koron; odległości między tymi wybranymi środkami zapisano w `tree-crown-picks.json`, wraz z bbox i skalą. Nie są to potwierdzone kolejne pnie. Nie wyliczono średniego rozstawu wszystkich drzew ani gatunków. Dawnego skrótu K1 „8 drzew / 200 m” nie potwierdzono jako kompletnego inwentarza.

Ponowna próba listy utrudnień15.11.2026: HTTP200 zwróciło tylko212bajtową odpowiedź skryptową ochrony automatyzacji, bez tabeli. Nie wykonywano dodatkowego żądania zasobu ochrony ani rozwiązywania wyzwania. Sam status200 nie jest dowodem odczytu aktualnych utrudnień; pozostają UNVERIFIED.

## Źródłowe oznakowanie czasowe

`temporary-marking/` zawiera17 ustaleń normatywnych SOURCED i1 warunek terenowy UNVERIFIED: żółte/białe oznakowanie oraz U-3/U-20/U-21. Źródła sprawdzono z nowelizacjami do2026. Agent obejrzał6 stron rysunków; koordynator ponownie obejrzał3, dodając wymiary wariantów U-21. To zasady i rysunki urzędowe, nie nowe kadry robót. Nie ustalają rozmieszczenia urządzeń w poszczególnych kaflach.

## Lokalne kadry właściciela — tylko obserwacje tekstowe

Osobno obejrzano3 kadry DK65, bez kopiowania zdjęć do repo ani tworzenia miniaturek. `data/owner-dk65-observations.json` zachowuje opis widocznych robót, poboczy, drzew i oznakowania; daty z nazw nie są potwierdzonym EXIF, kafle i azymuty UNVERIFIED. Widoczny jest fragment żółtych linii w osi oraz prosta biała strzałka na niebieskim kole z tabliczką wyjątku dla pojazdów budowy.

**Korekta kodu znaku:** kształt widoczny na dwóch kadrach odpowiada C-5, a nie C-1. Nazwy sprawdzono w §35 ust.1 pkt5/pkt1 Dz.U.2019poz.2310: C-5 nakazuje jazdę prosto, C-1 w prawo przed znakiem. Robocza wzmianka C-1/nakaz prosto w opisie zdjęć właściciela jest niespójna. Pozostałych małych tarcz i symbolu prawnego żółtych linii nie rozstrzygnięto. To obserwacje chwili zdjęcia, nie inwentaryzacja robót na15.11.2026.

## Zatoka Dobrzyniewo — ponowny przegląd K1

04-O02: istniejący kadr K1-008 obejrzano indywidualnie, bez nowego pobrania ani kopii. SOURCED [obraz i data/bus-bay-review.json]: jasne boczne poszerzenie, biała linia przerywana, szary prostokątny dach przy jego końcu; po przeciwnej stronie jasny wlot. Nazwa przystanku i node14067837805 pochodzą osobno z metadanych K1/OSM. Oznakowanie pionowe, wyposażenie wiaty i stan listopadowy UNVERIFIED. Nie wykonano nowego pomiaru szerokości. To ponowne wykorzystanie jednego kadru, nie nowa fotografia.

## Drzewa i skrajnia — rozdzielenie prawa od stanu terenu

regulations-vegetation.csv zawiera5 wierszy z paragrafami i datowanymi źródłami ELI. Dawnego minimum3m z2016/124 nie wolno uznać za uniwersalny aktualny wzorzec DK65. Sprawdzono2022/1518 oraz zmianę2025/1352 i przepisy przejściowe; reżim konkretnej inwestycji UNVERIFIED. To wymagania, nie pomiary zdjęć. Próba BDL w jednym punkcie lasu przy04-O01 zwróciła0 rekordów obu warstw drzewostanów; gatunków nie ustalono. Brak rekordu nie dowodzi braku drzew.

## Uzupełnienie listy GDDKiA — pełne rekordy S16

04-D05/D06: odczytano pełną oficjalną tabelę z innego publicznego URL, bez wykonywania skryptu challenge z wcześniejszej próby. Dane i metoda w data/gddkia-dk65-table-records.json. SOURCED jako treść rejestru: ręczne wahadło148+968–149+556, dojazd Chraboły147+713; osobno bypass przy152,3km. Zakres4,8km dotyczy obwiedni robót, nie długości wahadła. Terminy są planem w rejestrze; bez gwarancji faktycznego zakończenia. Dokładny stan terenowy15.11 i wygląd znaków nadal UNVERIFIED. Wcześniejszy04-D04 zachowuje dziennik nieskutecznego odczytu nr65; nie oznacza już braku jakichkolwiek pełnych danych o utrudnieniach.

Recenzja04/data/current-records-peer-review.json: pełne rekordy GDDKiA PASS. Skorygowano04-V04 o istotne wyjątki§80ust2 (warunki i wymagane zgody dla zmniejszonej skrajni). Bazowych wysokości nie stosować bezwarunkowo do istniejących wiaduktów. Doprecyzowano04-V05 o zamkniętym katalogu wyjątków noweli2025.

## Mapillary w przeglądarce — dwa kadry historyczne

mapillary-browser-round2:2 kadry picturehoover z27.06.2020 obejrzane indywidualnie, tylko bezpieczne publiczne linki. Pierwszy przy oznaczeniu65/Obwodowa daje pobocze i nieregularne grupy drzew; drugi przy Rynku daje chodniki, schody i fasady, bez przypisania doDK65. Podkład jawnieOpenStreetMap. Oficjalna pomoc Mapillary podajeCC BY-SA4.0; pełneTerms niewczytane bezlogowania. 0API, pobrań obrazów, zapisanych zrzutów i tokenów. GPS kamery/azymuty oraz aktualność2026 UNVERIFIED; nie dowodzi robótS16. Główny manifest teraz10 rekordów.

## Mapillary — drugi odcinek drzewa/bariery

mapillary-browser-round3:2 kolejne indywidualnie obejrzane kadry picturehoover,27.06.2020, link-only CC BY-SA4.0 wg pomocy zround2. Ełcka: drzewa, kruszywo, trawiaste obniżenie i zjazd. Studzienna: bariery, łuk i czerwono-białe pionowe tablice; wygrodzenia2020 nie przypisano do S16 z2026. Filtr2024+ nie pokazał pokrycia w zbadanych widokach; nie twierdzimy braku nowszych zdjęć w całym korytarzu. GPS/kafle/km niepotwierdzone. Główny manifest12 rekordów,0nowych pobrań obrazów.


Mapillary-corridor-round4:2 nowe link-only kadry picturehoover z27.06.2020, obejrzane osobno w dużym widoku. Jeden pokazuje zatokę z wiatą, znakiem autobusu, koszem, krawężnikiem i płytami; drugi przejście asfalt–kruszywo–trawa oraz obniżenie. Funkcja poszerzenia w drugim nieustalona, nie policzono drugiego przystanku. Wymiary/kilometraż/kafel/GPS kamery/azymut i stan2026 UNVERIFIED. 0 pobrań. Główny manifest14 rekordów:6 dokumentów,2 orto,6 Mapillary link-only.

## Zjazd, pobocze i zakres numeru drogi — obiegi5–6

Główny manifest17rekordów: [2historyczne Mapillary](accesses-verges-round5/README.md), 0pobrań/2link-only — jeden zjazd i jeden przekrój zboczy, bez rozpoznanej rury/czoła przepustu. Kontekst dawnej drogi65 z K1: way1399803717, version4 z20.10.2026, highway=secondary, old_ref=65, bez ref=65. GPS kamery, przypisanie konkretnego kadru do way/kafla i obecny status DK65 UNVERIFIED. Korekta obejmuje też04M3-002, bez zmiany obserwacji wyglądu. [Plac budowy](temporary-works-round6/README.md):1AUXlink-only z RadiaBiałystok/GDDKiA,0pobrań, żółtych linii/zapór nie rozpoznano. Nie zwiększa liczby kwalifikowanych referencji oznakowania.

## Czytelne oznakowanie i dane lasu — obiegi7–8

Główny manifest21rekordów. [TM7](temporary-marking-round7/README.md):3nowe fotografie kontraktu,0pobrań/3link-onlyARR, każda niezależnie obejrzana przez2agentów.1kadr pewnej żółtej linii przerywanej, wszystkie3pionowych czerwono-białych tablic na stopach; brak potwierdzonych poziomychU20 i dokładnego podtypuU21. PodpisyDK65 0+050/0+200/0+250 to lokalny zapis projektu, nie krajowy159+xxx; daty02/24.06.2026 wg podpisów, nieEXIF. W02widoczny okrągły wylot rury, bez średnicy/materiału/ciągłości. Nie aktualny stan15.11.2026.

[BDL](forest-context-round8/README.md):1rzeczywistewydzielenie przy K1km20/dk65-08,0fotografii. ŹródłoweSO/species_age129/a_year2026 i wspólnyidentyfikator108033211 w2warstwach. SO rozwinięto jako sosnę słownikiemLP, nie botanika ze zdjęcia. Nie potwierdzono semantyki roku/formalnej dominacji/80%udziału ani roku powstania. Koordynator obejrzał mapę i sprawdził literalneJSON; mapa tylko raw pozaGit, geometrynull. Gatunek szpaleru przyjezdni, wymiary/rozstaw/odsunięcie pni nadalUNVERIFIED. To kontekst lasu, nie dowód alei drzew.

## Dendrologia projektu — obiegi9–10

Główny manifest: 22 rekordy. [Dokument gminny](tree-inventory-round9/README.md) opisuje w pkt3.14.1 inwentaryzację z sierpnia2021 w liniach rozgraniczających S19 Krynice–Dobrzyniewo–Białystok Zachód. Agent i koordynator obejrzeli pełne strony PDF57/58 (druk58/59). CSV zawiera sześć wybranych gatunków z szerszej listy: sosna pospolita, brzoza brodawkowata, klon pospolity, jesion wyniosły, wierzba iwa, wierzba krucha. To kontekst gatunkowy, nie sześć rekordów drzew i nie dowód konkretnych gatunków szpaleru DK65. Obwody, położenia, rozstaw i stan2026 pozostają UNVERIFIED. Projekt nasadzeń z3.14.2 jest oddzielony od opisu stanu inwentaryzowanego.

[Spis załączników](tree-table-search-round10/README.md): 19 nazwanych PDF rodzica, bez osobno wskazanej tabeli dendrologicznej. Zbadano spis, nie treść19map; nie otwierano map ani nie pobierano ZIP. Publikacja22.03.2022 i odbiór dokumentacji18.03.2022 nie datują wykonania projektu. Brak tabeli w sprawdzonym spisie nie dowodzi jej nieistnienia gdzie indziej. 0 nowych pomiarów/zdjęć.


## Przystanek Ełcka — runda11

[bus-stop-round11](bus-stop-round11/README.md):1nowy Mapillary picturehoover27.06.2020,pKey1452388251821206,0pobrań. Indywidualnie obejrzana pełna jasna wiata/graffiti/ciemny dach, znakautobusu, peron/krawężnik/asfaltowazatoka i bariera. Ławka kompletna/nazwa/kosz/nawierzchniadotykowa niepotwierdzone. SelekcjaK1km14.261/L to lokalna miara korytarza, nie państwowy pikietaż; viewport nie GPS, kierunek kuBiałemustokowiESTIMATED, stan2026UNVERIFIED. Główny04ma23rekordy. Koordynator odczytał artefakty; indywidualny ogląd źródłowego kadru tylkoagent, nie drugi nowy oglądroot.


## Leśne pobocza i wjazd — runda12

[rural-verges-round12](rural-verges-round12/README.md):2 nowe kadry Mapillary picturehoover z27.06.2020, każdy osobno obejrzany przez agenta po powiększeniu i jawnym wyborze OSM. Wąski pas pobocza/trawa/obniżenie/ściana lasu oraz jasny kruszywowy klin i rzeczywisty wjazd.0 widocznych otworów rur/czół przepustów. Gatunki, odstępy, odsunięcie pni, metryka, przejezdność i stan2026 UNVERIFIED. K1km20/22 to punkty selekcji, nie kamera; dokładnego kafla/km nie przypisano.2 link-only/0pobrań/API/Commons. Główny04ma25 rekordów; koordynator sprawdził artefakty, nie deklaruje dodatkowego oglądu kadrów.

## Zakończenia barier — norma2026

[barrier-endings-law-round15](barrier-endings-law-round15/README.md):7 ustaleń ze wskazaniem §1pkt3lit.c i §§2–4 Dz.U.2026/132, odcinki zagłębione/zakotwione albo terminaleEN1317, wyjątek dla tymczasowych barier niskiego poziomu i zalecane żółte odblaski. Obejrzana strona18 istniejącegoPDF pozaGit. Nie pomiar DK65 ani pełna specyfikacja terminala. Główny25 bez zmian.

## Historyczny objazd w Fastach — runda16

[s19-fasty-traffic-round16](s19-fasty-traffic-round16/README.md): pełny komunikat14.10.2025 wiąże planowane przywrócenie stałejDK65 od15.10 godz9 z objazdem budowy wiaduktuS19 w Fastach. Tymczasowe rondoS19/DK65 w Krynicach jest osobnym miejscem. Aktualny rekord inwestycji wskazuje użytkowanie/20.10.2026, a3,5m/2,5m/min0,75m to parametry opisuS19, nie pomiarDK65.2 teksty/0 obrazów. Główny25 bez zmian.

## Korony przy dwóch fragmentachK1 — runda17

[tree-crowns-round17](tree-crowns-round17/README.md):2nowe i osobno dwukrotnie obejrzane ortokadryGUGiK800px,240×240m/EPSG2180. Nieregularny las i grupa koron przy łące, bez modelu stałego rozstawu pni. Jeden szacunek środka korony do asfaltu około12m±4mESTIMATED; nie odsunięcie pnia. Gatunki/data obecnego nalotuUNVERIFIED.2pobrania/2kanoniczneplikiGit, duplikatyRAW usunięte poSHA. Główny27.


### Fasty — jeden zjazd i dwa historyczne kadry

FB19-01/02, picturehoover27.06.2020, dwa permalinki Mapillary obejrzane indywidualnie także przez root w publicznym UI z OSM,0pobrań. Jeden czerwonołososiowy zjazd z prostokątnych elementów, szare ziarniste pobocze i trawiaste obniżenie. Dwa ujęcia nie oznaczają dwóch zjazdów. Przystanek/wiata/znak niepotwierdzone, funkcja obniżenia i przepust UNVERIFIED. Punkt K1km10.417 wdk65-02 wybrał miejsce, ale nie dowodzi GPS kamery/kafla obu fotografii ani aktualnego numeru drogi2026. [FB19](fasty-bus-stop-round19/README.md).


### Południowe podejście do Knyszyna — KS20

Dwa nowe kadry picturehoover27.06.2020 obejrzane także przez root: falująca niweleta, wąski ziarnisty pas przy białej krawędzi, trawa/wyższa roślinność przed lasem po prawej i szereg dużych nieregularnych pni po lewej. Bez gatunków, rozstawów, wymiarów rowu lub przepustu z domysłu. Dwa widoki tego samego odcinka, nie dwa odrębne szpalery. K1km24.6 służy selekcji, przypisanie do dk65-11 ESTIMATED, GPS aparatu UNVERIFIED. [KS20](knyszyn-south-verges-round20/README.md).


R21: trzy nowe kadry robót DK65 z lipca2026, agent i root osobno obejrzeli. Tablice na stopach, czerwono-białe moduły i kanał ruchu przy rowie. Żółte obrzeża tablic nie są żółtymi liniami poziomymi. Lokalny kilometr galerii nie jest pewnym kilometrażem krajowym/GPS; kontraktS19 nie oznacza, że zdjęcie przedstawia gotowąS19. Główny34.


R22 Knyszyn: dwa nowe kadry historycznego centrum z artykułu2022. Jeden pokazuje przeszkloną wiatę, ławkę i znak z autobusem; drugi posadzkę/ławki/słup ogłoszeniowy, bez wiaty. Root oba obejrzał. Jedno miejsce,0potwierdzonych wcięć zatoki i0nowych GPS/kafli. Relacja do obecnej DK65 nieustalona. Główny36. Dla sesji Knyszyn przydatne także nawierzchnie i mała architektura.


R23BDL: punkt w gęściej zadrzewionym fragmencie istniejącegoTC17-02 zwrócił1rekord warstwy pozaPGL6: kodSO, species_age100,a_year2017. Bez automatycznego rozwinięcia kodu/datowania wieku i bez przeniesienia na pojedyncze drzewa przy jezdni.0nowych zdjęć. Główny37.

R23 uzupełnienie słownika: root obejrzał stronę20 instrukcjiTAKSATORPU2023 opublikowanejBDL: SO=sosna zwyczajna. Kod rozwinięty dla rekordu wydzielenia; nie pojedynczych drzew przy DK65. Datowanie wieku i kod udziału nadal bez interpretacji.


R25: dwa nowe kadry rzeczywistej żółtej farby na asfalcie DK65, podpisy27/26.08.2026. Root oba obejrzał: przerywane odcinki/zygzak oraz cienka ciągła prawa krawędź. To nie same żółte obrzeża tablic. Bez kodówP/U, metrów i transferu do listopada2026. Główny39.

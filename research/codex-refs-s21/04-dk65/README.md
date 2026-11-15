# 04 — DK65: datowany stan inwestycji i organizacja ruchu — WIP

Stan bieżący manifestu:8 rekordów —6 dokumentacyjnych i2 ponownie obejrzane orto. Brak nowych fotografii naziemnych i brak pobranych obrazów firmowych. Normy i prywatne obserwacje tekstowe opisano osobno.

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

# 01 — Lampy i fotometria — WIP

Cel: uzupełnić lukę M59-FIX zdjęciami lamp ciągników i naczep z czytelną homologacją oraz przepisami. Stan: **NIESPEŁNIONE**.

## Materiał

- 01-001 — SOURCED [obraz, autor Dietmar Rabich, CC BY-SA 4.0, link w manifeście]: okrągła lampa wozu strażackiego, trzy widoczne pola, czytelne E1 i S1 na wycinku. Kontekst pomocniczy; nie liczyć jako naczepy ani ciągnika siodłowego. Marka widoczna: wyłącznie referencja kształtu. Oryginał poza gitem w `Data/raw/refs/codex-s21/01-lampy/straz.jpg`; miniatury ≤ 800 px.

## Fotometria

Źródło: [UNECE R148, E/ECE/TRANS/505/Rev.3/Add.147](https://unece.org/sites/default/files/2021-05/R148e.pdf), wersja dokumentu z 9 stycznia 2020 r. (katalog URL 2021-05); sprawdzić aktualne poprawki przed zastosowaniem prawnym. Wartości są wymaganiami badania, nie bezpośrednimi wartościami emisji shadera.

- SOURCED [R148 pkt 4.8.11]: co najmniej 5:1 dla pomiaru obu wspólnie włączonych lamp wobec samej tylnej pozycyjnej/obrysowej, jeśli jest wzajemnie sprzężona ze stopem; w polu ±5° V i ±10° H.
- SOURCED [R148 pkt 5.5.1 tabela 7]: S1 stałe: minimum 60 cd w osi H-V, maksimum pojedynczej lampy 260 cd w dowolnym kierunku.
- SOURCED [R148 pkt 5.6.1 tabela 8]: kierunkowskaz 2a stały: minimum 50 cd w osi odniesienia, maksimum pojedynczej lampy 500 cd w dowolnym kierunku.
- SOURCED [R148 pkt 5.11.3]: dla kategorii 1a/1b/1c/2a/2b luminancja w każdym wskazanym punkcie ≥ 2,5 cd/m²; gradient między punktami ≤ 2 × B₀/cm, gdzie B₀ to najmniejsza zmierzona luminancja.

## Luki

Częściowo uzupełniono kształty i czytelne oznaczenia (zob. Europoint/Europoint III/Volvo poniżej); kolejność funkcji poszczególnych pól i pełna reprezentatywność nadal UNVERIFIED. Brak właściwych kadrów włączonych, nocnych i lampek tablicy. Potrzeba ≥ 15 zbliżeń tylnych, ≥ 4 włączonych, ≥ 3 zmierzch/noc i ≥ 5 lampek tablicy według M59-FIX. 01-001 nie jest zaliczany do tych progów. Drugi obejrzany kandydat `CombinedLampReflector.jpg` przedstawia małą przyczepę o nieustalonej kategorii; nie jest podstawą wniosków o naczepach.

Dalszy krok: wyszukiwać osobno fotografie tylnych lamp zespołów drogowych i zbliżenia kloszy, weryfikując E-numery na oryginale.

## Dalszy przegląd

01-002…004: trzy europejskie ciężarówki, fotografie Cjp24 (CC BY-SA 4.0). Obejrzano całe kadry i osobno wycinki oryginałów. Żaden nie umożliwia odczytania homologacji. Materiał pomocniczy dla kształtów przednich lamp; nie zwiększa liczników M59-FIX. Liczba komór funkcjonalnych pozostaje UNVERIFIED. Zachowane są miniatury całych kadrów oraz wycinki.

01-005 — SOURCED [obraz w manifeście]: cztery pola poziomego klosza naczepy, widoczna rozetowa i żebrowana optyka. Góra lampy ucięta. E-numer pozostaje UNVERIFIED; biała obudowa przy tablicy nie potwierdza funkcji lampki. Wycinek obejrzany osobno.


## Uzupełnienie agentowe — sterowanie i oznaczenia (15.11.2026)

Bazowy `regulations.csv` zawiera24wpisy; poniżej opis wybranych ustaleńR48. Dane R48 zweryfikowano w pełnej istniejącej kopii **Rev.12, dokument16.10.2014, seria06 doSupplement4(09.10.2014); katalogURL2015**: `research/gptpro/p4-truck-regulations/files/P4-001.pdf`, s. 20, 42 i 48. Stronę 48 odczytano tekstowo oraz obejrzano w renderze. Ustalono rytm kierunkowskazu 90 ± 30 błysków/min, emisję do 1 s, pierwsze zgaśnięcie do 1,5 s oraz miganie awaryjnych w fazie. Strona 20 rozróżnia homologację pojazdu R48, a strona 42 określa obowiązkowość, liczbę i wysokość lamp cofania. Kategoria O1 ma opcjonalność z pkt 6.4.1; sam warunek długości w pkt 6.4.2 nie tworzy obowiązku. Dokładne warunki są w CSV, a SHA256 źródła i metoda w `regulation-evidence.json`. **To starszy zweryfikowany snapshot; aktualność prawna w 2026 r. pozostaje UNVERIFIED.** Nie redystrybuowano nowej kopii PDF.

Wpis 01-N04 przeniesiono z niezweryfikowanej poprawki R148 Amend.5 na pełny tekst bazowego R148 Add.147 z 9 stycznia 2020 r. (katalog URL 2021-05): ponownie otwarto zachowaną pełną odpowiedź web (2865 linii), pkt 3.3.2.1–4. Nie jest to fragment wyników wyszukiwania. Odczytano także tabelę 10, pkt 5.8.1 (01-N08): cofania — minimum 80 cd w H-V; maksima 300/600/8000 cd zależnie od kierunku. Warunki są w CSV. Bezpośrednie pobranie i screenshot PDF zwracały 403; nie deklarujemy nowej kopii ani obejrzenia składu strony. Próba odczytu publikacji EUR-Lex zwróciła weryfikację człowieka; CAPTCHA nie podejmowano. Starszej Rev.12 nie przedstawiamy jako potwierdzenia nowszej Rev.13.

Dodatkowi kandydaci obejrzani osobno:
- `Lorrylights.jpg` (Rxj, CC BY-SA 3.0): wąski, przepalony i rozmyty widok tyłu; oznaczenia nieczytelne. Odrzucony poza manifestem.
- `Grecja tablica.jpg` (pl:user:lcamtuf, CC BY-SA 3.0): okrągły bursztynowy klosz przy przedniej kratce i czerwonej tablicy, płytka głębia ostrości; E i funkcja nieczytelne. Poza manifestem.
- `Kippauflieger…`: niepobrany wskutek HTTP 429; nieobejrzany, nieopisany, nieliczony.

### 01-006 — kontekst tylnej lampy ciągnika

Ponownie obejrzano istniejącą kopię Commons z `Data/photos/nowe` (Asurnipal, CC BY-SA 4.0, EXIF 2022-06-08) oraz osobno wycinek lewej lampy. Lampa ma około 690 px szerokości w oryginalnym wycinku (**ESTIMATED**, odczyt pikselowy), ale E pozostaje nieczytelne. Materiał pokazuje klosz, barwne wstawki, żebrowanie, mocowanie na błotniku i pusty uchwyt tablicy. Liczba funkcjonalnych komór i świecenie pozostają UNVERIFIED. To 1 kadr z 2 plikami, bez nowego pobrania i bez duplikowania oryginału. **Łącznie 6 kadrów pomocniczych; kwalifikowane E ciągnika/naczepy: 0.**

Flickr: trzy wyszukiwania z filtrem licencji 4/5/9 dały 75 metadanych wyników. Indywidualna fotostrona potwierdza CC BY 2.0; oryginał zwrócił HTTP 429, więc domenę zatrzymano. Próba widoku w Chrome została przerwana przed nawigacją po wykryciu wejścia użytkownika. **Zero obserwacji obrazu Flickr i zero kwalifikowanych kadrów.** Wyniki nie trafiły do manifestu. Dowody: `agent-lamps-search-log.json` oraz `flickr-screening-2026-11-15.json`.

## R149 / R150 — uzupełnienie pierwotnych tekstów

Wiersze 01-N09…N20 uzupełniają `regulations.csv` o R149 i R150 (snapshots 2020; aktualność prawna 2026 UNVERIFIED). Pełne zachowane teksty PDF mają odpowiednio 6864 i 4847 linii; odczytano tabele wraz z warunkami i jednostkami. Nie oparto wpisów na samych fragmentach wyszukiwarki. Metoda, zakres i URL są w `regulation-evidence.json`.

R149: dla przykładowej klasy B zapisano różne punkty mijania i drogowych, wraz z kątami. Ograniczenie w punkcie olśnienia B50L i minimum przy prawej jezdni nie tworzą jednego globalnego zakresu światłości. Klasa konkretnej lampy ciężarówki pozostaje UNVERIFIED. Ekran 10/25 m dotyczy ustawiania granicy światło–cień; nie jest deklarowany jako uniwersalna odległość każdego badania. Warunki pomiaru modułów LED są osobnym wpisem.

R150: odblask opisują CIL/R′ i geometria oświetlenia–obserwacji; lampę opisuje własna światłość. Jednostek mcd/lx oraz cd/(m²·lx) nie wolno zamieniać w cd. **ESTIMATED — wniosek renderera:** odblask powinien reagować na zewnętrzne oświetlenie, a nie świecić stale jak lampa. Tabele obejmują tylko jawnie wskazane klasy, barwy i kąty; nie należy uogólniać ich na wszystkie odblaski.

## Nowe kadry firmowe — wyłącznie link-only

Do głównego manifestu włączono8 osobiście obejrzanych przez agenta kadrów:5 komponentów katalogowych (01-LNK-001…005) i3 rzeczywistej części reflektora (01-VOL-001…003). Każdy ma własny opis i kolumnę wartości z kolorami, kształtem i polami optycznymi; żadnego obrazu firmowego nie zapisano w raw ani repo. Szczegóły galerii i screening w `link-only-candidates/`.

Na etykiecie obudowy 01-VOL-003 czytelne E9 i grupy znaków potwierdzono niezależnie przez drugiego agenta (`data/volvo-label-peer-review.json`). To nowy dowód wyglądu oznaczenia przedniego reflektora ciężarówki, ze źródłowym przypisaniem FH4 i widocznym numerem części. Nie zalicza się do15 tylnych zbliżeń. Dwa generyczne komponenty lampek tablicy mają odczyty E9/L-00, ale przeznaczenia do ciężarówki/naczepy nie potwierdzono z zapisanych materiałów. Brak montażu sam w sobie nie jest dodatkowym warunkiem odrzucenia komponentu; zastosowanie, emisję i scenę trzeba udokumentować osobno. Białe tło katalogowe nie dowodzi pory dnia. Łącznie w głównym manifeście:6 lokalnych kadrów pomocniczych +8 link-only. Kryteria tylne M59 nadal niespełnione. Marek i numerów części nie kopiować na fikcyjny pojazd.

## Tylna lampa MAN 24 V — dwa kadry link-only

01-MAN-001/002: widok klosza i fizycznej etykiety tej samej galerii, bez pobrania. Odczyt etykiety niezależnie powtórzył drugi agent: E1 w okręgu przy 10R-04 7501; osobno MD E24 5884, 24Volt i moce funkcji (2/3/2/4/2/1,7 W) jako dane etykiety, nie pomiar. Szczegóły i granice w data/man-label-peer-review.json. R148 pkt3.3.4.5(b), s.11–12, dopuszcza kod modułu MD bez okręgu; sam brak okręgu nie obala tego kodu. Konkretna homologacja fotometryczna5884 i przypisanie funkcji polom nadal UNVERIFIED. Dwa kadry powiększają zbiór pomocniczy, nie liczniki potwierdzonej fotometrii, emisji ani nocy. Łącznie manifest01 ma16 kadrów:6 lokalnych i10 link-only.

## Europoint — pierwszy czytelny znak tylnej lampy naczepy

01-EUP-001: SOURCED [obejrzany obraz; niezależna recenzja drugiego agenta w link-only-candidates/europoint-observations.json] — E9 w okręgu,5497 oraz S1/IIIA/AR/R1 na fizycznym kloszu. Osobno E24 przy10R-06 0973. To1 pewny odczyt tylnej lampy naczepy, a nie dwa za dwa znaki. 01-EUP-002 to inny detal tej samej lampy bez odczytu E. Zastosowanie naczepowe z opisu oferty; karta TRP tego kodu dotyczy prawego wariantu, nie dowodzi napięcia i wymiarów sfotografowanego lewego. Emisja, noc i oświetlenie tablicy nadal UNVERIFIED. Nie ustalono konkretnej edycji R7/R23/R3/R148/R150 z samego numeru5497. Łącznie18 kadrów:6 lokalnych pomocniczych oraz12 link-only. Kryteria M59 nie są zamknięte.

Klucz symboli Europoint: data/europoint-symbols-regulation-review.json wiąże S1/AR/R1 z tabelą1 R148 i IIIA z tabelą1 oraz zał.5 R150. R148 jest dokumentem z9.01.2020 pod adresem katalogu2021-05; skorygowano etykietę snapshotu. Znaczenia symboli nie ustalają serii homologacji5497 ani rzeczywistej emisji egzemplarza.

## Europoint III — odmienny klosz i etykieta

01-EUP3-001…003: trzy fizyczne kadry jednej części,15 link-only łącznie z pozostałymi zestawami; cały manifest21 kadrów (6 lokalnych). Dwa zbliżenia niezależnie obejrzał drugi agent, data/europoint3-peer-review.json. Na kloszu pewne symbole2a/AR/S1/F1/R1/L i częściowo przycięte E9; pełny numer pozostaje UNVERIFIED. Na etykiecie czytelne E9/6985 przy SM1/IA; przetartego numeru głównej grupy nie odtworzono. To nie dwa egzemplarze ani dowód świecenia. Odczyt SM1/IA nie potwierdza homologacji wszystkich pozostałych funkcji. Katalogowy mały widok odłożono poza manifestem.

Cztery początkowe wartości fotometryczne poddano niezależnemu audytowi i dodano jako01-N21…N24 doCSV (teraz24 rekordy). Recenzja w data/photometry-four-values-peer-review.json doprecyzowuje stosunek5:1, kierunki minimalnej światłości i osobne maksima lamp oznaczonychD oraz powierzchnię/punkty badania tablicy. Steady nie oznacza jednakowej światłości w każdym kierunku ani braku migania kierunkowskazu.

## Dalsze fizyczne części i pierwszy nocny kontekst emisji

used-parts-round3:7 indywidualnie obejrzanych kadrów z3 galerii, tylko link-only. Rozmieszczenie pól i optyki, złącze oraz dolne okienko; E nieodczytane, funkcja tablicy z samego okienka UNVERIFIED. Dwa Iveco mają inne konfiguracje, nie utożsamiono egzemplarzy.

rear-night-round3:01-RN3-04 OathOn, CC BY-SA4.0, Gillingham2025-10-16, nocny zestaw. Agent i koordynator osobno obejrzeli czerwone tylne pola ciągnika pod przodem naczepy oraz czerwone odbicia na mokrej kostce. To1 przyjęty kontekst nocnej emisji, bez odczytuE i bez rozstrzygnięcia stop/pozycja. Nie liczyć go jako pełnego zbliżenia homologacyjnego. Główny manifest teraz29 kadrów:22 link-only i7 lokalnych; progi M59 nadal otwarte.

## Starsze R4/R6/R7 — odrębne datowane źródła

legacy-regulations-round2/regulations.csv:13 wierszy (11SOURCED,2UNVERIFIED). Odczytano pełne oficjalne R4Rev.3 z19.08.2013 iR7Rev.6 z22.11.2012: symbole, serie i warunki fotometrii. Numer rewizji dokumentu nie jest serią homologacji. R6 pozostaje luką po403 oficjalnych plików; przykład2a/01 wR4 nie zastępuje pełnej normyR6. Nie przypisano certyfikatu5497 ani aktualności2026. Nowe ustalenia są w osobnym CSV z punktami, nie powielają24-wierszowej tabeli bazowej.

rear-night-round4:2 kolejne kadry obejrzane i odrzucone jako przód/bok,1NOT_REVIEWED. Brak nowych przyjętych tylnych emisji, brak zachowanych obrazów. RN3-04 pozostaje1nocnym kontekstem, bez czytelnegoE.

## R6 — pełny starszy tekst odnaleziony

r6-source-round3/regulations.csv:9SOURCED z pełnego R6Rev.5,07.10.2011, Supplement21 serii01. Kategorie2a/2b, amber, znak/seria i kierunkowa fotometria z warunkami oraz ograniczeniem nocnego sterowania2b. Koordynator odczytał także tabelę i6.6.2 w pełnym tekście. Wcześniejsze403 Rev.7 pozostają dziennikiem dostępu; nie oznaczają już braku jakiegokolwiek pełnego R6. Snapshot2011 nie jest deklaracją aktualnej wersji2026. Tabele:24 bazowe +13legacy +9R6, z odrębnymi wersjami i statusami.


Used-parts-round4:4 nowe indywidualnie obejrzane kadry firmowe, wyłącznie link-only ARR. Fizyczne E2 DAF/Vignal potwierdzone przez dwóch agentów, pełny numer/funkcje UNVERIFIED; nie zwiększa pełnego licznika homologacji. Oferta DAF części nowej, Renault używanego kompletu. Kolory kloszy i optyczne pola nie dowodzą emisji ani liczby komór. Manifest główny33 rekordy kadrów(7 lokalnych,26 link-only).


R148-series01-round4:7 dodatkowych źródłowych porównań tabeli8, odrębnie od24+13+9 wcześniejszych wierszy. Pełny oficjalny R148Rev1Amendment2 (dokument16.12.2024, Supplement2serii01, wejście22.09.2024) odczytał agent. Kat.1/11 maks.single1200/D600 potwierdzone; ogólne„12bez zmian” względem pierwotnego2020 wymaga korekty: maks.D N.A.→250cd. Równość dla2a/2b/5/6 dotyczy tylko trzech kolumn; nie dowodzi niezmienności wszystkich testów. Źródła/punkty i ograniczenia dostępu koordynatora w podkatalogu. Nie jest to deklaracja aktualności2026.


Conditions-round5:6SOURCED+1UNVERIFIED o warunkachR148Amendment5serii01(03.03.2023). MinimumHV z wyjątkiem kategorii5/6 w kierunkuA; maksimum w każdym kierunku widoczności, minimum pozaosiowe i osobne geometryczne. D/Y rozdzielone; dla zespołuD maksimum przy obu włączonych, minimum przy awarii którejkolwiek — bez dzielenia minimum przez2. Koordynator odczytał zachowany ekstrakt punktów. Table8-comparison-round6 zawiera12porównań tekstowych Am5/Am2;4rozbieżności potęg nadalUNVERIFIED, bo screenshot tabeli zwrócił403. Nie są12nowymi zatwierdzonymi normami ani dowodem daty pierwszej zmiany. Zero nowych zdjęć.


Rear-night-europe-round5:3nowe kadry obejrzane,2odrzucone;1zachowanyAUX Devokewater BY-SA4.0 z31.07.2020. Koordynator osobno obejrzał miniaturę: żuraw i platforma wyglądają na wspólne podwozie, brak pewnego ciągnika/naczepy. Boczne bursztynowe źródła/żółte odbicia odrębne od małego prześwietlonego punktu z tyłu o nieustalonej funkcji. Przyrost kwalifikowanej sceny zestawu0, E0. Główny manifest34kadry(8lokalnych,26link-only); RN3-04 nadaljedynym przyjętym nowym kontekstem tylnej emisji ciągnika pod naczepą.


Front-approval-round5:3 indywidualnie obejrzane firmowe kadry1reflektora Renault GamaT, wyłącznie link-only ARR. Etykieta E2/11057 oraz00 HCR 25 RL 02A PL; osobne E2/10R-03 12010, numeryczęści odrębne. Niezależny przegląd wykrył złe mapowanieURL etykiety na obudowę; poprawiono przed publikacją, ponowny bezpośredni ogląd3URL i niezależnyPASS właściwej etykiety zachowane w raporcie. Literalnego02A nie rozwijano w niepotwierdzoną funkcję. 3główne pola optyczne nie dowodzą3komór ani emisji. Main37rekordów kadrów(8lokalnych,29link-only), nie37homologacji.


Evidence-audit-round6: dokumentacyjny ledger snapshotu37głównych kadrów plus9odrzuceń i3NOT_REVIEWED z określonych dzienników. Bez nowych oględzin/pobrań, nie zastępuje audytu wizualnego20%. Pełne odczyty4:2przód,1tyłEUP5497,1tylko boczna grupaSM1/IA; symbolE bez pełnego numeru/MD/EMC osobno. Geometryczne progi tylnych15zbliżeń niezatwierdzone;0bezspornych wymaganych włączonych/nocnych zbliżeń i0lampek tablicy o potwierdzonym ciężarowym zastosowaniu. Globalna liczba egzemplarzyUNVERIFIED. To plan braków, nie domknięcieM59.


Korekta datowaniaR48: koordynator niezależnie odczytał i obejrzał okładkę istniejącegoP4-001.pdf:16.10.2014, Rev12, seria06 doSupplement4wejście09.10.2014. Poprzedni skrót„snapshot2015” brał rok kataloguURL i został zastąpiony jawną datą dokumentu; wartości/punkty norm pozostały bez zmian. Skład źródła/hash nadal ten sam, render okładki wyłącznie poza gitem. R148 w metadanych także rozdziela dokument09.01.2020 odURL2021-05.


Heavy-plate-lamps-round7:4 nowe, indywidualnie obejrzane firmowe kadry1fizycznej częściSIM (całość, mocowanie, logo, optyka), tylko link-onlyARR. Zastosowanie tablicyKrone/Schmitz/Koegel/Fliegl zadeklarowane przez sprzedawcęPartsBit878531; nie pomiar zgodności ani odczytE/L. Oba najważniejszeURL(całość/optyka) niezależnie sprawdzone przez drugiego agenta. Jedno wspólne okno z3widocznymi grupami nie dowodzi3komór/źródeł. E/L/pełny numer i emisjaUNVERIFIED. To1udokumentowany typ referencyjny z deklaracją ciężarową, nie4egzemplarze i nie ukończone5lampekM59. Main41rekordów kadrów(8lokalnych,33link-only).

## Geometria lampki tablicy — obieg8

[Osobny CSV](plate-geometry-round8/norms.csv):8SOURCED i2UNVERIFIED,0nowychfotografii. R4pkt7:≤82°kąt padania, definicja krańca/środka krawędzi i przypisanego obszaru przy wielu lampkach. R1485.11.2:centrowanie próbki; formaty testowe tablic i łączenie siatek nie są wymiarami tablic polskich ani kategoriami kierunkowskazów. R48Rev12,16.10.2014,6.8.2–6.8.6 nie ustanawia uniwersalnej wysokości/odsunięcia lampki. R1485.11.5:wyjątek czerwieni tylko combined/grouped z tylną lampą; nie biała emisja ani samo sąsiedztwo. Kątów pól85°/60° i współrzędnych siatek bez bitmapy nie przyjęto. Datowane teksty nie zatwierdzają aktualności2026.

## Proplast — inna rodzina tablicowa, obieg9

Główny manifest45rekordów kadrów (8lokalnych/37link-only). [Heavy-plate-round9](heavy-plate-round9/README.md):4różne fotografie co najmniej1części Proplast40205506,0pobrań. Optyka czerwonego obrzeża/bezbarwnych rowków oraz osobne etykiety produktu. Niezależny peer obejrzał pełną optykę i etykietę40205506; etykieta potwierdza tekst funkcji, nie homologację. Actros/24V to oddzielne deklaracje oferty/etykiety, nie odczyt peer z dwóch zdjęć. E/L/pełny numer i emisja pozostająUNVERIFIED; nadrukMenge2 nie dowodzi2widocznych egzemplarzy. Nie są to4lampki ani4kwalifikowane tylne zbliżeniaECE. WzględemSIM inny model/IDoferty, nie powielony kadr.

## Ponowny audyt wizualny — obieg10

[Raport i10indywidualnych oglądów](qualification-audit-round10/README.md):10/45=22.22%, opisy zgodne10/sprzeczne0. Dobór celowy, seed2026111510 wyłącznie porządkuje wybraneID; nie losowa próba ani ocena pozostałych35.8dużychtylnychoptyk ma geometrię≥10%, z czego4mają potwierdzony właściwy typciągnik/naczepa; nie oznacza to4nowych pełnychodczytówECE ani pełnejkwalifikacjiM59. Inne4konfiguracjęstrict mająUNVERIFIED. RN3-04 rzeczywiście noc/emisja, ale rozmiar pojedynczej lampy nie potwierdza progu zbliżenia, więc0nocnych/włączonychzbliżeń ztejpróbki. HP7to1tablicowaczęść, nie4urządzenia. Główny snapshot45hash sprawdzony przez koordynatora, ID/jawne wyniki10/45 zgodne. Koordynator nie dopisał nowych oglądów do10agenta. Progi15/4/3/5 pozostająotwarte;35NOT_REVIEWED tejrundy nie uznano za złe ani zaliczone.

## Kandydat Hella i nocny AUX — bez wzrostu kwalifikacji

[Hella003389](heavy-plate-round11/README.md):3link-onlykadry, w tym2części i1opakowania,0pobrań. Oferta-061, pudełko-011; nie rozstrzygnięto tożsamości egzemplarza i ciężkiego zastosowania. KatalogoweE122819 nie jest odczytem fotografii. 1nowa rodzina-kandydat,0strictciężkichtablicowych; pozostaje tylko w osobnym podmanifeście, nie zwiększa głównego45.

[Tandem-night-round12](tandem-night-round12/README.md):1nowy kadrCCBY-SA3JoeKiser,1oryginał1127×674 pozaGit,1miniatura≤800. Koordynator i niezależnypeer osobno obejrzeli oryginał. Chłodnobiałe pola podłoża przy manewrowaniu i czerwone poświaty, bez fizycznegoE/kraju/systemuECE. TylkoAUXkontrastu, bez wzrostu15/4/3/5 i bez dodania do45głównychrekordów. Jasnego poziomego pasa nie utożsamiono z emiterem, koloru zLED/CCT ani powierzchni z solą/śniegiem. Oba podpakiety mają jawne źródła/opisy/ograniczenia.

## Pionowa Hella naczepy — kontekst, obieg12

[Rear-approval-round12](rear-approval-round12/README.md):3fotografie rzeczywistej części link-only,0pobrań; jeden pełny klosz i2AUXtyłu/etykiety. Oferta wiąże używanąHella2VP340961-531 z naczepąSchmitz, lecz etykieta czytelna tylko2VP340.961-53; nie dopisano końcówki ztytułu. CE,24V/21W i dataetykiety nie są ECE, pomiaremświatłości ani datąfotografii. Cztery duże strefy nie dowodzą4komór. FizycznyE/funkcje i emisja nieodczytane;1nowa rodzina kontekstowa,0nowych homologacji. Zachowano osobny podmanifest, bez wzrostu45głównych ani15/4/3/5.

## Optyka i świecenie — obieg13 po niezależnej recenzji

[Lit-rear-round13](lit-rear-round13/README.md):2fotografie producentów,0pobrań/2link-onlyARR, obie obejrzane osobno przez2agentów. Knapen:duża zamontowanaEuropointIII, szerokośćEST35–45%obrazu; czerwone pasma/refleks nie rozstrzygają załączenia wobec silnego słońca, emisjaUNVERIFIED. Ermax:rzeczywiste jasne czerwonepunkty/białeźródło/bursztynowepunkty, emisjaPASS, lecz pojedyncze okrągłe modułyEST7–8%szerokości i<300px. Nie zsumowano trzech lamp do jednej kwalifikacji ani szerokości zpowierzchnią. Ciemne wnętrze przy jasnym plenerze nie dowodzi nocy.0nowych włączonych/nocnychzbliżeń i0E. Osobny podmanifest, główny45bez zmian.


## Actros i uzupełnienie odblasków — obiegi14–15

Główny manifest47kadrów(8lokalnych/39link-only). [Actros](front-approval-round15/README.md):2nowe fotografie1fizycznego reflektoraKOITO zofertyA9618202639,0pobrań. DokładnyetykietowyURLpo dwukrotnymodczycie autora i niezależnympeer: E13wokręgu/13106,00DCR PL 01 1a 02 A 00 RL oraz27.5na tej samej naklejce. NieWatt, nieR27.5, nie zmierzonaświatłość. Pełnyklosz ietykieta to2kadry1części, bez wzrostu15tylnych/4włączonych/3nocnych. Historycznyaudyt10/45pozostajesnapshotem, nie zmieniono jego daty/denominatora po dodaniu2nowych.

[R150](retroreflection-round14/README.md):2020ma3potwierdzone tekstowowarunki i3macierzeUNVERIFIED, wyłączone z parametrów generatora. Woddzielnym2021HTMLtabela5rzeczywiścieobejrzana:3osobne wiarygodne rekordyCIL dlaIIIA/IIIBz jednostkami/kątami; nieemitowanecd. Nieutożsamiono snapshotów2020/2021ani aktualności2026. Metryki czasu recenzji obejmuje jawnaerrata review-time-audit, bez ruszaniaEXIF/dat źródeł.

## Wartość odniesienia, demonstracja i tylny klosz — obiegi16–18

Główny manifest:49kadrów (8lokalnych/41link-only). [EcopointII](rear-mark-closeup-round18/README.md):2fotografie jednego fizycznego klosza bez obudowy. Po dwóch niezależnych odczytach E9 wokręgu i S1/2a/IIIA/AR/F1/SM1 pewne; pełny numer, R1 i drobne serie UNVERIFIED. Nie zaliczono kandydata1853 jako pełnego numeru. KatalogKögel przypisuje6611489 całej lewej lampieHybrid, co nie potwierdza numeru osobnego klosza w ofercie. Emisja/noc0,0nowych pełnych numerów; geometria dużej optyki nie zastępuje tych dowodów.

[HR16](highbeam-reference-round16/README.md):cztery źródłowe warunki R1492020 wyjaśniają ilorazIM/4300, dyskretną listę wartości, zakres oznaczenia grupy oraz CoP.27.5×4300 i30×4300 to wyłącznie ESTIMATED algebraiczne przykłady, nie dokładne pomiary Actrosa/Volvo ani automatyczne przypisanie dawnychDCR doR149. Konkretne wersje/punkty/ograniczenia wCSV.

[LL17](live-light-demonstrations-round17/README.md):jeden oficjalny filmERMAX i trzy faktycznie obejrzane stany ztimecode’ami. Nie trzy fotografie. Technika fizycznego nagrania/montażu pozostajeUNVERIFIED, więc nie zwiększono fizycznychON/OFF ani progówM59. Tylko link i własne opisy,0pobrań/stillów. Pozostają otwarte15tylnych/4włączone/3nocne/5ciężkichtablicowych.


## VignalLC8 — kontekst fizycznej części, runda20

[physical-rear-approval-round20](physical-rear-approval-round20/README.md):3indywidualnie obejrzane kadry jednej realnej części156780/RIGHT,1600×1200 wUI; link-onlyARR,0pobrań. Przód/tył/etykieta, kolor/kształt/komorylubUNKNOWN wchildmanifest. Producent potwierdza zastosowanieTrucks/ScaniaP&R, sprzeczny parametr osobowe wofercie ujawniony. E/numer/funkcje nieczytelne na realnymkloszu, katalogowegoE2/2040 nie przeniesiono.0nowychpotwierdzonych homologacji/ON/noc. PozostajeAUX poza głównym49; nie3lampy i nie nowa rodzina wobec istniejącegoLC8, tylko odrębny model156780 vs156290.


## Światła drogowe: możliwe kombinacje — runda21

[highbeam-simultaneous-round21](highbeam-simultaneous-round21/README.md):4warunki/interpretacje,0fotografii. R48Rev12/16.10.2014,s32,6.1.9.1–.2:430000cd/ref100 dla reflektorów mogących być jednocześnie załączone, sumowanie znaków odniesienia; literalne stareR/CR→10 nie tylneR1. R149kwantyzacja uniemożliwia dokładne odtworzenieIM z27.5/30, bez nowychpomiarów. UNGRE2024/5 projekt redline usuwa podwójnyfragmentcd/przyref100, PROPOSAL_NOT_ADOPTION_PROOF, bez twierdzeniaEIF/aktualności2026. Agent obejrzał pełne dokumenty i bitmapy, root osobno R48s32/projekts2. Dokumenty/rendery pozaGit; nie zmieniono bazowych24norm ani HR16.


## Etap przyjęcia zmiany — runda22

[highbeam-adoption-round22](highbeam-adoption-round22/README.md):3oficjalne dokumenty/4etapy/0fotografii. GRE90odroczeniepoGRE2024/5→WP29/2025/36ref≤100→WP29/1184tabelas21AC1przyjęcieSupp1do09,34/0/0. Pkt69usuwa tylko6.2.6.1.2, nie6.1.9.1; zachowanie limituref100 w przyjętym pakiecie to jawna syntezaźródeł. Root osobnoobejrzałbitmapy§69/s15 i tabelis21, agentpełne3dokumenty. AC1_ADOPTION_CONFIRMED nieEIF; aktualnytekst2026/przejściowedlastarychciężarówek nadalUNVERIFIED. Runda21 pozostajehistoryczna, niepodmienionojejdowodów.2PDFraportówrawpozaGit, trzecidokumentodczytanyfullwebbezlokalnegoPDFpo404STOP.


## Definitywne wejście w życie — runda24

[highbeam-entry-force-round24](highbeam-entry-force-round24/README.md):pełna notaONZC.N.513.2025z06.10.2025potwierdza skutki od26.09.2025 i dokładnie wskazujeWP29/2025/36z§69raportu1184. Root+agentosobnoobejrzeli całąstronę;3ustalenia/2źródła/0fotografii. PowiązanieSupp1do09/ref100 jawnie złańcuchemHA22, nota sama nieprzepisujebrzmienia6.1.9.1. Stan całego tekstu2026/przejściowedlastarychDCR nadalUNVERIFIED. R21/R22historyczneniezmienione; późniejszydowód zamykaEIFwoddzielnymkatalogu.


## Chereau: rzeczywista emisja — runda23

[lit-rear-closeup-round23](lit-rear-closeup-round23/README.md):2nowe link-onlyARR kadry604×453. FLEX-C zamontowanydużymoduł, emisjaUNVERIFIED. Citylight:rzeczywisty zestaw nazewnętrznymplacu, dolne czerwone lampy świecą i oświetlajągrunt; root+agent osobno obejrzeliCitylight. Białe robocze/odblaski drzwi wydzielone. Pojedyncza obudowaEST10–12%szerokości/60–70px, granica przy poświacieBORDERLINE;0nowychstrictzbliżeń/E,natywne300FAIL. Zmierzchowawyglądemscena, ścisłanocUNVERIFIED; M59dopuszczazmierzch.0pobrań/screenshotów. AUXpoza głównym49, nie liczyć2lamp w1kadrze jako2kadrów.


## Lampka tablicy: znak L/E9 — runda25

[heavy-plate-round25](heavy-plate-round25/README.md):3nowe rzeczywiste link-onlyARR kadry1obudowy/optyki. MakroL / E9wokręgu /00 4127 zgodnie odczytane przezautora i root woddzielnychprzeglądarkach (peer nieślepy). Wnętrzeniekompletne; producentowyPN/konkretne ciężkie zastosowanieUNVERIFIED, sellerL004127nieuznanyzaPN.0ON/noc,0pobrań/screenshotów. Liczba funkcjonalnychkomórUNKNOWN. AUXpoza głównym49,3kadry nie3części ani arbitralny nowywymóg5rodzin; kwalifikacjaheavyoddzielonaodczytelnegoznaku.

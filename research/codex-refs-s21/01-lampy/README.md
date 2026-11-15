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

`regulations.csv` zawiera 8 wpisów. Dane R48 zweryfikowano w pełnej istniejącej kopii **Rev.12, seria 06 (snapshot z 2015 r.)**: `research/gptpro/p4-truck-regulations/files/P4-001.pdf`, s. 20, 42 i 48. Stronę 48 odczytano tekstowo oraz obejrzano w renderze. Ustalono rytm kierunkowskazu 90 ± 30 błysków/min, emisję do 1 s, pierwsze zgaśnięcie do 1,5 s oraz miganie awaryjnych w fazie. Strona 20 rozróżnia homologację pojazdu R48, a strona 42 określa obowiązkowość, liczbę i wysokość lamp cofania. Kategoria O1 ma opcjonalność z pkt 6.4.1; sam warunek długości w pkt 6.4.2 nie tworzy obowiązku. Dokładne warunki są w CSV, a SHA256 źródła i metoda w `regulation-evidence.json`. **To starszy zweryfikowany snapshot; aktualność prawna w 2026 r. pozostaje UNVERIFIED.** Nie redystrybuowano nowej kopii PDF.

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

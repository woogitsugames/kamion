# Przegląd Mistrala M52-FIX-3 (p2-surfaces-2) — s20, 2026-11-13

Gałąź `origin/research/mistral-p2-surfaces-2`, commity `1533368db` (cz. 1) i `26aeb871f` (finał). Wzorzec: blok M52-FIX-3 w `docs/owner/MISTRAL-FIXES-9.md` i przegląd s18 `docs/reports/REVIEW-2026-11-13-s18-mistral-fixes-r8.md`.
Metoda: `git archive` do scratch (bez worktree). OSM przeliczony z `Data/raw/osm/podlaskie-261108.osm.pbf` (pyosmium, odległość punkt–odcinek, kierunek odcinka mod 180). Obejrzałem 20 unikalnych kadrów z `research/_incoming/mistral-p2-surfaces-2/` (skala 900 px). Porównałem też md5 wszystkich 80 JPG.

## Werdykt: **FIX ponownie** (tylko pkt 2 — oględziny kadrów)

Punkty 1, 3, 4 i 5 są wykonane i sprawdzone. Liczby OSM nie są zmyślone. Pkt 2 („co widać”) jest wpisany we wszystkie 80 wierszy, ale w mojej próbie opis nie zgadza się z obrazem w ok. 40 % wierszy. Twierdzenie „4 pliki niedostępne w CDN” jest nieprawdziwe w praktyce, bo te same pliki są w paczce i są obejrzane w innych wierszach. Wniosek M52-116 („szary asfalt wszędzie”) jest zgodny z kadrami, które widziałem, ale stoi na tych samych oględzinach. Blok do wklejenia: `docs/owner/MISTRAL-FIXES-11.md` (M52-FIX-4).
Jeśli lider woli scalić teraz: część rysunkowa i przypisania ulic są poprawne. Scalenie z erratą jest możliwe pod warunkiem, że w REVIEW-NOTE kolumna „co widać” w wierszach kadrów (M52-029…108) zostanie oznaczona jako niewiarygodna.

## 1. Punkty bloku M52-FIX-3

| Pkt | Żądanie | Stan | Dowód |
|---|---|---|---|
| 1a | M52-103/104/105 → Al. Tysiąclecia | **TAK** | `element`/`lokalizacja` poprawione. OSM: way 946729184 w 6,3 m, Δ 0,9°; równoległa 536419697 w 5,4 m (moje przeliczenie jest identyczne). Kadry sokolska-01/03 pokazują dojazd do skrzyżowania z sygnalizacją, w tle Circle K i żółty wieżowiec. |
| 1b | Reguła M46 (≤25 m, ≤30°) + way_id + Δ we wszystkich wierszach route/crossings | **TAK, z uwagami** | 44 wiersze w formacie „M46 r3 (OSM): way …”. Wszystkie 44 zgadzają się z moim przeliczeniem (≤1 m, ≤2°). 9 wierszy w innym formacie (053–057, 075, 077, 083, 099) też się zgadza. Uwagi: (a) **M52-071** wybiera rondo 536419699 (9,6 m, Δ 29,1°), żeby „spełnić” regułę. Najbliższy odcinek to Andersa 177876107 (1,6 m, Δ 55,4°), a ten sam kadr w M52-075 opisano jako „artefakt magnetometru”. To niespójne. (b) W 30 wierszach zostały stare wpisy „N m od osi jezdni wg OSM” (13× „-1 m”, M52-053 „13 m”), sprzeczne z liczbami r3. (c) W M52-053/055/056/057 uzasadnienie M46 mówi „jezdnia estakady z barierami mostowymi”, a opis kadru mówi „na poziomie terenu”. M52-053 jest naprawdę na poziomie terenu (mikomax). |
| 2 | Oględziny każdego kadru + „co widać” + ocena elementu | **FORMALNIE TAK, MERYTORYCZNIE NIE** | Patrz §2. |
| 3 | P-5: wycofać „rozbieżność wewnętrzną” | **TAK** | M52-012 i tabela zad. 1: 0,32 = 2 × 0,16, zapis wycofany. Uwaga poza blokiem: przy P-13 (M52-020, README) nadal jest „rozbieżność wewnętrzna rozporządzenia” 0,2333 vs 0,2625. Blok tego nie obejmował; zostawiam jako otwarte. |
| 4 | Kopiuj-wklej M52-006/014/015/027 + nowy wiersz P-3b | **TAK** | M52-006 dotyczy tylko szerokości 0,12. Uwagi M52-014 (przerwa) i M52-015 (kreska) są teraz poprawne. M52-027 ma tylko stan r2. **M52-118** = P-3b kreska/przerwa 1,00/1,00, rys. 2.2.1.9, s. 539. Manifest ma 118 rekordów i 17 kolumn. |
| 5 | Samokontrola 20 %, nowy seed, „co widać” + ulica OSM + Δ | **TAK (formalnie)** | Seed 20261114: `random.Random(20261114).sample(sorted(ids),24)` odtwarza dokładnie listę z `audit_20_percent.json`. Próba zawiera jednak M52-031 i M52-071, a w obu są błędy z §2. Samokontrola ich nie wykryła („0 problemów”). |
| — | Zakres i PR | OK | Zmienione są tylko pliki `research/mistral/p2-surfaces-2/` (README, manifest, audit). Komentarz w PR #48 zawiera surowy `git diff --stat`. Gałąź nie jest zrebase'owana na obecny `origin/main` (1654f0143), ale zmienia tylko własny katalog, więc nie ma konfliktu. |

## 2. Oględziny kadrów — moja próba

Próbę wybrałem jawnym seedem **20261115**: `random.Random(20261115).sample(range(118),24)` → M52-004, 006, 013, 021, 023, 025, 031, 039, 046, 058, 061, 067, 078, 081, 085, 090, 092, 095, 099, 100, 103, 106, 107, 115. Dołożyłem cztery wiersze „niedostępne” (071/075/077/083) i podejrzane pary duplikatów (050/068, 089/102, 053, 105). Razem obejrzałem 20 unikalnych JPG, czyli 24 wiersze kadrów.

**Duplikaty bajtowe (md5):** 11 par plików jest identycznych, m.in. jar-03 = cross-andersa-02 (M52-031 = M52-071) i jar-05 = cross-andersa-06 (M52-033 = M52-075). Czyli „niedostępne w CDN” kadry M52-071 i M52-075 Mistral obejrzał w wierszach M52-031 i M52-033. Pliki M52-077 (cross-andersa-08) i M52-083 (cross-andersa-14) są w paczce ZIP Mistrala i otwierają się bez problemu.

| Wiersz (plik) | Opis Mistrala (skrót) | Co widać naprawdę | Ocena |
|---|---|---|---|
| M52-031 (jar-03) | podwójna ciągła, bariery z prawej, w tle rondo, kominy EC | pojedyncza przerywana linia pasa + krawędziowe, bariery obustronne, zbiornik EC z niebieskimi pasami, komin, słupy WN; ronda nie widać | ✗ |
| M52-033 (jar-05) | linie ciągłe i przerywane, bariery obustronne, „wieża ciśnień” z niebieskimi pasami | zgodne (to zbiornik EC, nie wieża ciśnień) | ✓ |
| M52-039 (jar-11) | „sekw. KV 14055”, podwójna ciągła, w tle rondo i kominy | sekwencja 2769366; przerywana linia pasa, bariery obustronne, słonecznie, bez kominów i ronda; za lewą barierą czerwony pas | ✗ |
| M52-071 / 075 | „PLIK NIEDOSTĘPNY” | pliki są w paczce (= jar-03 / jar-05) | ✗ |
| M52-077 (cross-andersa-08), M52-083 (‑14) | niedostępne; „kadr z estakady — przypisanie utrzymane” | **poziom terenu**: jezdnia DK19, łącznica z zebrą (P-10) i tablicą prowadzącą U-3, budynek mikomax (w ‑14 także D-1) — zgodne z łącznicą 177912090 | ✗ |
| M52-053 (andersa-14055-01) | opis: poziom terenu, mikomax; M46: „jezdnia estakady z barierami” | poziom terenu, bez barier mostowych | ½ (opis ✓, M46 ✗) |
| M52-061 (andersa-2769366-04) | „jezdnia na poziomie terenu”, bariera po prawej | **estakada**: balustrada mostowa obustronna | ✗ |
| M52-067 (andersa-3686129-04) | podwójna ciągła, poziom terenu | **estakada**, przerywana linia pasa, balustrady mostowe | ✗ |
| M52-068 (andersa-3686129-05 = jar-22) | „poziom terenu” | **estakada**; w M52-050 ten sam plik opisano jako estakadę | ✗ |
| M52-102 (tysiac-10 = cross-tys-06) | strzałki, pasy przejścia z płytkami, sygnalizatory | brak strzałek, przejścia i sygnalizatorów w kadrze; jest Orlen i wieżowiec (M52-089 dla tego samego pliku jest bliżej prawdy) | ✗ |
| M52-103 (sokolska-01) | strzałki, przejście, sygnalizacja, „znak ostrzegawczy” | zgodne; znak to D-1 (informacyjny), nie ostrzegawczy | ✓ (drobna) |
| M52-105 (sokolska-03) | linie, strzałki, sygnalizacja, stacje paliw | zgodne | ✓ |
| M52-090 (cross-tys-07) | Circle K, żółty wieżowiec, przejście, sygnalizatory | zgodne (płytek dotykowych nie widać) | ✓ |
| M52-099 (tysiac-07) | chodnik z lewej, sygnalizator, billboard „Kocham Polskę” | zgodne; podwójna ciągła widoczna | ✓ |
| M52-100 (tysiac-08) | podwójna ciągła, chodnik **po prawej** | podwójna ciągła ✓; chodnik jest po lewej, po prawej trawnik | ~ |
| M52-078 (cross-andersa-09) | ciężarówka, chodnik po prawej, brak przejścia w kadrze | zgodne | ✓ |
| M52-081 (cross-andersa-12) | bariery, znaki kierunkowe, billboardy, brak przejścia | zgodne | ✓ |
| M52-085 (cross-tys-02) | przejście z pasami i płytkami, metalowe barierki | zebra i D-6 przy prawej krawędzi ✓; płytek nie widać, zamiast metalowych barierek jest żółty płot i słupki | ~ |
| M52-092 (cross-tys-09) | podwójna ciągła, przejście z pasami, Orlen, żółty wieżowiec | Orlen i wieżowiec ✓; przejścia w kadrze nie ma | ~ |
| M52-089 (cross-tys-06) | podwójna ciągła, chodnik, Orlen, skrzyżowanie | zgodne | ✓ |
| M52-050 (jar-22) | estakada, bariery obustronne | zgodne | ✓ |
| M52-106 (rynek-cc0-01) | szara kostka, „płyt granitowych brak” | na pierwszym planie są wielkoformatowe jasne pasy płyt i drobnoziarnista nawierzchnia; „brak płyt” jest wątpliwe | ~ |

Wynik: **11 ✓, 5 ~, 10 ✗** na 26 ocen wierszy. Główne błędy są systemowe:
1. Szablon „jezdnia na poziomie terenu” trafił do wierszy route/ z sekwencji 2769366/3686129 przy rondzie, które leżą na estakadzie (061, 062, 067, 068). Dla identycznych plików jar-* mówią to samo co wiersze „estakada potwierdzona”, więc manifest sam sobie przeczy w 3 parach (029/057, 041/062, 050/068).
2. Wszystkie 17 wierszy jar-* z sekwencji 2769366/3686129 (M52-036…052) mają w opisie „sekw. KV 14055”.
3. „Podwójna ciągła” pojawia się tam, gdzie widać przerywaną linię pasa.

## 3. Wiersze nie-kadrowe z próby (seed 20261115)

M52-004, 006, 013, 021, 023, 025: kody, rysunki i strony (P-3a rys. 2.2.1.8 s. 538, P-6 rys. 2.2.1.12 s. 541, P-14 rys. 4.2.5.1 s. 573, P-21b tab. 5.3 s. 589) są zgodne z odczytem s17/s18 i z tabelą README. PDF-u nie renderowałem ponownie. M52-115 (Wytyczne ZDM 2025, BIP 103311): wymiary wpustów uczciwie oznaczone UNVERIFIED. Liczby wyglądają na niezmyślone.

## 4. Licencje

KartaView CC BY-SA 4.0 → `REFERENCE_NOT_TEXTURE` (wszystkie 77 wierszy KV). Commons: Rakoon CC0 ×2 i R. Botev CC BY 3.0 pl. OSM: ODbL (dane referencyjne). Dz.U./BIP: dokument urzędowy. Wpisy są spójne z `sources.md`. Nie ma Google ani Street View. Tokenów nie używałem i nie wypisywałem (kadry obejrzane z lokalnego `_incoming`).

## 5. Otwarte (poza blokiem)

- P-13: „rozbieżność wewnętrzna” 0,2333 vs 0,2625 nadal jest w README i w M52-020. Do potwierdzenia renderem przy następnej rundzie rysunków.
- jar-11 i andersa-3686129-05: za lewą barierą estakady widać czerwony pas (gzyms albo pas w pasie dzielącym). Nie leży na jezdni, ale zad. 4 dotyczy też pasów rowerowych. Wymaga jednego zdania w M52-116.

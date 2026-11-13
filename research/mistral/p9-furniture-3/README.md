# M50 — Wyposażenie uliczne (street furniture) 3: Białystok, kafel 53,152 N / 23,168 E

Badanie dla Kamiona (symulator ciężarówki, Białystok 1:1). Kontynuacja i uzupełnienie
`research/g5-street-furniture/` oraz `research/gptpro/p9-street-furniture-2/` — **żadna pozycja
z tamtych zestawień nie jest powtórzona** (odrzucono duplikaty: wcześniejsze numery M41–M49/G5/P9
dot. tych samych dokumentów/obiektów; tu wyłącznie nowe kadry i nowe odczyty).

- **Gałąź:** `research/mistral-p9-furniture-3` (od najnowszego `origin/main`)
- **Kafel (WGS84):** 53,143–53,161 N, 23,147–23,183 E (obwiednia wokół 53,152 N 23,168 E) —
  ul. gen. Wł. Andersa, Al. Tysiąclecia PP, ul. Sokólska, ul. Wileńska (+ skrzyżowania
  Kombatantów/Radzymińska/1 Armii WP)
- **Autor:** Vibe (Mistral), 2026-11-13

## Zakres (zgodnie z zadaniem)

1. Zdjęcia z poziomu kierowcy (z jezdni) dla 11 typów wyposażenia — ≥ 2 kadry na typ.
2. Odczyt skanów: OPZ ZMK DZ.26.2.8.2026.JO (stojaki rowerowe), STO ZDM Warszawa TOS_1
   (słupy oświetleniowe), Dz.U. 2019 poz. 2311 zał. 3 (sygnalizatory — wysokości montażu,
   skrajnia) i zał. 4 (słupki U-5a, bariery U-12, hydranty).
3. Model ławek i koszy Glasdon Europe AB dostarczonych do Białegostoku w 2019 (BIP, umowa,
   protokół) + wymiary z karty produktu (tylko fakty).
4. Wysokości latarni w Białymstoku wg klasy drogi (projekty oświetlenia BIP / standardy ZDM).
5. Karta żerdzi wirowanej E-12 u producenta **innego niż ZPUE** — potwierdzenie 12,0 m
   i średnic.

## Manifest

`manifest.csv` — id `M50-001…M50-066` (49 wierszy pierwotnych + 16 z pass B: M50-050…M50-065 + 1 z pass C: M50-066); kolumny zgodne z zadaniem:
`id, obiekt, model_wzor, wymiary_m, materiał, kolor_ral, dokument_strona, lat, lon,
kierunek_deg, data_zdjęcia, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu,
status, uwagi`.

Konwencje:
- `lat/lon` = pozycja kamery (WGS84, 6 miejsc), `kierunek_deg` = heading kamery z API KartaView;
  **azymut do obiektu i odległość** podane w `uwagi` (liczone z haversine/loksodroma względem
  obiektu z OSM — node OSM wskazany jawnie; jeśli obiekt nie jest w OSM, wskazany jest
  najbliższy node tego typu — to Kotwica ESTIMATED, opisana w uwagach).
- `sezon` wyliczony z miesiąca zdjęcia (lato V–VIII, jesień IX–X, zima XII–II, wiosna III–IV);
  `pora_dnia` ESTIMATED z `dateAdded` UTC+1 (zaznaczone w każdej uwadze).
- Wiersze dokumentowe: puste `lat/lon/kierunek_deg/data_zdjęcia/sezon/pora_dnia`, za to
  `dokument_strona` z **numerem strony**.

### Statusy
- `VERIFIED` — fakt odczytany bezpośrednio z warstwy tekstowej dokumentu (Dz.U. cz. 2, DOCX
  STO, BIP) lub z karty producenta (fakty, plik niepobrany).
- `VERIFIED_WIZJA` — obecność obiektu w kadrze potwierdzona analizą wizyjną modelu (OCR/VA).
- `TO_VERIFY` — pozycja kandydacka (wartość z OCR indeksu wyszukiwarki albo kadr do
  potwierdzenia wizją) — jawnie oznaczona, nigdy nie podawana jako fakt.
- `NOT_FOUND` — kadr kandydacki przeanalizowany wizyjnie, **obiektu nie ma w FOV** (w uwagach
  przyczyna: geometria FOV — odchyłka azymutu od osi kamery — albo brak obiektu w kadrze);
  typ może być potwierdzony w innym wierszu.
- `UNVERIFIED` / `ESTIMATED` — brak źródła liczbowego; w uwagach metoda/oszacowanie.

**M50-FIX (2026-11-13, wg specyfikacji docs/owner/MISTRAL-FIXES-8.md §M50-FIX i przeglądu r8):**
wszystkie 24 pierwotne kadry manifestu ponownie zweryfikowane wizyjnie (pass A — 1 kadr =
1 wywołanie modelu wizyjnego), wyniki korygujące wg przeglądu r8 zastosowane uczciwie
(hydranty 5062587/1326673829/1326673477, słupek U-5a 219381941, żerdź 1326673805,
bariera 993066622, szafka 219382225, latarnia 219382073 → NOT_FOUND; pozycje TO_VERIFY
M50-008/M50-023 domknięte drugim odczytem w pass B → NOT_FOUND). Pass B dołożył 16 nowych
wierszy: kadry z kotwicą geometryczną OSM (kryteria FIX: odchyłka azymutu ≤ 30°,
odległość ≤ 25 m, kotwica = node/way OSM) oraz uczciwe kadry negatywne near-miss.
Wynik pass A/B (65 wierszy): 25 × VERIFIED (dokumenty), 16 × VERIFIED_WIZJA,
24 × NOT_FOUND, 0 × TO_VERIFY.

**M50-FIX pass C (2026-11-13, wg erraty s17 z przeglądu REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md):**
pełny uczciwy przebieg wizyjny (63 kadry = 40 wierszy foto manifestu + 23 kadry Panoramax; **1 kadr =
1 wywołanie** modelu wizyjnego; limit 20 wywołań/turę rozłożony na 5 tur; pełny dziennik: `vision_run.json`).
Zastosowana errata s17: **M50-059/060 → NOT_FOUND** (na kadrach prywatne ogrodzenie prętowe posesji,
nie bariera U-12 — potwierdzone wizyjnie w pass C), **M50-017 → NOT_FOUND** (wiata/pawilon przy BP, nie
ławka). Nowe potwierdzenia wizyjne pass C: **M50-008 → VERIFIED_WIZJA** (stalowa odbojnica w-beam 5–10 m
po lewej — follow-up rozróżnił od ekranu/ogrodzenia; bez kotwicy OSM — bariery U-12 niemapowane w kaflu),
**nowy wiersz M50-066** (latarnia, kadr 993028082 z sekwencji 2769366, kotwica node 12625592983,
19,5 m/18°). Uzupełniony ekstrakt OSM (street_lamp: +2 węzły 12073055699/9845363978) potwierdza kotwice
M50-056/057 z pass B. Dodatkowo sprawdzono sąsiednie klatki (zapas): 219382387 (8,4 m/29°) i
219382391 (20,7 m/10°) — latarnie zakotwiczone, nie dodane jako wiersze (typ już ma ≥ 2).
Wynik końcowy (66 wierszy): **25 × VERIFIED (dokumenty), 15 × VERIFIED_WIZJA, 26 × NOT_FOUND,
0 × TO_VERIFY**.

## Zdjęcia (zadanie 1) — metodologia

- **Zakazane źródła Google (Maps/Street View/Earth/3D Tiles) nie były używane.**
- Źródła kadrów: **KartaView** (licencja CC BY-SA 4.0 — dla gry komercyjnej: referencja,
  nie tekstura; azymut/heading z API). Dodatkowo w kaflu są dostępne kadry **Panoramax**
  (CC BY-SA 4.0, azymut w `view:azimuth` — 23 kadrów; lista w `sources.md`), **Mapillary —
  pominięty: brak tokenu (UNVERIFIED, nie zgadywano kluczy)**. Wikimedia Commons/Openverse w
  tym kaflu nie mają kadrów z poziomu jezdni (weryfikacja 2026-11-13).
- Kadr zrzutowany z poziomu jezdni (trasy KartaView biegną jezdnią; kamery samochodowe,
  wysokość ~1,3–1,5 m — nie z chodnika).
- JPG w archiwum ≤ 1600 px (wariant `lth` z CDN KartaView).
- Zdjęcia **nie trafiają do gita** (`files/` w `.gitignore`); archiwum
  `mistral-p9-furniture-3-files-v2.zip` (kadry + skany dokumentów) — karta pobrania
  (artefakt) podlinkowana w PR i w `sources.md` (SHA-256).

### Pokrycie typów (zdjęcia) — stan po pass C (errata s17), 2026-11-13
Kryteria FIX dla „potwierdzonego kadru”: odchyłka azymutu do obiektu od osi kamery ≤ 30°,
odległość ≤ 25 m, obiekt zakotwiczony w node/way OSM (kotwica wskazana w uwagach manifestu).
W pass C sprawdzono geometrycznie **917 kadrów** (7 sekwencji KartaView w kaflu+margines, w tym nowo
odkryta sekwencja 25209 — Andersa) × 170 węzłów OSM 9 typów + 23 kadry Panoramax (view:azimuth).

| Typ | Kadry potwierdzające (kotwica OSM: odchyłka / odległość) | Kadry negatywne (uczciwie) | Werdykt |
|---|---|---|---|
| sygnalizator | M50-004 (node 2629251364, 15°/0,6 m), M50-052 (3890183128, 2°/10,8 m), M50-053 (9224916290, 4°/19,1 m), M50-006 (3136871040, 11°/8,2 m), M50-054 Panoramax (2629251388, 23°/12,0 m) — 7 × VERIFIED_WIZJA | M50-055 (sygnalizatory widoczne, kotwica 9,1 m ZA kamerą — 152°) | **≥ 2 kadry z kotwicą** ✓ |
| latarnia | M50-001 (12625592983, 24°/13,9 m), M50-056 (12073055699, 15°/10,3 m), M50-057 (9845363978, 17°/17,4 m), M50-058 (12625592998, 14°/14,2 m, kadr nocny — świecąca oprawa), M50-066 (12625592983, 18°/19,5 m) | M50-002 (latarnie widoczne ~100–150 m, kotwica 43 m/41° — poza kryterium), M50-003 | **≥ 2 kadry z kotwicą** ✓ |
| hydrant nadziemny | M50-050 (12752227206, 28°/23,2 m) — potwierdzony też przez s17 | M50-051 (geometria OK: 21°/14 m, ale hydrantu NIE widać w kadrze — pass C), M50-013/014/015, Panoramax 6ded8ec0 (M50-065: 13,7 m ale 102° od view:azimuth) | **1 kadr z kotwicą** — drugi kandydat geometryczny negatywny (uczciwie odnotowany) |
| bariera U-12/U-12b | M50-008 (VERIFIED_WIZJA pass C: stalowa odbojnica w-beam na słupkach, 5–10 m po lewej; **bez kotwicy OSM** — bariery U-12 niemapowane w kaflu; follow-up rozróżnił od ekranu akustycznego i ogrodzenia) | M50-007 (sygnalizatory + płot posesji), M50-059/060 (errata s17: prywatne ogrodzenie prętowe posesji) | **1 kadr wizyjny** — brak kotwic OSM dla barier drogowych w kaflu |
| ławka | — | M50-017 (errata s17: wiatą/pawilon przy BP — model wskazał siedzisko, ale wg erraty to nie samodzielna ławka), M50-018, M50-063 | **0 kadrów** — najbliższy node bench 30,6 m; typ udokumentowany BIP Glasdon (M50-044/046, VERIFIED) |
| kosz | — | M50-019/020 | **0 kadrów** — najbliższy node waste_basket 28,7 m; typ udokumentowany BIP Glasdon (VERIFIED) |
| stojak rowerowy | — | M50-021/022, M50-062 (stojaki 19 m, ale odchyłka ~135° — poza FOV) | **0 kadrów** — geometria nie pozwala; typ udokumentowany OPZ ZMK (M50-025/026, VERIFIED) |
| osłona drzewa | — | M50-023/024 (kadr nocny), M50-064 | **0 kadrów** — brak węzłów tree guard w OSM w kaflu; model wskazywał „kratki wokół pnia” na 3 kadrach Panoramax, ale bez kotwic OSM — uczciwie tylko odnotowane |
| słupek U-5a | — | M50-009/010; na M50-056/057 widoczne biało-czerwone słupki (~10–15 m; wskazówka s17) — **bez kotwicy OSM** (barrier=bollard najbliżej 87 m), typ UNVERIFIED | **0 kadrów z kotwicą** — typ udokumentowany Dz.U. (M50-040, VERIFIED) |
| żerdź energetyczna | — | M50-011 (słup w oddali ~100–150 m — bez potwierdzenia; węzeł power=pole najbliżej 377 m), M50-012 | **0 kadrów** — typ udokumentowany kartami producenta (M50-047/048, VERIFIED) |
| szafka gazowa/telekom | — | M50-016, M50-061 (węzeł 22 m, odchyłka 80°) | **0 kadrów** — żadna para kadr–węzeł nie spełnia kryteriów; typ wymiarowo wg STO ZDM (M50-032) |

Uczciwe podsumowanie pass C: **2 typy mają ≥ 2 kadry z kotwicą geometryczną** (sygnalizator — 7,
latarnia — 5 z kotwicą + 1 wizyjna daleka), **hydrant i bariera U-12 mają po 1 kadrze** (kandydat
na drugi hydrant okazał się negatywny wizyjnie; bariery U-12 nie są mapowane w OSM). Dla **ławy,
kosza, stojaka, osłony drzewa, słupka U-5a, żerdzi i szafki żadna para kadr–węzeł OSM w kaflu
nie spełnia kryteriów ≤ 30°/≤ 25 m** (917 kadrów KartaView + 23 Panoramax przeliczone geometrycznie;
minimalne odległości/odchyłki w tabeli i uwagach manifestu) — typy te są udokumentowane wierszami
dokumentowymi (VERIFIED: Dz.U. 2311, OPZ ZMK, BIP Glasdon, karty Solbet/Gislebork) i uczciwymi
kadrami negatywnymi NOT_FOUND. Nie podano żadnego fałszywego potwierdzenia. Panoramax: wszystkie
23 kadry w kaflu obejrzane w pass C (potwierdzenia M50-054; poza osią: M50-055/065; w pozostałych
latarnie/sygnalizatory poza kryteriami azymut/dystans, rzekome bariery U-12 na 07820d85 to ekran
akustyczny — follow-up); Mapillary pominięty (brak tokenu).

## Dokumenty (zadania 2–5) — kluczowe fakty

### OPZ ZMK Białystok DZ.26.2.8.2026.JO — stojaki rowerowe (M50-025/026)
Skan 1-stronicowy (PDF 331 KB, w archiwum). **Odczyt wizyjny skanu s. 1 (2026-11-13) —
VERIFIED:** stojak **U 80x80 ze stali nierdzewnej**, wys. całk. **110 cm w wersji do
zabetonowania (80 cm nad gruntem)**, szer. **80 cm**, rura **48,3 mm**, grubość ścianki
**2 mm**, **2 stanowiska** (parkowanie dwustronne), montaż: **wbetonowanie**, **54 szt.**
(lokalizacje: Barszczańska/Klepacka/Fabryczna); nagłówek strony: „Załącznik nr 1".

### STO ZDM Warszawa TOS_1 — słupy oświetleniowe (M50-027…030)
Wersja obowiązująca v09/2024 to skan 12 stron (bez warstwy tekstowej; wydruk „Strona X z 12";
plik w archiwum). **Próba odczytu numeracji stron skanu (2026-11-13, wizja — kompozyt stopek
12 stron + strona 7 osobno): stopki skanu nie zawierają numerów „Strona X z 12", a str. 7
bez sekcji o słupach — numeracja skanu NIECZYTELNA/NIEOBECNA.** Dlatego wymogi cytowane są z
warstwy tekstowej DOCX v03/2020 (sekcja „Wymagania stawiane słupom i masztom
oświetleniowym", akapity 91–100 pliku) i potwierdza: stal obustronnie ocynkowana, przekrój
okrągły, ścianka min. 4 mm; słupy aluminiowe anodowane z warstwą elastomeru; „antyplakat"
do 2,0 m przy przystankach/przejściach; fundamenty prefabrykowane; uchwyt Zhaga Ø wewn.
60–72 mm, pochylenie ±10°. **STO nie specyfikuje wysokości słupów (8/10 m) — tylko wymagania
materiałowo-konstrukcyjne.**

### Dz.U. 2019 poz. 2311 — sygnalizatory i urządzenia (M50-031…040)
Ekstrakcja tekstu własnym parserem PDF (Python; Obsługiwane ObjStm/ToUnicode/TJ) z części 2
dziennika (s. 526–906; część 1 zawiera wyłącznie zał. 1 — znaki). **Rozbieżność z zadaniem:**
polecenie wskazywało „zał. 4, rysunek s. 370" — w rzeczywistej paginacji sygnalizatory są w
**zał. 3 (s. 691–807)**, rysunek 7.2.1 „Zasady umieszczania sygnalizatorów w stosunku do
poszczególnych elementów drogi" jest na **s. 756**; zał. 4 (urządzenia) zaczyna się na s. 806.
W manifeście podano rzeczywiste strony.

Fakty (VERIFIED, z warstwy tekstowej):
- sygnalizatory dodatkowe nad jezdnią **4,5–5,5 m** (s. 754); tabela 7.2 (s. 757): nad jezdnią
  4,5 m → LZW 8,0/12,5/25,0 m; 5,5 m → LZW 10,5/15,0/30,0 m; obok jezdni LZW
  2,0(0,5)/2,0/4,0(9,0) m;
- pomocnicze obok jezdni **0,8–1,5 m** (s. 759), dla pieszych **1,5–1,7 m** (s. 760);
- sygnały dźwiękowe ≥ **2,20 m** (s. 714); ekrany 850/650/520 mm przy soczewkach 300/200 mm
  (s. 716);
- U-5a: wys. **0,90–1,20 m**, szer. przy wierzchołku **0,20–0,30 m**, barwa żółta + pasy
  żółtej folii odblaskowej (s. 827–828);
- U-12a segmentowe: wys. **0,80–1,20 m** (s. 843); U-12b łańcuchowe: wys. **1,10 m**,
  rozstaw słupków **1,5/2,0 m**, strzałka ugięcia łańcucha ≤ 0,10 m (s. 843); U-12c słupki
  blokujące: **0,6–0,8 m** (s. 847).

Rys. 7.2.1 (s. 756) złożony z 3 pasów rastra (2129×422 każdy) do pojedynczego PNG
(`files/docs/du_p756_rys721.png`) — **odczyt wizyjny 2026-11-13 (M50-039, VERIFIED)**:
wysokości montażu nad jezdnią 4,5–5,5 m — zgodne z warstwą tekstową (s. 754); wartości
skrajni odczytane z rysunku (pion. 2,2–2,7 m, poziom. 0,5–2,0 m) pozostają **UNVERIFIED**
(liczby występują wyłącznie w grafice, nie w tekście — nie zgadujemy). Plik Dz.U. cz. 2
ma 41 MB — **nie jest w archiwum**, tylko link w `sources.md`.

### Glasdon Europe AB — Białystok 2019 (M50-041…046)
Zamówienie **DGK-IV.271.58.2019** „Dostawa wandaloodpornych ławek i koszy na śmieci"
(UM Białystok, Departament Gospodarki Komunalnej): wykonawca **Glasdon Europe AB** (August
Barks Gata 25, SE-421 32 Västra Frölunda, Szwecja), cena brutto **17 146,20 zł**, jedyna
oferta (art. 4 pkt 8 PZP). Dostawa: **4 ławki + 3 kosze**, montaż na zieleńcu przy pomniku
ks. Popiełuszki (aktualizacja miejska 30.07.2019); wcześniejsze zamówienie 2018:
10 ławek + 5 koszy na Skwerze Armii Krajowej (DGK-IV.271.76.2018).

**Odczyty wizyjne 2026-11-13 (VERIFIED):**
- **Zawiadomienie o wyborze** (skan 240 KB w archiwum, wyekstrahowany z PDF obj. 23):
  wykonawca **Glasdon Europe AB**, cena **17 146,20 zł brutto**, **Białystok, 26.06.2019**,
  nr **DGK-IV.271.58.2019**, przedmiot „Dostawa wandaloodpornych ławek i koszy na śmieci"
  (cena przekracza kwotę przeznaczoną 17 145,40 zł — tryb poza konkurencyjny).
- **Zał. nr 1 „Przykładowy wygląd"** (skan-obraz): ławka — proste siedzisko i oparcie z
  listew drewnopodobnych (wg BIP: materiał z recyklingu), nogi/podparcia boczne **odlewane
  stalowe czarne z elementami ozdobnymi**; kosz — **walec metalowy czarny**, okrągły otwór
  wrzutowy, mocowany do podłoża; na koszu emblematy (orzeł biały na czerwonym polu + herb
  żółto-czerwony). **Brak oznaczeń modelu i wymiarów na wzorze** — identyfikacja konkretnego
  modelu Glasdon **UNVERIFIED** (nie zgadujemy; karty produktów bez pobierania plików nie
  pozwoliły na jednoznaczne dopasowanie). Zdjęcia z załącznika — referencja, nie tekstura.

### Latarnie — Białystok (M50-031/032, kolumna latarnia: M50-027…030)
- Projekt „Rozbudowa Al. Tysiąclecia PP od ul. Wileńskiej do terenu kolejowego przy ul.
  Poleskiej" (ARKAS-PROJEKT, umowa ZDI-III.272.32.2015 z 15.07.2015, opis techniczny zał. 9
  BIP, rozdz. 3.11, s. 19): oświetlenie z **opraw sodowych na podatnych słupach
  aluminiowych**, zasilanych z szafki na rogu 1000-lecia/Kombatantów; szczegóły w tomie 1.2.5,
  który nie jest opublikowany w BIP.
- Warunki techniczne ZDM Białystok (boilerplate projektowy, np. ZDM-VII.7021.1.10.2018):
  normy PKN-CEN/TR 13201, N SEP-003/004; oprawy IP66, korpus z aluminium odlewanego
  ciśnieniowo, klosz płaski szklany, certyfikaty ENEC+CE; nowa linia kablowa nN 0,4 kV.
- **Wysokości słupów (wys. słupa/wysięgnik/rozstaw) dla Andersa, Al. Tysiąclecia i Sokólskiej
  pozostają UNVERIFIED** — w dostępnych dokumentach BIP (opisy PAB, warunki ZDM, SIWZ) brak
  liczb; tom branżowy 1.2.5 niedostępny online. Nie zgadywano typowych wartości.

### Żerdź wirowana E-12 — potwierdzenie u innego producenta niż ZPUE (M50-047/048)
Karta **Solbet Kolbuszowa S.A.** (typoszereg 9–15 m; fakty z odczytu karty, plik niepobrany):
dla długości 12,0 m — E 12/2,5…E 12/25; **D (średnica zewn. podstawy) 353–443 mm**, **d
(średnica zewn. wierzchołka) 173–263 mm** zależnie od siły wierzchołkowej; np. E 12/6:
D=398, d=218, L1=2,2 m; E 12/12: D=398, d=218, masa transp. 2050 kg, 12 kN; beton C40/50,
PN-EN 12843. Potwierdzenie krzyżowe: karta dystrybutora Gislebork (te same D/d dla E 12/x;
aprobata ITB AT-15-3690/99, AT-15-5989/2003) oraz sklep Elektriko (E12/12, kod 107560,
„wysokość słupa: 12 m łącznie", wytwórca Strunobet-Migacz). Zgodne z kartą ZPUE z badań
poprzednich (P9-023) — niezależne potwierdzenie.

## Samokontrola 20 % — `audit_20_percent.json`
Jawny seed: **2026111361** (nowy, po pass C — 20 % z 66 pozycji). Deterministyczny wybór
(`random.Random(2026111361).sample` na 66 wierszach; próba = 13), dla każdej sprawdzonej pozycji:
obecność źródła (URL), licencja, status ze słownika, format WGS84 i komplet pól foto
(sezon/pora_dnia) dla wierszy zdjęciowych, numer strony dla wierszy dokumentowych; dla
wierszy wizyjnych przywołany cytat „co widać” z uwag **porównany z kolumną obiekt i statusem**
(VERIFIED_WIZJA ⇒ obiekt widoczny; NOT_FOUND ⇒ „NIE widać”), dla dokumentowych — cytat źródłowy.
Próba celnie objęła wiersze erraty (M50-017/059/060), nowy M50-066 i negatywy. Wynik w pliku.

## Pliki i archiwum
- `files/` (ignorowane przez git w tym katalogu): kadry JPG (wariant lth ≤ 1600 px) +
  `files/docs/` (dokumenty źródłowe odczytów: OPZ ZMK 331 KB, STO ZDM v09 1,1 MB,
  STO v03 DOCX, warunki oświetleniowe ZDM 2025 2 MB, zawiadomienie Glasdon 240 KB,
  ogłoszenie 1,6 MB, zał. 1 wzoru ławki/kosza 1,5 MB).
- `mistral-p9-furniture-3-files-v2.zip` — **v2 (przebudowane po pass C)**: WSZYSTKIE kadry
  z manifestu (66 wierszy = 41 kadrów foto: M50-001…024 + M50-050…066; Panoramax przez wsrv.nl
  ≤ 1600 px) + `files/docs/` (7 dokumentów źródłowych); artefakt do pobrania (SHA-256 w
  `sources.md`); Dz.U. cz. 2 (41 MB) i opis PAB (11,7 MB) celowo **poza archiwum** — tylko linki.
- Nie zmieniono niczego poza `research/mistral/p9-furniture-3/`.

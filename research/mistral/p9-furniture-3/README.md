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

`manifest.csv` — id `M50-001…M50-049`; kolumny zgodne z zadaniem:
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
- `UNVERIFIED` / `ESTIMATED` — brak źródła liczbowego; w uwagach metoda/oszacowanie.

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
  `mistral-p9-furniture-3-files.zip` (kadry + skany dokumentów ≤ 5 MB) — karta pobrania
  (artefakt) podlinkowana w PR i w `sources.md` (SHA-256).

### Pokrycie typów (zdjęcia)
| Typ | Kadry (id KartaView) | Status |
|---|---|---|
| ławka | 1326673717, 219382277 (przystanki BKM) | TO_VERIFY |
| kosz | 993065622, 219382231 (przystanki BKM) | TO_VERIFY |
| stojak rowerowy | najbliższe kadry do OSM amenity=bicycle_parking | TO_VERIFY |
| osłona drzewa | 219382233 (23 m), 1326673433 (75 m) do natural=tree | TO_VERIFY |
| bariera U-12/U-12b | 993066622 (panele — wizja), 993066706 | VERIFIED_WIZJA / TO_VERIFY |
| słupek U-5a | 219381941 (wizja), 219382163 (pylon) | VERIFIED_WIZJA / TO_VERIFY |
| sygnalizator na maszcie | 5062571, 219381879, 993066622 | VERIFIED_WIZJA |
| latarnia | 1326673445, 993040942, 219382073 | VERIFIED_WIZJA |
| żerdź energetyczna | 1326673805 (wizja: słup betonowy/żerdź), 1326673801 | VERIFIED_WIZJA / TO_VERIFY |
| hydrant nadziemny | 5062587, 1326673829, 1326673477 | VERIFIED_WIZJA |
| szafka gazowa/telekom | 219382225 (szafka ~35 m od kamery) | VERIFIED_WIZJA |

Uczciwe zastrzeżenie: w klastrze Andersa-północ analizą wizyjną poprzednich tur **nie
potwierdzono** ławek/koszy/stojaków w FOV (obiekty stoją poza kadrem) — dlatego te typy mają
kadry kandydackie przy przystankach (wiaty BKM) ze statusem TO_VERIFY. Świadomie nie
podano fałszywych potwierdzeń.

## Dokumenty (zadania 2–5) — kluczowe fakty

### OPZ ZMK Białystok DZ.26.2.8.2026.JO — stojaki rowerowe (M50-025/026)
Skan 1-stronicowy (PDF 331 KB, w archiwum). Wymiary wg OCR indeksu wyszukiwarki (status
TO_VERIFY do czasu odczytu wizyjnego s. 1): stojak U 80x80, stal nierdzewna, wys. całk.
1,10 m (0,80 m nad gruntem), szer. 0,80 m, rura 48,3×2 mm, 2 stanowiska, wbetonowanie,
54 szt. (Barszczańska/Klepacka/Fabryczna).

### STO ZDM Warszawa TOS_1 — słupy oświetleniowe (M50-027…030)
Wersja obowiązująca v09/2024 to skan 12 stron (bez warstwy tekstowej; wydruk „Strona X z 12";
plik w archiwum — numery stron skanu do odczytu wizyjnego). Wersja v03/2020 (DOCX, tekst —
URL w `sources.md`) potwierdza wymagania: stal obustronnie ocynkowana, przekrój okrągły,
ścianka min. 4 mm; słupy aluminiowe anodowane z warstwą elastomeru; „antyplakat" do 2,0 m
przy przystankach/przejściach; fundamenty prefabrykowane; uchwyt Zhaga Ø wewn. 60–72 mm,
pochylenie ±10°. **STO nie specyfikuje wysokości słupów (8/10 m) — tylko wymagania
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
(`files/docs/du_p756_rys721.png`) — odczyt wizyjny wymiarów z rysunku: w toku (M50-036,
TO_VERIFY). Plik Dz.U. cz. 2 ma 41 MB — **nie jest w archiwum**, tylko link w `sources.md`.

### Glasdon Europe AB — Białystok 2019 (M50-041…043)
Zamówienie **DGK-IV.271.58.2019** „Dostawa wandaloodpornych ławek i koszy na śmieci"
(UM Białystok, Departament Gospodarki Komunalnej): wykonawca **Glasdon Europe AB** (August
Barks Gata 25, SE-421 32 Västra Frölunda, Szwecja), cena brutto **17 146,20 zł**, jedyna
oferta (art. 4 pkt 8 PZP). Dostawa: **4 ławki + 3 kosze**, montaż na zieleńcu przy pomniku
ks. Popiełuszki (aktualizacja miejska 30.07.2019); wcześniejsze zamówienie 2018:
10 ławek + 5 koszy na Skwerze Armii Krajowej (DGK-IV.271.76.2018). Modele ławki/kosza nie
są nazwane w tekście BIP — zał. nr 1 („przykładowy wygląd") to skan-obraz; identyfikacja
modelu (porównanie z kartami Glasdon, np. rodzina Nexus) i wymiary z karty produktu —
**tylko fakty, bez pobierania plików** — oznaczone TO_VERIFY do porównania wizyjnego.
Zawiadomienie o wyborze (skan, 240 KB) w archiwum.

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
Jawny seed: **20261113**. Deterministyczny wybór 20 % pozycji manifestu (sortowanie po id,
`random.Random(20261113).sample`), dla każdej sprawdzone: obecność źródła (URL), licencja,
status ze słownika, format WGS84 (6 miejsc) i komplet pól foto (sezon/pora_dnia) dla wierszy
zdjęciowych, numer strony dla wierszy dokumentowych. Wynik w pliku.

## Pliki i archiwum
- `files/` (ignorowane przez git w tym katalogu): kadry JPG (wariant lth ≤ 1600 px) +
  `files/docs/` (skany urzędowe ≤ 5 MB: OPZ ZMK 331 KB, STO v09 1,1 MB, STO v07, warunki ZDM
  2,0 MB, zawiadomienie Glasdon 240 KB, PNG rys. 7.2.1).
- `mistral-p9-furniture-3-files.zip` — artefakt do pobrania (SHA-256 w `sources.md`); Dz.U.
  cz. 2 (41 MB) i opis PAB (11,7 MB) celowo **poza archiwum** — tylko linki.
- Nie zmieniono niczego poza `research/mistral/p9-furniture-3/`.

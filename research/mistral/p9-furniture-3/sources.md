# M50 (p9-furniture-3) — źródła

Wszystkie URL-e zweryfikowane 2026-11-13. Licencje komercyjne dopuszczalne; NC/ND oznaczone
„tylko referencja, nie pobrano"; CC BY-SA — „referencja, nie tekstura" (Kamion nie może
używać ich jako tekstur bez zgodnej licencji). Karty producentów: tylko fakty z odczytu,
pliki niepobrane.

## Archiwum plików (zdjęcia + skany)

- `mistral-p9-furniture-3-files-v2.zip` (14,1 MB — przebudowane po pass C, errata s17) — karta pobrania (artefakt) podlinkowana w PR.
- SHA-256: `9a748ceb5370ba0cc3b7c7261acc2d958fe34ca9c478e81277f6ceb29ef78942`
- Zawartość v2 (pełna, po pass C):
  - `files/frames/` — **wszystkie 41 kadrów** wskazanych w manifest.csv (M50-001…024 +
    M50-050…066, w tym nowy wiersz M50-066 — latarnia, kadr 993028082), jeden plik na wiersz,
    nazwa = id wiersza. Kadry KartaView: wariant lth, 1280×720 (≤ 1600 px); kadry Panoramax
    (M50-054/055/065): oryginały 2560×1920 przeskalowane do szer. 1600 px przez
    `https://wsrv.nl/?url=…&w=1600&output=jpg&q=85`.
    Poprawki względem v1: dodany kadr M50-017 (foto 1326673717), brakujący w v1, oraz 16 kadrów
    nowych wierszy M50-050…065 (pass B) i kadr M50-066 (pass C).
  - `files/docs/` — 7 dokumentów źródłowych (PDF/DOCX): OPZ ZMK (331 KB), STO ZDM TOS_1
    v09/2024 (1,1 MB), STO v03/2020 DOCX, warunki oświetleniowe ZDM Białystok 2025 (2 MB),
    zawiadomienie o wyborze oferty Glasdon (240 KB), ogłoszenie o zamówieniu (1,6 MB),
    zał. nr 1 — wzór ławki i kosza (1,5 MB).
- Celowo poza archiwum (tylko linki poniżej): Dz.U. 2019 poz. 2311 cz. 2 (41 MB),
  Dz.U. cz. 1 (39,7 MB), opis PAB Al. Tysiąclecia (11,7 MB).
- v1 (`mistral-p9-furniture-3-files.zip`, SHA-256
  `1b4e23a359c9dbd00bd5c3bc5249d6ecf99018592febda6f82eb0bff2f4c4b1c`) — zastąpiona
  przez v2 (v1 nie zawierała kadru M50-017 i nie obejmowała wierszy M50-050…065).
- v2 poprzednie (SHA-256 `93075520d5d162b49a4455b354c58ff7d3d04cf21f96a25d8e01a64dde23a0ea`,
  10,9 MB, 40 kadrów) — zastąpione przez v2 po pass C (dodano kadr M50-066; przebudowane archiwum).

## Zadanie 1 — zdjęcia

- KartaView (OpenStreetCam) — licencja **CC BY-SA 4.0** (referencja, nie tekstura):
  - API: `https://api.openstreetcam.org/2.0/photo/?lat1=53.143&lng1=23.147&lat2=53.161&lng2=23.183&page=1&itemsPerPage=150`
  - Sekwencje w kaflu+marginesie (pass C, komplet 917 kadrów z 7 sekwencji): 10733, 1155711,
    14055, **25209** (nowo odkryta w pass C — trasa Andersą, 52 kadry w kaflu; paginacja
    `/2.0/photo/?sequenceId=25209&itemsPerPage=150`, kadr w kaflu id 51415632 na str. 218;
    kamera skierowana na północ przy jeździe na południe — brak nowych kandydatów ≤30°/≤25 m),
    2763230, 2769366, 3686129; odkrywanie siatką radius 500 m (`/2.0/photo/?lat=..&lng=..&radius=500&zoomLevel=15&itemsPerPage=150`).
  - Kadry w manifeście: URL-e CDN `https://cdn.kartaview.org/pr:sharp/...` (wariant lth,
    1280×720), pozycje/heading z API.
- Panoramax — **CC BY-SA 4.0** (referencja, nie tekstura); 23 kadrów w kaflu (wszystkie
  NW narożnik, ok. 53,159°N/23,148–23,152°E, zdjęcia z auta Nexus S 2019-08-15 i
  2019-09-01), azymut w `view:azimuth`:
  - API: `https://api.panoramax.xyz/api/search?bbox=23.147,53.143,23.183,53.161`
  - Kolekcje w kaflu (m.in. `b3131ba1-86e3-4528-a0ff-a754528bba5b`).
  - Pełna lista 23 kadrów (id 8 znaków | view:azimuth | lat | lon | data):
    `3eba62ce|65|53.1588361|23.1519614|2019-08-15`,
    `07820d85|53|53.1590657|23.1519814|2019-08-15`,
    `6fc62548|100|53.1587146|23.1517760|2019-08-15`,
    `6ded8ec0|56|53.1594129|23.1518848|2019-08-15`,
    `35224dcb|121|53.1588664|23.1514397|2019-08-15`,
    `a228a704|59|53.1599485|23.1518258|2019-08-15`,
    `3717771d|242|53.1596776|23.1514525|2019-09-01`,
    `9ff60a64|54|53.1604169|23.1518905|2019-08-15`,
    `386598e7|204|53.1599671|23.1515819|2019-09-01`,
    `8176a172|194|53.1604626|23.1517099|2019-09-01`,
    `239c71e8|268|53.1595055|23.1511271|2019-09-01`,
    `7196532e|54|53.1609152|23.1519778|2019-08-15`,
    `844e35c7|113|53.1590866|23.1508602|2019-08-15`,
    `02830ea2|191|53.1608591|23.1517886|2019-09-01`,
    `f16bbe61|274|53.1594970|23.1506714|2019-09-01`,
    `03ec4841|101|53.1592532|23.1499917|2019-08-15`,
    `9cf05b43|275|53.1595590|23.1498171|2019-09-01`,
    `9f85aac8|98|53.1593321|23.1492930|2019-08-15`,
    `8ccad44c|273|53.1596409|23.1489894|2019-09-01`,
    `6248550a|105|53.1594072|23.1486052|2019-08-15`,
    `e84d565e|270|53.1596952|23.1480806|2019-09-01`,
    `b27d2652|107|53.1594763|23.1478377|2019-08-15`,
    `b0419ba6|269|53.1596978|23.1471538|2019-09-01`.
  - Weryfikacja wizyjna pass C (2026-11-13, **wszystkie 23 kadry** obejrzane — 1 kadr =
    1 wywołanie, dziennik w `vision_run.json`): `3717771d` → sygnalizator na wysięgniku
    nad jezdnią, prawo 10-15 m — VERIFIED_WIZJA (M50-054, kotwica node 2629251388,
    12,0 m/23° — spełnia kryteria FIX); `35224dcb` → sygnalizatory widoczne (M50-055,
    kotwica 9,1 m ZA kamerą — 152°, poza kryterium); `6ded8ec0` → hydrantu brak
    (M50-065, NOT_FOUND; węzeł 13,7 m, azymut 102° od view:azimuth). Pozostałe 20 kadrów:
    latarnie i sygnalizatory widoczne w większości kadrów (wzdłuż Andersa), ale żadna
    para kadr–węzeł poza M50-054 nie spełnia kryteriów ≤30°/≤25 m; rzekome bariery U-12
    (07820d85 i ~15 kadrów wzdłuż jezdni) — po follow-upie 07820d85: EKRAN AKUSTYCZNY
    (transparentny, 3-4 m; w OSM przy pozycjach barrier=wall wall=noise_barrier), nie
    odbojnica; rzekome osłony drzew (9ff60a64/02830ea2/8ccad44c) i żerdzie — bez kotwic
    OSM (tree_guard/power=pole poza kryteriami). Wyniki: 0 nowych wierszy z Panoramax.
- Mapillary — **pominięty: brak tokenu API (UNVERIFIED)**; nie użyto cudzych kluczy.
- Wikimedia Commons / Openverse — brak kadrów z poziomu jezdni w kaflu (weryfikacja
  2026-11-13, wyszukiwanie geo „Białystok Andersa/Tysiąclecia/Sokólska/Wileńska").
- Google Maps/Street View/Earth — **nie używane** (zakaz z zadania).
- OSM (OpenStreetMap, ODbL) — geometrie obiektów (bench/bike/lamp/signal/hydrant/bollard/
  cabinet/tree) do kotwiczenia azymutu/odległości: `https://www.openstreetmap.org`
  (ekstrakcja Overpass API, snapshot w metadanych badania).

## Zadanie 2 — dokumenty (odczyty)

1. **OPZ ZMK Białystok DZ.26.2.8.2026.JO** (stojaki rowerowe, s. 1):
   - strona postępowania BIP ZMK: [https://bip.zmk.bialystok.pl/zamowienia/dostawa-i-montaz-nowych-stojakow-rowerowych-na-terenie-miasta-bialystok-.html](https://bip.zmk.bialystok.pl/) — pozycja BIP: [BIP ZMK — stojaki rowerowe](search-result://Hq9imPW6)
   - PDF OPZ (331 KB, skan): [zał. nr 3 — OPZ DZ.26.2.8.2026.JO.pdf](https://bip.zmk.bialystok.pl/resource/209/575/za%C5%82.+nr+3+-+OPZ+DZ.26.2.8.2026.JO.pdf) — wynik wyszukiwania: [OPZ PDF](search-result://QvK6LSoP)
2. **STO ZDM Warszawa TOS_1** (słupy oświetleniowe):
   - v09/02.2024 (obowiązująca; skan 12 stron): [STO_ZDM_TOS_1-wersja-09-2024.pdf](https://zdm.waw.pl/wp-content/uploads/2018/04/STO_ZDM_TOS_1-wersja-09-2024.pdf) — wynik: [STO v09](search-result://D8kgiXza)
   - v03/2020 (DOCX z warstwą tekstową): [Specyfikacja-STO_ZDM_TOS_1_2020-v03-1.docx](https://zdm.waw.pl/wp-content/uploads/2020/10/Specyfikacja-STO_ZDM_TOS_1_2020-v03-1.docx) — wynik: [STO v03 DOCX](search-result://aaHaM3Ja)
3. **Dz.U. 2019 poz. 2311** (Załącznik do obwieszczenia MSWiA — znaki i sygnały drogowe):
   - część 2 (zał. 2–4, s. 526–906; sygnalizatory zał. 3 s. 691–807, urządzenia zał. 4 od s. 806):
     [D2019000231102.pdf](https://www.dziennikustaw.gov.pl/D2019000231102.pdf)
   - część 1 (zał. 1, s. 1–525): [DU/2019/2311/text.pdf](https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text.pdf)
   - Ekstrakcja tekstu: własny parser PDF w Pythonie (ObjStm/ToUnicode/TJ; skrypt
     `extract_pdf.py` opisany w README).

## Zadanie 3 — Glasdon Europe AB (Białystok 2019)

- Strona postępowania BIP UM Białystok (wykonawca, cena 17 146,20 zł):
  [Dostawa wandaloodpornych ławek i koszy na śmieci — DGK-IV.271.58.2019](https://www.bip.bialystok.pl/postepowania/zamowienia/dostawa-wandaloodpornych-lawek-i-koszy-na-smieci-1.html)
- Zawiadomienie o wyborze najkorzystniejszej oferty (skan, 240 KB; w archiwum):
  [Zawiadomienie-BIP.pdf](https://www.bip.bialystok.pl/resource/51035/Zawiadomienie+-BIP.pdf)
- Ogłoszenie o zamówieniu (skan, 1,6 MB; w archiwum):
  [Ogłoszenie o zamówieniu.pdf](https://www.bip.bialystok.pl/resource/50301/Og%C5%82oszenie+o+zam%C3%B3wieniu.pdf)
- Zał. nr 1 — przykładowy wygląd ławki i kosza (skan-obraz 1,5 MB; w archiwum; obrazy =
  referencja do identyfikacji modelu):
  [zał. nr 1 — wzór ławki i kosza.pdf](https://www.bip.bialystok.pl/resource/50301/za%C5%82.+nr+1-+wz%C3%B3r+%C5%82awki+i+kosza+na+%C5%9Bmieci.pdf)
- Aktualizacja miejska (4 ławki + 3 kosze, pomnik ks. Popiełuszki, 30.07.2019):
  [Nowoczesne ławki parkowe — bialystok.pl](https://www.bialystok.pl/pl/wiadomosci/aktualnosci/nowoczesne-lawki-parkowe.html)
- Relacja prasowa (2018: 10 ławek + 5 koszy, Skwer Armii Krajowej):
  [bialystokonline.pl](https://www.bialystokonline.pl/nowe-wandaloodporne-lawki-i-kosze-w-bialymstoku,artykul,113479,1,1.html)
- Karty produktów Glasdon (fakty; pliki niepobierane; do identyfikacji modelu):
  [Ławki plastikowe z recyklingu — Glasdon](https://www.glasdon.com/pl/siedziska/lawki-plastikowe-surowcow-wtornych),
  [Kosze na śmieci — Glasdon](https://www.glasdon.com/pl/kosze-na-smieci)

## Zadanie 4 — latarnie Białystok

- Projekt „Rozbudowa Al. Tysiąclecia PP w Białymstoku od ul. Wileńskiej do terenu
  kolejowego przy ul. Poleskiej wraz z infrastrukturą techniczną" (ARKAS-PROJEKT,
  umowa ZDI-III.272.32.2015 z 15.07.2015), opis techniczny, rozdz. 3.11 (s. 19):
  [Załącznik 9 — opis.pdf](https://www.bip.bialystok.pl/resource/26539/Za%C5%82%C4%85cznik+9+-+opis.pdf)
- Warunki techniczne ZDM Białystok dla projektowania oświetlenia (boilerplate):
  [WARUNKI TECHNICZNE — ZDM-VII.7021.1.10.2018](https://www.bip.bialystok.pl/resource/36929/WARUNKI+TECHNICZNE.pdf),
  [warunki oświetlenie ZDM — ZDM-VII.7021.1.16.2025 (skan, w archiwum)](https://www.bip.bialystok.pl/resource/99308/za%C5%82.+7+-+warunki+o%C5%9Bwietlenie+ZDM.pdf)
- Zamówienie „Budowa urządzeń oświetlenia ulicznego na terenie miasta Białegostoku
  w formule «zaprojektuj i wybuduj»" (ZDM-XIV.271.65.2022):
  [strona postępowania BIP](https://www.bip.bialystok.pl/postepowania/zamowienia/budowa-urzadzen-oswietlenia-ulicznego-na-terenie-miasta-bialegostoku-w-formule-zaprojektuj-i-wybuduj.html?PageSpeed=noscript)
- Modernizacja oświetlenia (tło):
  [bialystok.pl — Modernizacja oświetlenia ulicznego](https://www.bialystok.pl/pl/dla_mieszkancow/drogi_i_inwestycje/modernizacja-oswietlenia-ulicznego.html)

## Zadanie 5 — żerdź wirowana E-12 (producenci inni niż ZPUE)

- Karta Solbet Kolbuszowa S.A. (typoszereg E 9–15 m, tabela D/d/L/L1; **fakty, plik
  niepobrany**):
  [STRUNOBETONOWE WIROWANE ŻERDZIE ELEKTROENERGETYCZNE TYPU E](https://www.solbet-kolbuszowa.com.pl/wp-content/uploads/2017/12/fr_zerdzie_A4_2017-1.pdf)
- Karta dystrybutora Gislebork (weryfikacja krzyżowa; fakty, plik niepobrany):
  [ENERGETYCZNE STRUNOBETONOWE ŻERDZIE WIROWANE TYPU E](https://gislebork.pl/images/slupy-zerdzie-konstrukcje/wirbet_e.pdf)
- Sklep Elektriko (E12/12, kod 107560, „wysokość słupa: 12 m łącznie"):
  [Żerdź wirowana E12/12 — elektriko.pl](https://www.elektriko.pl/slupy-oswietleniowe/zerdz-wirowana-e/107560.html)
- Strunobet-Migacz (strona ofertowa producenta, 70+ pozycji E 9–18 m):
  [strunobet.pl — żerdzie wirowane typu E](https://www.strunobet.pl/oferta/zerdzie-wirowane-typu-e/)

## Wcześniejsze badania (niepowtarzane)

- `research/g5-street-furniture/README.md` i `research/gptpro/p9-street-furniture-2/README.md`
  + manifesty — lista pozycji sprawdzona pod kątem duplikatów; pozycja ZPUE (żerdź E-12,
  P9-023) tam zawarta jest tu tylko potwierdzona u innych producentów (zgodnie z zadaniem).

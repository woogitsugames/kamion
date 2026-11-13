# M50 (p9-furniture-3) — źródła

Wszystkie URL-e zweryfikowane 2026-11-13. Licencje komercyjne dopuszczalne; NC/ND oznaczone
„tylko referencja, nie pobrano"; CC BY-SA — „referencja, nie tekstura" (Kamion nie może
używać ich jako tekstur bez zgodnej licencji). Karty producentów: tylko fakty z odczytu,
pliki niepobrane.

## Archiwum plików (zdjęcia + skany)

- `mistral-p9-furniture-3-files.zip` — karta pobrania (artefakt) podlinkowana w PR.
- SHA-256: `cfc9c258b02f15296e4f88ce10e260930f2ef9629b879297607d0f396820670b`
- Zawartość: `files/frames/` (65 kadrów KartaView, wariant lth, 1280×720 ≤ 1600 px),
  `files/docs/` (skany urzędowe ≤ 5 MB).
- Celowo poza archiwum (tylko linki poniżej): Dz.U. 2019 poz. 2311 cz. 2 (41 MB),
  Dz.U. cz. 1 (39,7 MB), opis PAB Al. Tysiąclecia (11,7 MB).

## Zadanie 1 — zdjęcia

- KartaView (OpenStreetCam) — licencja **CC BY-SA 4.0** (referencja, nie tekstura):
  - API: `https://api.openstreetcam.org/2.0/photo/?lat1=53.143&lng1=23.147&lat2=53.161&lng2=23.183&page=1&itemsPerPage=150`
  - Kadry w manifeście: URL-e CDN `https://cdn.kartaview.org/pr:sharp/...` (wariant lth,
    1280×720), pozycje/heading z API.
- Panoramax — **CC BY-SA 4.0** (referencja, nie tekstura); 23 kadrów w kaflu, azymut w
  `view:azimuth`:
  - API: `https://api.panoramax.xyz/api/search?bbox=23.147,53.143,23.183,53.161`
  - Kolekcje w kaflu (m.in. `b3131ba1-86e3-4528-a0ff-a754528bba5b`).
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

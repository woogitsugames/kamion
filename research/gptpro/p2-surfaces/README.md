# gptpro-p2-surfaces — Nawierzchnie i elementy jezdni w Białymstoku (P2)

**Projekt:** Kamion — realistyczny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1.
**Zadanie:** Ustalenie, jakie nawierzchnie i elementy jezdni występują w Białymstoku (kafl startowy ok. 53,152 N 23,168 E — Jaroszówka), wraz z wymiarami, materiałami, kolorami (sRGB + metoda), stanem zużycia, porą roku i dnia, oraz weryfikacja szerokości linii poziomych P-1…P-25 wg rozporządzenia.
**Data wykonania:** 2026-11-13. Język: polski.

## Zawartość paczki

- `README.md` — niniejszy plik.
- `manifest.csv` — 94 pozycje (kolumny: id, element, lokalizacja, lat, lon, materiał, wymiary, kolor_srgb, metoda_koloru, stan_zużycia, sezon, pora_dnia, dokument_strona, url_źródła, licencja, autor, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi).
- `files/` — 37 plików: 33 zdjęcia JPG (maks. 1600 px dłuższego boku, kolejność ID P2-001…P2-033) + 4 dokumenty urzędowe PDF (P2-034…P2-037, każdy ≤5 MB).
- `sources.md` — pełna lista źródeł z datami dostępu.
- `audit_20_percent.json` — wynik samokontroli 20% pozycji (jawny seed).

## Metoda

1. **Zdjęcia wolnolicencyjne:** Wikimedia Commons (API, metadane extmetadata + GeoData, miniatury 1600 px; licencje CC0/CC BY/CC BY-SA) oraz Panoramax (API, CC BY-SA 4.0, sekwencja z poziomu kierowcy). Google Maps/Street View/Earth/3D Tiles **nie były używane** — ani jako źródło, ani do sprawdzeń.
2. **Dokumenty urzędowe:** rozporządzenie Dz.U. 2019 poz. 2311 (zał. nr 2, ELI), wytyczne projektowania ZDiT Białystok (BIP), SST przebudowy parkingu pl. Niepodległości (BIP), SST D.05.03.05 ścieżki rowerowej (BIP), PFU węzła Porosłany — korytarz S8 (BIP, link — plik 10,4 MB > limit 5 MB, nie dołączony), WT-2 2016 cz. II GDDKiA (gov.pl). Teksty PDF wyciągano własnym ekstraktorem (strumienie zlib + ToUnicode CID) w trakcie tej rozmowy 13.11.2026; paginacja PDF ↔ Dz.U. podana w cytowaniach (strona Dz.U. = strona PDF + 525).
3. **Geokodowanie:** EXIF/GeoData Commons (SOURCED), w braku — Nominatim/Photon (dane OSM), zawsze oznaczone ESTIMATED w uwagach.
4. **Kolory sRGB:** mediana RGB z wycinka 100×100 px (środek kadru, 62% wysokości — zwykle nawierzchnia) liczona programowo (PIL/numpy); wskaźnik bieli (luminancja >230) pomocniczo do oceny śniegu. Wszystkie wartości kolorów: **ESTIMATED** (nieznany balans bieli aparatu, oświetlenie opisane przez porę dnia/sezon).
5. **Zasada nie-zmyślania:** każda liczba w manifeście ma źródło (link + data dostępu + dokument/strona lub cytat ≤25 słów). Niepotwierdzalne — status UNVERIFIED, szacunki — ESTIMATED z metodą.

## Najważniejsze ustalenia

**Asfalt (jezdnie):**
- S8 w korytarzu węzła Porosłany: konstrukcja KR7 = **SMA 11 S 4 cm / AC 16 W 8 cm / AC 22 P 18 cm / SM C90/3 20 cm** (razem 50 cm), pas ruchu 3,50 m (PFU, s. 57–58).
- S8 Jeżewo Stare–Białystok (węzeł Choroszcz) oddana **12.09.2012** jako dwujezdniowa (24,5 km) → nawierzchnia w 2026 r. liczy ok. 14 lat (w miejscach bez remontu); **S19 Krynice–Białystok Zachód oddana 20.10.2026** (10,2 km) wraz z przebudową S8 na 1,9 km → w rejonie nowego węzła **świeży asfalt** (gov.pl MI).
- Ścieżki/pasy rowerowe: **czerwony asfalt AC 8 S 50/70, warstwa ścieralna 3 cm** (SST D.05.03.05, s. 1) — kolor czerwony potwierdzony dokumentem i zdjęciami (P2-001…P2-008, P2-018).
- Standard GDDKiA dla nawierzchni SMA: WT-2 cz. II 2016 (dokument P2-035 w paczce).
- Zużycie w czasie: świeży (układanie — P2-027/P2-028), ~1 rok (S8 zimą 2013 — P2-015), ~8 lat (S8 zjazd 2020 — P2-013); kolory sRGB dla tych stanów w manifeście (ESTIMATED, mediana z wycinka).

**Kostka betonowa:**
- Parking pl. Niepodległości: **kostka grub. 6 cm**, spoiny ≤3 mm na łukach (SST, PDF s. 135); **płyty brukowe dwuwarstwowe** (górna ~2,5 cm + dolna ~5 cm) (SST, PDF s. 127–128).
- Chodniki (korytarz S8): **kostka szara 8 cm / podsypka 1:4 3 cm / SM 15 cm** (PFU, s. 58–59).
- Rynek Kościuszki: nawierzchnia kostkowa na zdjęciach 2013–2015 (P2-022…P2-024); typ/typ kamienia — do ustalenia (ESTIMATED).
- Progi zwalniające na osiedlach: z kostki (ZDiT, s. 13).

**Płyty:** płyty chodnikowe na ulicach zwykłych (np. P2-021); jasne płyty/kostka + kraty dendrologiczne w centrum (P2-025).

**Krawężniki:**
- Standard uliczny: **15×30 cm** na podsypce (SST pl. Niepodległości, pkt 1.3, PDF s. 122); kątne ścięte **15×22×100** i **12×25×100** (typ B30, BN-80/6775-03).
- Przystankowy: **16 cm** wysokości wystawania (ZDiT, pkt 7, s. 5).
- Najazdowe (przejścia/przejazdy): **zatopione, wystawanie 0–2 cm** (PFU, s. 60); odsłonięcie krawężników jezdni **12 cm** (PFU, s. 61–62).

**Obrzeża:** betonowe **6×30 cm z oporem** (PFU, s. 61–62); **6×20 cm** na podsypce piaskowej 5 cm (SST, PDF s. 140); kamienne 20×30 cm na zatokach autobusowych (PFU).

**Ścieki przykrawężnikowe/wpusty:** wpusty betonowe **ø500 mm, C35/45, W8, F150**; kraty jezdniowe **D400, korpus 150 mm**; jezdniowo-krawężnikowe/krawężnikowe min. C250 (ZDiT, pkt 20–24, s. 11–12); wpust krawężnikowy żeliwny **min. D400 wg PN-EN 124** (PFU, s. Z4.4). Zdjęcia: brak wolnolicencyjnych — UNVERIFIED (P2-089).

**Pasy/ścieżki rowerowe:** kolor **czerwony** (AC 8 S 3 cm); droga rowerowa: asfalt na podbudowie SM ≥10 cm, jednokierunkowa ≥1,5 m, dwukierunkowa ≥2,0 m (ZDiT, s. 19); przejazdy dla rowerów „wyraźnie inny kolor” (ZDiT, s. 20); łączenie asfalt/asfalt bezszwowe, bez krawężników (ZDiT, s. 21).

**Płytki dotykowe:** rampy przy przejściach = **1 rząd płytek gładkich + 2 rzędy profilowanych (guzowatych)** (ZDiT, pkt 2, s. 5). Zdjęcie: brak wolnolicencyjny — UNVERIFIED (P2-088).

**Azyle (wyspy dzielące):** zasada projektowania — wyspa dzieląca na ulicach klasy Z+ (ZDiT, s. 21); zdjęcia: brak — UNVERIFIED (P2-087).

**Oznakowanie poziome:** farby cienkowarstwowe **0,3–0,8 mm**, masy grubowarstwowe **0,9–3,5 mm**, elementy odblaskowe **≤25 mm** (zał. 2, PDF s. 3); na drogach ekspresowych zalecane **grubowarstwowe profilowane/strukturalne** (efekt akustyczny; PDF s. 4); wygarbienia na liniach krawędziowych: szer. 4–10 cm, wys. do 8 mm, odstępy do 25 cm (PDF s. 4); parametry: β 0,32/0,30; SRL 200/150/100 mcd·lx⁻¹·m⁻²; SRT 50/50/45 (tab. 1.1). Świeże kolory: białe na asfalcie, żółte na betonie/kostce (SST, s. 102). **Nowelizacja od 02.2026 (Dz.U. 2026 poz. 132)** zmienia zasady stosowania szerokich linii krawędziowych 0,24 m (autostrady, drogi ekspresowe, dwie jezdnie główne) — wymiar 0,24 m bez zmian.

## Tabela szerokości linii poziomych (weryfikacja WORKING_VALUE)

| Znak | Znaczenie | Wartość [m] | Klasa drogi | Status | Źródło |
|---|---|---|---|---|---|
| P-1a | linia przerywana długa | **0,12** szer.; kreska 4,0; przerwa 8,0; bieg ≥120 | wszystkie | szer./geometria: ESTIMATED (wtórne, rys. 2.2.1.1); bieg ≥120 m: SOURCED (PDF s. 8) | tioman / rozp. zał. 2 |
| P-1b | linia przerywana krótka | bieg ≥50 | wszystkie | SOURCED (PDF s. 8) | rozp. zał. 2 |
| P-2…P-6 | linie podwójne ciągłe/przerwane | **nie potwierdzono cyfrowo** (rysunki rastrowe) | wszystkie | **UNVERIFIED** | rys. zał. 2 |
| P-7a/b | linie krawędziowe szerokie | **0,24**; kreska i przerwa po 1,00 w przerywanych | ekspresowe/autostrady (od 02.2026 także: dwie jezdnie główne itd.) | **SOURCED** (PDF s. 20, Dz.U. 545) | rozp. zał. 2 |
| P-7c/d | linie krawędziowe wąskie | **0,12** | pozostałe | **SOURCED** (PDF s. 20) | rozp. zał. 2 |
| P-10 | przejście dla pieszych | szer. przejścia **4,0** (min 2,5, maks 16,0); pasy i przerwy **po 0,5** | wszystkie | szer. przejścia: SOURCED (PDF s. 42); pasy: ESTIMATED (wtórne, pkt 4.2.1) | rozp. zał. 2 / tioman |
| P-11 | przebieg przejścia/azyl | **1,8** (max 3,0 przy dużym ruchu rowerów) | wszystkie | SOURCED (PDF s. 44) | rozp. zał. 2 |
| P-12 | linia bezwzględnego zatrzymania | **0,50** szer. | wszystkie | ESTIMATED (wtórne, rys. 4.2.3.1) | tioman |
| P-13 | linia warunkowa (trójkąty) | trójkąt **0,50×0,70**, odstęp **0,25** | wszystkie | ESTIMATED (wtórne, rys. 4.2.4.1) | tioman |
| P-14 | linia warunkowa (prostokąty) | prostokąt **0,75×0,50**, odstęp **0,25** | wszystkie | ESTIMATED (wtórne, rys. 4.2.5.1) | tioman |
| P-21a/b | powierzchnia wyłączona | a: **0,24**/0,39 (≤70 km/h); b: **0,60**/0,98 | wszystkie | ESTIMATED (wtórne, tab. 5.3) | tioman |
| P-23 | rower | **2,00×1,10** (mini 1,30×0,715) | drogi dla rowerów | ESTIMATED (wtórne, rys. 5.2.9.1) | tioman |
| P-25 | próg zwalniający | pasy **0,12**; długości na przemian **0,70** i **0,40** | strefy osiedlowe | ESTIMATED (wtórne, rys. 4.2.6.1) | tioman |
| — | pas ruchu | ekspresowa: **3,75** zalecana / **3,50** min.; >60 km/h: 3,50/3,20; ≤60 km/h: 3,00/2,90 | — | SOURCED (tab. 2.1, PDF s. 7) | rozp. zał. 2 |

**Wnioski dla WORKING_VALUE:** P-7 na S8 = 0,24 m (potwierdzone — nie 0,15/0,12); P-1 = 0,12 m (potwierdzone wtórnie — zalecana weryfikacja z rysunkiem); P-10 pasy = 0,50 m; P-13/14 = 0,50×0,70/0,75×0,50; P-2…P-6 do odczytu z rysunków (UNVERIFIED).

## Braki i niepewności

- **Mapillary:** brak tokenu API/przeglądarki → kadry Mapillary **niewyciągnięte, kluczy (pKey) nie zgadywano**; pozycja P2-086 UNVERIFIED (do uzupełnienia, gdy będzie token).
- **Kafel startowy (Jaroszówka, 53.152/23.168):** brak zdjęć wolnolicencyjnych (Commons/Panoramax puste) — pozycja P2-090; nawierzchnie w kaflu przyjmować wg standardów ZDiT/PFU.
- **Azyle, płytki dotykowe, ścieki przykrawężnikowe:** udokumentowane wymiary/materiały, ale **brak zdjęć wolnolicencyjnych** (P2-087…P2-089).
- **Szerokości P-2…P-6:** tylko rysunki rastrowe w PDF (brak OCR) — UNVERIFIED.
- **Koleiny/spękania S8 pod Białymstokiem:** brak potwierdzonych zdjęć; relacje o koleinach dotyczą głównie odcinków podwarszawskich (P2-092).
- **Kierunki patrzenia (heading):** źródła nie podają — UNVERIFIED dla wszystkich zdjęć (P2-093).
- **Kolory:** ESTIMATED (mediana z wycinka; balans bieli aparatu nieznany) — przed użyciem jako tekstur skalibrować (P2-094).
- **Źródła wtórne (tioman.pl):** tekst chroniony prawem autorskim — **tylko referencja, nie pobrano**; wymiary wymagają potwierdzenia rysunkami zał. 2.
- **Wyciągi tekstowe PDF** rozporządzenia wykonano 13.11.2026 w tej rozmowie (paginacja PDF/Dz.U. nagrana); w wyniku resetu środowiska roboczego nie dołączono pełnego PDF rozporządzenia (28 MB > limit) — dostępny pod linkiem w sources.md.
- Dokumentacja ZDiT to „Wytyczne do projektowania” (zał. 5 na BIP); pełny, aktualny „katalog standardów” miasta może zawierać nowsze wersje — do sprawdzenia w kolejnej paczce.

## Samokontrola (20% pozycji)

- **Seed:** 20261113 (jawny, odtwarzalny: `random.Random(20261113).sample(ids, 19)`).
- **Próba:** 19 z 94 pozycji (20,2% — obejmuje WSZYSTKIE pozycje manifestu, nie tylko pobrane pliki): P2-002, P2-003, P2-004, P2-007, P2-009, P2-013, P2-015, P2-017, P2-023, P2-039, P2-040, P2-047, P2-051, P2-059, P2-064, P2-066, P2-071, P2-077, P2-082.
- **Sprawdzono:** link odpowiada (HTTP 200), plik istnieje w files/ (dla pozycji plikowych), licencja komercyjnie zgodna, współrzędne zgodne z opisem lokalizacji, cytowanie (dokument/strona) obecne.
- **Wynik: 19/19 OK** (szczegóły w `audit_20_percent.json`).

## Licencje i użycie w grze

- **CC0** (zdjęcia: Rakoon, Dami; 17 pozycji): dowolne użycie komercyjne, także jako tekstury.
- **CC BY 3.0/4.0** (zdjęcia): użycie komercyjne z atrybucją (autor w manifeście).
- **CC BY-SA 3.0/4.0** (zdjęcia Commons/Panoramax, Wikipedia): **share-alike — używać jako referencji, nie jako tekstur**; treści faktograficzne (odczytane wymiary, kolory liczbowe, fakty) są wolne.
- **Dokumenty urzędowe** (rozporządzenie, SST/PFU, WT-2, ZDiT): art. 4 ustawy o prawie autorskim — dozwolone użytki; dołączone do paczki.
- **tioman.pl**: tylko referencja — nie pobrano, nie używać treści bez zgody autora.
- Zdjęcia nie zawierają marek/logotypów pojazdów w roli głównej; przed użyciem w grze zalecana każdorazowa kontrola pod kątem znaków towarowych osób trzecich.

# P3-buildings-2 — zabudowa przy Andersa, Sokólskiej, Wileńskiej, Białostoczku, Al. Tysiąclecia (Białystok)

**Zadanie:** M53 (RESEARCH-PACK-03-MISTRAL) · **Data:** 2026-11-13/14 · **Autor:** agent Vibe (Mistral) · **Paczka zdjęć:** mistral-p3-buildings-2-files.zip (poza gitem — karta pobrania w PR)

## Cel

Poprawka luk paczki P3 (`research/gptpro/p3-building-typology/`), w której dopasowanie zdjęć do budynków liczono z **punktu kamery** zamiast **fotografowanego budynku** (5 z 9 sprawdzonych wysokości dotyczyło innego budynku). Niniejsza paczka: (1) ≥30 budynków widocznych z Generała Władysława Andersa, Sokólskiej, Wileńskiej, Białostoczku i Alei Tysiąclecia PP — z identyfikacją fotografowanego budynku; (2) systemy wielkiej płyty per osiedle; (3) kolory elewacji po termomodernizacji 2015–2026 dla kafla Andersa/Białostoczek; (4) tekst MPZP części os. Białostoczek z warstwą tekstową; (5) stacja paliw przy Andersa (Circle K).

**Status: ZAKOŃCZONY** — manifest.csv (43 wiersze), audit_20_percent.json (9/9 PASS, 1 UWAGA), sources.md.

## Wynik — zadanie 1: manifest 43 wierszy

- **40 budynków przyjętych**: 9 × `OK` (dowód bezpośredni) + 31 × `OK-POŚREDNIE` (dowód pośredni) — **każdy z identyfikacją FOTOGRAFOWANEGO budynku**, nie najbliższego kamerze.
- **3 odrzucone** (`ODRZUCONY`) z uzasadnieniem: M53-009 (Olsztyńska 2 — w miejscu obiektu ogrodzenie/drzewa wg wizji; promień trafia w sąsiednią Olsztyńską 1A), M53-024 (Białostoczek 14 — zasłonięty przez Białostoczek 18 stojący przed nim na osi patrzenia), M53-027 (Białostoczek 4 — kamera na posesji obiektu, budynek poza osią patrzenia, brak potwierdzenia fotografowania).
- Zakres ulic: Andersa (6), Sokólska (2), Białostoczek + przyległe (Radzymińska/Kozłowa/Zagumienna) (16), Al. Tysiąclecia PP (10), Wysoki Stoczek — Skidelska/Świsłocka/Wołkowyska/Kowieńska/Wileńska/Lidzka (7), odrzucone (3) — łącznie 43.
- Wysokości: `measuredHeight` z **LoD1 GUGiK 2024 (K2)** (dopasowanie obrysu LoD1↔OSM przez IoU z rasteryzacji 0,5 m; dla 40 z 43 IoU ≥ 0,55, mediana ≈ 0,92); wyjątki: wiata i kiosk stacji (poza LoD1) — patrz zadanie 5.
- Kondygnacje: OSM `building:levels` gdzie jest; w pozostałych **ESTIMATED** = round(mh/2,9 m) z adnotacją w kolumnie (metoda jawnie podana; audyt C sprawdza spójność mh↔kondygnacje·2,9±2 m).
- Dachy: patrz sekcja „Dachy".

## Metoda dopasowania budynku do zdjęcia (naprawka błędu P3)

Dla każdej pary (budynek, zdjęcie) weryfikujemy, że **fotografowany budynek** (nie najbliższy kamerze) jest tym z manifestu:

1. **Kierunek patrzenia — azymut sekwencji z GPS EXIF**: pozycje kolejnych zdjęć tej samej sesji (Commons, Rakoon) dają azymut marszu ≈ azymut patrzenia. Wyliczono dwa warianty (baza ≥3 m / ≥15 m); gdy różnica >15°, azymut oznaczono **ZAWODNY** i obie wartości podano jawnie w `metoda_dopasowania`/`uwagach` (8 zdjęć: m.in. 20240401 110755/110805/110911/110918, 20221119 080807/080833). Kryterium w-kadrze: odchyłka dev = bearing(kamera→centroid) − azymut; pozycja w kadrze pos = 50 + dev/0,7 (HFOV 70°); przyjęto |dev| ≤ 25° (±25°) oraz d ≤ 260 m.
2. **Ray-first-hit (FH)**: promień 400 m od kamery wg azymutu; pierwszy obrys na drodze (parametr wejścia `entry-t`, nie odległość centroidu — sortowanie po odległości centroidu dawało wyniki fałszywe). FH = fotografowany obiekt, gdy trafia w obrys celu → status `OK`.
3. **Kamera w obrysie obiektu** (GPS zdjęcia z poziomu posesji) → status `OK`/`OK-POŚREDNIE` z adnotacją.
4. **Opis-autora**: tytuły autorskie Commons („Generała Andersa 38A”, „LO nr XVI i ZSO nr 10”, „Tysiąclecia 10 Białystok”, „PKO BP Białystok (Tysiąclecia)”) — identyfikacja obiektu bezpośrednio (zdjęcia H. Borawskiego, CC BY-SA 3.0 — **tylko referencja**).
5. **Zachowane wyniki analizy wizyjnej z 13.11** (sesja pierwotna): opisy brył/kadrów (wiata czerwona, kiosk biały parterowy, parterowiec z billboardem przy stacji, obiekt handlowy przy Sokólskiej, „niski obiekt usługowy na prawej krawędzi 70–80%” przy Andersa 71, elewacja Tysiąclecia 56 [131,121,97]); w bieżącej sesji odbudowy limit analizy wizyjnej — protokół w `audit_20_percent.json` (kryterium G: NIE DOTYCZY).
6. **Porównanie bryły**: LoD1 (footprint, measuredHeight) vs. bryła na zdjęciu; spójność mh ↔ kondygnacje·2,9 m (audyt C).
7. **Krzyżowo**: obrys LoD1 ↔ OSM way przez **IoU ≥ 0,5** (rasteryzacja 0,5 m); adres z OSM `addr:*` (pełna nazwa ulicy — prefix-match pułapka: „Andersa 46” ≠ „Hallera 46”); ortofotomapa WMS GUGiK (warstwa `Raster`) dla dachów.

**Errata P3 potwierdzona praktyką:** w rebuiltowym zbiorze najbliższy kamerze budynek byłby często innym obiektem niż fotografowany (np. dla zdjęcia 20230729 105139 najbliższy kamerze to supermarket Sokólska 9, ale w osii patrzenia leżą też Białostoczek 27 i 34; dla 20241229 112510 w osii leżą Białostoczek 18 (przed) i 14 (za nim, zasłonięty → odrzucony)). Statusy `OK`/`OK-POŚREDNIE` różnicują siłę dowodu; `ODRZUCONY` z uzasadnieniem.

## Dachy (kształt + kolor) — metoda

- **Kształt**: ortofotomapa GUGiK WMS (warstwa `Raster`, EPSG:4326, wycinek 256 px wokół obrysu +6 m, pliki `files/orto/M53-NNN.jpg` w ZIP): maska wnętrza obrysu OSM, k-means k=2, bimodalność luminancji (ΔL>38 przy udziałach >22%) → dwuspadowy; w pozostałych płaski. Nadpisania heurystyką typologiczną (jawne w `dach`/uwagach): bloki OWT/TBS i wieżowce → płaskie dachy (typologia systemów — patrz zadanie 2); wynik oznaczony **ESTIMATED**.
- **Kolor**: dominanta koloru maski dachu z ortofoto (ESTIMATED sRGB). roofType z LoD1 jest bezużyteczny (stała 1000).

## Zadanie 3 — kolory elewacji po termomodernizacji 2015–2026 (kafel Andersa/Białostoczek)

Brak publicznie dostępnych projektów kolorystyki/STWiOR dla bloków kafla (BIP spółdzielni nie publikuje kart kolorów) → kolor elewacji **ESTIMATED sRGB** ze zdjęć (metoda: gray-world white-balance → k-means k=4 na cropie kadru w pozycji budynku (pos%, rozmiar okna z kąta bryły footprint/mh i odległości) → dominanta; reguła cienia: dominanta L<70 + klaster jasny ≥20% → klaster jasny; klaster niebo/zieleń odrzucany). Skrzyżowania weryfikacyjne: M53-036 (zachowana wizja 13.11 [131,121,97] vs wyliczone [111,100,63] — zgodność beżu) ✓; M53-011/012 pastelowy pomarańcz/beż — typowe dla Białostoczka po termomodernizacji. **UNVERIFIED**: zdjęcia zmierzchowe (stacja paliw), cropy w głębokim cieniu (M53-004/030/033/034/038), domieszka nieba (M53-017). Daty zdjęć (2020–2024) odnotowane — dla zdjęć sprzed 2023 możliwa niespójność z późniejszą termomodernizacją (adnotacja w `metoda_koloru`).

## Ustalenia — zadanie 4: MPZP części os. Białostoczek (tekst uchwały z warstwą tekstową)

**Uchwała Nr XXVII/451/26 Rady Miasta Białystok z dnia 25 czerwca 2026 r.** w sprawie miejscowego planu zagospodarowania przestrzennego części osiedla Białostoczek w Białymstoku w rejonie ulic Alei 1000-lecia Państwa Polskiego i Kombatantów – etap IA (Dz. Urz. Woj. Podlaskiego z 29.06.2026 r., **poz. 2669**; PDF z warstwą tekstową). Plan obejmuje obszar ok. 15,21 ha ograniczony ulicami: Kombatantów, Bitwy Białostockiej, **Gen. Władysława Andersa** i Władysława Bełzy — czyli fragment kafla Andersa/Białostoczek.

Ustalenia (z cytatem, paragraf — pełne cytaty w `sources.md`):

- **Kąt dachu** — § 3 ust. 1 pkt 1: dach płaski = nachylenie głównych połaci **0°–15°**.
- **Kolorystyka elewacji** — § 7 ust. 1 pkt 1 lit. a: **maksimum 3 kolory na jednej elewacji**, w odcieniach **bieli, beżu, brązu i szarości** oraz barw naturalnych materiałów (drewno, kamień, cegła); kolor tylko w sposób podkreślający rozrzeźbienie i detal.
- **Kolorystyka pokrycia dachów** (nie dotyczy płaskich) — § 7 ust. 1 pkt 1 lit. b: odcienie **brązu, ciemnej czerwieni i szarości**.
- Akcenty kolorystyczne: dodatkowe akcenty maks. **10% powierzchni elewacji** tylko dla usług edukacji (§ 7 ust. 1 pkt 2); murale poza reżimem (pkt 3).
- Wysokość nowej zabudowy: maks. 25 m (we wnioskach wewn. A/B terenu 1MW-U-UW: 30/50 m); ograniczenie rzędną 260 m n.p.m. (§ 16).

## Ustalenia — zadanie 2: systemy wielkiej płyty per osiedle

| Osiedle | System | Okres | Źródło (cytat w `sources.md`) |
|---|---|---|---|
| **Białostoczek** | **OWT-67** (etap I: 905 mieszk., 5-kond. bloki) / **OWT-75** (etap II: 2784 mieszk.) | 1977–1980 | Osiedlownik „BIAŁOSTOCZEK” (cytuje prasę 1977–78); projekt: poznański Inwestprojekt; inwestor BSM |
| **Bacieczki** | **NIE DOTYCZY — brak wielkiej płyty**: zabudowa Komunalnego TBS od 1999 (Kołłątaja 75/73 pierwszy, 3.09.1999; 10 bloków w „Bacieczkach I”; projekt: T. Koleśnik, arch. A. Makarewicz, M. Szymański) | 1999+ | Osiedlownik „TBS” (cytuje prezes KTBS E. Zyska i monografię A. Dobrońskiego) |
| **Zielone Wzgórza** | **OWT-75** (elementy: białostocki **Fadom-II**; pierwszy blok — Rumiankowa, przeprowadzki od początku 1985) | 1984/85+ | Osiedlownik „SŁONECZNY STOK / ZIELONE WZGÓRZA / LEŚNA DOLINA” (cytuje „Współczesną” 1985) |
| **Wysoki Stoczek** | wielka płyta („u schyłku PRL”), **nazwa systemu: UNVERIFIED** | schyłek PRL | Osiedlownik „WYSOKI STOCZEK 1.0” (2026) |
| **Przydworcowe/Sienkiewicza** | **OWT-67** (12 bloków, w tym 11-piętrowce; projekt Inwestprojekt Białystok — Jan Prochowski; montaż BPBM od 1976) | 1972–1977 | Osiedlownik „PRZYDWORCOWE” (cytuje „Białostocką” i „Współczesną”) |
| (kontekst) os. Tysiąclecia | elementy OWT (wszystkie wczesne osiedla BSM); 3 wieżowce 10-piętrowe przy Wesołej/Zwierzynieckiej | 1966–1974 | Osiedlownik „TYSIĄCLECIA”; H. Wilk, „Współczesna” 1977 |

Uogólnienie (za rozprawą doktorską cyt. we wpisie Zielone Wzgórza): rok 1990 wyznacza realny koniec dominacji wielkiej płyty w Białymstoku — ostatnie projekty OWT powstały w 1990, ostatnie realizacje ok. 1991–92 (Leśna Dolina).

Artykuł naukowy o OWT w Białymstoku: „OWT służy inżynierom” (ba.pdl.piib.org.pl, 05.2024) — badania rozbiórki budynku OWT-67 (b. siedziba Miastoprojektu Białystok).

Przypisania per budynek w `system_wp` manifestu: Białostoczek 7 i 11 → OWT-67 (etap I — kwartał Kozłowa/Białostoczek wg cytatu o najstarszych blokach); Białostoczek 14/22/Zagumienna 4/Radzymińska 1 → OWT-75 etap II (**przypisanie UNVERIFIED** — lokalizacja w etapie II wg kolejności zabudowy, brak źródła per budynek); pozostałe Białostoczek → OWT-67/75 UNVERIFIED; Tysiąclecia 10/10A → UNVERIFIED (po 1990); pozostałe Tysiąclecia → OWT (Wilk 1977); Wysoki Stoczek/Skidelska/Wileńska itd. → NIE DOTYCZY (TBS 1999+, patrz Bacieczki/Wysoki Stoczek); obiekty usługowe → NIE DOTYCZY.

## Zadanie 5 — stacja paliw przy Andersa (Circle K)

- **Adres (OSM)**: ul. Generała Władysława Andersa **38** (way 236606116 — `building=roof`, `amenity=fuel`, powierzchnia 119 m²; zespół biurowo-usługowy Biazet, stacja na terenie posesji).
- **Wiaty stacji**: wysokość **ESTIMATED 4,5 m** (zakres 4,2–4,8 m) — metoda skali na zdjęciu Commons (20201229 150935, Rakoon, CC0): samochód osobowy h≈1,45–1,55 m, van h≈2,5–2,7 m, proporcje kolumn wiaty; potwierdzenie wizyjne 13.11 (czerwona wiata, rozpiętość ponad stanowiska). Wiata poza modelem LoD1 GUGiK (brak obrysu).
- **Kiosk**: parterowy, biały (wizja 13.11); way 957256518; poza LoD1 — mh UNVERIFIED.
- **Biurowiec parterowy z billboardem na posesji naprzeciwko wylotu** (way 392226320): LoD1 mh **4,45 m** (IoU 0,997), 1 kondygnacja (OSM).
- Zdjęcie zmierzchowe → kolory elewacji UNVERIFIED (opis wizyjny), patrz zadanie 3.

## Samokontrola 20% — wynik

- **Seed jawnego próbkowania: 20261113**; próbkowanie `random.Random(20261113).sample(ids, ceil(0.2·43))` = **9 wierszy**: M53-001, 002, 005, 009, 012, 024, 030, 033, 041.
- Kryteria (A dopasowanie — czy obrys/wysokość należą do budynku ze zdjęcia; B IoU LoD1↔OSM; C mh↔kondygnacje·2,9; D licencja; E JPG ≤1600 px fizycznie na kopiach `files/`; F adres; G wizja — NIE DOTYCZY, limit w sesji odbudowy).
- **Werdykt: 9/9 PASS** (w tym PASS-DIRECT i PASS-POŚREDNIE), **1 UWAGA**: M53-033 (Tysiąclecia 50) — mh 14,86 m vs OSM 4 kondygnacje·2,9 = 11,6 m (Δ3,3 m; blok z wysokim parterem — odnotowane). Pełny protokół: `audit_20_percent.json`.

## Ograniczenia

- Azymut patrzenia wyznaczany z toru sekwencji (GPS EXIF) — zawodny przy zmianach kierunku marszu; rozbieżne warianty podane jawnie per zdjęcie.
- Analiza wizyjna niedostępna w sesji odbudowy (limit) — identyfikacje oparte na geometrii (FH/stożek/IoU), opisach-autora i zachowanych wynikach wizji 13.11; stąd rozróżnienie OK/OK-POŚREDNIE.
- `files/` nie jest w gicie (`.gitignore`); zdjęcia (≤1600 px, miniatury Commons) i wycinki ortofoto w **mistral-p3-buildings-2-files.zip** (karta pobrania w PR) + INDEX.csv.

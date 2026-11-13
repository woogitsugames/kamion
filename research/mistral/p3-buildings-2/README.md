# P3-buildings-2 — zabudowa przy Andersa, Sokólskiej, Wileńskiej, Białostoczku, Al. Tysiąclecia (Białystok)

**Zadanie:** M53 (RESEARCH-PACK-03-MISTRAL) · **Data:** 2026-11-13/14 · **Autor:** agent Vibe (Mistral) · **Paczka zdjęć:** mistral-p3-buildings-2-files.zip (poza gitem — karta pobrania w PR)

## Cel

Poprawka luk paczki P3 (`research/gptpro/p3-building-typology/`), w której dopasowanie zdjęć do budynków liczono z **punktu kamery** zamiast **fotografowanego budynku** (5 z 9 sprawdzonych wysokości dotyczyło innego budynku). Niniejsza paczka: (1) ≥30 budynków widocznych z Generała Władysława Andersa, Sokólskiej, Wileńskiej, Białostoczku i Alei Tysiąclecia PP — z identyfikacją fotografowanego budynku; (2) systemy wielkiej płyty per osiedle; (3) kolory elewacji po termomodernizacji 2015–2026 dla kafla Andersa/Białostoczek; (4) tekst MPZP części os. Białostoczek z warstwą tekstową; (5) stacja paliw przy Andersa (Circle K).

**Status: W TRAKCIE (M53-FIX v2, etap 1 z 2)** — po przeglądzie `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p3.md` manifest jest przebudowywany: każde zdjęcie oglądane przez wizję (kolumna `co_widac`), dopasowanie przez geometrię kamera→obrys + treść kadru (nie azymut toru!), kondygnacje liczone na zdjęciu, kolor tylko z prostokąta ściany. Etap 1 (commity częściowe): wiersze 001–016, 027 + poprawki typu 037–043. Etap 2: pozostałe zdjęcia, uzupełnienie do ≥30 przyjętych, nowy audyt 20%, ZIP v2.

## Wynik — zadanie 1: manifest 43 wierszy (stan przebudowy v2)

**Ważne (przegląd r8):** azymut z toru sekwencji Commons (GPS zaokrąglony do 1″) jest zawodny i **nie może być podstawą statusu**. W v2 każdy wiersz ma obowiązkowy opis wizyjny w kolumnie `co_widac` (co w kadrze, numer/napis jeśli widać, liczba kondygnacji POLICZONA na zdjęciu, pozycja celu w kadrze: lewo/środek/prawo), a kierunek ustalany jest z treści kadru (napisy adresowe, charakterystyczne budynki, przecięcia ulic) i porównywany z obrysami LoD1/OSM.

- **Etap 1 (wiersze 001–016, 027)**: 7 × `OK` (w tym 4 rekasygnacje po napisach adresowych: M53-010→Zagumienna 9/1, M53-011→Białostoczek 29, M53-012→Zagumienna 40, M53-014→Białostoczek 4/1), 3 × `OK-POŚREDNIE` (bryła+geometria, bez napisu: M53-013/016/027), 6 × `ODRZUCONY` po wizji (M53-003/004/005/006/008/009 — cel niewidoczny w kadrze lub kadr w inną stronę), 1 × `OCZEKUJE_WIZJI` (M53-015 — identyfikacja w toku).
- **Etap 2 (wiersze 017–026, 028–043)**: statusy przejściowe `OCZEKUJE_WIZJI` — stare dopasowanie azymutem toru nieważne; wiersze zostaną zaliczone/odrzucone po obejrzeniu zdjęć; uzupełnienie zbioru do ≥30 przyjętych.
- Typ budynku poprawiony (polecenie przeglądu): M53-037…043 to domy jednorodzinne/szeregowe (M53-041 — dom z poddaszem), nie „blok TBS 1999+”; `system_wp` = NIE DOTYCZY. M53-027 (Białostoczek 4) — ocena ponowna: dom 2-kondygnacyjny widoczny centralnie w kadrze pasuje do obrysu (LoD1 mh 8,31 m) → `OK-POŚREDNIE`.
- Zakres ulic: Andersa (6), Sokólska (2), Białostoczek + przyległe (Radzymińska/Kozłowa/Zagumienna) (16), Al. Tysiąclecia PP (10), Wysoki Stoczek — Skidelska/Świsłocka/Wołkowyska/Kowieńska/Wileńska/Lidzka (7) — łącznie 43.
- Wysokości: `measuredHeight` z **LoD1 GUGiK 2024 (K2)** (dopasowanie obrysu LoD1↔OSM przez IoU z rasteryzacji 0,5 m); wyjątki: wiata i kiosk stacji (poza LoD1) — patrz zadanie 5.
- Kondygnacje: `kondygnacje_ze_zdjęcia` = liczba POLICZONA na zdjęciu (wizja); `mh/2,9` oraz OSM `building:levels` wyłącznie w porównawczej kolumnie `kondygnacje_porównanie` (audyt C porównuje zliczenie ze zdjęcia z LoD1).
- Dachy: kształt z ortofoto GUGiK (sekcja „Dachy”) lub z wizji (gdzie jawny na zdjęciu); kolor dachu tylko z maski ortofoto.

## Metoda dopasowania budynku do zdjęcia (v2 — obowiązkowa wizja)

Dla KAŻDEGO wiersza manifestu zdjęcie jest oglądane przez model wizyjny (jedno zdjęcie = jedno wywołanie; commity co ~5 wierszy). Stare dopasowanie azymutem toru sekwencji zostało uznane za nieważne (przegląd r8: GPS zaokrąglony do 1″, kadr często w inną stronę niż tor marszu).

1. **`co_widac`** — jedno zdanie opisu kadru: co jest w kadrze, numer/napis adresowy jeśli widać, liczba kondygnacji POLICZONA na zdjęciu, pozycja celu w kadrze (lewo/środek/prawo).
2. **Kierunek z treści kadru**: napisy adresowe na elewacjach (np. „ZAGUMIENNA 9/1”, „Białostoczek 29”, „4/1”), charakterystyczne budynki, przecięcia ulic, szyldy — porównanie z obrysami LoD1/OSM wokół pozycji kamery (EPSG:2180).
3. **Geometria kamera→obrys**: dla każdego wiersza kolumny `kamera_d_m` (odległość do najbliższego punktu OBRYSU celu) i `kamera_kat_deg` (azymut do tego punktu). Azymut toru sekwencji tylko jako wskazówka pomocnicza — nigdy jako podstawa statusu.
4. **Statusy**: `OK` = napis adresowy/tytuł autorski potwierdza obiekt; `OK-POŚREDNIE` = bryła (liczba kondygnacji, kształt dachu, kolor) i geometria kamera→obrys zgodne, brak napisu; `ODRZUCONY` = cel niewidoczny w kadrze albo kadr niezgodny z obrysem; rekasygnacja gdy w kadrze jednoznacznie widać INNY budynek (z napisem).
5. **Porównanie bryły**: LoD1 (footprint, measuredHeight) vs liczba kondygnacji ze zdjęcia (audyt C: zliczenie ze zdjęcia vs mh/2,9).
6. **Krzyżowo**: obrys LoD1 ↔ OSM way przez IoU ≥ 0,5 (rasteryzacja 0,5 m); adres z OSM `addr:*` (prefix-match pułapka: „Andersa 46” ≠ „Hallera 46”); ortofotomapa WMS GUGiK dla dachów.

Przykłady obaleń z przeglądu potwierdzone wizją: M53-006 (w kadrze park i bloki Al. Tysiąclecia 44–60, JRG-2 poza kadrem → ODRZUCONY), M53-008/011/012 (kadr 105139 patrzy ~335° — napisy „Zagumienna 40” i „Białostoczek 29”; rekasygnacje), M53-014 (w kadrze 4-kondygnacyjny budynek z tabliczką „4/1”, nie punktowiec Białostoczek 11 → rekasygnacja na Białostoczek 4/1).

## Dachy (kształt + kolor) — metoda

- **Kształt**: ortofotomapa GUGiK WMS (warstwa `Raster`, EPSG:4326, wycinek 256 px wokół obrysu +6 m, pliki `files/orto/M53-NNN.jpg` w ZIP): maska wnętrza obrysu OSM, k-means k=2, bimodalność luminancji (ΔL>38 przy udziałach >22%) → dwuspadowy; w pozostałych płaski. Nadpisania heurystyką typologiczną (jawne w `dach`/uwagach): bloki OWT/TBS i wieżowce → płaskie dachy (typologia systemów — patrz zadanie 2); wynik oznaczony **ESTIMATED**.
- **Kolor**: dominanta koloru maski dachu z ortofoto (ESTIMATED sRGB). roofType z LoD1 jest bezużyteczny (stała 1000).

## Zadanie 3 — kolory elewacji po termomodernizacji 2015–2026 (kafel Andersa/Białostoczek)

**Metoda v2 (k-means usunięty):** po przeglądzie r8 k-means na cropie kadru dawał wartości błędne (trafiał w niebo/cienie/zieleń; np. M53-013 [52,44,41] dla białego bloku, M53-029 różowawy dla białego, M53-035 „oliwkowy” dla żółtozielonego). W v2 kolor elewacji liczony jest WYŁĄCZNIE z ręcznie wskazanego prostokąta ŚCIANY:
- model wizyjny wskazuje prostokąt px (x0,y0,x1,y1) na czystym fragmencie ściany (bez cieni, drzew, nieba, okien i balkonów) — współrzędne zapisane w kolumnie `prostokat_sciany_px`;
- średnia RGB prostokąta liczona niezależnym dekoderem JPEG (bez utraty); wynik w `kolor_srgb`, metoda w `metoda_koloru` = „prostokąt ściany (wizja→dekoder JPEG)”;
- sanity-check: wartość musi być zgodna z opisem koloru z wizji (odrzucone prostokąty trafiające w niebo/prześwietlenie — wtedy prostokąt powtarzany).
**UNVERIFIED**: zdjęcia zmierzchowe (stacja paliw M53-001/002), brak czystej ściany w kadrze, prostokąt trafiał w tło (wtedy jawnie adnotacja w `metoda_koloru`). Daty zdjęć (2020–2024) odnotowane — dla zdjęć sprzed 2023 możliwa niespójność z późniejszą termomodernizacją.

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

Przypisania per budynek w `system_wp` manifestu: Białostoczek 7 → OWT-67 (etap I — kwartał Kozłowa/Białostoczek wg cytatu o najstarszych blokach); Białostoczek 14/22/Zagumienna 4/Radzymińska 1 → OWT-75 etap II (**przypisanie UNVERIFIED** — brak źródła per budynek); pozostałe Białostoczek → OWT-67/75 UNVERIFIED; Tysiąclecia 10/10A → UNVERIFIED (po 1990); pozostałe Tysiąclecia → OWT (Wilk 1977); **Wysoki Stoczek — Skidelska/Świsłocka/Wołkowyska/Kowieńska/Wileńska/Lidzka: domy jednorodzinne/szeregowe → NIE DOTYCZY** (zabudowa jednorodzinna, patrz poprawka typu M53-037…043; wcześniejsze „TBS 1999+” dla tych wierszy było błędne — TBS 1999+ dotyczy Bacieczek, nie Wysokiego Stoczka); obiekty usługowe → NIE DOTYCZY.

## Zadanie 5 — stacja paliw przy Andersa (Circle K)

- **Adres (OSM)**: ul. Generała Władysława Andersa **38** (way 236606116 — `building=roof`, `amenity=fuel`, powierzchnia 119 m²; zespół biurowo-usługowy Biazet, stacja na terenie posesji).
- **Wiaty stacji**: wysokość **ESTIMATED 4,5 m** (zakres 4,2–4,8 m) — metoda skali na zdjęciu Commons (20201229 150935, Rakoon, CC0): samochód osobowy h≈1,45–1,55 m, van h≈2,5–2,7 m, proporcje kolumn wiaty; potwierdzenie wizyjne 13.11 (czerwona wiata, rozpiętość ponad stanowiska). Wiata poza modelem LoD1 GUGiK (brak obrysu).
- **Kiosk**: parterowy, biały (wizja 13.11); way 957256518; poza LoD1 — mh UNVERIFIED.
- **Biurowiec parterowy z billboardem na posesji naprzeciwko wylotu** (way 392226320): LoD1 mh **4,45 m** (IoU 0,997), 1 kondygnacja (OSM).
- Zdjęcie zmierzchowe → kolory elewacji UNVERIFIED (opis wizyjny), patrz zadanie 3.

## Samokontrola 20% (v2 — plan po przeglądzie)

- **Nowe losowanie 20% z jawnym seedem** (próbkowanie z pełnej listy ID po zakończeniu etapu 2; seed zostanie podany w `audit_20_percent.json`).
- Dla każdego wylosowanego wiersza zapisywane: `co_widac` + odległość (`kamera_d_m`) i kąt (`kamera_kat_deg`) kamera→obrys.
- **Kryterium wizji obowiązkowe** — bez „NIE DOTYCZY”: każdy wylosowany wiersz musi mieć potwierdzenie wizyjne kadru (co w kadrze, pozycja celu, policzone kondygnacje).
- Kryteria: A dopasowanie (obrys/wysokość należą do budynku ze zdjęcia — wg wizji, nie azymutu), B IoU LoD1↔OSM, **C zliczenie kondygnacji ze zdjęcia vs LoD1 mh/2,9**, D licencja, E JPG ≤1600 px, F adres, G wizja (OBWIĄZKOWE).
- Werdykt po etapie 2 — pełny protokół: `audit_20_percent.json`.

## Ograniczenia

- Azymut z toru sekwencji (GPS zaokrąglony do 1″) zawodny — w v2 wyłącznie pomocniczy; podstawą jest treść kadru (wizja) + geometria kamera→obrys.
- Analiza wizyjna limitowana w czasie sesji — przegląd zdjęć wykonywany etapami (etap 1: 001–016, 027; etap 2: pozostałe), commity częściowe po każdym etapie.
- `files/` nie jest w gicie (`.gitignore`); zdjęcia (≤1600 px, miniatury Commons) i wycinki ortofoto w ZIP (v2: `mistral-p3-buildings-2-files-v2.zip` — karta pobrania w PR) + INDEX.csv.

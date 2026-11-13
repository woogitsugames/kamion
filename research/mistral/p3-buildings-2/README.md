# P3-buildings-2 — zabudowa przy Andersa, Sokólskiej, Wileńskiej, Białostoczku, Al. Tysiąclecia (Białystok)

**Zadanie:** M53 (RESEARCH-PACK-03-MISTRAL) · **Data:** 2026-11-13 · **Autor:** agent Vibe (Mistral) · **Paczka zdjęć:** mistral-p3-buildings-2-files.zip (poza gitem — karta pobrania w PR)

## Cel

Poprawka luk paczki P3 (`research/gptpro/p3-building-typology/`), w której dopasowanie zdjęć do budynków liczono z **punktu kamery** zamiast **fotografowanego budynku** (5 z 9 sprawdzonych wysokości dotyczyło innego budynku). Niniejsza paczka: (1) ≥30 budynków widocznych z Generała Władysława Andersa, Sokólskiej, Wileńskiej, Białostoczku i Alei Tysiąclecia PP — z identyfikacją fotografowanego budynku; (2) systemy wielkiej płyty per osiedle; (3) kolory elewacji po termomodernizacji 2015–2026 dla kafla Andersa/Białostoczek; (4) tekst MPZP części os. Białostoczek z warstwą tekstową; (5) stacja paliw przy Andersa (Circle K).

**Status: W TOKU** — gałąź robocza; manifest i samokontrola dojdą w kolejnych commitach.

## Metoda dopasowania budynku do zdjęcia (naprawka błędu P3)

Dla każdej pary (budynek, zdjęcie) weryfikujemy, że **fotografowany budynek** (nie najbliższy kamerze) jest tym z manifestu:

1. **Kierunek patrzenia**: pozycja kamery (GPS zdjęcia) + heading kamery (KartaView `heading` — odrzucany jako niewiarygodny, gdy różni się >25° od azymutu wyznaczonego z kolejnych pozycji sekwencji; Panoramax `view:azimuth`). Budynek musi leżeć w ±30° od osi patrzenia (kryterium `sdev` w danych roboczych).
2. **Odległość**: kamera–budynek (odległość do centroidu obrysu); typowo 48–130 m.
3. **Porównanie bryły**: LoD1/BDOT10k (footprint L×W, measuredHeight) vs. bryła na zdjęciu — liczba kondygnacji liczona na zdjęciu musi być spójna z `measuredHeight / (2,9 ± 1) m`; szerokość elewacji z footprintu odpowiada liczbie klatek.
4. **Pozycja w kadrze**: model wizyjny wymienia budynki L→P z pozycją w kadrze; akceptujemy parę tylko gdy pozycja budynku w kadrze (lewa/środek/prawa) jest zgodna ze znakiem odchyłki azymutu kamery od środka kadru (sdev<0 = lewa połowa, >0 = prawa) i opis bryły pasuje do obrysu.
5. **Krzyżowo**: obrys LoD1 ↔ OSM way przez IoU ≥ 0,5 (rasteryzacja obrysów); adres z OSM `addr:*`; ortofotomapa WMS GUGiK dla wątpliwych przypadków.

Dopasowanie uznajemy za potwierdzone dopiero po pozytywnej analizie wizyjnej zdjęcia (kroki 3–4). Budynek najbliższy kamerze, ale poza osią patrzenia — odrzucany (to był błąd P3).

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
| **Białostoczek** | **OWT-67** (etap I: 905 mieszk., 5-kond. bloki) / **OWT-75** (etap II: 2784 mieszk.) | 1977–1980 | Osiedlownik „BIAŁOSTOCZEK" (cytuje prasę 1977–78); projekt: poznański Inwestprojekt; inwestor BSM |
| **Bacieczki** | **NIE DOTYCZY — brak wielkiej płyty**: zabudowa Komunalnego TBS od 1999 (Kołłątaja 75/73 pierwszy, 3.09.1999; 10 bloków w „Bacieczkach I"; projekt: T. Koleśnik, arch. A. Makarewicz, M. Szymański) | 1999+ | Osiedlownik „TBS" (cytuje prezes KTBS E. Zyska i monografię A. Dobrońskiego) |
| **Zielone Wzgórza** | **OWT-75** (elementy: białostocki **Fadom-II**; pierwszy blok — Rumiankowa, przeprowadzki od początku 1985) | 1984/85+ | Osiedlownik „SŁONECZNY STOK / ZIELONE WZGÓRZA / LEŚNA DOLINA" (cytuje „Współczesną" 1985) |
| **Wysoki Stoczek** | wielka płyta („u schyłku PRL"), **nazwa systemu: UNVERIFIED** | schyłek PRL | Osiedlownik „WYSOKI STOCZEK 1.0" (2026) |
| **Przydworcowe/Sienkiewicza** | **OWT-67** (12 bloków, w tym 11-piętrowce; projekt Inwestprojekt Białystok — Jan Prochowski; montaż BPBM od 1976) | 1972–1977 | Osiedlownik „PRZYDWORCOWE" (cytuje „Białostocką" i „Współczesną") |
| (kontekst) os. Tysiąclecia | elementy OWT (wszystkie wczesne osiedla BSM); 3 wieżowce 10-piętrowe przy Wesołej/Zwierzynieckiej | 1966–1974 | Osiedlownik „TYSIĄCLECIA"; H. Wilk, „Współczesna" 1977 |

Uogólnienie (za rozprawą doktorską cyt. we wpisie Zielone Wzgórza): rok 1990 wyznacza realny koniec dominacji wielkiej płyty w Białymstoku — ostatnie projekty OWT powstały w 1990, ostatnie realizacje ok. 1991–92 (Leśna Dolina).

Artykuł naukowy o OWT w Białymstoku: „OWT służy inżynierom" (ba.pdl.piib.org.pl, 05.2024) — badania rozbiórki budynku OWT-67 (b. siedziba Miastoprojektu Białystok).

## Zadanie 3 — kolory elewacji po termomodernizacji 2015–2026 (kafel Andersa/Białostoczek)

W TOKU. Priorytet: STWiOR/kolorystyka z BIP spółdzielni (BSM) i przetargów; gdy brak — ESTIMATED sRGB ze zdjęć 2023+ (Commons/Panoramax), metoda: dominujący kolor elewacji z opisu wizyjnego, balans bieli nieznany → status ESTIMATED z zakresem.

## Samokontrola (w toku)

Seed jawnego próbkowania: **20261113**; próbkowanie ≥20% wierszy manifestu; pełny protokół: `audit_20_percent.json` (dojdzie z manifestem).

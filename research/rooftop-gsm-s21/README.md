# K67 (blok M67) — dachowe instalacje GSM: geometria elementów

Sesja chmurowa s21, 2026-11-15. Gałąź `research/rooftop-gsm-s21`.

## Uzgodnienie z M57
To uzupełnienie M57. **Lokalizacji ani układu masztów na wieżowcu przy Andersa nie powtarzam.**
Z recenzji `docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md` (§4, §6) przyjmuję tylko to, co recenzja potwierdziła:
- maszt kratowy środkowy ok. 10–12 m nad dachem;
- maszty ok. 4–6 m przy końcu NE;
- maszt W z odciągami;
- panele wzdłuż krawędzi SE.

Odrzucone przez recenzję tezy M57 (nadbudówka, siatka NW, P14-007) nie są tu używane.

Pliki w katalogu:
- `manifest.csv` — 35 wierszy K67-001…035. Kolumny jak w bloku M67, na końcu dopisane `plik` i `sha256_pliku`.
- `sources.md`, `audit_20_percent.json`.
- `files/` — 16 wycinków ortofoto GUGiK, 1,9 MB.
- `uke_match.json`, `uke_tall.json`, `roof_masts.json` — dopasowania.
- `tools/`.

## 1. Katalog elementów (13 wierszy, ≥ 8 typów)

| # | element | wymiary | kolor (opis) | status |
|---|---|---|---|---|
| 1 | antena sektorowa panelowa, długa | 2688 × 498 × 197 mm, 56,5 kg; pochylenie elektryczne 2–12° | jasnoszary matowy radom (RAL 7035) | SOURCED (karta) |
| 2 | antena sektorowa panelowa, krótka | 1499 × 498 × 197 mm, 35 kg | jw. | SOURCED |
| 3 | antena radioliniowa 0,6 m | Ø 0,6 m, 6,7 kg, rura 48–120 mm | czasza biała, radom szary | SOURCED |
| 4 | antena radioliniowa 0,3 m | Ø 0,3 m, 4,08 kg | jw. | SOURCED |
| 5 | antena radioliniowa 0,9 / 1,2 m | — | — | UNVERIFIED |
| 6 | moduł RRU przy antenie | 425 × 296 × 130 mm, 18,3 kg, IP65 | UNVERIFIED | SOURCED (wymiary) |
| 7 | szafa/kontener na dachu | rzut ok. 2 × 1 m | jasnoszary | ESTIMATED (ortofoto) |
| 8 | rama krzyżowa (X) pod maszt | rozpiętość ramion ok. 12 (11–13) m | stal szara | ESTIMATED (ortofoto 0,05 m/px) |
| 9 | maszt rurowy z odciągami | 6–8 odciągów, kotwienie w promieniu ok. 3–4 m | stal | ESTIMATED |
| 10 | maszt kratowy 3-nożny | 10–12 m (środkowy), 4–6 m | stal | SOURCED_SECONDARY (M57) |
| 11 | koryto kablowe drabinkowe | szer. 0,4–0,5 m, wzdłuż attyk do narożników | stal ocynkowana, jasna | ESTIMATED |
| 12 | wysięgnik/maszt narożny przy attyce | położenie: narożniki dachu | szary | VERIFIED_WIZJA (rzut) |
| 13 | rozmieszczenie sektorów | 3 × 120° — typowe przyjęcie | — | UNVERIFIED |

Nazwy producentów występują wyłącznie w URL. Kolumny opisu ich nie zawierają.

## 2. Dachy w Białymstoku

Wybór dachów oparłem na skrzyżowaniu dwóch źródeł:
- OSM: `man_made=mast|antenna|tower` w obrysie budynku;
- wykaz UKE (xlsx „stan na 2026-10-26”): adres stacji w Białymstoku dopasowany do budynków OSM z `building:levels` ≥ 8.

| dach | źródło | operatorzy (UKE) | rzut z ortofoto | wysokość masztu nad dachem |
|---|---|---|---|---|
| Skorupska 17 | OSM + UKE | B | rama X przez całą szerokość, maszt w środku z odciągami, koryta do narożników NE i SW | **UNVERIFIED** |
| Dobra 3 | OSM + UKE | A | skupisko wsporników i talerzy przy narożniku NW, rama z urządzeniami | UNVERIFIED |
| Zwierzyniecka 4 (11 kond., 34 m) | OSM (guyed_tube) | brak dopasowania | maszt w środku podwyższenia SE z odciągami | UNVERIFIED |
| Hallera 19 | OSM (tower) | brak | masztu nie rozpoznano | UNVERIFIED |
| Kopernika 5A / 7 (12 kond.) | UKE | B / A | skupiska szaf ok. 2 × 1 m | UNVERIFIED |
| wieżowiec przy Kwadrat Park | M57 (odsyłacz) | B, C | — | **10–12; 4–6** (SOURCED_SECONDARY) |

**Negatyw.** Na 8 innych blokach z ≥ 12 kondygnacjami masztów w rzucie nie ma. Były to Tysiąclecia 10A, Waszyngtona 36, Łąkowa 7, Kraszewskiego 45A/B, Mieszka I 11, Wąska 4, Wasilkowska 47 i Towarowa 8A. Ta próba jest nielosowa.

**Rozkład wysokości masztu nad dachem (min / mediana / max): NIE SPEŁNIONO.** Wartości z metodą są tylko dla 1 dachu (M57). Na pozostałych 5 dachach wysokości nie da się wiarygodnie odczytać z ortofoto: budynki są w nim przechylone, a cień masztu jest nieczytelny. Kadrów z boku nie pozyskałem (luka 1).

Kontekst prawny dla zakresu wysokości (nie jest to pomiar): instalacja radiokomunikacyjna na obiekcie budowlanym wymaga
- zgłoszenia, gdy ma **> 3 m i ≤ 12 m** (art. 29 ust. 3 pkt 3 lit. a Prawa budowlanego);
- niczego, gdy ma **≤ 3 m** (art. 29 ust. 4 pkt 3 lit. a).

Wieżowiec z M57 (10–12 m) mieści się w zakresie zgłoszenia.

## 3. Wygląd na tle nieba
**UNVERIFIED.** Nie ma obejrzanych kadrów z boku z odległości 100–200 m (luka 1). Opisy z M57 zostają w M57.

## 4. Przepisy i UKE
- **Wykaz UKE** ma kolumny: operator, nr decyzji, rodzaj, data ważności, dł./szer. geogr., miejscowość, lokalizacja (adres), IdStacji, TERYT.
  - **Nie zawiera wysokości anteny** ani azymutów.
  - W Białymstoku w 4 plikach (LTE800, LTE1800, GSM900, 5G3600) jest 419 wierszy i 124 lokalizacje.
  - Operatorów oznaczam A, B, C (bez nazw firm).
- **Prawo budowlane art. 29:** progi 3 m i 12 m, jak wyżej. Cytat ze standardyprawa.pl; potwierdzenie w ISAP nie zostało wykonane.
- **Rozporządzenie MI z 12.01.2021 w sprawie przeszkód lotniczych** (Dz.U. 2021 poz. 264):
  - § 35 ust. 1: przeszkoda < 45 m npt — światła małej intensywności typu A lub B na szczycie;
  - § 36: od 45 m — średniej intensywności;
  - § 46 ust. 1 pkt 1: zwolnienie z oznakowania dziennego budynków mieszkalnych i użyteczności publicznej, chyba że dominanta przewyższa budynek o ≥ 5 m.
  - Kolor świateł: rozporządzenie odsyła do Załącznika 14 ICAO, sam tekst go nie podaje.
  - Biało-czerwonego malowania nie widać na żadnym z obejrzanych dachów (rzut).

## 5. Kadry
Obejrzałem 16 wycinków ortofoto (80 m przy 0,1 m/px oraz 45 m przy 0,05 m/px), a także wycinek 2× do audytu.
- Kryterium „≥ 15 obejrzanych kadrów” jest spełnione **tylko jako ortofoto**.
- **Kadrów naziemnych 0.**
- Data arkusza ortofoto jest UNVERIFIED (mozaika WMS). Sezon z obrazu: wiosna. Cienie padają na NW.

## 6. Luki (uczciwie)
1. **Kadry naziemne niedostępne w tej sesji.**
   - Commons API i `upload.wikimedia.org` zwracały HTTP 429 („robot policy”), więc nie pobrałem m.in. „Antenna tower in Białystok (Cieszyńska/Kawaleryjska)”, „Waszyngtona 36 Białystok 2/3”, „Tysiąclecia 10A Białystok 1/2” ani zdjęć ulic Zwierzyniecka, Dobra i Kopernika.
   - Próba obejścia przez obcy CDN obrazów została zablokowana i jej nie ponawiałem.
   - KartaView API niedostępne (certyfikat). Panoramax nie ma pokrycia przy tych dachach.
   - Listę tytułów do pobrania wpisałem w `sources.md`.
2. Wysokości masztów nad dachem dla 5 dachów: UNVERIFIED.
3. Karty szaf zewnętrznych i anten radioliniowych 0,9/1,2 m nie zostały zweryfikowane.
4. Data arkusza ortofoto.

## 7. Samokontrola
Seed 20261115, próba 7/35. Wynik: **7 PASS, 0 FIX**.
- Ponownie pobrałem 2 karty i tekst art. 29.
- Ponownie obejrzałem 3 obrazy, w tym wycinek 2×.

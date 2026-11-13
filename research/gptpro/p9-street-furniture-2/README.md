# gptpro-p9-street-furniture-2 — research/g5-street-furniture (uzupełnienie)

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku 1:1 (OSM + GUGiK).
**Zadanie (P9):** wymiary mebli ulicznych Białegostoku z przetargów i norm; domknięcie luk z G5.
**Data wykonania:** 13.11.2026. Język: polski.

## Cel
Uzupełnić bazę wymiarów mebli ulicznych (ławki, kosze, stojaki, osłony drzew, bariery, słupki,
sygnalizatory, żerdzie energetyczne/oświetleniowe, hydranty, szafki gazowe i telekomunikacyjne,
przystanki) o wartości potwierdzone dokumentami, z licencjami dopuszczającymi użytek komercyjny.

## Metoda
1. Przeszukano BIP Białegostoku (UM, ZDM, ZMK), dokumenty przetargowe (PSMPT Piotrków Tryb. jako
   proxy), rozporządzenia (Dz.U. 2019 poz. 2311 + zał. 4), standardy zarządców dróg (ZDiUM Wrocław
   2022 — proxy, ZDM Warszawa STO TOS_1, ZDM Kraków 162/2025) oraz karty producentów
   (ZPUE, AKWA, Oldisvet, ANCO, KZA, Zano) — tylko fakty techniczne.
2. Każdy fakt w manifest.csv ma: URL, cytatu nie dłuższy niż 25 słów (lub numer punktu/strony),
   datę dostępu, licencję i autora. Wartości niepotwierdzone → UNVERIFIED, wyliczone z dowodów →
   ESTIMATED z metodą w uwagach.
3. Przystanki: zamiast niedostępnego załącznika 8 z G5 przyjęto numery inwentarzowe GTFS
   Białystok (stop_code); dopasowano je do węzłów OSM `highway=bus_stop` (zrzut API OSM dla bbox
   53,140–53,165 N; 23,150–23,185 E) po nazwie i odległości ≤ 30 m.
4. Zdjęcia: Wikimedia Commons geosearch (≤ 300 m od centrum kafla 53,152 N 23,168 E), miniatury
   1600 px JPG. Mapillary — brak tokenu/przeglądarki → zgodnie z zasadą A paczki 02 pozycje
   oznaczono UNVERIFIED (nie zgadnięto kluczy).
5. Paczka ZIP ≤ 80 MB; dokumenty PDF/XLSX tylko urzędowe ≤ 5 MB (zasada D); karty producentów —
   tylko linki w manifeście („tylko referencja, nie pobrano”).

## Najważniejsze ustalenia
- **Ławka (Białystok, DGK-IV.271.45.2015):** min. 1900×450×450 mm; beton + dąb/wiąz lakierobejca
  PALISANDER; deski ≥ 40 mm; podstawa grafitowa/jasnoszara. Dokument w paczce (P9-001.pdf).
- **Ławki/kosze wandaloodporne (Białystok 2019):** wykonawca Glasdon Europe AB (17 146,20 zł);
  model bez wymiarów w dokumentach → UNVERIFIED.
- **Kosz (proxy PSMPT):** stal ocynk. + proszek szary, pojemnik 35 l, daszek szary, słupek czarny
  z kotwą, mechanizm obrotu. **Stojak (proxy PSMPT):** 5-stanowiskowy, 148×38×26 cm, rura ø30/22,
  odstęp ~35 cm. **Ławka (proxy PSMPT):** 1900–2000×700–900×400–600 mm, rura ø50–60.
- **Stojaki ZMK Białystok (DZ.26.2.8.2026.JO):** rozstrzygnięte; OPZ to skan bez OCR — montaż
  „wbetonowanie” odczytany z fragmentu tekstu, pełne wymiary UNVERIFIED.
- **Bariery (wytyczne ZDM UM Białystok, 13.07.2018 — dokument w paczce):**
  - U-5a pylon: polietylen, wys. 90 cm, ø20 cm, podstawa 30 cm, RAL 1012;
  - panel „olsztyński”: słupki rura ø60,3 (ścianka 2–3,2 mm), przęsło ø48,3, RAL 1012;
  - U-12b łańcuchowe: słupki 1,10 m, rozstaw 1,50/1,80 m, strzałka łańcucha 0,10 m;
  - U-12: przęsło 2,50×0,83 m, 5 drutów płaskich 15×6 mm, druty pionowe ≥5 mm co 5 cm,
    słupki profil 60×40×1,5 (RAL 3020), panel RAL 1012;
  - słupek podznakowy: rura bezszwowa ø60,3 mm, ścianka ≥ 2,9 mm, kotwa.
- **Sygnalizatory:** zał. 4 rozporządzenia — soczewki S-1 ø200 mm, S-2 ø300 mm, strzałka 200 mm;
  skrajnia min. 2,20 m nad terenem (od 2003 r., rys. na s. 370 zał. 4 — wg wtórnego źródła
  zm.org.pl; oryginał to skan bez OCR). Proxy ZDiUM Wrocław 2022: sygnalizatory od dołu 2,50 m
  (maszty HY/słupy), 5,50 m (wysięgniki/bramy), skrajnia podwyższona 5,50 m; maszt HY wysoki do
  4,3 m (rura ø108), niski 1,5 m; wysięgnik do ~12 m. Producent z Białegostoku Oldisvet SS3ak:
  słupek H=5,8 m (63/265 mm).
- **Decyzje dla gry:** `signal_pole` 4,0 m (G5) → rekomendacja 4,3 m (maszt HY) lub 5,8 m (słupek
  SS3) — **skorygowano**; `signal_mast` 6,8 m (G5) → **niepotwierdzone**, głowka nad jezdnią
  powinna wisieć ≥ 5,50 m; `power_pole` 10 vs 12 m → w katalogu ZPUE **nie ma żerdzi „E-10”**
  (są 9,0 / 10,5 / 12,0 m) → rekomendacja E-12 (12,0 m; ø podstawy 0,398 m, wierzchołka 0,218 m).
- **Oświetlenie:** proxy (Rapio): parkingi/chodniki 4–6 m, drogi publiczne 8–10 m; zapis z G5
  „oprawy do 11 m” nie udało się ponownie potwierdzić (G5 niedostępne). STO ZDM TOS_1: słupy
  stalowe, ścianka ≥ 4 mm, uchwyt ø60–72 mm (dokument w paczce).
- **Hydrant nadziemny (AKWA typ 3000, DN80, PN-EN 14384):** H=1900/2150/2450 mm przy
  Rd=1250/1500/1800 mm; kolumna ø101,6×4,0 mm; RAL 3000/5015. **Wysokość nad gruntem ≈ 0,65 m**
  (ESTIMATED; metoda: H − Rd, spójne dla wszystkich trzech Rd; potwierdzenie kod Onninen
  10.080.250.1250 → HN3 H=1900, Rd=1250).
- **Szafka gazowa (proxy ANCO; operator w Białymstoku: PSG):** 600×600×250 mm, tworzywo
  trudnozapalne, RAL 7035, zamek trójkątny 9 mm.
- **Szafka telekomunikacyjna (proxy KZA Lublin):** 27U: 1200 (użytkowa)/1523 mm (całkowita bez
  fundamentu), 865×660 mm; 36U: 1600/1923 mm. Orange nie publikuje karty szafki naziemnej
  (dokument OPL dotyczy wyłącznie kanalizacji kablowej).
- **Osłona drzewa (proxy Zano 11.040):** krata ø 120/150/200 cm, grubość 4 cm, płaskowniki
  40×6/30×6/20×6, stal S235JR, 110 kg.
- **Przystanki:** 52 węzły OSM `highway=bus_stop` w bbox; **50/50 pewnych dopasowań** do GTFS
  (nazwa zgodna + odległość ≤ 30 m); 2 niepewne (literówka w nazwie OSM). Pełna tabela w P9-401.csv.

## Braki i niepewności
1. **Załącznik 8 z G5** (numery inwentarzowe przystanków) — niedostępny w środowisku; zastąpiono
   numeracją GTFS (stop_code). Kolumna `status_poprzedni` w większości wierszy = „G5 niedostępne”.
2. **Mapillary** — brak tokenu i przeglądarki; pozycje zdjęć z poziomu kierowcy (11 typów mebli)
   oznaczono UNVERIFIED zgodnie z zasadą A paczki 02. Zdjęcia Commons z kafla są z poziomu
   pieszego i zawartość merytoryczna (widoczność konkretnych mebli) nie została wizualnie
   zweryfikowana w sesji — status UNVERIFIED.
3. **Skany bez OCR** w BIP (OPZ ZMK, załączniki ZDM Białystok o numerach 99232/99308/36929/12790,
   t.j. Dz.U. 2019 poz. 2311 zał. 4, WR-D-72 GDDKiA) — brak narzędzia OCR w środowisku; tam, gdzie
   fragment tekstu był odczytalny, zacytowano go; resztę oznaczono UNVERIFIED.
4. **Serwery wi.wroc.pl / zdium.wroc.pl** nieosiągalne z sieci sesji — wytyczne ZDiUM Wrocław 2022
   pobrano przez Wayback Machine (29.07.2026, snapshot 20260707155954).
5. **Model ławek/koszy Glasdon** — dokumentacja przetargowa nie podaje modelu ani wymiarów.
6. **Rozkład wysokości latarni wg klas dróg w standardzie ZDM** — nie znaleziono w tej sesji
   tekstowego standardu z taką tabelą; podano proxy (Rapio + PN-EN 13201 jako kontekst) i
   oznaczono ESTIMATED. Zapis z G5 „oprawy do 11 m” nie został ponownie potwierdzony.
7. **Karta AKWA** ma uszkodzone mapowanie fontów — wymiary potwierdzono w sesji przed kompresją
   kontekstu oraz pośrednio stroną produktu (RAL 3000/5015, PN-EN 14384) i katalogiem Onninen.
8. Platformazakupowa.pl blokuje automatyczny dostęp (SWZ nowych przetargów za loginem).
9. Środowisko sesji zostało zresetowane w trakcie (utracono pierwotne pliki robocze) — wszystkie
   dokumenty w paczce pobrano ponownie i zweryfikowano 13.11.2026.

## Samokontrola 20% (zasada F)
- Seed losowania: **20261113** (Python `random.sample` na liście 100 pozycji manifestu).
- Próba: **20 pozycji** (20%): P9-002, P9-003, P9-004, P9-007, P9-009, P9-013, P9-015, P9-017,
  P9-023, P9-108, P9-109, P9-116, P9-120, P9-128, P9-133, P9-135, P9-140, P9-146, P9-151, P9-301.
- Wyniki (szczegóły w `audit_20_percent.json`):
  - 19/20 URL-i odpowiedziało HTTP 200; licencje zgodne z zapisem w manifeście;
  - 10 pozycji przystankowych: współrzędne z manifestu zgodne ze zrzutem OSM (±1e-6°);
  - P9-301 (zdjęcie Commons): współrzędne zgodne z metadanymi geosearch;
  - P9-015 (ZDiUM Wrocław): oryginalny URL nieosiągalny z sieci sesji (HTTP 000); kopia
    archiwalna pobrana wcześniej poprawnie i zweryfikowana treściowo (plik P9-004.pdf w paczce) —
    wynik: PASS z zastrzeżeniem.
- **Podsumowanie: 20/20 pozycji PASS (1 z zastrzeżeniem nieosiągalności serwera z sesji).**

## Zawartość paczki
- `README.md` — ten plik.
- `manifest.csv` — 100 wierszy (kolumny wg zadania + id, url_zrodla, licencja, autor,
  data_dostepu, status, status_poprzedni, zmiana, sezon, pora_dnia, uwagi).
- `files/` — dokumenty urzędowe (P9-001…007), zdjęcia JPG ≤ 1600 px (P9-301…306), tabela
  dopasowań przystanków (P9-401.csv). Karty producentów celowo NIE pobrano do paczki
  (zasada D + brak licencji komercyjnej poza faktami) — tylko linki w manifeście.
- `sources.md` — lista źródeł z datami dostępu.
- `audit_20_percent.json` — protokół samokontroli.

## GitHub
Brak prawa zapisu do repo woogitsugames/kamion w tej sesji → zgodnie z zasadą G dostarczono
wyłącznie plik ZIP `gptpro-p9-street-furniture-2.zip`.

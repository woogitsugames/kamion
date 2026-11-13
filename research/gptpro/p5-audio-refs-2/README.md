# gptpro-p5-audio-refs-2 — paczka audio-referencji dla projektu Kamion (część 2)

**Data wykonania:** 13–14 listopada 2026 (data dostępu do źródeł: 2026-11-13/14)
**Cel:** uzupełnienie paczki G9 (72 dźwięki Freesound + 7 z Wikimedia Commons) o brakujące kategorie dźwięków ciężarówki/autobusu: (1) retarder, (2) hamulec silnikowy dekompresyjny/wydechowy, (3) pneumatyka (osuszacz, ogranicznik, ostrzegacz), (4) zautomatyzowana skrzynia biegów, (5) silnik R6 diesel 12–13 l z nazwanym modelem, (6) kabina cab-over w jeździe, (7) foley wnętrza kabiny.

## Zawartość paczki

- `manifest.csv` — **83 pozycje** (P5-001…P5-083, ciągłe, bez luk), kolumny: id, kategoria, opis, długość_s, format, sample_rate, bit_depth, kabina_zewnetrz, freesound_id, jakosc_1_5, typ_silnika, oryginal, atrybucja, url_zrodla, licencja, autor, data_dostepu, status, uwagi.
- `files/` — **51 plików, łącznie 74 MB** (limit 80 MB zachowany): 43 podglądy MP3 HQ z Freesound, 7 oryginałów z Wikimedia Commons (OGG Vorbis/Opus), 1 fragment WAV 96 kHz/24 bit wycięty bezstratnie z oryginału OpenGameArt.
- `download_list.csv` — **59 pozycji** Freesound (id, URL, licencja, autor, plik_docelowy) do ręcznego pobrania ORYGINAŁÓW przez właściciela konta Freesound. Wykluczono pozycje NonCommercial (te są tylko w manifeście z dopiskiem „tylko referencja, nie pobrano”).
- `sources.md` — lista źródeł z datą dostępu.
- `audit_20_percent.json` — wynik samokontroli.

**Żadne z 72 ID Freesound z paczki G9 nie zostało powtórzone.** Konwencja ID: `P5-NNN` (tekst).

## Metoda

1. Przeszukano Freesound (wyszukiwarka + parsing stron dźwięków `freesound.org/s/<id>/` — tytuł, opis autora, licencja, długość, sample rate, bit depth), Wikimedia Commons (API, z uwzględnieniem rate limitu), OpenGameArt, katalog BBC Sound Effects (mirror na Internet Archive — tylko identyfikatory katalogowe jako referencja).
2. Z każdego źródła pobierano TYLKO pliki z licencją komercyjną: CC0, CC BY, CC BY-SA. Licencje NC — wyłącznie link w manifeście z dopiskiem „tylko referencja, nie pobrano”. BBC Sound Effects — wyłącznie linki (RemArc, licencja niekomercyjna; NIE pobierano).
3. Freesound bez zalogowania udostępnia tylko podgląd MP3 — pobrano podglądy HQ i wpisano `oryginal=NIE (podgląd MP3)`; pełna lista do pobrania oryginałów w `download_list.csv`. Pliki z Commons i OGA to oryginały (`oryginal=TAK`).
4. Długość każdej pozycji pobranej zmierzono własnym parserem (MP3: ramki MPEG 1/2/2.5 Layer III; Ogg: granulepos; WAV: RIFF) i porównano z deklaracją strony — automatyczny test MISMATCH. W manifeście długość pobranych plików = pomiar pliku (zgodny z odtwarzaczem); dla niepobranych = deklaracja strony.
5. Status UNVERIFIED nadano pozycjom, których opis autora nie potwierdza jednoznacznie treści (lub które są tylko analogiem/symulacją).

## Najważniejsze ustalenia

- **Kategoria 1 (retarder): WOLNE ŹRÓDŁA NIE ZAWIERAJĄ nagrania retardera hydrokinetycznego ani elektromagnetycznego** (przeszukano Freesound, Commons, OGA; pojęcie „retarder” w opisach nie występuje dla pojedynczych pojazdów). Najbliższy analog akustyczny: whine hamowania elektrycznego w trolejbusie (P5-001, Freesound 723106, CC0, UNVERIFIED jako odpowiednik). Dodatkowo: autobusy New Flyer z przekładnią Voith D864 mogą mieć retarder zintegrowany z konwerterem — w uwagach serii New Flyer zaznaczono „możliwy retarder integralny — UNVERIFIED”.
- **Kategoria 2 (hamulec silnikowy): brak nagrania pojedynczego pojazdu z kabiny/z zewnątrz.** Najlepsze dostępne: (a) fragment 20 s z nagrania autostrady I-15 (jake brake wielu ciężarówek w ruchu; wycięty bezstratnie WAV 96 kHz/24 bit z oryginału CC BY 4.0 na OpenGameArt — P5-002), (b) symulacja „Jbrake” wykonana w FL Studio wg International (P5-003, CC0, UNVERIFIED — dźwięk syntetyczny), (c) ambient uliczny z jake brake (P5-004, CC0).
- **Kategoria 3 (pneumatyka):** znaleziono spusty powietrza, syczenie zaworów, ostrzegacz ciśnienia, pneumatyczne drzwi. **Regeneracja osuszacza („psssst” cykliczne) — brak pewnego nagrania**: pozycja P5-013 jest UNVERIFIED (profil autora sugeruje osuszacz budowlany, nie pojazdowy). To najpoważniejsza luka kategorii 3.
- **Kategoria 4 (skrzynia biegów):** najlepsza seria to autobusy New Flyer D40LF/D40LFR (autor chungus43A, CC BY 4.0, 8 nagrań startów i jazdy) z silnikiem Cummins ISL (R6, 8,9 l) i przekładnią **Voith D864 — hydrokinetyczna (automat klasyczny), NIE zautomatyzowana skrzynia mechaniczna z przerwą momentu**. Uczciwie zaznaczono: **nagrania AMT (automatycznej skrzyni mechanicznej ze sprzęgłem i przerwą momentu) w wolnych źródłach nie znaleziono**; pozycje New Flyer są referencją dźwięku zmiany biegu przekładni hydrokinetycznej.
- **Kategoria 5 (silnik R6 12–13 l z NAZWANYM modelem): WPROST — nie znaleziono nagrania z nazwanym modelem silnika R6 o pojemności 12–13 l.** Najbliższe: **MAN D2566MUM** — R6, 11 413 cm³ (**11,4 l — poniżej dolnej granicy 12 l**), 176 kW, z autobusu MAN/Avtomontaža 1991 (Commons, Work With Sounds, CC BY 4.0, 3 pliki: silnik, klakson, drzwi). Dalsze: DAF (P5-030, producent UNVERIFIED — opis autora nie podaje modelu silnika), Scania K230UB (tylko referencja NC). W nazwach plików w ZIP nie ma marek (wymóg paczki); model silnika zapisano w kolumnach `opis`/`typ_silnika`/`uwagi`.
- **Kategoria 6 (kabina cab-over):** zamiast aut osobowych pozyskano: wnętrze **Volvo F4 Turbo** (start, jazda autostradą, stop — Beeld en Geluid, CC BY-SA 3.0, 8:20), wnętrze autobusu miejskiego w Monachium (CC0), polski **Solaris** (jak w flocie Białegostoku), **Mercedes-Benz 709D** (kabina nad silnikiem, jazda po oblodzonej drodze, CC0), Gillig (Cummins ISL9, CC BY-SA 4.0).
- **Kategoria 7 (foley wnętrza):** 33 pozycje — rzeczywiste sygnały cofania (backup beeper), gongi/ostrzeżenia kabiny, pasy bezpieczeństwa, drzwi kabiny (w tym pneumatyczne), wycieraczki (w tym z Forda Transit nagrane 192 kHz — do spowolnienia), przełączniki/stalki, nawiew, kierunkowskazy.
- Licencja Sonniss GDC (sprawdzono): *„Licensee may use and modify the licensed sound effects for personal and commercial projects without attribution to the original creator.”* (GDC Game Audio Bundle, wersja 2.0, effective 27.08.2026) — pozwala na użytek komercyjny, ale w pakiecie ostatecznie nie wykorzystano plików Sonniss (brak odpowiedników kategorii 1–4).

## Braki i niepewności

- Retarder (kat. 1) — **brak nagrania**; tylko analog UNVERIFIED (trolejbus).
- AMT z przerwą momentu (kat. 4) — **brak nagrania**; przekładnie hydrokinetyczne tylko.
- Silnik R6 12–13 l nazwany — **brak**; najbliższy MAN D2566MUM 11,4 l (poniżej zakresu o 0,6 l).
- Osuszacz powietrza (kat. 3) — pozycja P5-013 UNVERIFIED (prawdopodobnie osuszacz budowlany); regeneracji cyklicznej nie potwierdzono.
- Pozycje syntetyczne: P5-003 (hamulec silnikowy, FL Studio), P5-042 (backup beeper rysowany w Audacity) — referencje barwy/wzorca, nie nagrania terenowe.
- P5-058 — nagrzewnica pokojowa (3 prędkości), NIE pojazd — analog nawiewu.
- BBC Sound Effects — 12 pozycji tylko link (RemArc); strona bbcrewind.co.uk odpowiada (HTTP 200, tekst licencji potwierdzony), ale API/dane techniczne niedostępne z sandboxa — długości i parametry UNVERIFIED.
- Podglądy MP3 Freesound: jakość referencyjna (128–256 kbps); oryginały WAV/FLAC do pobrania z `download_list.csv`.
- Kolumny `sezon`/`pora_dnia` (obowiązkowe dla zdjęć w paczkach 02) **nie dotyczą paczki audio** — paczka nie zawiera zdjęć.
- Mapillary (zasada A paczek 02) — nieużyty w tej paczce (brak elementów wizualnych).

## Samokontrola (20 %, jawny seed)

- **Seed: 20261113**, metoda: `random.seed(20261113); random.sample(83, k=17)` — wylosowano 17 pozycji (≥20% wszystkich, nie tylko pobranych): P5-002, P5-003, P5-004, P5-007, P5-009, P5-013, P5-015, P5-017, P5-023, P5-039, P5-040, P5-047, P5-051, P5-059, P5-066, P5-073, P5-081.
- Sprawdzono dla każdej: (a) link działa — HTTP 200: **17/17 OK**; (b) licencja na żywo zgodna z manifestem: **17/17 OK** (P5-081/BBC: tekst RemArc potwierdzony na stronie); (c) długość: pozycje Freesound porównane z odtwarzaczem na stronie — zgodne; P5-002 (OGA) — pomiar lokalny RIFF; P5-081 (BBC) — UNVERIFIED (brak danych).
- Dodatkowo (poza losowaniem) sprawdzone wszystkie 7 pozycji Wikimedia Commons przez API: licencje **7/7 zgodne**.
- Wykryto i naprawiono błąd pomiaru długości dla podglądów MPEG-2 (16 kHz) — po poprawce P5-031: 126,5 s wobec 126,4 s na stronie (zgodnie z wymogiem zgodności z odtwarzaczem; w G9 tego typu błąd wystąpił jako 41 s vs 82 s).
- Pełne wyniki: `audit_20_percent.json`.

## GitHub

Brak prawa zapisu do repo `woogitsugames/kamion` z tego środowiska — zgodnie z zasadą F dostarczono wyłącznie ZIP.

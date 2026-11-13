# Przegląd paczek ZIP od ChatGPT 6 Pro: G9, G3, G2 (s16, 2026-11-13)

Przeglądający: agent geo-worldgen (tylko odczyt źródeł; nic nie uruchamiano z ZIP-ów). ZIP-y rozpakowane do osobnych katalogów `research/_incoming/{g9,g3,g2}/` (nieśledzone przez git, do usunięcia po scaleniu). Nic nie commitowano.

## Werdykty

| ZIP | Werdykt |
|---|---|
| G3 `gptpro-3-s8-signs.zip` | **IDENTYCZNY** z `research/gptpro/3-s8-signs/` (nic do dodania) |
| G2 `gptpro-2-next-regions.zip` | **IDENTYCZNY** z `research/gptpro/2-next-regions/` + 4 pliki celowo pominięte wcześniej (D01, D07, D08, D09); nic nie dodano |
| G9 `gptpro-9-audio-refs.zip` | **PRZYJĄĆ jako referencję, z zastrzeżeniami** (licencje czyste, prawdziwość 25/25 w próbie, ale pobrane są podglądy MP3, braki w kluczowych kategoriach) |

## 1. G3 i G2: porównanie z `research/gptpro/`

Metoda: SHA-256 każdego pliku, dla tekstów (md, csv, json, geojson) po normalizacji CRLF do LF (repo ma `text=auto`, więc w katalogu roboczym pliki mają CRLF; surowe hashe różnią się wszędzie z tego powodu).

- **G3:** 187 plików po obu stronach, 0 tylko w ZIP, 0 tylko w repo. Po normalizacji końców linii wszystkie 187 identyczne (w tym `files/G3-OSM010.osm`, różnica rozmiaru 70 B = 70 końców linii). Wniosek: ZIP = gałąź GitHub, żadnej poprawki.
- **G2:** 34 pliki wspólne, wszystkie identyczne po normalizacji. W ZIP są ponadto cztery pliki, których lider nie scalił z uzasadnieniem z poprzedniego raportu: `G2-D01.geojson` (2,6 MB, wycinek OSM, ODbL, opcjonalny), `G2-D07.pdf` (ogłoszenie Poczty Polskiej SA, licencja dyskusyjna), `G2-D08.png` (PNG wymaga LFS), `G2-D09.pdf` (4,6 MB, wyciąg zbędny przy D02). Zgodnie ze zleceniem nie kopiowano ich. W ZIP nie ma niczego nowego ani poprawionego względem gałęzi, więc zastrzeżenia z poprzedniego raportu (rekomendacja kafli, UNVERIFIED) pozostają.

## 2. G9 (nowe): przegląd

### 2.1 Format

README.md, manifest.csv, sources.md, files/: zgodne. Manifest ma 106 wierszy (BOM UTF-8 na początku, kolumna `id` jest czytana jako `﻿id`; importować z `utf-8-sig`). Kolumny: id, kategoria, opis, dlugosc_s, format, sample_rate, kabina_zewnatrz, freesound_id, jakosc_1_5, typ_silnika, url_zrodla, licencja, licencja_url, autor, data_dostepu, status, zrodlo, uwagi. Zawiera wszystkie kolumny wymagane przez zlecenie. Składa się z 79 pozycji Freesound (z tego 51 plików w ZIP, reszta tylko link), 7 z Commons (3 pobrane), 27 BBC (tylko link). Zgodność plików z manifestem: 51 plików w `files/` = 51 pozycji oznaczonych „w ZIP”, zero rozbieżności. Rozmiar 71,1 MB (limit 80 MB).

Drobiazgi: `G9-C01` ma literówki w opisie („zakolcu”, „sĄsiedztwo”); `sample_rate` dla Commons to UNVERIFIED (ffprobe: C01 8 kHz, C02/C03 44,1 kHz); numeracja bez G9-054, G9-033/034/045/048/049 wykluczone z ZIP (limit), pliki G9-033, 034, 045, 048, 049 nie istnieją w `files/` zgodnie z README.

### 2.2 Licencje

- W `files/` wyłącznie CC0 (32 pozycje), CC BY 3.0/4.0 (19 pozycji; po 4 w kategorii „kierunkowskaz”, „hamulce”, „kabina”), Commons: C01 CC0, C02/C03 CC BY 4.0. Skan: 0 wierszy z NC/ND/SA w pobranych; 0 wskazań na NC w `licencja_url`.
- BBC RemArc: 27 wierszy, wyłącznie link, nic nie pobrano. Zgodne ze zleceniem. Strony BBC nie dały się sprawdzić (WebFetch zablokowany dla `sound-effects.bbcrewind.co.uk`), więc opisy i długości B01–B27 pozostają niesprawdzone.
- CC BY-SA z Commons (K02, K03, K04 i inne): tylko link, poprawnie poza ZIP.
- Nazwy plików to same identyfikatory (G9-xxx), bez marek. Marki występują w tytułach/opisach u autorów (Ford LTL, Mack, Freightliner, Renault, Peterbilt, Toyota, Solaris, Tarpan), co README opisuje; tytuły stron Freesound nie wchodzą do gry.
- **Odchylenie, ważne:** zlecenie wymagało oryginałów bez konwersji. W ZIP są **podglądy MP3 z CDN Freesound** (ffprobe: MP3 48 kHz, ok. 180–185 kbps VBR, głównie stereo; oryginał G9-010 miał 96 kHz). Licencyjnie to bez znaczenia (CC pozwalają na kopie), ale do analizy widm i do gry potrzebne są oryginały (WAV/FLAC; Freesound wymaga darmowego konta). README to uczciwie opisuje.
- Licencje CC BY wymagają atrybucji: dopisać do `docs/LICENSES.md` i ekranu licencji w grze dopiero przy faktycznym użyciu; w manifeście brak gotowego tekstu atrybucji.
- Dwa pliki OGG (Commons) wymagają LFS wg `.gitattributes` (`*.ogg`); MP3 nie są objęte LFS, a razem to 71 MB do git.

### 2.3 Prawdziwość: próba 25 z 106 (23,6 %)

Wybór: seed 1113 (24 losowe) plus ręczne dobranie kategorii krytycznych, niezależnie od seed=42 autora. Sprawdzano na żywo (WebFetch) tytuł, autora, licencję, długość.

- Freesound, 23 pozycje: **23/23 zgodne co do autora, licencji i długości** (G9-003 49769 Attribution 3.0, 22,593 s; G9-004; 007; 008; 009; 010 (96 kHz potwierdzone, 4:15,7); 011; 012 (CC0; tytuł zawiera „engine brakes”, opisu brak); 013; 015; 021; 025; 027; 041; 043; 053; L05 (Attribution 4.0); L09; L11; L13; L16; L17; 006 438080). Opisy w manifeście zgodne z tytułami stron, w tym G9-L11 (tytuł pliku „caravan ambience”, lecz opis autora „ambience inside truck cab”, trasa Flensburg–Kiel: manifest poprawny).
- Commons, 2 pozycje: C01 CC0 (Ke4roh, 4,713 s) zgodne; **K03** (CC BY-SA 3.0, Edvvc) licencja zgodna, ale **długość 81,9 s, a w manifeście 41,0 s** (błąd w polu długości; ta pozycja i tak nie jest w ZIP).
- BBC (B05, B08, B09, B10, B17, B19, B22, B26 wylosowane): niesprawdzalne technicznie (serwer zablokowany dla narzędzia). Liczone jako niesprawdzone, nie jako błędne.
- Razem: 25 OK, 1 drobny błąd (K03 długość), 8 niesprawdzonych (BBC). Zmyśleń w licencjach nie stwierdzono. Samokontrola autora (21/21 po poprawkach, seed 42) wiarygodna.
- Pozostałe wątpliwości z opisu: tytuły wielu pozycji pokazują nagrania **aut osobowych/busów**, nie ciężarówek (G9-014 Toyota, 038–040 auta, 046–048 auta, 050–053 auta, L07/L08/L12–L17). To akceptowalna referencja dla opon, deszczu i dylatacji, ale nie dla silnika ciężarówki.

### 2.4 Jakość i przydatność dla audio gry

Kontekst: `docs/08_AUDIO.md` (CC0/CC BY, zakaz nagrań silników konkretnych marek z gier/filmów/YouTube), ADR 0137/0148/0156 (zestaw ElevenLabs jest decyzją właściciela, silnik zostaje; zestaw syntezy zostaje; analiza spektrogramów i ucho właściciela przesądzają).

Co G9 daje realnie:
- **Referencja widmowa wnętrza kabiny:** G9-010 (CC0, 96 kHz, 4:15, ciężarówka w jeździe, ocena autora 5) i G9-L11 (CC BY, kabina, trasa Niemcy; w ZIP go nie ma, link). Najlepsze z całej paczki, ale to nie R6 13 l, ani model znany.
- **Silnik ciężarówki z zewnątrz pod obciążeniem:** G9-006 (260 s), 007, 008, 005 (CC0) do porównania charakteru narastania i wibracji; przydatne do kalibracji `engine_synth.py` i do oceny, czy zestaw ElevenLabs jest za „czysty”. To głównie ciężarówki amerykańskie (Mack, Freightliner), więc inny charakter niż europejski R6.
- **Pneumatyka:** G9-015 (spust, 96 kHz), 016, 018, 019, 021 oraz sprężarka 022/023/024 dają porównanie spustu i pracy sprężarki. Większość to autobusy/śmieciarki, nie ciągnik z naczepą.
- **Dylatacja wiaduktu:** 041, 042 (zewnątrz), 043 (kabina, auto), dobra para „zjawisko z zewnątrz vs w kabinie”; ciężarówki nie są wyróżnione.
- **Opony mokre/suche, deszcz na dachu, ekspresówka, ruch miejski z kabiny:** użyteczne jako tła i do kalibracji widm; wszystkie z aut osobowych/busów, bez ciężarówek. Dla gry lepsze byłoby wygenerowanie własnymi narzędziami warstw i użycie tych nagrań jako celu spektralnego niż wprost jako asset.
- **Kierunkowskaz, sygnał cofania:** 025, 026, 027, 031 itd. bez problemu (gra ma już własną syntezę sygnałów; kliknięcie przekaźnika z ciężarówki byłoby lepsze).

Braki (README je uczciwie wymienia):
- **Retarder: 0 pozycji.** G9-L04 (śmieciarka, 2/5) to UNVERIFIED.
- **Hamulec silnikowy: 0 pewnych.** G9-012 to ruch uliczny z „engine brakes” w tytule autora, bez opisu; G9-L19 (23 min) i G9-044 także UNVERIFIED. ADR 0137 notuje, że ElevenLabs ma „hamulec wydechowy, retarder” jako zdarzenia, więc tu brak jest realny.
- **Osuszacz powietrza:** brak.
- **Zautomatyzowana skrzynia:** brak (G9-013 to dźwignia, G9-014 auto osobowe).
- **R6 13 l:** brak potwierdzonego typu silnika w jakimkolwiek opisie.
- **Pliki:** podglądy MP3 zamiast oryginałów.
- Jakość 1–5 jest subiektywna autora (22 pliki w ZIP z oceną ≥ 4).

Użyteczność: **średnia** (referencja widmowa dla opon, deszczu, wiaduktów i ciężarówki z zewnątrz pod obciążeniem; do użycia w grze wprost nie nadaje się bez pobrania oryginałów i weryfikacji na słuch). BBC „Articulated Lorry 1976” (27 linków, RemArc) to najlepsza referencja wnętrza i zewnątrza ciągnika z naczepą, ale tylko do odsłuchu i widm przez właściciela, bez pobierania do repo.

### 2.5 Porównanie z gałęzią `gptpro/9-audio-refs`

Gałąź (fetch, tylko odczyt) ma 4 pliki: README.md, manifest.csv, sources.md (identyczne z ZIP po normalizacji CRLF, hash zgodny) oraz `UWAGA_GITHUB.md` (informacja, że 51 plików audio nie weszło do gita, bo narzędzie MCP przyjmuje tylko tekst). Pliki audio są tylko w ZIP. `UWAGA_GITHUB.md` nie skopiowano (zbędne).

### 2.6 Co scalono

`research/gptpro/9-audio-refs/` = cała zawartość ZIP bez zmian (README.md, manifest.csv, sources.md, `files/` 51 plików audio, 71 MB). Wszystkie pobrane pliki mają poprawną licencję (CC0 lub CC BY), więc nic nie wycięto; reszta (27 BBC, 4 Commons BY-SA, 19 Freesound link-only) jest w manifeście tylko jako link. **Decyzja dla lidera:** 71 MB audio w gicie. Rekomendacja: albo dodać `*.mp3` do Git LFS jak `*.wav/*.ogg`, albo nie commitować `files/` (trzymać lokalnie i w `docs/LICENSES.md` zapisać tylko manifest), bo MP3 to i tak podglądy, a do gry potrzebne są oryginały.

## 3. RESEARCH-PACK-02

Plik: `docs/owner/RESEARCH-PACK-02.md`. Dziesięć samodzielnych bloków (zasady z GPT-PRO-RESEARCH-01 skopiowane do każdego, plus dodatkowe zasady A–G wynikające z tego przeglądu: ręczny Mapillary przez przeglądarkę, drugi sezon, share-alike Mapillary, JPG zamiast PNG, spójne id, losowanie 20 % z seedem na wszystkich pozycjach, gałąź `research/<nr>-<slug>`):

| Blok | Zlecenie | Treść |
|---|---|---|
| P1 | G1 (nieoddane) | zdjęcia trasy z wysokości kabiny, ≥ 3 ujęcia/ulicę w obu kierunkach, ronda/wiadukty ≥ 6, drugi sezon, kolumny sezon/pora dnia |
| P2 | G6 (nieoddane) | nawierzchnie, krawężniki, oznakowanie poziome; tabela szerokości linii z rozporządzenia |
| P3 | G4 (nieoddane) | typologia zabudowy z dowodami i porównaniem z LoD1 GUGiK |
| P4 | G8 (nieoddane) | R48, R104/R70, R46, R58/R73, 96/53/WE, tablice PL; tabele z punktem przepisu |
| P5 | G9 uzupełnienie | retarder, hamulec silnikowy, osuszacz, AMT, R6 13 l, kabina ciężarówki cab-over, foley kabiny; oryginały albo `download_list.csv`; lista 72 już posiadanych id Freesound |
| P6 | G2 uzupełnienie | kafle Dojlidy/Krywlany/Fabryczna/północ DK8 w EPSG:2180, zamknięcie UNVERIFIED (WIM RS16, Panattoni, Biazet, TED, S19, MOP Haćki), trasy dojazdu z OSM, bramy z ortofoto GUGiK |
| P7 | G3 uzupełnienie | stan 2025–2026, oś czasu bramownic Andersa 2019–2026, DK19/DK65/S19, bezpośrednia kontrola 25 pozycji na Mapillary |
| P8 | G10 uzupełnienie | skrajnie wiaduktów (Putra), lista e-TOLL, aktualność planu UM 2018, sprzeczne tagi OSM, tagi do grafu gry |
| P9 | G5 uzupełnienie | kosze, ławki, szafki, sygnalizatory, żerdzie, hydranty, współrzędne przystanków |
| P10 | G7 uzupełnienie | rejestr drzew (albo gotowy wniosek o informację publiczną, niewysyłany), drugi sezon, żywopłoty, młode drzewa przy Andersa |

Braki w oddanych zleceniach, które pokrywają bloki P5–P10 (źródła w przeglądach): G9 (retarder, osuszacz, AMT, oryginały), G2 (rekomendacja kafli, WIM, niesprawdzone źródła), G3 (aktualność, DK19/65, epoki bramownic, Mapillary niesprawdzone), G10 (skrajnia, e-TOLL, plan 2018), G5 (5 UNVERIFIED, 11 ESTIMATED), G7 (rejestr drzew, jeden sezon).

## 4. Ograniczenia przeglądu

- BBC Sound Effects: serwer niedostępny dla narzędzia, 27 pozycji tylko jako link, bez weryfikacji.
- Nie odsłuchiwano plików (analiza widm poza zakresem); sprawdzono tylko nagłówki ffprobe (kodek, częstotliwość, długość).
- Nie oceniano, czy poszczególne pliki trafiają w charakter europejskiego R6 13 l (żaden opis tego nie potwierdza).
- G2/G3: nie ponawiano kontroli prawdziwości (identyczne z już przejrzanymi).
- Nie zmieniano `docs/LICENSES.md` ani `docs/adr` (poza zakresem; lider).

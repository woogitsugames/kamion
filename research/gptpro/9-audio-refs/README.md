# G9 — Nagrania referencyjne dźwięków ciężarówki z naczepą i otoczenia (audio-refs)

Projekt: **Kamion** — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku 1:1 (OSM/GUGiK).
Cel zadania: zebrać nagrania referencyjne (do porównania widm i ewentualnego użycia) dźwięków ciężkiej
ciężarówki z naczepą oraz otoczenia drogowego: silnik diesla R6 ~13 l (bieg jałowy i pod obciążeniem,
kabina/zewnątrz), hamulec silnikowy, retarder, zautomatyzowana skrzynia biegów, hamulce pneumatyczne
(spust, „psyknięcie”, osuszacz), sprężarka, kierunkowskaz w kabinie, sygnał cofania, opony na mokrym
i suchym, przejazd po dylatacji wiaduktu, ruch miejski i ekspresówka z kabiny, deszcz na dachu kabiny.

Data dostępu do wszystkich źródeł: **2026-11-12**.

## Zawartość pakietu

- `README.md` — ten plik.
- `manifest.csv` — **106 pozycji**: 48 plików Freesound pobranych do ZIP, 5 pozycji Freesound wykluczonych
  z ZIP (limit 80 MB — tylko referencja), 3 pliki Wikimedia Commons pobrane (CC0/CC BY), 19 pozycji
  Freesound tylko-link, 4 pozycje Commons tylko-link (CC BY-SA — poza zakresem ZIP), 27 pozycji BBC Sound
  Effects tylko-link (licencja RemArc — nie pobierano). Kolumny: id, kategoria, opis, dlugosc_s, format,
  sample_rate, kabina_zewnatrz, freesound_id, jakosc_1_5, typ_silnika, url_zrodla, licencja, licencja_url,
  autor, data_dostepu, status, zrodlo, uwagi.
- `files/` — **51 plików audio** (48 MP3 z Freesound, 3 OGG z Commons), razem ~71,5 MB.
- `sources.md` — lista wszystkich źródeł z datą dostępu.

Rozkład licencji w manifeście: CC0 — 50 pozycji, CC BY 3.0/4.0 — 26, CC BY-SA — 3 (tylko link),
RemArc (BBC) — 27 (tylko link). Do ZIP trafiły wyłącznie pliki CC0 i CC BY (zgodnie ze specyfikacją G9).

## Metoda

1. **Freesound** — przeszukiwanie strony freesound.org (zapytania: truck idle, diesel engine cab,
   air brakes, air dryer, retarder, jake brake, turn signal, reverse beeper, highway rain, expansion
   joint itd.). Dla każdego trafienia pobierano stronę dźwięku i wyciągano metadane: tytuł, opis,
   licencję (link `creativecommons.org`), długość, format, częstotliwość próbkowania, rozmiar pliku,
   URL podglądu HQ. Kryterium włączenia: licencja CC0 lub CC BY oraz zgodność z kategorią zadania.
2. **Wikimedia Commons** — API (`action=query`, `prop=imageinfo`, `iiprop=extmetadata`) — metadane
   licencyjne (`LicenseShortName`) i pliki audio (.ogg). Do ZIP pobrano tylko CC0 i CC BY; CC BY-SA —
   tylko link (specyfikacja G9 dopuszcza do ZIP wyłącznie CC0/CC BY, węższa niż ogólna reguła projektu).
3. **BBC Sound Effects** — katalog sound-effects.bbcrewind.co.uk przeszukany API
   (`sound-effects-api.bbcrewind.co.uk/api/sfx/search`). Licencja RemArc (personal/educational use)
   **nie zezwala na użycie komercyjne** — zgodnie z zadaniem podano wyłącznie linki, nic nie pobrano.
4. Selekcja, ocena jakości (subiektywna skala 1–5 wg przebiegu testowego, zakresu częstotliwości
   i „użyteczności” dla symulacji), przypisanie kategorii i typu silnika.
5. Walidacja programistyczna manifestu (liczba kolumn, URL-e, licencje) + samokontrola 20% (niżej).

## Odchylenie od specyfikacji — podglądy HQ zamiast oryginałów (ISTOTNE)

Oryginalne pliki Freesound (WAV/FLAC) wymagają zalogowania (darmowe konto) — bez klucza API dostępny
jest wyłącznie publiczny podgląd HQ (MP3 ~128 kbps) z CDN Freesound. Do ZIP pobrano **podglądy HQ MP3**
zamiast oryginałów. Jest to odchylenie od wymogu „oryginalne pliki, bez konwersji”, wymuszone
technicznie; **licencyjnie nieszkodliwe** (CC0 i CC BY zezwalają na transkodowane kopie), ale przed
użyciem w grze należy pobrać oryginalne bezstratne pliki z Freesound (wymagane darmowe konto; CC BY —
pamiętać o atrybucji). W manifeście kolumny `format`/`sample_rate` opisują **oryginał** ze strony
dźwięku, a kolumna `uwagi` zaznacza postać pobranego pliku.

## Najważniejsze ustalenia

- **Perła katalogu: seria BBC „Articulated Lorry: 1976 Diesel”** (G9-B01–B27) — professionalnie
  nagrane wnętrze kabiny i zewnątrz: idle, jazda, hamulce pneumatyczne, sygnały. Licencja RemArc
  uniemożliwia użycie komercyjne, ale seria to bezcenna referencja do porównania widm (tylko linki).
- **FS 433871 (CC0)** — jazda z kabiny ciężarówki, nagranie 96 kHz — najlepsza baza do analizy widm
  wnętrza kabiny w tym, co pobrano.
- **FS 438080 (CC0)** — sekwencja przejazdów ciężkiej ciężarówki z bliska (diesel pod obciążeniem,
  zewnątrz) — referencja charakteru silnika pod obciążeniem.
- **Dylatacje wiaduktu**: FS 241011 i 866213 (mosty metalowe, zewnątrz, CC0) + FS 521767
  (z kabiny, CC0) — dobra para „zjawisko z zewnątrz vs w kabinie”.
- **Hamulce pneumatyczne**: kilkanaście pozycji CC0/CC BY pokrywa spust, „psyknięcie” i pracę
  sprężarki (m.in. FS 455305 — sprężarka + zawór na końcu cyklu).
- **Sygnał cofania**: pewne pozycje CC0 (m.in. Back-up beeper.ogg z Commons, CC0) — kategoria
  pokryta dobrze.
- **Opony mokre/suche, deszcz na dachu, ruch miejski i ekspresówka z kabiny** — pokryte licznymi
  nagraniami CC0/CC BY (kategorie: opony_mokre 7, opony_suche 5, deszcz_dach_kabiny 6,
  ruch_miejski_kabina 6, ekspresowka_kabina 6, ekspresowka_zewnatrz 4).

## Braki i niepewności

- **Retarder — BRAK pozycji** w Freesound, Commons i BBC (zapytania: „retarder”, „Telma”,
  „auxiliary brake”). Kategoria niepokryta; jedyny kandydat G9-L04 (FS 717867, UNVERIFIED) ma
  charakter dźwięku niepotwierdzony. Do nagrania we własnym zakresie lub pozyskania inaczej.
- **Osuszacz powietrza** — brak dedykowanego nagrania; najbliższy odpowiednik G9-023 (FS 455305,
  sprężarka + zawór na końcu) — status UNVERIFIED dla tej funkcji.
- **Hamulec silnikowy** — brak pewnego nagrania; pośrednie kandydaty (G9-012 FS 451149,
  G9-044 FS 508058, G9-L19 FS 631966, G9-L04 FS 717867) — status UNVERIFIED.
- **Typ silnika R6 ~13 l** — w żadnym opisie źródłowym nie potwierdzono rzędowej szóstki 13 l;
  wszędzie „diesel (model nieznany)”. Kolumna `typ_silnika` opisuje wyłącznie to, co wynika
  z opisu autora nagrania.
- **Zautomatyzowana skrzynia biegów** — brak nagrania konkretnie zmiany biegów automatycznej
  skrzyni ciężarówki; kategoria skrzynia_biegow (2 pozycje) zawiera ogólne przejazdy ze zmianami
  biegów słyszalnymi z zewnątrz.
- **Marki w tytułach** — pozycje z marką producenta w opisie (FS 435656 „Ford LTL 9000” — G9-002,
  FS 669417 „Mack” — G9-008, FS 637921 „Mack/Peterbilt” — G9-017, FS 165168 „Freightliner” — G9-011,
  FS 425839 „Renault” — G9-029) mają adnotację w `uwagi` — marka w opisie/nazwie nie rodzi roszczeń
  licencyjnych (licencje CC0/CC BY obejmują utwór), ale jeśli nazwa marki jest istotna np. dla
  znaków towarowych — traktować jako referencję referencyjną, nie asset finalny.
- **Jakość 1–5** — ocena subiektywna autora researchu (przebieg testowy, zakres widma, szum tła),
  nie mierzalna metryka.
- Wiersze z pustym `typ_silnika` — autor nagrania nie podał typu silnika w opisie.

## Samokontrola (wymóg: losowe 20% pozycji)

Wykonano 2026-11-12. Losowo (deterministycznie, seed=42) wybrano **21 z 106 pozycji** (≈20%):
G9-004, G9-005, G9-012, G9-014, G9-015, G9-018, G9-026, G9-028, G9-029, G9-030, G9-032, G9-036,
G9-B03, G9-B08, G9-B16, G9-C02, G9-K01, G9-K03, G9-L09, G9-L14, G9-L16.

Sprawdzono: (a) URL `url_zrodla` zwraca HTTP 200, (b) licencja na żywej stronie/API zgadza się
z `licencja` w manifeście.

**Wynik: 21/21 OK po poprawkach.** Podczas kontroli wykryto i naprawiono 2 błędy:

1. **G9-L05** (FS 867375) — w manifeście pusta licencja (brak metadanych w scrapie). Pobrano stronę
   dźwięku i potwierdzono **Attribution 4.0** (creativecommons.org/licenses/by/4.0/) — manifest
   poprawiony.
2. **G9-L09** (FS 155379) — URL z niezakodowaną spacją („cognito perceptu”) powodował błąd HTTP.
   Poprawiono na `cognito%20perceptu` — HTTP 200, licencja CC0 potwierdzona na stronie.

Dodatkowo: początkowy test licencji Commons nie umiał odczytać `LicenseShortName` (błąd parsowania
API — pole zagnieżdżone w `value`); po poprawieniu parsera wszystkie 3 wylosowane pozycje Commons
(G9-C02, G9-K01, G9-K03) potwierdziły licencje zgodne z manifestem (CC BY 4.0, CC BY 3.0,
CC BY-SA 3.0).

## Uwagi końcowe

- Limit 80 MB ZIP: 5 największych plików (G9-033 FS 398859, G9-034 FS 648786, G9-045 FS 149429,
  G9-048 FS 582529, G9-049 FS 35051) wykluczono z ZIP — w manifeście z dopiskiem
  „tylko referencja, nie pobrano do ZIP (limit 80 MB)”.
- BBC RemArc i Commons CC BY-SA: wyłącznie linki w manifeście — nic nie pobrano.
- Pliki w ZIP nie były konwertowane poza pobraniem podglądów HQ (patrz sekcja „Odchylenie”).

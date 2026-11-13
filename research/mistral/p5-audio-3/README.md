# mistral-p5-audio-3 — paczka audio-referencji M55 (3. podejście do luk dźwiękowych Kamion)

**Data wykonania:** 13 listopada 2026 (data dostępu do źródeł: 2026-11-13, UTC)
**Cel:** trzecie (po G9 i P5) podejście do pięciu kategorii nagrań dla komercyjnego symulatora ciężarówki, tylko licencje komercyjne: (1) retarder hydrokinetyczny/elektromagnetyczny w ciężarówce lub autobusie — z kabiny i z zewnątrz; (2) hamulec silnikowy (dekompresyjny/wydechowy) pojedynczego pojazdu — z kabiny i z zewnątrz, z prędkością/biegiem; (3) zautomatyzowana skrzynia mechaniczna (AMT) z przerwą momentu przy zmianie biegu — wnętrze i zewnątrz; (4) silnik R6 diesel 12–13 l z NAZWANYM modelem (rozruch, jałowy, obciążenie, rozpędzanie); (5) cykliczna regeneracja osuszacza powietrza w pojeździe („psssst” co kilkadziesiąt sekund) i zawór zabezpieczający/ogranicznik ciśnienia.

**Deduplikacja:** żadne ID Freesound ani plik z paczek `research/gptpro/9-audio-refs` (72 ID FS + pliki Commons) i `research/gptpro/p5-audio-refs-2` (64 ID FS + 7 plików Commons) nie został powtórzony — sprawdzono 135 ID Freesound oraz wszystkie URL-e Commons obu paczek. W szczególności **celowo pominięto** duplikaty bliskie: Solaris Urbino 18/12 Hybrid „engine sounds Szczecin” (już w G9), „Het rijden van een vrachtwagen” (już w P5), „WWS City Bus MAN SG 220 – engine” z nazwanym silnikiem MAN D2566MUM R6 11 413 cm³ (już w P5), serię New Flyer D40LF/D40LFR (MiWay) 833735–833748 (już w P5), 803768 MAN/Solaris (już w P5), 659579 valimaa Scania (już w P5).

## Zawartość paczki

- `manifest.csv` — **13 pozycji** (M55-001…M55-013, ciągłe, bez luk), kolumny identyczne jak w `research/gptpro/p5-audio-refs-2/manifest.csv`: id, kategoria, opis, dlugosc_s, format, sample_rate, bit_depth, kabina_zewnetrz, freesound_id, jakosc_1_5, typ_silnika, oryginal, atrybucja, url_zrodla, licencja, autor, data_dostepu, status, uwagi. Kolumna `opis` to parafraza opisu autora skrócona do ≤25 słów; kluczowe cytaty autora w `uwagi`.
- `files/` — **13 plików, łącznie 74,8 MB** (NIE w repo — ignorowane przez `.gitignore`): 8 podglądów MP3 HQ (128 kbps) z Freesound + 5 oryginałów Ogg Vorbis z Wikimedia Commons.
- `mistral-p5-audio-3-files.zip` — archiwum `files/` dostarczone **poza git** (lokalizacja w opisie PR) — zgodnie z konwencją paczki `research/mistral/p1-route-photos-2`.
- `download_list.csv` — **8 pozycji** Freesound (id, URL, licencja, autor, plik_docelowy) do ręcznego pobrania ORYGINAŁÓW przez właściciela konta Freesound.
- `sources.md` — źródła z datą dostępu i pełną listą zapytań (również negatywnych).
- `audit_20_percent.json` — wynik samokontroli (seed 20261113).

## Metoda

1. Przeszukano Freesound (wyszukiwarka HTML z filtrem licencji + strony dźwięków `freesound.org/s/<id>/`), Wikimedia Commons (API `imageinfo` + `extmetadata`, z odstępami dla rate limitu), OpenGameArt, Sonniss GDC Bundle (listowanie plików wszystkich bundli 2015–2026 przez mirory Internet Archive), archive.org (biblioteki SFX z jawnymi licencjami), Openverse audio (wyczerpany limit anonimowy).
2. Z każdego źródła brano TYLKO pliki z licencją komercyjną: CC0, CC BY, CC BY-SA. NC/ND — pominięte; RemArc (BBC) — nie wystąpił w wynikach; Pegaso Z-207 1957 na archive.org ma licencję Public Domain Mark 1.0 (poza białą listą CC0/BY/BY-SA) → tylko wzmianka referencyjna w sources.md.
3. Freesound bez zalogowania daje tylko podgląd MP3 — pobrano podglądy **HQ (128 kbps)**, oryginały wpisano do `download_list.csv` (`oryginal=NIE (podgląd MP3 HQ)`). Pliki Commons to oryginały (`oryginal=TAK`).
4. Długość KAŻDEGO pobranego pliku zmierzono własnym parserem (MP3: ramki MPEG 1/2/2.5 Layer III z poprawną tabelą bitrate L3; Ogg Vorbis: granulepos ostatniej strony / sample rate z nagłówka) i porównano z deklaracją strony — wyniki w `uwagi` i w audycie. Wykryto i naprawiono błąd własny: błędna tabela bitrate MPEG1 (tabela Layer II zamiast Layer III) dawała ~50% zaniżone czasy — po poprawce wszystkie pomiary zgodne ±1 ramka.
5. Status UNVERIFIED nadano pozycjom, których opis autora nie potwierdza jednoznacznie treści wymaganej przez kategorię (lub które są tylko analogiem akustycznym); SOURCED — treść potwierdzona opisem autora (M55-013).

## Najważniejsze ustalenia (per kategoria)

- **Kategoria 1 (retarder): NEGATYW — potwierdzony po raz trzeci.** Pojęcie „retarder” nie występuje w opisach autorów dla pojedynczych pojazdów w żadnym z 6 dozwolonych źródeł (Freesound: 0 trafień; Commons: 0/913 tytułów; OGA/Sonniss/IA/Openverse: 0). Najbliższy NOWY analog: **Orion VII Hybrid-Electric** (M55-011, Commons, CC BY-SA 2.5, 5:33 jazdy) — hamowanie elektrogeneracyjne hybrydy o barwie zbliżonej do retardera elektromagnetycznego (UNVERIFIED, NIE jest retarderem). Uzupełnia analog trolejbusowy P5-001.
- **Kategoria 2 (hamulec silnikowy pojedynczego pojazdu): NEGATYW.** „jake brake” na Freesound → 2 wyniki śmieciowe; „engine brake”/„exhaust brake” → wyłącznie tła wielopojazdowe lub niepojazdowe. Nowe najbliższe analogi: **M55-001** (kyles, CC0: ciężarówka — jałowy, spust powietrza, przejazd z gazem, zwolnienie do zatrzymania; UNVERIFIED) i **M55-009** (Beeld en Geluid, CC BY-SA 3.0: hamowanie do zatrzymania + wyłączenie silnika z WNĘTRZA — hamowanie służbowe, nie silnikowe; UNVERIFIED). Zestaw z P5 (I-15 jake brake wielopojazdowy, symulacja FL Studio) pozostaje najlepszym materiałem.
- **Kategoria 3 (AMT z przerwą momentu): NEGATYW — żaden autor nie potwierdza AMT.** Nowi kandydaci: **M55-002** — THACO Bluesky 120S|Volvo B8R (Freesound, CC0, **22:00 jazdy autostradą z kabiny**, autor: „occasional gear shifts”; B8R fabrycznie z I-Shift, ale autor nie nazywa skrzyni → UNVERIFIED — najbliższy kandydat na AMT w wolnych źródłach w ogóle) oraz **M55-003** — digifishmusic CC BY 4.0 (3:09 z kabiny, „lots of gearbox whine”, ~80 km/h, zwalnianie na rondach; typ skrzyni nie podany → UNVERIFIED). Wcześniej znane Voith D864 (New Flyer) to przekładnia hydrokinetyczna — bez przerwy momentu.
- **Kategoria 4 (R6 diesel 12–13 l z NAZWANYM modelem silnika): NEGATYW.** Po wykluczeniu duplikatu MAN D2566MUM (11,4 l — P5) w wolnych źródłach NIE MA nowego nagrania z nazwanym modelem silnika R6 12–13 l. Nowe pozycje z nazwanym MODELEM POJAZDU (nie silnika): **Volvo 8900 ×3** (M55-005…007, valimaa, CC0, drive-by z zewnątrz, Tampere), **Nissan Diesel P-DA66U** (M55-012, Commons, CC BY-SA 3.0, 23:48 jazdy autobusem szosowym Hokkaidō), **International MaxxForce** (M55-004, CC0 — rodzina silników; odmiana 13 to R6 12,4 l, ale autor nie precyzuje wersji → UNVERIFIED), **THACO/Volvo B8R** (M55-002). Wszystkie UNVERIFIED dla wymogu „nazwany model silnika 12–13 l”. Dodatkowo przydatne sekwencje bez nazwania silnika: rozruch→jałowy→odjazd z zewnątrz (M55-010), jałowy z zewnątrz (M55-008).
- **Kategoria 5 (regeneracja osuszacza „psssst” + zawór zabezpieczający/ogranicznik): NEGATYW — potwierdzony po raz trzeci.** „air dryer”/„air dryer purge”/„spitter valve”/„air tank purge” na Freesound → 0 pojazdowych (spitter valve = tylko pociągi); Commons → 0/913 (kompresory tylko przemysłowe/tramwajowe/wymowy Lingua Libre); OGA/Sonniss/IA → 0. Najbliższy materiał pozostaje P5-013 (UNVERIFIED, osuszacz budowlany). Jedyne powiązane nagrania w paczce: spusty hamulca pneumatycznego w M55-001/M55-009.
- **Dodatkowo (poza kategoriami):** M55-013 — Ford AA (1931), przejazdy zewnętrzne 40 km/h (jedyna pozycja z prędkością podaną przez autora; SOURCED).
- **Sonniss GDC (sprawdzono wszystkie bundle 2015–2026, ~34 tys. plików audio):** brak odpowiedników kategorii 1–5 (najbliższe: FLYSOUND URAL 4320 V8 diesel, M1 Corbitt, Chevrolet Silverado tow truck, „Interior Ambiance Of A Moving Bus” — żaden nie spełnia kryteriów). Licencja pozwala na użytek komercyjny bez atrybucji (cytat w sources.md) — ale w paczce nie wykorzystano plików Sonniss.
- **Przeglądnięte, odrzucone (bez powtórzenia w manifeście):** JR shikoku bus P-MS725SAkai (Commons, CC BY 3.0, 36:31, 41,5 MB — wartość dublowana przez M55-012, zbyt duży), „A ride on 102-Road Bus in Fanhe Town” ×2 (CC BY-SA 4.0, FLAC 24–42 MB — brak modelu), „Bus veurne.ogg” (8 s), „Recording of rickety sleeper bus Pune-Aurangabad” (CC BY-SA 3.0), kyles 55093 (nagrane z wnętrza auta autora — ani kabina, ani zewnątrz), NWFB N796 Hong Kong 41:47 (CC BY 4.0 — brak modelu pojazdu, rozmiar), 833737 New Flyer D40LF „Loud Engine Fan” (rodzina już w P5).

## Braki i niepewności

- Kategorie 1, 3, 4 (co do modelu silnika) i 5 pozostają **luki** po trzech pakietach (G9, P5, M55) — realistyczne źródła nagrań retardera, AMT i osuszacza pojazdowego to wyłącznie biblioteki płatne (np. komercyjne pakiety SFX pojazdów ciężarowych), co potwierdzają negatywy z Openverse/IA/Sonniss (agregatory indeksują te same wolne źródła).
- Podglądy MP3 Freesound (128 kbps) — jakość referencyjna; oryginały FLAC/WAV/M4A do pobrania z `download_list.csv`.
- Pozycje valimaa (M55-005…007) — nagrania telefonem z lekkim wiatrem; krótkie (5–6 s); model Volvo 8900 w tytule.
- M55-004 — 9,8 s, miejsce nagrania nieokreślone; jakość 2/5.
- Nie wszystkie pozycje wnętrza/zewnątrz mają potwierdzenie autora (M55-011, M55-012 — przyjęto wnętrze jako typowe dla nagrań z jazdy; odnotowano w uwagach).
- Openverse audio: limit anonimowych zapytań wyczerpany w sesji (dokumentacja w sources.md) — indeksuje i tak te same Freesound/Commons.

## Samokontrola (20 %, jawny seed)

- **Seed: 20261113**, metoda: `random.seed(20261113); random.sample(13, k=4)` — wylosowano **4 z 13 pozycji (30,8 % ≥ 20 %)**: M55-001, M55-003, M55-006, M55-013.
- Dla każdej: (a) link — HTTP 200: **4/4 OK** (curl -I -L, 2026-11-13); (b) licencja na żywo zgodna z manifestem: **4/4 OK** (strony dźwięków Freesound przez renderowane open_url: „Creative Commons 0” ×2, „Attribution 4.0” ×1; Commons API extmetadata: CC BY-SA 3.0 ×1); (c) długość pomiar vs manifest: **4/4 OK** (71,2 vs 1:11.138; 188,9 vs 3:08.806; 5,74 vs 0:05.674 — różnica < 1 ramki MP3; 47,06 vs API 47,061).
- Dodatkowo (poza losowaniem) sprawdzone **wszystkie 5 pozycji Wikimedia Commons** przez API extmetadata w dniu dostępu: licencje **5/5 zgodne** (CC BY-SA 3.0 ×3, CC BY-SA 2.5 ×1, CC BY-SA 3.0 ×1), rozmiary plików zgodne bajt w bajt z pobranymi.
- Wykryto i naprawiono błąd własnego parsera MP3 (tabela bitrate Layer III) — szczegóły w §Metoda i w audit_20_percent.json.
- Pełne wyniki: `audit_20_percent.json`.

## Struktura katalogu

```
research/mistral/p5-audio-3/
├── README.md            (ten plik)
├── .gitignore           (ignoruje files/ i *.zip)
├── manifest.csv          (13 pozycji M55-001…M55-013)
├── download_list.csv     (8 oryginałów Freesound do pobrania ręcznego)
├── sources.md            (źródła, licencje, zapytania — pełna lista, również negatywne)
├── audit_20_percent.json (samokontrola 30,8 %, seed 20261113)
└── files/               (NIE w repo — 13 plików / 74,8 MB w ZIP poza gitem)
```

## GitHub

Gałąź `research/mistral-p5-audio-3` od najnowszego origin/main; PR do `main` (bez draft). Pliki audio i ZIP poza gitem — archiwum `mistral-p5-audio-3-files.zip` (13 plików z katalogu `files/`, 74,8 MB) dostarczono poza repo, lokalizacja podana w opisie PR.

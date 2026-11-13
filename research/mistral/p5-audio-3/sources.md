# sources.md — źródła paczki mistral-p5-audio-3 (M55)

Wszystkie daty dostępu: **2026-11-13 (UTC)**.

## 1. Freesound (https://freesound.org)

- Wyszukiwarka: `https://freesound.org/search/?q=...` (parsing wyników server-side; filtr licencji `f=license:"..."`).
- Strony dźwięków: `https://freesound.org/s/<id>/` — dla wszystkich pozycji odczytano na żywo: tytuł, opis autora, licencję (+URL), długość, sample rate, bit depth, format, kanały (strony renderowane; curl daje 302, HTTP 200 potwierdzony z `-L`).
- Podglądy MP3 HQ (VBR — zmierzony średni bitrate 174–191 kb/s, mediana ~182 kb/s): `https://cdn.freesound.org/previews/...` — pobrano 8 plików.
- Warunki korzystania: https://freesound.org/help/terms/ ; how-to-credit: https://freesound.org/help/terms/#how-to-credit

### Zapytania Freesound (wyniki >0 są opisane; „0” = brak wyników dla kategorii)

**Kategoria 1 (retarder):** `retarder` (z filtrami CC0/CC BY) → wyłącznie śmieciowe/niepojazdowe; `retarder truck`, `retarder bus` → 0 realnych; **WYNIK: NEGATYW**.

**Kategoria 2 (hamulec silnikowy):** `jake brake` → 2 wyniki śmieciowe; `jake brake truck`, `engine brake` → tła wielopojazdowe; `engine brake diesel` → 9 wyników, wszystkie niepojazdowe lub niewymierne (VW Golf, pociągi, ambience); `exhaust brake` → 6 wyników, wszystkie niepojazdowe; **WYNIK: NEGATYW** (analogi: 637922, Beeld en Geluid).

**Kategoria 3 (AMT):** `automated manual transmission` → 0; `I-Shift` → 45 wyników, wszystkie niepowiązane (muzyka/remiksy); `Opticruise` → 0; `gear shift gap bus` → 0; `AMT gearbox truck` → 0; `bus gear change`/`bus transmission` (batch wstępny) → autobusy z przekładnią hydrokinetyczną (już w P5) lub bez opisu skrzyni; **WYNIK: NEGATYW** (kandydaci: 846043 Volvo B8R, 57931 gearbox whine — oba UNVERIFIED).

**Kategoria 4 (R6 12–13 l):** `diesel engine 12 liter`, `R6 diesel`, `inline 6 diesel truck`, `Maxxforce`, `Volvo 8900`, `D2566`, `PE6`, `user:valimaa bus` itd. (batch wstępny ~500 kandydatów w 5 kategoriach); nazwany model SILNIKA nie występuje w żadnym nowym opisie (duplikat MAN D2566MUM — już w P5); **WYNIK: NEGATYW co do modelu silnika** (pozyskane: nazwane modele pojazdów: Volvo 8900 ×3, Volvo B8R, Nissan Diesel P-DA66U, MaxxForce).

**Kategoria 5 (osuszacz/ogranicznik):** `air dryer` → 0 pojazdowych; `air dryer purge` → 0; `spitter valve` → 3 wyniki, wszystkie POCIĄGI (TGV Lyria 750185, 750222, 473958); `air brake compressor truck` → 0; `air tank purge` → 0; `purge valve` → niepojazdowe; `governor compressor` → niepojazdowe; **WYNIK: NEGATYW**.

## 2. Wikimedia Commons (https://commons.wikimedia.org)

- API metadanych: `https://commons.wikimedia.org/w/api.php?action=query&titles=File:...&prop=imageinfo&iiprop=url|size|extmetadata&format=json` (odstępy ≥3,5–8 s; UA `KamionAudioResearch/1.0 (research task)`).
- Przeskanowano **913 tytułów plików audio** (kolekcje: WWS, Beeld en Geluid, japońskie autobusy, Lingua Libre, kompresory, tiry) — frazy `dryer|purge|spitter|compressor|governor|retard|jake|engine brake|exhaust brake|i-shift|opticruise|amt|gearbox|transmission` → **0 trafień pojazdowych dla kategorii 1/3/5** (kompresory: przemysłowe, tramwajowe, wymowy Lingua Libre).
- Pliki użyte (oryginały, pobrane — wszystkie licencje potwierdzone API 2026-11-13):
  - `File:Het parkeren van een vrachtwagen - SoundCloud - Beeld en Geluid.ogg` — Beeld en Geluid (SoundCloud 9632342), CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) — M55-009
  - `File:Het wegrijden van een vrachtwagen - SoundCloud - Beeld en Geluid.ogg` — Beeld en Geluid, CC BY-SA 3.0 — M55-010
  - `File:HEV 3574b 2006OrionVII.ogg` — Michael P., CC BY-SA 2.5 (https://creativecommons.org/licenses/by-sa/2.5) — M55-011
  - `File:Hokkaido chuo bus kosoku asahikawa UD P-DA66U.ogg` — Spaceaero2, CC BY-SA 3.0 — M55-012
  - `File:Het voorbijrijden van een AA FORD vrachtwagen - SoundCloud - Beeld en Geluid.ogg` — Beeld en Geluid, CC BY-SA 3.0 — M55-013
- Przeglądnięte, odrzucone (bez pominięcia śladu): `File:JR shikoku bus kochirelaybus P-MS725SAkai.ogg` (spaceaero2, CC BY 3.0, 36:31, 41,5 MB — duplikat wartości M55-012), `File:A ride on 102-Road Bus in Fanhe Town, Tieling audio track 01/02.flac` (Karl Osj. G, CC BY-SA 4.0, 24–42 MB, brak modelu), `File:Bus veurne.ogg` (Tom1992, CC BY-SA 3.0, 8 s), `File:Recording of rickety sleeper bus from Pune to Aurangabad.ogg` (CC BY-SA 3.0), `File:Bus drive ambience with talk.ogg` (qubodup, PD — poza white-listą dla pozyskania), `File:Abashiri bus Ki200F 0091.OGG` (PD), `File:OM 67 4.ogg` (niepojazdowe).
- Duplikaty wykluczone (już w G9/P5): Solaris Urbino 18/12 Hybrid „engine sounds, Szczecin 2022” (G9), „Het rijden van een vrachtwagen” (P5-083), WWS City Bus MAN SG 220 engine/horn/doors (P5), Volvo F4 Turbo (P5-027), 20180323-bus-munich (P5), Merced The Bus Gillig (P5).

## 3. OpenGameArt (https://opengameart.org)

- Zapytania: `engine`, `truck`, `bus`, `brake`, `semi`, `lorry`, `air brake` (odstępy ~4 s) → jedyny relevantny wynik to „AMERICAN INTERSTATES! … JAKE BRAKE …” (freetousesounds, CC BY 4.0) — **już wykorzystany w P5-002**, nie powtórzono. **WYNIK: NEGATYW** (brak nowych materiałów dla kat. 1–5).

## 4. Sonniss GDC Game Audio Bundle (gdc.sonniss.com; mirory na archive.org)

- Przeskanowano listy plików **wszystkich bundli 2015–2026** (22 itemy IA, w tym gameaudiogdc-part1through7 ~7,7 tys. plików, sonniss-gdc-20XX-normalized; łącznie ~34 tys. plików audio) pod kątem `truck|bus|brake|jake|retard|engine|trans|gear|air dryer|compressor|diesel|lorry|exhaust|semi|hgv|cab`.
- Najbliższe trafienia (żadne nie spełnia kat. 1–5): FLYSOUND URAL 4320 Diesel (V8, wojskowy), Pole Position M1 Corbitt (1941, benzyna), Chevrolet Silverado 2012 Tow Truck (pickup), Pole Position Barge Bronz diesel 1941 (barka), „Interior Ambiance Of A Moving Bus” (344 Audio, ambience bez detali), „Trucks On Docks Passing” (tła). **WYNIK: NEGATYW.**
- Licencja (cytat, weryfikacja 2026-11-13): *„Licensee may use and modify the licensed sound effects for personal and commercial projects without attribution to the original creator.”* — GDC Game Audio Bundle License v2.0, effective 27.08.2026, https://sonniss.com/gameaudiobundle-gdc/ (licencja pozwala na użytek komercyjny bez atrybucji; w paczce nie wykorzystano plików Sonniss).

## 5. archive.org

- Biblioteki SFX z jawnymi licencjami (metadane IA): GOLD_TAPE_14_Trucks, Red_Library_Trucks, SSE_Library_VEHICLES, Designers-Choice-Collection-Vehicles, GOLD_TAPE_13_Cars (USC/Sunset Editorial, licencje CC0/CC BY na itemach) — stare ciężarówki Hollywood, brak kategorii 1–5; częściowa redundancja z wrzutami craigsmith na Freesound (część ID już w G9/P5).
- `24.08.15DAFEindhoven001/002` (CC BY-SA 3.0) — opis: parking fabryki, brak dźwięków ciężarówek → odrzucone.
- **Pegaso Z-207 1957** — licencja Public Domain Mark 1.0 → poza białą listą (CC0/BY/BY-SA) → **tylko referencja, nie pobrano**: https://archive.org/details/PegasoZ-207.
- **WYNIK: NEGATYW** dla kat. 1–5.

## 6. Openverse audio (https://api.openverse.org/v1/audio/)

- Limit anonimowych zapytań wyczerpany w sesji (HTTP 429/401); indeksuje te same źródła Freesound/Wikimedia Commons, które przeszukano bezpośrednio (wyżej). **WYNIK: brak nowych źródeł; dokumentowane jako przeszukane z notką o rate limicie.**

## 7. BBC Sound Effects / RemArc

- W wynikach wyszukiwań w tej sesji nie wystąpiły kandydaci BBC; RemArc (licencja niekomercyjna) — brak pozycji do załączenia jako „tylko referencja”.

## 8. Narzędzia i metody weryfikacji

- Własne parsery długości: MP3 (ramki MPEG 1/2/2.5 Layer III, poprawna tabela bitrate L3: 32…320 kbit/s; pomiar = suma ramek × 1152/576 próbek; uwzględniono ID3v2), Ogg Vorbis (sample rate z nagłówka identyfikacyjnego + granulepos ostatniej strony), WAV (RIFF fmt/data — nieużyty w paczce).
- Pomiary porównano z deklaracjami stron (Freesound player / Commons API) — różnice ≤ 1 ramki MP3 (26 ms) lub ≤ 0,1 s.
- HTTP 200: curl `-sIL` (Freesound, Commons, CDN, upload.wikimedia.org) — 2026-11-13.
- Audyt 20%+: linki HTTP, licencje na żywo (open_url stron Freesound / API Commons), długości — patrz `audit_20_percent.json`.

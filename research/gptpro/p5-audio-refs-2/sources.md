# sources.md — źródła paczki gptpro-p5-audio-refs-2

Wszystkie daty dostępu: **2026-11-13/14** (UTC), chyba że zaznaczono inaczej.

## 1. Freesound (https://freesound.org)
- Wyszukiwarka: https://freesound.org/search/ (zapytania: retarder, jake brake, engine brake, exhaust brake, air dryer, air brake, pressure valve, bus transmission, bus gear change, truck cab interior, cab over, backup beeper, seat belt, wipers, indicator stalk, air doors itd.)
- Strony dźwięków: https://freesound.org/s/<id>/ — dla wszystkich 64 pozycji Freesound w manifeście odczytano na żywo: tytuł, opis autora, licencję (+URL licencji), długość, sample rate, bit depth, format.
- Podglądy MP3 HQ: https://cdn.freesound.org/previews/...
- Licencje w paczce: CC0 (domena publiczna), CC BY 3.0/4.0, CC BY-NC (tylko referencja, nie pobrano).
- Warunki korzystania Freesound: https://freesound.org/help/terms/ ; how-to-credit: https://freesound.org/help/terms/#how-to-credit

## 2. Wikimedia Commons (https://commons.wikimedia.org)
- API metadanych: https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata (rate limit respektowany — odstępy ≥8 s)
- Pliki użyte (oryginały, pobrane):
  - File:WWS_CityBusMANSG220engine.ogg — MAN D2566MUM, R6 11 413 cm³, 176 kW (Work With Sounds / Technical Museum of Slovenia, CC BY 4.0)
  - File:WWS_CityBusMANSG220horn.ogg (j.w., CC BY 4.0)
  - File:WWS_CityBusMANSG220dooropeningclosing.ogg (j.w., CC BY 4.0)
  - File:Merced_The_Bus_Gillig_engine_start.ogg (Evan0512, CC BY-SA 4.0)
  - File:Volvo_F4_Turbo,_starten,_over_de_snelweg_rijden_en_stoppen_-_SoundCloud_-_Beeld_en_Geluid.ogg (Beeld en Geluid, CC BY-SA 3.0)
  - File:20180323-bus-munich.opus (MartinThoma, CC0)
  - File:Het_rijden_van_een_vrachtwagen_-_SoundCloud_-_Beeld_en_Geluid.ogg (Beeld en Geluid, CC BY-SA 3.0)
- Licencje: https://creativecommons.org/licenses/by/4.0/ , https://creativecommons.org/licenses/by-sa/4.0/ , https://creativecommons.org/licenses/by-sa/3.0/ , https://creativecommons.org/publicdomain/zero/1.0/

## 3. OpenGameArt (https://opengameart.org)
- „AMERICAN INTERSTATES! FROM IOWA TO CALIFORNIA SOUND! INCLUDING JAKE BRAKE IN LAS VEGAS! (Interstate 15 before Las Vegas)” — freetousesounds, CC BY 4.0: https://opengameart.org/content/american-interstates-from-iowa-to-california-sound-including-jake-brake-in-las-vegas
- Licencja CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
- Pobrano oryginał (168 MB zip), do paczki wycięto bezstratnie fragment 2:00–2:20 (WAV 96 kHz/24 bit).

## 4. BBC Sound Effects (tylko linki — RemArc, NIE pobierano)
- Strona pozycji: https://sound-effects.bbcrewind.co.uk/<id> (12 pozycji w manifeście; HTTP 200 potwierdzony, tekst licencji RemArc na stronie)
- Licencja RemArc (personal, educational, research — NIEKOMERCYJNA): https://sound-effects.bbcrewind.co.uk/help#remarc
- Katalog BBC (mirror Internet Archive, tylko identyfikatory/nazwy jako referencja): https://archive.org/details/bbcsoundeffects (katalog przetworzony lokalnie z pliku danych lustra IA).

## 5. Sonniss GDC Game Audio Bundle (sprawdzono, nie wykorzystano)
- Licencja (cytat): „Licensee may use and modify the licensed sound effects for personal and commercial projects without attribution to the original creator.” — GDC Game Audio Bundle License v2.0, effective 27.08.2026: https://sonniss.com/gameaudiobundle-gdc/
- W paczce brak plików Sonniss (nie znaleziono odpowiedników kategorii 1–4 o lepszej jakości niż źródła CC0/CC BY).

## 6. Narzędzia i metody weryfikacji
- Własne parsery długości: MP3 (ramki MPEG 1/2/2.5 Layer III, uwzględnione tablice SR wg wersji), Ogg Vorbis (granulepos), Opus (48 kHz, granulepos), WAV (RIFF fmt/data).
- Audyt 20%: linki HTTP (curl), licencje na żywo (strona Freesound / Commons API / strona BBC), długości vs odtwarzacz — patrz audit_20_percent.json.

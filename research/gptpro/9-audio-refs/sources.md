# Źródła — G9 audio-refs

Wszystkie źródła udostępnione publicznie; data dostępu: **2026-11-12** (dla każdego URL poniżej).

## Freesound (freesound.org, cdn.freesound.org)

- Strona główna i wyszukiwarka: https://freesound.org — data dostępu: 2026-11-12
- Strony dźwięków (wzorzec): `https://freesound.org/people/<autor>/sounds/<id>/` — każda pozycja
  kolumny `url_zrodla` z `zrodlo` = „Freesound” w `manifest.csv` była pobrana i sprawdzona w dniu
  2026-11-12 (licencja, metadane: długość, format, sample rate, autor).
- Pliki podglądów HQ (CDN Freesound): `https://cdn.freesound.org/previews/...` — pobrane
  2026-11-12; licencja podglądu = licencja dźwięku (CC0 lub CC BY wg manifestu).
- Licencje: Creative Commons Public Domain Dedication CC0 1.0
  (https://creativecommons.org/publicdomain/zero/1.0/) oraz CC BY 3.0 / CC BY 4.0
  (https://creativecommons.org/licenses/by/3.0/, https://creativecommons.org/licenses/by/4.0/)
  — data dostępu: 2026-11-12.

## Wikimedia Commons (commons.wikimedia.org)

- API metadanych plików: `https://commons.wikimedia.org/w/api.php` (action=query, prop=imageinfo,
  iiprop=extmetadata) — data dostępu: 2026-11-12 (m.in. pola LicenseShortName, Artist, duration).
- Strony plików audio: URL-e w `manifest.csv` (`zrodlo` = „Wikimedia Commons”) — data dostępu:
  2026-11-12.

## BBC Sound Effects (tylko linki — licencja RemArc, nie pobierano)

- Katalog: https://sound-effects.bbcrewind.co.uk — data dostępu: 2026-11-12.
- Strony pojedynczych efektów (wzorzec): `https://sound-effects.bbcrewind.co.uk/sfx/<id>` —
  data dostępu: 2026-11-12 (pozycje G9-B01–G9-B27 w `manifest.csv`).
- API wyszukiwania: `https://sound-effects-api.bbcrewind.co.uk/api/sfx/search` — data dostępu:
  2026-11-12 (metadane: opis, długość).
- Licencja RemArc (personal, educational, research use — bez użycia komercyjnego):
  https://www.bbc.co.uk/usingthebbc/terms-of-use/ — data dostępu: 2026-11-12.

## Creative Commons (definicje licencji)

- CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/ — data dostępu: 2026-11-12
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ — data dostępu: 2026-11-12
- CC BY 3.0: https://creativecommons.org/licenses/by/3.0/ — data dostępu: 2026-11-12
- CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/ — data dostępu: 2026-11-12
- CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/ — data dostępu: 2026-11-12

## Uwaga

Google Maps / Street View / Earth / 3D Tiles — **nie używano** (zakaz w zadaniu). Nie pobierano
żadnych plików z licencjami NC/ND/niejasnymi; pliki BBC RemArc i Commons CC BY-SA — wyłącznie linki.

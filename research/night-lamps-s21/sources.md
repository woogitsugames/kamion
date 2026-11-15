# Źródła K69 (dostęp 2026-11-15)

## Dokumenty urzędowe (SOURCED) — platforma e-zamówień Miasta Białystok (publiczna)
| postępowanie | URL | plik | sha256 | cytat (≤ 25 słów) |
|---|---|---|---|---|
| ZDM-XIV.271.31.2023 „Dostawa i montaż opraw … (I)” | https://miastobialystok.ezamawiajacy.pl/pn/miastobialystok/demand/notice/public/93688/details | Zał. nr 9 do SWZ – Warunki techniczne.pdf (ZDM-VII.7021.1.14.2023, 3 s., skan; 1 203 294 B) | 05301ed100b3f6988e2e3b077060ad8adef2d960458a169070ca2a863fca3a92 | s. 1: „na ul. Gen. W. Andersa, al. 1000-lecia Państwa Polskiego do granic miasta, ul. Gen. S. Maczka”; pkt 2a: „temperatura barwowa diod dla opraw oświetlenia ulicznego 4000°K” |
| ZDM-XIV.271.3.2024 (I) | …/notice/public/120561/details | Zał. nr 9 do SWZ – Warunki techniczne.zip → ZDM-VII.7021.1.4.2024.pdf | ZIP fffc44b5cad73a0a377346b20c984706352f8006f03ce113e9b98c497d701134; PDF 1.2.2024: d977bb0e…; 1.4.2024: ba5c0990… (pełne w README tools) | s. 1: „ul. W. Wysockiego”; pkt 2a–b: „4000°K”, „…doświetlenia przejść dla pieszych 5700°K” |
| ZDM-XIV.271.13.2024 (II) | …/notice/public/122716/details | Zał. nr 9 i 10 do SWZ – Warunki tech., schematy.zip (3 037 570 B) → ZDM-VII.7021.1.7.2024.pdf (5 s., skan) | ZIP bd6534a09b3714025215e96241c4922640063c4d285da04b4312689586ca9bdc; PDF 0f5a124bcfa7f68b053345fc80a84cf4555f10a5b3afaa2566e317794802826f | s. 1: „A. Mickiewicza … J. Kuronia, Dywizjonu 303”; „o mocach 70, 100, 150, 250”; s. 4 pkt 12: „określenie wysokości słupów, długości wysięgników … leży w gestii Wykonawcy” |
| SWZ ZDM-XIV.271.13.2024 (do odczytu) | jw. | SWZ (do odczytu).docx | — | pkt 3.4: „Demontaż istniejących opraw o mocy 70W, 100W, 150W, 250W i 400W” |
| TED (API v3 /notices/search) | https://ted.europa.eu/pl/notice/-/detail/658997-2023 ; …/769998-2024 ; 73896-2024 ; 122818-2024 | — | — | 122818-2024: „dostawa i montaż energooszczędnych opraw ledowych … 22) na ul. J. Kuronia, 23) na ul. Dywizjonu 303” |

Duże PDF-y nie są w gicie (skany; pobranie: `tools/ezam.py tools <id> <outdir> warunki`). Nazwy handlowe opraw z dokumentu 2023 celowo pominięte.

## OSM (ODbL 1.0, © OpenStreetMap contributors)
- OSM API 0.6 `/map`, kafle 0,01°, bbox 53.095–53.165 N / 23.120–23.215 E, 15.11.2026 ~09:50 UTC → `osm-street-lamps.json` (1443 węzły). Overpass niedostępny (zapytania w `tools/*.overpassql`).

## Kadry
- Panoramax (CC BY-SA 4.0, referencja): 17 kadrów — URL API `https://api.panoramax.xyz/api/collections/<kolekcja>/items/<id>` w manifeście; kierunek = `view:azimuth`.
- Wikimedia Commons (CC0, Rakoon): 9 kadrów — strony plików w manifeście; licencja sprawdzona w HTML strony pliku (API 429).
- Openverse → Flickr: piszczu (CC BY 2.0) 2653184103, 2653183441; Cezary Borysiuk (CC BY 2.0) 4372739745, 4225459902, 4181639418; access.denied (CC BY-SA 2.0) 3357771560. Data „Taken on” ze strony Flickr.
- Odrzucone z Openverse: „Lamp”, „L-Lens” (sprzęt foto, nie Białystok), kadry zabytków bez latarń; NC/ND (84 wyniki by-nc-sa) — nie pobrane.

## Przywołane (nie powtarzane)
- C60: `origin/research/cloud-p17-dusk-lighting:research/cloud/p17-dusk-lighting/ortho_lamp_spacing.csv`, recenzja `docs/reports/REVIEW-2026-11-14-s20-cloud-m60-compare.md`; M60 Mistral: `docs/reports/REVIEW-2026-11-14-s20-mistral-m60.md`.
- ADR 0191, 0192 (`docs/adr/`).

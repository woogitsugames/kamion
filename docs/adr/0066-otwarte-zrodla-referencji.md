# ADR 0066: Otwarte źródła referencji (D43)

Status: przyjęty (geo-worldgen), 2026-11-10. Źródło: `docs/11` D43 (zmiana D41: właściciel nie robi zdjęć). Uzupełnia ADR 0002 (zakaz Google) i ADR 0065 (Mapillary).

## Kontekst
Bez zdjęć własnych potrzebujemy referencji trasy startowej (55 ujęć z `docs/owner/PHOTO-LIST.md`: Kwadrat Park, Andersa,
Rondo Putry, Al. Tysiąclecia) z legalnych, otwartych źródeł. Google Maps/Street View/Earth/3D Tiles/Elevation (także
przez Gemini) pozostają zakazane.

## Decyzja
Moduł `tools/refs/` (uv, bez kluczy i kont) obsługuje źródła, każde z manifestem `manifest.jsonl` (URL strony i pliku,
autor, data, licencja + URL licencji, SHA256, klasa użycia, numery ujęć), cache odpowiedzi, limitem zapytań
(domyślnie >= 0,5 s), backoffem na 429/5xx i testami z mockami HTTP (`tests/refs/test_open_sources.py`, bez sieci):

| Źródło | Moduł | Dane | Wyjście |
|---|---|---|---|
| KartaView (CC BY-SA 4.0) | `open_sources.py --source kartaview` | API v2 `/2.0/photo` (promień <= 500 m) + starsze v1 `nearby-photos` (więcej historii), bez klucza | `Data/raw/refs/kartaview/` |
| Panoramax (licencja per zdjęcie) | `--source panoramax` | `api.panoramax.xyz/api/search?bbox=`, licencja z pola `license` zdjęcia | `Data/raw/refs/panoramax/` |
| Wikimedia Commons | `--source commons [--categories]` | `geosearch` wokół ujęć + kategorie; licencja z `extmetadata` | `Data/raw/refs/commons/` |
| Openverse | `--source openverse` | wyszukiwanie tekstowe, filtr serwera `cc0,pdm,by,by-sa` + ponowna kontrola | `Data/raw/refs/openverse/` |
| GUGiK ortofotomapa | `gugik_ortho.py` | WMS `ORTO/WMS/HighResolution`, EPSG:2180, okno 160 m na ujęcie | `Data/raw/refs/gugik-ortho/` |
| Miasto Białystok (ArcGIS Online) | `bialystok_open_data.py` | publiczne feature services (parki, pomniki przyrody, straż pożarna, monitoring, itd.) wg bbox trasy | `Data/raw/refs/bialystok-open-data/` |

Montaże per ujęcie: `artifacts/refs/<źródło>/shot_NN.jpg` (miniatury z podpisem id, daty, licencji, autora).
`--only-weak` ogranicza do ujęć SŁABE/BRAK z `artifacts/refs/coverage.json` (Mapillary), gdy plik istnieje.

LoD2 (`Data/raw/gugik/lod2-2017-2061`) i pełne arkusze ortofotomapy (`gugik-orto-2024-...`) już są pobrane, nie dublujemy ich.

## Bramka licencyjna (kod: `refs_common.normalize_license`)
- Pobierane są tylko CC0, domena publiczna (PDM), CC BY, CC BY-SA. NC, ND, "all rights reserved", nieznane i obiekty z
  ograniczeniami (Commons `Restrictions`) są odrzucane i liczone w raporcie, nigdy nie pobierane.
- Klasa użycia zapisana w manifeście: `texture_ok` (CC0/PDM/CC BY), `reference_only_owner_decision_for_pixels` (CC BY-SA).
- **Zasada**: referencje służą jako WZÓR (kadr, kolor, proporcje, rytm detalu). Piksele w teksturach tylko z CC0 / PDM /
  CC BY (z atrybucją w `docs/LICENSES.md`). CC BY-SA: pikseli nie wycinamy do tekstur bez osobnej decyzji właściciela
  (utwór zależny = share-alike, patrz ADR 0065). Dane miejskie bez deklarowanej licencji: tylko referencja do czasu
  przeglądu prawnego (`LEGAL_REVIEW_REQUIRED`). Ortofotomapa GUGiK: referencja i kontrola dopasowania (jak w manifeście `gugik-orto-*`).
- Faktyczne użycie zdjęcia (np. kalibracja koloru) zapisujemy i dopisujemy autora do `docs/LICENSES.md`.

## Konsekwencje
- Brak kluczy: wszystkie źródła działają anonimowo. Limity anonimowe (Openverse, Commons) szanowane opóźnieniem i backoffem.
- Starsze API KartaView v1 jest oficjalnie przestarzałe, ale nadal zwraca dane bez klucza; v2 ma krótszą historię. Gdyby v1 zniknęło, zostaje v2.
- WMS GUGiK bywa chwilowo zwraca puste (białe) kafle: klient ponawia z opóźnieniem i pomija ujęcie po 5 próbach.
- `dane.gov.pl` był nieosiągalny z tej sieci (timeout połączenia); Miasto Białystok udostępnia dane przez ArcGIS Online (bez licencji w metadanych).
- Pokrycie: ujęcia 1-12 (prywatny teren Kwadrat Parku) nie mają pokrycia ulicznego w żadnym z otwartych źródeł; pozostają
  ortofotomapa, Commons i ewentualnie Mapillary (agent równoległy).

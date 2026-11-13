# Źródła P7 — s8-signs-2 (uzupełnienie paczki G3)

Data dostępu wszystkich pozycji, o ile wyraźnie nie podano inaczej: **2026-11-13 (UTC)**.
Daty zdjęć są osobne. Każdy fakt w manifeście ma własną kolumnę `data_dostępu`.

## Źródła urzędowe i kontekstowe

| ID | Źródło | Co potwierdza | Pobrano |
|---|---|---|---|
| CONTEXT-2026 | GDDKiA: [Dwie eski połączone koło Białegostoku](https://www.gov.pl/web/gddkia-bialystok/dwie-eski-polaczone-kolo-bialegostoku) (komunikat 20.10.2026) | Otwarcie S19 Krynice–Dobrzyniewo–Białystok Zachód (10,2 km) i przebudowa 1,9 km S8 w węźle Białystok Zachód. Fotografie w stopce CC BY-NC-ND — **tylko link, zdjęć nie pobrano**. | Link (G3 pobierało 2026-11-12; P7 weryfikowało istnienie komunikatu 2026-11-13 przez wyszukiwarkę) |
| S19-DOR-2026 | Wykonawca PORR/UNIBEP: [Wprowadzenie docelowej organizacji ruchu](https://www.s19-krynice-ksiezyno.pl/tresci/wprowadzenie-docelowej-organizacji-ruchu-1796) (15.10.2026) | Cytat: „w dniu 20.10.2026r. o godzinie 08:30 zostanie wprowadzona docelowa organizacja ruchu na drogach S8, S19 i DK65" — zatwierdzona **klauzulą nr 1249/2024**. | Link (2026-11-13) |
| S19-COR-WARSZAWSKA-2026 | Wykonawca PORR/UNIBEP: [Włączenie do ruchu ul. Warszawskiej przy węźle Białystok Zachód](https://www.s19-krynice-ksiezyno.pl/tresci/w-czenie-do-ruchu-ul-warszawskiej-przy-w-le-bia-ystok-zachod-1784) (09.09.2026) | Czasowa organizacja ruchu nr 200337-3.1-33, **klauzula nr 3860c/2026 z 21.08.2026**, wdrożona 16.09.2026 o 13:00 — zmiana oznakowania przy węźle Białystok Zachód na DK19 (ul. Warszawska). | Link (2026-11-13) |
| ZDM-REJESTR | BIP UM Białystok: [Ewidencja stałych i czasowych projektów zmian organizacji ruchu drogowego](https://www.bip.bialystok.pl/urzad_miejski/rejestry_ewidencje_archiwa/ewidencja-stalych-i-czasowych-projektow-zmian-organizacji-ruchu-drogowego.html) | Rejestr prowadzi ZDM (Referat Rozwoju i Inżynierii Ruchu); rejestr nie jest publikowany online — **numer decyzji o zmianie oznakowania łącznicy Maczka–rondo Putry (wiosna 2021) nieustalony**. | Link (2026-11-13) |
| GDDKIA-PRZYGOTOWANIE | GDDKiA Oddział Białystok: [Przygotowanie inwestycji drogowych w województwie podlaskim](https://www.gov.pl/web/gddkia-bialystok/przygotowanie-inwestycji-drogowych-w-wojewodztwie-podlaskim2) | Planowane odcinki S19 (Białystok Północ–Dobrzyniewo, Czarna Białostocka–Białystok Północ), S8 Knyszyn–Raczki, południowa obwodnica Białegostoku; odwołania od DŚU. | Link (G3 pobierało 23.05.2024 wg notatek; P7 nie powtarzało pobrania) |

## Mapillary

| ID | Źródło | Co potwierdza | Pobrano |
|---|---|---|---|
| MLY-API | [Mapillary Graph API](https://graph.mapillary.com) (endpoint `images` z bbox; od 13.11.2026 endpoint `/images/{id}` i `?ids=` nie odpowiada — metadane pobierano zapytaniami bbox), publiczny token odczytu z kodu strony embed mapillary.com | Metadane kadrów: klucz, `geometry`, `captured_at`, `creator`, `compass_angle`, `computed_compass_angle`; miniatury `thumb_1024_url` (1024 px ≤ limit 1600 px). Licencja **CC BY-SA 4.0** — kadry w paczce **tylko jako referencja/odczyt faktograficzny, nie jako tekstury** (zasada share-alike). W paczce nie ma tokena. | 2026-11-13 |
| MLY-COVERAGE | Mapillary — pokrycie rejonu Białegostoku (zapytania bbox w korytarzach DK19/DK65/DK8/S19/S8, skany z 12–13.11.2026) | **Brak kadrów 2025–2026 w całym badanym regionie** (najświeższe 2024-09-01, quickness805; jedyny 2025: fantoment 2025-03-28, 20 kadrów w centrum miasta, bez liści). Stan oznakowania 2025–26 = UNVERIFIED poza dokumentami urzędowymi. | 2026-11-13 |

## OpenStreetMap

| ID | Źródło | Co potwierdza | Pobrano |
|---|---|---|---|
| OSM-ODBL | [OpenStreetMap](https://www.openstreetmap.org/) przez Overpass API (instance overpass.private.coffee; maps.mail.ru przestało odpowiadać JSON-em, overpass-api.de odmawia połączenia) | Geometria dróg 19/65/8/676/S19/S8, węzły motorway_junction (m.in. **Białystok Zachód ref=10**, edycja 2026-10-20), węzły `traffic_sign`. Fakty z OSM na licencji **ODbL**. | 2026-11-13 |

## Paczka G3 (poprzednia)

Pozycje P7 odsyłają do manifestu G3 (research/gptpro/3-s8-signs): odczyty tablic przy rondzie Putry (G3-P001–P020), Commons 2021–2022 (G3-C001–C023), korytarz północny DK8/DK19 (MN001–MN024). P7 nie dubluje pozycji G3 — uzupełnia o oś czasu i nowe obszary.

## Zasady licencyjne paczki

- Kadry Mapillary: CC BY-SA 4.0, wyłącznie referencja (odczyt treści tablicy jest faktograficzny i wolny; wycinka nie wolno użyć jako tekstury w grze komercyjnej bez przeniesienia share-alike).
- Commons: licencje per plik (G3 odnotowało autorów i licencje; P7-006: CC0, Rakoon).
- Dokumenty urzędowe (klauzule, komunikaty): art. 4 ustawy o prawie autorskim — materiały urzędowe; w P7 brak PDF w paczce — tylko linki.
- Fakty o ruchu drogowym pochodzące z OSM: ODbL, "© OpenStreetMap contributors".

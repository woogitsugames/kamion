# Źródła — K1 DK65 Białystok → Knyszyn (dostęp 2026-11-15)

## Dokumenty urzędowe
| id | dokument | data | cytat (≤ 25 słów) | URL / plik |
|---|---|---|---|---|
| S1 | Minister Infrastruktury, odpowiedź na interpelację nr 5277, znak DDP-6.054.39.2024 | 2024-12-10 | „przebudowa skrzyżowania DK 65 z DW 671 na skrzyżowanie z ruchem okrężnym, przebudowa chodników … budowa oświetlenia dedykowanego na przejściach dla pieszych” (s. 1) | https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDBUJN7/i05277-o1.pdf · `files/docs/MI-odp-interpelacja-5277-2024-12-10.pdf` (134 KB) |
| S1 | jw. | 2024-12-10 | „GDDKiA – złożyła wniosek o ZRiD dla przebudowy skrzyżowania na DK 65 w m. Knyszyn w VII 2024 r.” (s. 1) | jw. |
| S1 | jw. | 2024-12-10 | „w III kwartale 2026 r. po … oddaniu do użytkowania … S19 … DK 65 na przedmiotowym odcinku drogi … utraci status drogi krajowej” (s. 2) | jw. |
| S2 | GDDKiA O/Białystok, „Zmiana organizacji ruchu na drodze krajowej nr 65” | 2025-10-14 | „Zamykamy tymczasowy objazd wiaduktu, który powstaje w ciągu drogi ekspresowej S19 Krynice - Białystok Zachód. Ruch wraca na stały przebieg DK65.” | https://www.gov.pl/web/gddkia-bialystok/zmiana-organizacji-ruchu-na-drodze-krajowej-nr-65 — **strona niedostępna 2026-11-15 (HTTP 503 / connection reset); cytat tylko z indeksu wyszukiwarki → UNVERIFIED** |

## Prasa (tylko referencja, cytaty)
| id | źródło | data | cytat |
|---|---|---|---|
| P1 | wartowiedziec.pl, „Nowy odcinek S19 otwarty” | 2026-10-21 | „Trasa o długości 10,2 km została oddana do ruchu 20 października 2026 roku” — https://wartowiedziec.pl/komunikacja-i-transport/82331-nowy-odcinek-s19-otwarty |
| P2 | Auto Świat, nowe drogi w październiku 2026 | 2026-10-13 | lista GDDKiA: „Oddanie do ruchu S19 Krynice — Dobrzyniewo — Białystok Zachód” — https://www.auto-swiat.pl/wiadomosci/aktualnosci/jakie-nowe-drogi-beda-gotowe-w-pazdzierniku-2026-r-gddkia-podaje-nowe-odcinki/e3ld8mg |
| P3 | Auto Świat, S16 Knyszyn–Krynice w budowie | 2026-05-14 | „Nowy odcinek S16 rozpocznie się rondem na drodze krajowej nr 65, około 3 km na południe od Knyszyna”; „ograniczenia prędkości do 50 km na godz.”; „oddana do użytku w 2028 r.” — https://www.auto-swiat.pl/wiadomosci/aktualnosci/s16-knyszynkrynice-w-budowie-kluczowy-odcinek-wchodzi-w-faze-realizacji/vtwl63z |

## Dane
| id | źródło | szczegóły | licencja |
|---|---|---|---|
| D1 | GUGiK ortofotomapa, WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution` (warstwa Raster) | wycinki 0,1 m/px; najnowsze arkusze wg skorowidza WFS `gugik:SkorowidzOrtofomapy2025`: 2025-05-25 (korytarz) i 2025-05-27 (Knyszyn), piksel 0,1 m, zgłoszenie GK-FOTO.6201.11.2025; godła i URL GeoTIFF w `data/orto_*_meta.json` | dane GUGiK bez opłat (art. 40a ust. 2 pkt 1 PGiK) |
| D2 | OpenStreetMap API 0.6 (`/ways`, `/map`, `/way/{id}/full`) | tagi 41 odcinków trasy (`data/osm_route_ways.json`), korytarz ±300 m co 500 m (`data/osm_corridor.json`), ronda (`dl` w tools) | ODbL © OpenStreetMap contributors |
| D3 | Plan trasy ADR 0203 `docs/reports/map/dk65_route_plan.json` (repo) | polilinia wariantu A, kilometraż trasy, kafle | repo |
| D4 | Wikimedia Commons (API geosearch, search, imageinfo) | 42 pliki pobrane (thumb.php ≤ 1600 px), licencje CC0/CC BY/CC BY-SA/PD, autor i URL w manifeście | wg pliku |
| D5 | Panoramax (api.panoramax.xyz, panoramax.openstreetmap.fr, panoramax.ign.fr) STAC search per kafel | 9 zdjęć tylko w dk65-01 (1,7 km od trasy), reszta 0 — `data/query_log.json` | — |
| D6 | Openverse | anonimowo page_size ≤ 20; „Knyszyn” → tylko wyniki z Wikimedia | — |
| D7 | KartaView | api.openstreetcam.org — błąd TLS (nazwa certyfikatu), luka | — |
| D8 | Mapillary | brak tokenu (COMMON.md) — nie odpytywano | — |
| D9 | Overpass | overpass-api.de — reset połączenia przez proxy (4 próby z backoffem), zastąpione API 0.6 | — |

## Wcześniejsze materiały w repo (nie dublowane, porównane)
- ADR 0203 (plan kafli, budowa S19 w OSM), 0204 (Knyszyn; orto 2025 — skrzyżowanie DK65/DW671 nie-rondo; DK65 7,5 m), 0205 (dk65-01: 6,0 m, linie), 0207 (dk65-02…05: override 7,6 m vs rozstaw linii 6,25–7,0 m), 0209/0212 (Knyszyn: 6,8 m linia–linia, zatoka km 25).
- docs/11 D64/D65 (decyzje właściciela), docs/owner/OWNER-PHOTOS-KNYSZYN.md (kadry właściciela — poza gitem, nieużyte).

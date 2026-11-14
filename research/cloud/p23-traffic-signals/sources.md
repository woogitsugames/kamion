# Źródła — M66 (cloud p23-traffic-signals), dostęp 2026-11-14

## Przepisy (akty prawne, art. 4 pr. aut.)
- Dz.U. 2019 poz. 2311 (tekst jednolity rozporządzenia MI z 3.07.2003 r. w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych…; akt pierwotny Dz.U. 2003 nr 220 poz. 2181). Metadane: `https://api.sejm.gov.pl/eli/acts/DU/2019/2311` (status: obowiązujący). Plik z zał. 3: `https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text/I/D20192311-c2.pdf` (27 996 609 B, 381 s. = s. 526–906; sha256 8abcce24766fe743b5bbcd3d64771e70c1a6709c1db72fdf72adfebbfdc5d5c4).
  Uwaga: pliki `text/O/D20192311-c1.pdf` i `text/O/…-c2.pdf` w API są identyczne (część 1, s. 1–525) — części 2 trzeba szukać pod `text/I/`. `dziennikustaw.gov.pl` i pobieranie z `isap.sejm.gov.pl` były niedostępne przez proxy (reset / 403).
  Tekst: `pdftotext -layout`; rysunki i tabela 7.1: `pdftoppm` 100–600 dpi, obejrzane (s. 757, 802, 803, 804).
- Nowelizacje sprawdzone (`…/eli/acts/DU/<rok>/<poz>/text/O/<plik>.pdf`): 2021/438, 2021/2066, 2022/2377 (sha256 4da83eef…9248; cytat z s. 15), 2026/132; sprostowanie 2020/862.

## OSM (ODbL, © autorzy OpenStreetMap)
- Overpass (mirror): `https://maps.mail.ru/osm/tools/overpass/api/interpreter`, POST `data=[out:json][timeout:25];node["highway"="traffic_signals"](53.09,23.10,53.17,23.22);out body;` — 2026-11-14T16:59:03Z, `timestamp_osm_base` 2026-11-14T16:57:38Z → 457 węzłów. Większa bbox (53.06,23.03,53.20,23.29) kończyła się HTTP 504 — inwentarz obejmuje więc środek miasta, nie całe granice.
- Skupiska: łączenie węzłów odległych < 70 m (ENU, X = wschód, Z = północ) → 151 skupisk. Nazwy ulic: `https://api.openstreetmap.org/api/0.6/node/<id>/ways.json` (2026-11-14, ~17:16Z).

## KartaView (CC BY-SA 4.0 — referencja, nie tekstura)
- `POST https://api.kartaview.org/1.0/list/nearby-photos/` (lat, lng, radius=70) dla 151 skupisk; `POST https://api.kartaview.org/1.0/sequence/photo-list/` (sequenceId) dla sekwencji 3686129, 2769366, 2763230, 1155711, 1155438, 14055, 13550, 10733, 11712050/52/54/57/79. Pozycja, `Heading`, `shot_date` z tych odpowiedzi.
- Pliki: pełna rozdzielczość `https://storage13.openstreetcam.org/files/photo/…/proc/…jpg`; dla `storage7` (2018) bezpośredni URL daje 502 → `https://cdn.kartaview.org/pr:sharp/<base64 URL-a storage7>` (suma sha256 stabilna w 2 pobraniach).
- Dobór: kadr 14–40 m od węzła sygnalizacji, różnica Heading vs namiar kamera→węzeł ≤ 22° (pierwsza selekcja ≤ 30°).
- Pseudonimy autorów sekwencji (z API): TMishaaa (2021), gpsmapper999 (2019), telenavdrives (2018), zx-osm-user (2026).

## Wikimedia Commons (CC0, autor: Rakoon)
- `list=geosearch&gsbbox=…&gsnamespace=6&gslimit=500&gsprimary=all` kaflami 0,01° × 0,015° — ukończono 24 z 64 kafli (API 429 / „search too busy”); z tego 136 plików ≤ 45 m od węzła sygnalizacji; `prop=imageinfo` (url, sha1, extmetadata, metadata).
- Pobrano miniatury 1920 px (`…/thumb/…/1920px-<nazwa>`); oryginały i 3840 px: HTTP 429 dla User-Agenta bez danych kontaktowych (zasada prywatności briefu). URL oryginału i sha1 w kolumnie `uwagi`.

## Panoramax
- `https://api.panoramax.xyz/api/collections?bbox=23.03,53.06,23.29,53.20` i `…/api/search?bbox=…` wokół 151 skupisk: wyniki tylko przy Rondzie Putry (2019, sekwencje przelotowe) — nie użyto (lepsze kadry KartaView z tego samego roku).

## Repo (nie dublowane)
- `docs/adr/0172-p1b-sygnalizator-182011-znaki-cm924.md` (wysięgnik 8,8 m), `research/mistral/p9-furniture-3` (M50-033…039), `research/mistral/p11-dojlidy-photos` (P11-063), `docs/reports/REVIEW-…-0179.md` (uwaga o białej tarczy).

## Nieużyte / zakazane
- Google/Bing/Apple/Yandex — nie. Mapillary — nie (brak tokenu). PN-EN 12368 — płatna, nie cytowana. Karty katalogowe producentów — nie pozyskano.

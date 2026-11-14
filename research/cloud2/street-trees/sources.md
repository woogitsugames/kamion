# Źródła — R5 street-trees (dostęp: 2026-11-14)

| # | Tytuł | URL | Licencja / status | Do czego |
|---|---|---|---|---|
| 1 | OpenStreetMap — ekstrakt woj. podlaskiego (PBF), stan `2026-11-13T01:06:06Z` (podlaskie.state.txt), pobrano 2026-11-14 17:10 UTC, sha256 82939b5f…a396c | https://download.openstreetmap.fr/extracts/europe/poland/podlaskie.osm.pbf | ODbL 1.0 | drzewa, szpalery, żywopłoty, osie dróg |
| 2 | Łaska G. (2015) Synanthropization of dendroflora near main roads in Białystok, Biodiv. Res. Conserv. 38: 9–24 | https://doi.org/10.1515/biorc-2015-0013 (PDF: pressto.amu.edu.pl) | © UAM, all rights reserved — tylko cytaty | gatunki, klasy wysokości i obwodu, rzędy przy Andersa |
| 3 | NIK, wystąpienie pokontrolne LBI.403.7.2023 (Białystok, tereny zielone) | https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,lbi~i_23_006_202410081310371728385837~id0~01,typ,kj.pdf | dokument urzędowy | brak inwentaryzacji, liczby nasadzeń |
| 4 | UM Białystok, przetarg DGK-IV.271.2.2017 „Kompleksowa pielęgnacja drzew i krzewów w pasach drogowych… wraz z nasadzeniami”, zał. 2 (OPZ) i zał. 3 (wykaz lokalizacji) | https://www.bip.bialystok.pl/postepowania/zamowienia/kompleksowa-pielegnacja-drzew-i-krzewow-w-pasach-drogowych-na-terenie-miasta-bialegostoku-wraz-z-nasadzeniami.html | BIP — informacja publiczna | paleta gatunków, specyfikacja nasadzeń, liczby drzew per ulica |
| 5 | UM Białystok, „Zieleń w Białymstoku 2019” | https://www.bialystok.pl/resource/14062/32307/Ziele%25C5%2584+w+Bia%25C5%2582ymstoku+2019.pdf | dokument urzędowy | nasadzenia antysmogowe |
| 6 | Rozp. Ministra Infrastruktury z 24.06.2022 — przepisy techniczno-budowlane dot. dróg publicznych, Dz.U. 2022 poz. 1518 | https://eli.gov.pl/api/acts/DU/2022/1518/text/O/D20221518.pdf | akt prawny | § 26, § 80, § 113, § 117 |
| 7 | Rozp. MTiGM z 2.03.1999 — warunki techniczne dróg publicznych, t.j. Dz.U. 2016 poz. 124 (uchylone 21.09.2022) | https://eli.gov.pl/api/acts/DU/2016/124/text/O/D20160124.pdf | akt prawny | § 53: 3,0 m |
| 8 | McPherson, van Doorn, Peper (2016) Urban tree database, USDA FS Research Data Archive (opis: PSW-GTR-253, doi:10.2737/PSW-GTR-253) | https://doi.org/10.2737/RDS-2016-0005 | dane rządu USA | allometria (TS3_Raw_tree_data.csv) |
| 9 | Związek Szkółkarzy Polskich, e-katalog roślin: Thuja occidentalis ‘Smaragd’ (7170), ‘Brabant’ (7109), Ligustrum vulgare (3735) | https://e-katalogroslin.pl/plants/7170,… /7109,… /3735,… | © ZSzP — tylko cytaty | wymiary i rozstaw żywopłotów |
| 10 | Czernecki, Nowosad, Jabłońska (2018) Machine learning modeling of plant phenology…, Int. J. Biometeorol. 62 | https://doi.org/10.1007/s00484-018-1534-2 (PMC6028898) | CC BY 4.0 | fenologia (tekst + Fig. 2) |
| 11 | KartaView — sekwencje 3686129 (2021-06-23), 2769366 (2019-08-25), 2763230 (2019-08-04), 14055 (2016-08-24) | API: `POST https://api.kartaview.org/1.0/list/nearby-photos/` (lat=53.158, lng=23.160, radius=1500) | CC BY-SA 4.0 — referencja, nie tekstura | 18 kadrów trasy C (heading z API) |
| 12 | Panoramax — kolekcje b3131ba1…, 989ab5f4… (2019), a7cf963f… (2026) | `https://api.panoramax.xyz/api/search?bbox=23.07,53.07,23.25,53.19&limit=1000` | CC BY-SA 4.0 — referencja, nie tekstura | 10 kadrów (view:azimuth) |
| 13 | Wikimedia Commons — 26 plików autora Rakoon (2020–2023) | API geosearch + imageinfo (miniatury 1280 px) | CC0 (22), CC BY 3.0 (4 — referencja) | Dojlidy, Lipowa, osiedla |
| 14 | research/g7-street-greenery, research/gptpro/p10-street-greenery-2, research/mistral/p10-greenery-3, p9-furniture-3, p11-dojlidy-photos; ADR 0163, 0170 | repo | — | stan wiedzy, kotwice, unikanie dubli |

## Zapytanie Overpass (nie wykonane — serwery nieosiągalne 2026-11-14 17:05–17:10 UTC: overpass-api.de reset, kumi.systems timeout 200 s, private.coffee reset)
```
[out:json][timeout:180];
area["boundary"="administrative"]["admin_level"="8"]["name"="Białystok"]->.a;
( node["natural"="tree"](area.a); way["natural"="tree_row"](area.a); way["barrier"="hedge"](area.a); );
out body geom;
```
Zamiennik: `uv run --with osmium --with shapely python -I tools/osm_extract_trees.py files/osm/podlaskie.osm.pbf files/osm/` (te same filtry, granica = relacja 2910925). Surowe wyniki: `data/osm_trees.json` (2549), `data/osm_rows.json` (35), `data/osm_hedges.json` (138), `data/osm_roads.json` (osie dróg, 4 MB).

## Nie użyto
Google/Bing/Apple/Yandex, Mapillary (brak tokenu). Źródła niedostępne: TED (PDF pusty), baztech (captcha), platforma ezamawiajacy (przetargi 2020/2023), KartaView API 2.0 bbox („Restricted access”), Openverse (tylko test).
Uwaga: w kilku pierwszych zapytaniach do API Commons nagłówek User-Agent zawierał nazwę organizacji repozytorium; potem zmieniono na ogólny.

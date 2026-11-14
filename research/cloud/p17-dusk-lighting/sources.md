# Źródła — M60 (dostęp 2026-11-14)

## Literatura i dokumenty
| Skrót | Źródło | URL | Licencja | Użycie |
|---|---|---|---|---|
| Schlyter | P. Schlyter, „Radiometry and photometry in astronomy” (FAQ; tabela „Solar illumination on horizontal surface”, tabela luminancji; odsyła do Seidelmann, Explanatory Supplement 1992, s. 490–493) | https://stjarnhimlen.se/comp/radfaq.html | tekst autora — cytowane liczby | C60-001…007, 017…019 |
| Fotios 2024 | Fotios, Uttley i in., „Variance in odds ratios for estimating the deterrent effect of darkness on cycling”, PLOS ONE 2024, Tabela 1 (za Muneerem) | https://pmc.ncbi.nlm.nih.gov/articles/PMC11469482/ (DOI 10.1371/journal.pone.0311964) | CC BY 4.0 | C60-008…010 |
| Patat 2006 | Patat, Ugolnikov, Postylyakov, „UBVRI twilight sky brightness at ESO-Paranal”, A&A 455, 385; Tabela 1 | https://arxiv.org/abs/astro-ph/0604128 | arXiv | C60-012…016 |
| Spitschan 2016 | Spitschan, Aguirre, Brainard, Sweeney, Sci. Rep. 6:26756 | https://pmc.ncbi.nlm.nih.gov/articles/PMC4895134/ | CC BY 4.0 | C60-021…023 |
| PIL | Performance in Lighting — strona „EN 13201-2:2015” (streszczenie klas M, C, P) | https://www.performanceinlighting.com/ww/pl/en-13201-2-2015 | strona producenta; wtórne | C60-025…034 |
| Sensors 2024 | „Comprehensive Assessment of Context-Adaptive Street Lighting…”, Sensors 2024 („class M1 requires an average luminance of 2 cd/m2, while class M2 requires 1.5 cd/m2 and class M6 only requires 0.3 cd/m2”) | https://pmc.ncbi.nlm.nih.gov/articles/PMC11435540/ | CC BY 4.0 | kontrola krzyżowa klas M |
| DIALux M6 | wydruk obliczeń DIALux (03.08.2021) w dokumentacji zamówienia publicznego: „Jezdnia 1 (M6) Lm ≥ 0.30 cd/m², Uo ≥ 0.35, Ul ≥ 0.40, TI ≤ 20 %” | https://platformazakupowa.pl/file/get_new/6b204d06d94a54215924c0e37cf52f7a.pdf | dokument przetargowy | kontrola krzyżowa M6 |
| TED | Ogłoszenia Miasta Białystok (ZDM) „Dostawa i montaż opraw oświetleniowych na terenie Miasta Białegostoku”: 281034-2023, 658997-2023, 697205-2023, 73896-2024 (+ 27 innych przejrzanych) | https://ted.europa.eu/pl/notice/-/detail/<nr> ; API: https://api.ted.europa.eu/v3/notices/search | ogłoszenia urzędowe | C60-037…043 |
| KIO 3018/24 | Wyrok KIO z 17.09.2024 (przetarg ZDM-XIV.271.13.2024) | https://orzeczenia.uzp.gov.pl/Home/PdfContent/20229?Kind=KIO | orzeczenie | C60-045 |
| Augustów | „Audyt energetyczny oświetlenia ulicznego Miasto Augustów…” (BIP) | https://bip.um.augustow.pl/resource/16731/21519/Audyt+energetyczny+o%25C5%259Bwietlenia+ulicznego+Miasto+August%25C3%25B3w+z+instalacja+OZE+%2528002%2529.pdf | dokument urzędowy | C60-036, 054 (ANALOG) |
| BPN-T | OPZ BPN-T.261.1.66.2026, zał. nr 2 | https://bpnt.bialystok.pl/wp-content/uploads/2026/03/BPN-T.261.1.66.2026-ZALACZNIK-NR-2-OPZ.docx | dokument zamówienia | C60-046 (ANALOG) |
| Novak 2025 | Novak i in., „Large residential area light pollution modelling”, CIE x051:2025, DOI 10.25039/x051.2025/kc7797 | https://files.cie.co.at/x051_2025/P0796_ID298TomasNovak_OA_with_cover.pdf | CC BY-NC 4.0 — **tylko referencja, nie pobrano do paczki** | C60-055…058 |
| Bará 2017 | Bará i in., „Estimating the relative contribution of streetlights, vehicles and residential lighting to the urban night sky brightness” | https://arxiv.org/abs/1706.04458 | arXiv | C60-059 |
| NOAA | NOAA GML Solar Calculator — opis obliczeń (formuły w `sun.py`) | https://gml.noaa.gov/grad/solcalc/calcdetails.html | US Gov | tabela zmierzchu |

Zapytania pełnotekstowe TED (POST `https://api.ted.europa.eu/v3/notices/search`, 2026-11-14 ok. 16:50–16:56 UTC), np.
`{"query":"FT ~ \"Gen. W. Andersa, Al. 1000-lecia Państwa Polskiego\" AND publication-number=281034-2023","fields":["publication-number"],"limit":5}` → 1 trafienie.
Frazy z trafieniem w 281034-2023: „Miasta Białegostoku (I)”, „ZDM-XIV.271.31.2023”, „Gen. W. Andersa, Al. 1000-lecia Państwa Polskiego”, „Gen. S. Maczka”,
„Gen. F. Kleeberga”, „Dostawę energooszczędnych opraw ledowych”, „z 07 kwietnia 2023”. W 697205-2023: „Miasta Białegostoku (II)”, „ZDM-XIV.271.32.2023”,
„Gen. Nikodema Saulika, Gen. S. Sosabowskiego, Gen. W. Andersa”, „W. Wysockiego”, „ZDM-VII.7021.1.13.2023”. W 658997-2023: „Miasta Białegostoku (I)”,
„Gen. W. Andersa”, „Udzielenie zamówienia”. Bez trafień (w ogłoszeniach z „opraw” i „Białegostoku”): „Sokólskiej”, „Kombatantów”, „Putry”, „Tysiąclecia”.

## Dane przestrzenne
- **GUGiK ortofoto** WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution` (GetMap 1.3.0, LAYERS=Raster, CRS=EPSG:4326,
  FORMAT=image/jpeg), 2026-11-14 ok. 17:00–17:10 UTC. BBOX (lat/lon min, max), rozmiar:
  Andersa `53.1455155,23.1774451,53.1487145,23.1827431` 3537 px; Maczka `53.1577655,23.1299393,53.1609864,23.1352749` 3561 px;
  Sokólska `53.1484533,23.1504790,53.1508338,23.1544215` 2632 px; Tysiąclecia `53.1427065,23.1546801,53.1458904,23.1599530` 3521 px;
  dodatkowo kafel 0,05 m/px wokół 53.146957, 23.180170 (±48 m, 1920 px) do potwierdzenia 4 słupów na wycinkach 3×. Data nalotu — nieodczytana.
- **OSM** (ODbL, © autorzy OpenStreetMap): Overpass mirror `https://maps.mail.ru/osm/tools/overpass/api/interpreter`, 2026-11-14T16:57:12Z,
  `timestamp_osm_base` 2026-11-14T16:56:36Z, zapytanie: `tools/osm_route_lamps.overpassql` (1663 węzły `highway=street_lamp` w bbox, 198 odcinków ulic trasy).
- **Wikimedia Commons** — 24 kadry autora „Rakoon” (CC0, 2 pliki CC BY 3.0: C60-074, C60-084); metadane z API
  (`action=query&prop=imageinfo|coordinates&iiprop=url|sha1|size|extmetadata|metadata`), lista w `frames_meta.json`. Kandydaci:
  `list=geosearch` w 9 punktach trasy (promień 500–900 m; 1615 plików, limit 500/punkt osiągnięty w 2 punktach) oraz kategorie
  „Apartment blocks in Białystok”, „Housing estates in Białystok”, „Office buildings in Białystok” (47 kategorii, 549 plików),
  „Lipowa Street in Białystok at night”, „Night in Białystok”. Filtr: elewacja Słońca < 1° wg znacznika w nazwie, potem weryfikacja EXIF.
- **Panoramax** `https://api.panoramax.xyz/api/collections?bbox=23.09,53.14,23.20,53.18` — 11 kolekcji, żadna lokalna o zmierzchu/nocą.

## Atrybucja (CC BY 3.0)
- C60-074: „20200710 210912 Wysockiego Street in Białystok.jpg”, Rakoon, CC BY 3.0, Wikimedia Commons (kadr odrzucony, referencja).
- C60-084: „20211216 155723 December 2021 in Białystok.jpg”, Rakoon, CC BY 3.0, Wikimedia Commons (referencja, nie tekstura).

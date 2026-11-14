# M68 — źródła (dostęp 2026-11-14, czasy UTC)

Wszystkie zapytania z User-Agent `kamion-research/1.0 (open-data reference collection)`. Nie używano Google/Bing/Apple/Yandex ani Mapillary.

## 1. OpenStreetMap (ODbL 1.0, © OpenStreetMap contributors)
- Overpass, mirror `https://maps.mail.ru/osm/tools/overpass/api/interpreter` (POST `data=`), **2026-11-14 16:47 UTC**, `timestamp_osm_base` 2026-11-14T16:46:28Z. Zapytanie: `tools/osm_query.overpassql` (bbox 53.070,23.130,53.120,23.235: `landuse=forest`, `natural=wood|scrub`, `aeroway`, nazwane drogi, `barrier=fence`; `out body geom`). Wynik: 130 lasów/zarośli (ways) + 3 relacje, 1 aerodrome, drogi: Dywizjonu 303 (15 ways, 3400 m), Mickiewicza (43; 5967 m), Kuronia (26; 4210 m), Ciołkowskiego (72; 10 049 m).
- Drugie zapytanie (`tools/osm_query_roads.overpassql`, wszystkie drogi) — mirror zwrócił HTTP 504 (3 próby, 17:19–17:21 UTC); zastąpione przez OSM API 0.6: `https://api.openstreetmap.org/api/0.6/map?bbox=23.1870,53.0920,23.1960,53.1010` (17:34 UTC) — stąd strona drogi rowerowej przy ul. Mickiewicza (way 237088754, `highway=path`, `segregated=yes`, po stronie NE osi way 977514047).
- Audyt: `https://api.openstreetmap.org/api/0.6/<typ>/<id>` dla wylosowanych obiektów.

## 2. GUGiK
- **BDOT10k** (PTLZ): `https://opendata.geoportal.gov.pl/bdot10k/schemat2021/20/2061_GML.zip` (m. Białystok; 15 617 449 B; sha256 `12072c1abc654d190b9b16f25b1cea3619635c566276797a22f18c118cff8af8`; pliki z 2026-10-02, wersje obiektów 2024-09-23) oraz `…/20/2002_GML.zip` (pow. białostocki; 91 533 036 B; sha256 `549654815938a2572a1e488db57111639d2597df7cf99cf38acb873cdf1a0875`) — tylko do przypisania kadrów z DK19. Adres paczek z usługi `https://mapy.geoportal.gov.pl/wss/service/PZGIK/BDOT/WFS/PobieranieBDOT10k`.
- **NMPT, lot 2023-09-15** (ARC/INFO ASCII GRID, 0,5 m, PL-1992 / PL-EVRF2007-NH, błąd śr. wysokości 0,10 m, zgłoszenie GI-FOTO.6201.24.2023) — `https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/`:
  - `82987a061eff781688b359d5442402e79f1b3af56c884edae611ecd61b8b367d` 78825_1436510_N-34-107-C-b-3-2.asc
  - `de0cf2d25352ee2d5951548b6b9f7f4b0513d0695e4924b49913359ee1cbc8ac` 78825_1436511_N-34-107-C-b-3-3.asc
  - `b175a3cdedadbab0404c33e9651857e99d17fb7c112a578eac6799f911a30502` 78825_1436512_N-34-107-C-b-3-4.asc
  - `795a6f4d02081ba3ecf7acab3a47c036867709c0b6c4fbd8f3cccfb3c599aba2` 78825_1436515_N-34-107-C-b-4-3.asc
  (pliki: `78825_1436510_N-34-107-C-b-3-2.asc`, `78825_1436511_…-3-3.asc`, `78825_1436512_…-3-4.asc`, `78825_1436515_…-4-3.asc`). Metadane arkuszy: WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/WMS/SkorowidzeUkladEVRF2007` (GetFeatureInfo w 7 punktach) → `data/skorowidze.json`; dla tych samych arkuszy istnieje też lot 2025-04-18 (błąd 0,09 m).
- **NMPT z WCS**: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel`, pokrycie `DSM_PL-KRON86-NH`, `FORMAT=image/x-aaigrid`, `SCALEFACTOR=0.5` (1 m), 92 kafle 250 m (`data/tiles.json`, `tools/dem_fetch.py`). Ustalono (`tools/which_dsm.py`), że usługa podaje lot **2025-04-18** (bezlistny). Uwaga: `FORMAT=image/tiff` zwraca tu obraz 8-bitowy — nie używać.
- **NMT z WCS**: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF`, pokrycie `DTM_PL-KRON86-NH_TIFF`, float32, 1 m, te same 92 kafle. Parametry: `SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&SUBSET=x(E1,E2)&SUBSET=y(N1,N2)&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/2180` (x = współrzędna wschodnia). Skorowidz NMT: `…/NMT/WMS/SkorowidzeUkladEVRF2007` (arkusze 2019–2025).
- Licencja: dane PZGiK udostępniane bezpłatnie do dowolnego wykorzystania (art. 40a ust. 2 pkt 1 Prawa geodezyjnego i kartograficznego); w Capabilities WCS: `Fees: none`, `AccessConstraints: none`. Atrybucja: GUGiK.

## 3. Bank Danych o Lasach (BULiGL / PGL Lasy Państwowe)
- Geometria i atrybuty wydzieleń LP: `https://ogcapi.bdl.lasy.gov.pl/collections/RDLP_Bialystok_wydzielenia/items?f=json&bbox=23.140,53.078,23.215,53.118&limit=1000` → 141 obiektów (`nazwa` = `BDL_01_08_DOJLIDY_2026`).
- Wydzielenia poza LP wg kategorii własności: `https://mapserver.bdl.lasy.gov.pl/ArcGIS/rest/services/WMS_BDL_kat_wlasnosci/MapServer/6/query` (obwiednia 23.135,53.078,23.215,53.122; `outSR=2180`) → 175 obiektów (prywatne 98, gminne 76, inne Skarbu Państwa 1; stan 2023); identyfikacja punktowa: `…/MapServer/identify`.
- Opis taksacyjny: `https://www.bdl.lasy.gov.pl/portal/BULiGL.BDL.Reports/Map/StandDescriptionData?arodesIntNum=…&aYear=…&adressForest=…&jointOwnership=false&label=owner_cat_name` (punkt wywoływany przez narzędzie „opis taksacyjny” mapy `https://www.bdl.lasy.gov.pl/portal/mapy`), 0,4 s między zapytaniami. Nagłówek opisu: „Podlaskie / M. Białystok / RDLP Białystok / Nadleśnictwo Dojlidy / leśnictwo Solnicki Las / PUL 2017-2026”.
- Warunki: `https://www.bdl.lasy.gov.pl/portal/regulamin` — cz. III: „Dostęp do usług … jest powszechny i nieodpłatny”; cz. V: wykorzystujący jest obowiązany „poinformować o źródle, czasie wytworzenia i pozyskania informacji publicznej”; „Prezentowane dane w serwisach mapowych mają charakter poglądowy”. To nie jest licencja CC — dane tabelaryczne przytaczamy ze wskazaniem źródła (BDL, stan 2026 / 2023, pozyskano 2026-11-14).

## 4. Kadry
- **Wikimedia Commons**: `list=geosearch` (16 punktów, promień 600 m, 436 plików) + `prop=imageinfo` (`url|sha1|size|extmetadata`) → 61 kandydatów ≤80 m od głównych kompleksów i ≤120 m od dróg/≤150 m od lotniska; 42 pobrane jako miniatury 1280 px i obejrzane, 29 w manifeście, 13 odrzuconych. Licencje: CC0 (Rakoon) ×28; CC BY-SA 3.0 ×1 (Mickiewicza 2010 — referencja, nie tekstura). API i `upload.wikimedia.org` zwracały HTTP 429 dla wspólnego adresu wyjściowego (oryginały: `retry-after: 600` przez całą sesję) — patrz README §8.
- **Panoramax**: `https://api.panoramax.xyz/api/search?bbox=…&limit=1000`; okno Krywlan (23.135,53.078,23.215,53.122) → **0 kadrów**; DK19 na N od Białegostoku (bbox 23.10,53.205,23.22,53.26 i 23.10,53.26,23.30,53.34) → 415 kadrów w 2 sekwencjach (`989ab5f4-…` 2019-09-01, `b3131ba1-…` 2019-08-15, producent „stanton”, CC BY-SA 4.0); 44 miniatury przejrzane na arkuszu, 13 pobranych w HD (`data/panoramax_pick.json`).
- **KartaView**: `POST https://api.kartaview.org/1.0/list/nearby-photos/` (promień 500 m) w 6 punktach przy lotnisku i Mickiewicza → 0 kadrów (kontrola: centrum miasta 239 kadrów — API działa).
- Openverse: nie użyto do pobierania.
- Poprzednie paczki (bez dublowania): `research/mistral/p11-dojlidy-photos` (P11-056 — tu obejrzany ponownie, z kierunkiem i opisem horyzontu), `research/mistral/p10-greenery-3` i `research/g7-street-greenery` (zieleń uliczna osiedla — inny obszar i inny temat: żywopłoty, korony pojedynczych drzew).

## 5. Obliczenia pomocnicze
- Azymut słońca: `tools/sun.py` (uproszczony algorytm NOAA; czasy z Commons przyjęte jako czas lokalny).
- Zbieżność południków w EPSG:2180 dla λ≈23,17°: +3,3° (dodana do azymutów osi ulic).

# Rynek 3 — nowy punkt PRG i model, runda 29

Odczyt i ogląd: 2026-11-16, bez odtwarzania godziny. **1 nowe ograniczone zapytanie PRG, 1 nowo przeanalizowana bryła, 1 własna figura 800 × 480 px, 0 nowych ZIP i fotografii.**

## Odpowiedź PRG i selekcja

Jedno autoryzowane GetFeature do [KINA/PRG WFS GUGiK](https://mapy.geoportal.gov.pl/wss/ext/wfs/KrajowaIntegracjaNumeracjiAdresowej), z konfiguracją i schematem już odczytanym w R23. Bbox 300 × 300 m wokół wcześniejszego punktu Rynku, limit 100 rekordów, User-Agent Mozilla/5.0, timeout 20 s. Odpowiedź HTTP 200: **51 dopasowanych i 51 zwróconych punktów**, 60127 bajtów, SHA256 `611a8da8a6fe092c608efd24623d579cbac0a8fd3a57776f0c1ca8e23c93e4e8`. Nie wykonano drugiego zapytania lub wariantów endpointu.

SOURCED [literalne rekordy GML]:

| Adres | Literalne gml:pos N,E | E,N do obliczeń |
|---|---|---|
| Knyszyn Rynek 3 | 612337.13 760894.58 | 760894.58, 612337.13 |
| Knyszyn Rynek 4 | 612326.58 760910.8 | 760910.8, 612326.58 |

WFS 2.0 z URN EPSG:2180 ma tu kolejność N,E zarówno dla bbox, jak i punktów. Rysunek i własne obliczenia używają E,N. Dokładny URL, bbox, hash, licznik i źródłowy `timeStamp` są w `source-review.json` i własnym raw `request.json`. Timestamp odpowiedzi nie jest odtworzoną godziną oglądu.

Wybrano **tylko Rynek 3**. Własny test punkt-w-poligonie umieszcza punkt w jednym poligonie lokalnego BDOT oraz w obu modelach. **Adres→buildingId ESTIMATED, formalny wspólny klucz UNVERIFIED.** Punkt Rynek 4 pozyskano przy tym samym zapytaniu, lecz nie tworzono dla niego drugiej analizy CityGML.

## Identyfikator i geometria

SOURCED [pola CityGML i BDOT]: `buildingId` = `LOKALNYID` = **2002917F-3066-5C99-E053-CC2BA8C01CFC**, przestrzeń **PL.PZGiK.335.BDOT10k**. BDOT ma `WERSJA=2025-10-16T00:00:00.000` i `IDEGIB=200804_4.0054.2460_BUD`. Ten ostatni jest wskaźnikiem źródłowym, bez odczytu EGiB lub właścicieli. Literalne ID nie występowało wcześniej w 03/K1; nie jest to ponowienie modeli 3002 lub 3031.

| Produkt | SOURCED — atrybuty | ESTIMATED — geometria |
|---|---|---|
| LoD2 2017 | `lod2Solid`; `wersjaId=2018-01-16T00:00:00`; `zrodloDach=ALS_I`; `aktZrodla=2016`; `roofType=1130` bez dekodowania | min Z 127.12, max Z 135.22, pionowy zasięg około **8.10 m** |
| LoD1 2024 | `lod1Solid`; `wersjaId=2023-11-10T00:00:00`; `zrodloDach=ALS_I`; `aktZrodla=2016`; **measuredHeight=6.77, uom=meter** | min Z 127.320, max Z 134.085, zakres **6.765 m**; obrys zgodny z BDOT, IoU 1.0 |

Nazwy produktów nie są datą dachu: w obu źródłem jest 2016 r. Pole `wersjaId` LoD2 zawiera 2018 r. i nie zostało zastąpione nazwą produktu 2017. LoD1 ma przybliżoną miarę uproszczonego modelu; nie jest ona automatycznie kalenicą. **6.77–8.10 m nie stanowi przedziału tolerancji rzeczywistej wysokości.** Ilościowa dokładność terenowa pozostaje UNVERIFIED.

LoD2 używa pionowo PL-KRON86-NH, LoD1 EPSG:9651; nie odejmowano bezwzględnych Z między produktami. Różnice nie dowodzą przebudowy ani stanu 2026. Nie wyprowadzono kondygnacji, kolorów ścian lub materiału dachu.

## Ogląd i przechowanie

Osobno obejrzano [własną figurę](files/03-RM29-models.png), a po poprawie układu legendy obejrzano ją ponownie: punkt leży wewnątrz niemal zgodnych obrysów, LoD2 pokazuje spadziste połacie i niewielki uskok dachu, LoD1 uproszczony blok. Barwy oznaczają produkty, nie materiał; rzut ma północ siatkową ku górze. Podstawy Z każdego modelu wyzerowano osobno.

Źródła archiwów pozostają te same: [LoD2 GUGiK](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2008_gml.zip) i [LoD1 2024 GUGiK](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2008.zip), CC BY 4.0 według metadanych indeksu R22. Nie przypisano tej licencji automatycznie PRG i BDOT. Oba wspólne ZIP odczytano w miejscu, ich SHA256 potwierdzono; SQLite otwarto `mode=ro`. Małe ekstrakty jednego obiektu, odpowiedź PRG i obliczenia są tylko we własnym raw R29, bez kopiowania archiwów.

Shared `Data/raw/gugik`, R23/R25/R28 oraz parenty pozostały nietknięte. Brak Chrome, Google, 3D Tiles, Overpass/OSM API, Commons/Flickr i git.

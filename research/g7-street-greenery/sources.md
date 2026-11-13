# Źródła G7 (data dostępu 2026-11-13)

## Dane lokalne repo (tylko odczyt)
- OpenStreetMap, ekstrakt Geofabrik `podlaskie-261108.osm.pbf` (stan 2026-11-08), ODbL 1.0, (c) OpenStreetMap contributors. Manifest: `Data/SourceManifests/osm-geofabrik-podlaskie.json` (SHA256 0ff26cd4...). Liczenie: `tools/osm_tile_greenery.py` (wynik: 0 `barrier=hedge`, 0 `natural=tree_row`, 2 `natural=tree` w tile).
- GUGiK BDOT10k powiat 2061 (wycinek tile w `Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json`), dane otwarte GUGiK. Manifest: `Data/SourceManifests/gugik-bdot10k-2061.json`.
- GUGiK ortofotomapa RGB 0,25 m, 2024-05-27 (lokalnie `Data/raw/derived/bialystok-industrial-c/ortho_0p25m.tif`), dane otwarte. Manifest: `Data/SourceManifests/gugik-orto-2024-rgb-0p25-bialystok-industrial-c.json`. Na jej podstawie repo wygenerowało `Data/Regions/bialystok-industrial-c/plot_canopy.json` (korony), użyte w `tools/house_streets_agg.py`.
- Graf dróg tile: `Data/Regions/bialystok-industrial-c/roads.graph.json` (nazwy i osie ulic).
- Kadry Mapillary już pobrane do repo (CC BY-SA 4.0): `Data/raw/mapillary/posesje/manifest.jsonl` (64 kadry). Mapillary API bez tokenu niedostępne — nie odpytywano go. Kadry NIE są kopiowane do `files/`; klasyfikacja: `mapillary_sample.csv`.

## Dokumenty urzędowe
- SGGW (M. Suchocka, K. Kais) dla UM Białystok, "Ocena i wycena usług ekosystemowych wybranych drzew na terenie Miasta Białystok", 15.09.2022, Tab. 2 "Parametry dendrometryczne": https://www.bialystok.pl/resource/26984/66421/Ekspertza+-+wycena+us%25C5%2582ug+ekosystemowych.pdf — pobrane do odczytu (nie dołączone do `files/`), użyte: wysokości, szerokości koron, CBH 4 drzew (G7-T01..T04).
- UM Białystok, "Zieleń w Białymstoku 2019" (plan prac; ochrona drzew w pasach drogowych, rozdz. 14): https://www.bialystok.pl/resource/14062/32307/Ziele%C5%84+w+Bia%C5%82ymstoku+2019.pdf — przeczytane; brak danych o gatunkach/gęstości drzew przyulicznych (tylko cebule kwiatowe, ozdobne drzewa owocowe — wiśnia piłkowana 'Kanzan' ok. 40 szt. w jednej lokalizacji, osłony drzew). Nie użyte do liczb.

## Katalogi botaniczne (liczby, nie teksty)
- Ebben, katalog TreeEbb (karty PDF, wersja polska): adresy w `manifest.csv` (G7-S01..S12). Pola: Kształt korony, Struktura korony, Wysokość, Szerokość.
- (Wynik wyszukiwania, nie użyte) e-katalogroslin.pl (PZSz) — Thuja 'Smaragd' 4-6 m / 1-1,8 m zgodne z Ebben.

## Wikimedia Commons (zdjęcia, geotagi)
Zapytanie `list=geosearch` (promień 1,2 km od 53,1535 N 23,1515 E, przestrzeń nazw plików) i `prop=imageinfo|extmetadata`; 300 wyników: CC0 256, CC BY-SA 3.0 23, CC BY 3.0 10 i inne. Wybrano 12 plików autora Rakoon (CC0), strona opisu w `manifest.csv` (G7-P01..P12). Autor wskazany mimo braku wymogu CC0.

## Źródła przeczytane, ale NIE użyte do liczb
- pl.wikipedia: Lipa drobnolistna, Klon zwyczajny, Kasztanowiec zwyczajny, Jesion wyniosły (wysokości gatunków 18-30 m; tabelki przyrostu w artykułach (np. klon 20 lat = 20 m) niezgodne z pomiarem białostockim 170 lat = 20 m — pominięte).
- Wyniki wyszukiwania (bez pobrania): ZDM Warszawa "Drzewa w mieście" (spadek udziału lip z 48% w 1973); Borowski & Latocha, Rocznik Dendrologiczny 54 (straty drzew przyulicznych w Warszawie); ZZW Warszawa, Załącznik 1 do Standardu sadzenia drzew (lista gatunków bez wymiarów koron) https://zzw.waw.pl/wp-content/uploads/2026/03/Zalacznik-nr-1-do-Standardu-sadzenia-drzew-na-terenie-m.st_.-Warszawy-z-doborem-gatunkowym.pdf; poradniki żywopłotów (muratordom.pl, kb.pl, obi.pl) — bez ilościowych danych o udziale posesji z żywopłotem.

## Wykluczone / niedostępne
- Google Maps/Street View/Earth/3D Tiles: niewykorzystane.
- Mapillary Graph API: wymaga tokenu — niedostępne; Panoramax (api.panoramax.xyz, zapytanie bbox 23,1465-23,1555 E, 53,1495-53,1595 N, 2026-11-13): 12 kadrów, wszystkie przy północnym końcu Andersa (53,1587-53,1595 N), brak pokrycia ulic domów (autor stanton, 2019, CC BY-SA 4.0) — niepobrane.
- Brak otwartego rejestru drzew przyulicznych Białegostoku (BIP/Geoportal miejski) w wynikach wyszukiwania i w `Data/raw/refs/bialystok-open-data` (tylko parki, skwery, lasy, pomniki przyrody).

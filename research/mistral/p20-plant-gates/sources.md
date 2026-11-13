# P20 — źródła

Wszystkie źródła licencyjnie zgodne z komercyjnym użyciem w grze (CC0/ODbL/licencja otwarta GUGiK) lub użyte wyłącznie jako **referencja** (bez pobrania treści do tekstur). Zdjęcia CC BY-SA 4.0 (Panoramax) — referencja, nie tekstura. Żadnych treści Google.

## 1. Dane przestrzenne GUGiK (licencja otwarta)

- **NMPT (DSM) 1 m, EVRF2007-NH** — WCS:
  `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DSM_PL-EVRF2007-NH&SUBSET=x(E1,E2)&SUBSET=y(N1,N2)&FORMAT=image/x-aaigrid`
  (SUBSET w nawiasach; śródokna: A: x(780520,780840) y(590180,590500); B: x(780050,780300) y(590320,590510); pobranie 2026-11-13)
- **NMT (DTM) 1 m, EVRF2007-NH** — WCS:
  `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModel?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-EVRF2007-NH&SUBSET=x(E1,E2)&SUBSET=y(N1,N2)&FORMAT=image/x-aaigrid`
- **LoD1 2024 (Modele 3D budynków)**: https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/
  - hala A: gml:id `ID-2061-2BE4B431-BC59-1BF0-E053-CC2BA8C0D140`, measuredHeight **18,92 m** (152,06→170,98);
  - zakład B: gml:id `ID-2061-941cfc23-bd8b-40d5-a49b-d1bba751d5bd`, measuredHeight **12,72 m**;
  - LoD2 2017: obu budynków brak w zbiorze (luka).
- **KIEG (geoportal ewidencyjny)** — GetFeatureInfo: działki 206101_1.0021.767/20 (A) i 767/29 (B), obrysy EGiB 206101_1.0021.1495_BUD / 1580_BUD; integracja.gugik.gov.pl, dostęp 2026-11-12.
- **WFS PZGIK (BDOT10k/EGiB atrybuty)**: brak dostępu (HTTP Unauthorized) — kody funkcji UNVERIFIED.

## 2. OSM (ODbL)

- Hala A: https://www.openstreetmap.org/way/471492583 (API: /api/0.6/way/471492583/full)
- Zakład B: https://www.openstreetmap.org/way/513010463 (API: /api/0.6/way/513010463/full)

## 3. Kadry — Wikimedia Commons (wszystkie Rakoon; miniatury ≤1600 px przez thumb.php)

| id robocze | plik | data | licencja | url |
|---|---|---|---|---|
| P11-094 | 20230903 135016 | 2023-09-03 | CC0 | https://commons.wikimedia.org/wiki/File:20230903_135016_September_2023_in_Bia%C5%82ystok.jpg |
| P11-095 | 20230903 135017 | 2023-09-03 | CC0 | https://commons.wikimedia.org/wiki/File:20230903_135017_September_2023_in_Bia%C5%82ystok.jpg |
| P11-093 | 20230903 135135 | 2023-09-03 | CC0 | https://commons.wikimedia.org/wiki/File:20230903_135135_September_2023_in_Bia%C5%82ystok.jpg |
| NEW 134854 | 20230903 134854 | 2023-09-03 | CC0 | https://commons.wikimedia.org/wiki/File:20230903_134854_September_2023_in_Bia%C5%82ystok.jpg |
| NEW 124730 | 20240623 124730 | 2024-06-23 | CC0 | https://commons.wikimedia.org/wiki/File:20240623_124730_June_2024_in_Bia%C5%82ystok.jpg |
| NEW 124756 | 20240623 124756 | 2024-06-23 | CC0 | https://commons.wikimedia.org/wiki/File:20240623_124756_June_2024_in_Bia%C5%82ystok.jpg |
| NEW 151306 | 20221103 151306 | 2022-11-03 | CC0 | https://commons.wikimedia.org/wiki/File:20221103_151306_November_2022_in_Bia%C5%82ystok.jpg |
| NEW 151248 | 20221103 151248 | 2022-11-03 | CC0 | https://commons.wikimedia.org/wiki/File:20221103_151248_November_2022_in_Bia%C5%82ystok.jpg |
| P11-122/8866 | 8866 November 2022 | 2022-11-03 | CC0 | https://commons.wikimedia.org/wiki/File:8866_November_2022_in_Bia%C5%82ystok.jpg |
| 8865/8870/8872/8873/8877/8880 | seria Kuronia | 2022-11-03 | CC0 | https://commons.wikimedia.org/wiki/File:8865_November_2022_in_Bia%C5%82ystok.jpg (i analogicznie 8870, 8872, 8873, 8877, 8880) |
| P11-063 | 20240623 124644 | 2024-06-23 | CC0 | https://commons.wikimedia.org/wiki/File:20240623_124644_June_2024_in_Bia%C5%82ystok.jpg |

Seria B z 2019-11-10 (Rakoon, CC0, 5520 px, bez EXIF GPS — pozycja z tytułu/kategorii; do oględzin):
6722 „Intersection of Mickiewicza and Kuronia street in Bialystok 2019”, 6719, 6721, 6724, 6726, 6727 (Kuronia); 6703, 6706, 6709, 6710, „DSC 6711”, 6712, 6697, 6698 (Adama Mickiewicza). URL-e w formacie `https://commons.wikimedia.org/wiki/File:<tytuł z podkreślnikami>.jpg`.

## 4. Typowe wymiary bram (liczby; bez nazw producentów w opisach dla gry)

1. Karta produktu segmentowej bramy przemysłowej (PDF):
   https://www.assaabloyentrance.com/master-blueprint/pl/product-assets/commercial-industrial-doors/oh1042p/downloads/product-datasheet/product_datasheet_assa_abloy_oh1042p_psdi_pl-pl.pdf
   Cytat: „Szerokość światła bramy Min.: 1200 mm Maks.: 8000 mm; Wysokość światła otworu Maks.: 6000 mm”. Dodatkowo: grubość panelu 42 mm, wysokość sekcji 545 mm.
2. Specyfikacja techniczna bram segmentowych przemysłowych (PDF):
   https://staszynska.pl/wp-content/uploads/2019/02/STASZY%C5%83SKA-Bramy-segmentowe-przemys%C5%82owe-specyfikacja-techniczna.pdf
   Cytat: „szerokość maksymalna - 4500mm, z kształtownikiem usztywniającym od 4500mm do 8000mm; wysokość maksymalna - 6000mm”; minimum dla samochodów osobowych: 2300×2000 mm.
3. Norma odniesienia: **PN-EN 13241** „Bramy przemysłowe, handlowe, garażowe i bramy dla pomieszczeń użytkowych — wymagania i klasyfikacja” (odniesienie bibliograficzne; nie cytowano liczb z tekstu normy).

## 5. Sondy ujemne (dokumentacja luk)

- **Panoramax (api.panoramax.xyz)**: 0 kadrów w otoczeniu A i B (zapytania bbox/point, 2026-11-12/13). Licencja zdjęć CC BY-SA 4.0 — tylko referencja.
- **KartaView**: 0 kadrów w rejonie (sonda obszarowa).
- **Openverse** (CC0/BY/BY-SA): wyniki = lustro Wikimedia Commons/Flickr; nic nowego poza manifeście P11 („Rosti” — strona jedzeniowa, nieistotna).
- **Mapillary**: nie sondowano — API wymaga tokenu; zadanie zabrania używania cudzego tokenu.
- **dane.gov.pl/api, bialystok.geoportal2.pl**: nieosiągalne z środowiska badawczego (timeout/DNS).
- **WFS PZGIK (BDOT10k/EGiB)**: HTTP Unauthorized — kody funkcji budynków UNVERIFIED.
- Kadry Commons ≤60 m od obrysów A/B: wszystkie już w manifeście P11 (porównanie URL, 2026-11-12).

## 6. Zasady

- Google Maps/Street View/Earth/3D Tiles — **nieużywane** (zakaz D43).
- Kolor opisany wyłącznie słownie; brak odczytów RGB z pikseli.
- Wymiary: SOURCED (źródło) albo ESTIMATED z metodą; nierozstrzygalne: UNVERIFIED z powodem.
- Marki (nazwy firm z OSM/Commons) — tylko w uwagach technicznych; w opisach dla gry: „napis firmowy, nie odtwarzamy”.

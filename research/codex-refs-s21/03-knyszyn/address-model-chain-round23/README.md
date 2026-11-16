# Knyszyn — adres i identyfikator modelu, runda 23

Odczyt 2026-11-16, bez dokładnej godziny. **Wynik: oficjalny punkt „Rynek 1” znajduje się wewnątrz badanego obrysu, ale formalne połączenie adresu z CityGML pozostaje UNVERIFIED.** Przypisanie do Rynek 1 jest teraz poparte danymi urzędowymi jako **wniosek przestrzenny ESTIMATED**, a nie samym OSM lub podpisem K1.

## Łańcuch danych

1. **SOURCED [istniejący CityGML R22 i lokalny BDOT10k]:** model ma `buildingId=2002917F-3002-5C99-E053-CC2BA8C01CFC`, przestrzeń nazw `PL.PZGiK.335.BDOT10k`. Dokładnie te same wartości znajdują się w polach `LOKALNYID` i `PRZESTRZENNAZW` tabeli `OT_BUBD_A`. To zgodność identyfikatora i przestrzeni nazw, nie dopasowanie przez podobny kształt.
2. **SOURCED [ten sam rekord BDOT]:** pole `IDEGIB` ma literalną wartość `200804_4.0054.2323_BUD`. Wersja rekordu BDOT: `2025-10-16T00:00:00.000`. Nie sprawdzano rekordu EGiB ani informacji o właścicielach; nie twierdzimy, że sam odczyt tego pola zweryfikował aktualność ewidencji.
3. **SOURCED [jedna odpowiedź produkcyjnej usługi WFS KINA GUGiK, typ `adresyUlice:A07_Punkty_adresowe`]:** w bbox 40 × 40 m otrzymano dwa punkty adresowe PRG, Knyszyn / Rynek / 1 oraz 2. Punkt numeru 1 ma pozycję WFS EPSG:2180 `612352.56 760870.95` w kolejności N,E. Po uporządkowaniu jako GIS E,N jest to E 760870,95 / N 612352,56. To pozycja punktu adresowego, **nie GPS aparatu ani narożnik domu**.
4. **ESTIMATED [własna kontrola geometrii]:** punkt numeru 1 leży wewnątrz obrysu BDOT oraz przyziemi obu modeli LoD1/LoD2 z R22. Punkt numeru 2 jest poza tymi obrysami. Przyziemie odczytanego BDOT i LoD1 2024 jest identyczne geometrycznie — iloraz pola przecięcia i sumy wynosi 1,000. Nie trzeba tu przenosić niepewności dopasowania OSM na identyfikator BDOT, ale punkt-w-poligonie nadal nie jest urzędowym kluczem adres–budynek.

## Dlaczego nie jest to pełny join

SOURCED [DescribeFeatureType]: usługa punktów udostępnia adres, identyfikatory gminy/miejscowości/ulicy, `ID_IIP` i punkt. Nie ma pola `buildingId`, `LOKALNYID` ani `IDEGIB`. Identyfikator adresu numer 1 to `PL.PZGIK.200.PRG_0d6d3d35-8d36-44d4-bd36-fa6fb91bf437_2025-10-01T14:00:58+02:00`; nie jest równy identyfikatorowi modelu i nie zawiera odczytanego klucza powiązania. Data wewnątrz tego ciągu pozostaje częścią literalnego identyfikatora wersji — nie datą oględzin ani przebudowy domu.

Nie wywodzimy z tego prawa do automatycznego przypisania każdej historycznej fotografii K1 do tej bryły. Nadal nie jest to pomiar stanu 2026, liczby kondygnacji lub rzeczywistej wysokości kalenicy. R22 pozostaje nietknięty, wraz z jego oznaczeniem kandydata i ograniczeniami wymiarów.

## Źródła, zakres i odtwarzalność

Najpierw przeczytano K1 i dane modelu/OSM z R22. Wykorzystano wyłącznie istniejący lokalny plik:

`C:/Users/matma/Documents/Claude/kamion/Data/raw/gugik/bdot10k-2008/gpkg/PL.PZGiK.335.BDOT10k.2008__OT_BUBD_A.gpkg`

Plik otwarto SQLite `mode=ro`. Wybrano jeden rekord po dokładnym `LOKALNYID`; nie kopiowano archiwum ani tabel osób. SHA256 źródła, wybrane pola i obrys kontrolny znajdują się we własnym raw R23.

Produkcyjny endpoint: `https://mapy.geoportal.gov.pl/wss/ext/wfs/KrajowaIntegracjaNumeracjiAdresowej`. Odczytano GetCapabilities i DescribeFeatureType, następnie wykonano **1 zapytanie danych GetFeature** ograniczone bbox i `count=10`; odpowiedź zawiera dokładnie 2 punkty. Nie wykonano drugiego zapytania danych. Brak pola łączącego adres z budynkiem jest wnioskiem z przeczytanego schematu, nie z samego braku dopasowania nazw.

Oficjalny [opis usług adresowych PRG](https://www.geoportal.gov.pl/aktualnosci/nowe-uslugi-ogc-api-features-dla-danych-prg-i-prng/) przeczytano jako dokumentację. Jego kolekcja OGC API zawierała odsyłacze do hosta `ogcapitest`; nie odpytywano tam obiektów. Zastosowano produkcyjny WFS wskazany w oficjalnym wyniku wyszukiwania GUGiK, którego własne GetCapabilities określa dane jako PRG. Pełny komunikat gov o zmianie adresu zwrócił timeout; nie ponawiano. Nie przypisano punktom licencji CC bez jej jawnego potwierdzenia.

`source-review.json` i `manifest.csv` zawierają własne parafrazy, metadane i odnośniki. Surowe odpowiedzi: `C:/Users/matma/Documents/Claude/kamion/Data/raw/refs/codex-s21/03-knyszyn/address-model-chain-round23/`. 0 nowych archiwów, 0 zdjęć, bez Chrome, Google, 3D Tiles, Commons, Flickr, OSM API i Overpass. Bez zmian parentów, R22 i gita.

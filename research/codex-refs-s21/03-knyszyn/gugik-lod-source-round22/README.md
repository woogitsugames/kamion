# Knyszyn — źródło CityGML i porównanie jednej bryły, runda 22

Odczyt 2026-11-16, bez dokładnej godziny. **0 nowych pobranych archiwów, 0 fotografii, 1 nowa analiza porównawcza istniejących danych i 1 obejrzany wykres 800 × 500 px.** Oba wspólne ZIP-y GUGiK pozostały niezmienione. Nie użyto 3D Tiles, Geoportalu 3D, Google ani kodu gry.

## Dostępność i publiczne źródła

Najpierw porównano istniejące `03-M01`, dane LoD2 i K1. K1-061 / fotografia K1-P02 ma podpis „Rynek 1”, ale nie ma współrzędnych. Punkt selekcyjny wyznaczono więc z istniejącego lokalnego obrysu OSM way 300667350, użytego wcześniej jako kandydata tego adresu. To jawna selekcja przestrzenna, **nie nowy urzędowy dowód adresu**. Punkt ma E 760869,95 / N 612349,10 w EPSG:2180; nie jest pozycją aparatu ani narożnikiem budynku.

SOURCED [GetCapabilities i GetFeatureInfo oficjalnej usługi `https://mapy.geoportal.gov.pl/wss/service/PZGIK/FOTO/WMS/ModeleBudynkow3D`, odpowiedzi w raw]: pod tym punktem skorowidz wskazuje powiat moniecki, TERYT 2008, oraz:

| Produkt | Publiczne archiwum | HEAD 16.11.2026 | Rozmiar |
|---|---|---|---|
| LoD1 2024 | [2008.zip](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2008.zip) | 200 | SOURCED 8 267 243 B |
| LoD2 2017 | [2008_gml.zip](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2008_gml.zip) | 200 | SOURCED 14 184 918 B |

Skorowidz bezpośrednio łączy oba produkty z [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.pl). Lokalny rozmiar każdego wcześniejszego ZIP-a zgadza się z HEAD; SHA256 policzono lokalnie i zapisano w JSON. Nie deklarujemy weryfikacji SHA pliku z serwera przez ponowny GET. Last-Modified w HTTP to data pliku na serwerze, nie data pomiaru dachu.

## Co oznacza LoD1

SOURCED [oficjalna dokumentacja GUGiK, sekcje o LoD1 i atrybutach 2024, [strona źródłowa](https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/)]: CityGML 2.0 LoD1 upraszcza budynek do bryły z płaską górą. Podstawa pochodzi z BDOT10k/NMT, góra z mediany ALS. Dokument wskazuje PL-EVRF2007-NH i określa `measuredHeight` jako przybliżoną wysokość. `aktZrodla` dotyczy aktualności geometrii dachu. **Nie znaleziono na tej stronie ilościowej dokładności ± dla wybranego obiektu; pozostaje UNVERIFIED.** LoD1 nie dowodzi płaskiego rzeczywistego dachu, wysokości kalenicy ani liczby kondygnacji.

## Ten sam identyfikator, różne modele

SOURCED [oba oryginalne CityGML, jeden wyodrębniony obiekt z każdego produktu]: `buildingId=2002917F-3002-5C99-E053-CC2BA8C01CFC`, przestrzeń nazw `PL.PZGiK.335.BDOT10k`. Zgodność identyfikatora w obu produktach jest pewna. **Przypisanie do adresu Rynek 1 pozostaje ESTIMATED** z lokalnego OSM, nie z adresu wpisanego w CityGML.

| Właściwość | LoD2 2017 | LoD1 2024 |
|---|---|---|
| `wersjaId` — literalny atrybut BDOT | SOURCED 2013-01-01T00:00:00 | SOURCED 2023-11-10T00:00:00 |
| `aktZrodla` dachu | SOURCED 2016 | SOURCED 2016 |
| `zrodloDach` | SOURCED ALS_I | SOURCED ALS_I |
| `measuredHeight` | brak tego atrybutu w obiekcie | SOURCED 7.5, `uom=meter` |
| Względny zasięg Z od własnej podstawy | ESTIMATED 8,7 m | ESTIMATED 7,5 m |
| Minimalny obrócony prostokąt przyziemia | ESTIMATED 8,4 × 13,5 m | ESTIMATED 8,4 × 8,7 m |
| Pole modelowego przyziemia | ESTIMATED 95,0 m² | ESTIMATED 68,7 m² |

To parametry **konkretnej geometrii źródłowej**, nie pomiar geodezyjny obecnego budynku ani powierzchnia użytkowa. Wymiary prostokąta nie są automatycznie długościami elewacji. Zapisane dokładniejsze liczby w JSON służą odtworzeniu obliczeń, nie zwiększają dokładności terenowej.

Współczynnik nakładania przyziemi LoD1/LoD2, pole przecięcia / pole sumy: ESTIMATED 0,640. Dopasowanie do lokalnego OSM: odpowiednio 0,619 i 0,673. Nie jest na tyle jednoznaczne, by usuwać oznaczenie kandydata adresowego. Pozycje obrysów i ich zakresy różnią się; **nie interpretujemy tego jako dowodu rozbudowy lub rozbiórki**. Oba modele zachowują to samo stare źródło dachu mimo różnych roczników produktów.

LoD2 deklaruje w GML EPSG:2180 + PL-KRON86-NH; LoD1 deklaruje EPSG:2180 + EPSG:9651. Nie odejmowano bezwzględnych Z między produktami. Wykres pokazuje każdą bryłę względem jej własnego minimum Z; różnica 8,7 / 7,5 m obejmuje inne uproszczenie i obrys, nie jest pomiarem zmiany wysokości.

## Ogląd i odtwarzalność

`files/03-GL22-model-comparison.png` obejrzano po wygenerowaniu; legendę przeniesiono poza obrysy, a poprawiony obraz obejrzano ponownie. Po lewej są rzuty źródłowych przyziemi i OSM, po prawej rzeczywiste ściany/powierzchnie jednego ID odczytane z CityGML. Niebieski model ma zróżnicowane połacie i niższą część, pomarańczowy jest uproszczoną bryłą. Barwy służą identyfikacji produktu, nie opisują materiału dachu. Góra rzutu to północ siatkowa EPSG:2180, nie ustalony azymut aparatu.

Parser obsłużył zarówno `gml:pos`, jak i `gml:posList`; pierwsza próba ograniczona do posList nie znalazła geometrii LoD2 i została poprawiona przed obliczeniami. Pole liczono z pierścienia przyziemia, prostokąt z minimum rotated rectangle, zasięg Z jako max–min. Pełne ściany i dwa małe ekstrakty GML zapisano wyłącznie we własnym raw R22. Do gita trafiły własne parafrazy, metadane, mały JSON z obrysami i wykres; bez kolejnej kopii ZIP.

Pełne źródła, żądanie punktowe, SHA i ograniczenia: `source-review.json`, `geometry-summary.json`. Wyniki surowe: `C:/Users/matma/Documents/Claude/kamion/Data/raw/refs/codex-s21/03-knyszyn/gugik-lod-source-round22`. Główne manifesty, wcześniejsza analiza i wspólne dane poza tym katalogiem bez zmian. Nie używano Chrome, OSM API, Overpass, Commons ani Flickr.

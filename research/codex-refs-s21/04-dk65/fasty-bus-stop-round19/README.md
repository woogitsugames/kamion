# Fasty: zjazd i pobocze — runda 19

Cel: zweryfikować słabiej udokumentowany punkt przystankowy w Fastach i rzeczywiste styki nawierzchni w korytarzu DK65. Wynik jest użyteczny dla zjazdu i pobocza; przystanku te kadry nie potwierdzają.

## Wynik

- SOURCED [indywidualny ogląd dwóch permalinków w manifest.csv]: **2 nowe ekspozycje**, **1 ten sam widoczny zjazd**, **0 potwierdzonych wiat lub znaków przystanku**, **0 pobranych fotografii**. Obejrzano każdy obraz osobno, z powiększonym panelem zdjęcia; bez zapisu zrzutów.
- SOURCED [UI obu kadrów]: autor picturehoover, data **27 czerwca 2020 r.** Są to referencje historyczne. Stan po robotach w 2026 r. pozostaje UNVERIFIED.
- SOURCED [obrazy]: czerwonołososiowe prostokątne elementy zjazdu dochodzą do szarego ziarnistego pobocza; dalej widać czarne ogrodzenie z pionowych prętów i trawiaste podłużne obniżenie. Drugi kadr lepiej pokazuje kontakt pobocza z trawą. Barwy są obserwacją obrazu w jego oświetleniu, bez parametrów RAL/RGB.
- UNVERIFIED: beton/ceramika elementów, skład pobocza, głębokość i funkcja obniżenia, konstrukcja przepustu, gatunki drzew, wymiary oraz przejezdność ciężarówki. Ciemna plama w trawie nie stanowi dowodu otworu przepustu.

## Lokalizacja i ograniczenia

SOURCED [istniejące `research/dk65-knyszyn-refs/data/osm_corridor.json`]: punkt wyboru OSM7283285540 ma tagi bus=yes, highway=bus_stop, public_transport=platform i współrzędne 53.1755996,23.0312231. Brakuje nazwy. K1 przypisuje mu **10,417 km trasy badawczej**, co nie jest państwowym kilometrażem DK65. Punkt mieści się w bbox kafla dk65-02 zapisanym w `tiles_wgs84.json`.

To źródło służyło do wyboru miejsca. Kamera GPS i dokładne przypisanie każdego kadru do osi/kafla pozostają UNVERIFIED; środek viewportu nie został użyty jako GPS. Zbieżność miejsca zaznaczonego w viewerze z punktem selekcji jest kontekstem, nie pomiarem pozycji kamery. Bieżące oznaczenie drogi po zmianach przebiegu pozostaje UNVERIFIED.

Podkład OpenStreetMap oraz All captures potwierdzono w widocznym menu. Nie korzystano z API Mapillary, tokenów, nowego OSM/Overpass ani pobierania mediów. Licencję obrazów odsyłamy do wcześniejszego oficjalnego audytu `../mapillary-browser-round2/`; w tej rundzie przechowujemy wyłącznie permalinki i własne opisy.

Dokładne ID nie występowały wcześniej w lokalnym s21/K1. Dwa kadry przedstawiają tę samą fizyczną przestrzeń i zjazd, dlatego nie zwiększają liczby odrębnych zjazdów do dwóch. Data własnego oglądu: **2026-11-16**, bez deklarowania niezmierzonej godziny.

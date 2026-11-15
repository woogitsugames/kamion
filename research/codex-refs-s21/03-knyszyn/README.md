# 03 — Knyszyn: bryły i detale fasad — WIP

Cel: dać sesji rynku rozróżnienia brył, kolorów i detali, które gubią się w ogólnym opisie „1–2 kondygnacje”. Pięć kadrów obejrzano osobno ponownie. To pogłębienie istniejącego K1, **0 nowych pobrań zdjęć**, 5 pomniejszeń lokalnych kopii K1, 0 kadrów link-only. Licencje i autorów ponownie sprawdzono przez Commons API; zapis w `data/licences-commons.json`. Daty 2009/2012/2024, aktualny stan 2026 UNVERIFIED. Miniatury ≤ 800 px. To nie są zdjęcia właściciela.

## Wnioski dla generatora

- 03-001, Rynek 1 (2012): SOURCED [obraz, manifest] — 2 górne okna po prawej stoją w podniesionej części dachu, z nisko schodzącymi połaciami po bokach; z lewej osobna mniejsza część z oknem. Nie wystarczy opisać całości jako prostego pełnego piętra. Pełna konstrukcja/przekrój dachu UNVERIFIED.
- 03-002, UM (2009): SOURCED [obraz] — 2 pełne kondygnacje plus rząd lukarn; głęboka dwupoziomowa loggia, 4 kolumny widoczne w kadrze. Czerwony dach, jasny tynk, żółtobeżowe opaski; kolor fizyczny/RAL UNVERIFIED.
- 03-003, Kościelna 4 (2012): SOURCED [obraz] — parter z szeroką centralną lukarną/balkonem i dużymi połaciami dachu po bokach. Wejście pod 2 łukami, ogrodzenie ceglane z metalowymi przęsłami. Pełny typ i geometria dachu UNVERIFIED poza widocznym kształtem.
- 03-004, kościół (2024): SOURCED [obraz] — jasna fasada, czerwony ostrosłupowy hełm, rozeta, czerwone gzymsy/obróbki; mur przed figurą i czarne dwuramienne latarnie. Bruk układa się w łukowe pasy, nie w regularną prostokątną siatkę.
- 03-005, ceglana fasada przy Rynku (2012): SOURCED [obraz] — 2 pełne poziomy plus okno w szczycie, balkon, podwyższony parter i boczne biegi schodów. Okno w szczycie nie oznacza trzeciego pełnego piętra.

## Luki

Wymiary metryczne i proporcje ortogonalnej elewacji UNVERIFIED: kadry są perspektywiczne. Nie wyprowadzono szerokości z liczby okien ani kondygnacji z wysokości modelu. Budynki 03-001/003 wymagają kontroli bryły z LoD2/ortofoto, szczególnie przed przyjęciem etykiety „dach mansardowy”. Aktualność elewacji/ogrodzeń z 2009/2012 UNVERIFIED. Dzisiejsze pierzeje, DK65 przez miasto i mała architektura wymagają dalszego uzupełnienia. Obrys posadzki fontanny został sprawdzony nowym WMS w 03-006 poniżej; wygląd z poziomu ulicy i układ dysz pozostają UNVERIFIED.


## Uzupełnienie: nowy wycinek GUGiK fontanny (03-006)

**Nowy materiał:** 1 wycinek ortofoto WMS (480×480 px, 48×48 m), pobrany 2026-11-15; 5 wcześniejszych kadrów fasad pozostaje pogłębieniem K1. Żadnych nowych zdjęć ulicznych ani zdjęć właściciela. `data/fountain-wms.json` zawiera pełny URL, bbox EPSG:2180, skalę 0,1 m/px i SHA256. Wycinek obejrzano osobno.

SOURCED [03-006, Geoportal WMS]: w jasnej płaskiej posadzce widoczny kwadratowy ciemny obrys i mały ciemny element przy środku; nie widać strumieni wody ani podniesionej misy. Korony i cienie drzew zasłaniają część otoczenia. Nie określam tego elementu jako kratki odpływowej bez obrazu z ziemi.

ESTIMATED [własny pomiar 03-006]: cztery ręcznie wskazane narożniki `(91,179), (145,169), (156,223), (102,234)` px; odległości euklidesowe ×0,1 m/px i pole wzorem Gaussa. Widoczny obrys ma około **5,5×5,6 m**, pole około **31 m²**; przyjmuję ostrożnie ±0,4 m dla boków (wybór narożników ±2 px, brak pomiaru terenowego). To wymiary **obrysu na posadzce**, nie potwierdzona długość instalacji/dysz ani rozmiar całego okrągłego placu. K1 podawał ~6,3×5,8 m — tej wartości nie powielam jako własnego pomiaru; różnica może wynikać z wyboru krawędzi. Przed skalowaniem modelu zalecane porównanie obu obrysów.

SOURCED [WFS GUGiK, `data/fountain-sheet-2025.xml`]: arkusz N-34-106-B-b-1-4 ma datę 2025-05-27 i piksel 0,1 m. Zapytanie do skorowidza 2026 dla tego bbox zwróciło pustą kolekcję (`data/fountain-sheet-2026.xml`). WMS nie jest czasowo przypięty do arkusza; przyporządkowanie daty to najnowszy znaleziony arkusz w tych zapytaniach, nie gwarancja serwera WMS.

UNVERIFIED: liczba i układ dysz, wysokość strumieni, rodzaj odpływu, kolor podświetlenia, stan działający w dniu pobrania. Ortofoto nie potwierdza tych szczegółów. OSM API zwróciło429; nie korzystano z niepobranych geometrii i nie próbowano obejścia.


## Komunikaty UM: chronologia i wyposażenie (2 źródła tekstowe link-only)

SOURCED [03-D01, UM, 2023-08-25](https://www.knyszyn.pl/asp/i-%E2%99%A5-knyszyn,239,artykul,1,5400): zrewitalizowany rynek dostępny od2020; fontanna podświetlana, nocą świeci kolorowo. W sierpniu2023 dołożono przenośny podświetlany napis „I ♥ KNYSZYN”. To potwierdza istnienie światła, ale nie liczbę reflektorów, moc ani stałą barwę. Pozycja przenośnego napisu w2026 UNVERIFIED.

SOURCED [03-D02, UM, 2022-07-21](https://www.knyszyn.pl/asp/nasz-wspolny-rynek---apel-do-mieszkancow,239,artykul,1,4982): po rewitalizacji są brukowane alejki, podświetlana fontanna, ławki i stoliki; w sezonie2022 urząd opisuje czerwone pelargonie w donicach. Nie przenosimy gatunku i koloru sezonowych nasadzeń bezwarunkowo do2026.

**Wniosek dla generatora:** fotografie wnętrza parku sprzed2020 nie są dowodem obecnego układu nawierzchni/wyposażenia. Bryły fasad z2009/2012 również wymagają aktualizacji, choć sama data rewitalizacji nie dowodzi ich przebudowy. Źródła tekstowe są odczytane; zdjęć z komunikatów nie pobrano i nie opisano. Łączny nowy materiał w tym uzupełnieniu: 1 ortofoto + 2 dokumenty tekstowe link-only, 0 nowych fotografii ulicznych; 5 poprzednich fotografii to ponowny przegląd K1.

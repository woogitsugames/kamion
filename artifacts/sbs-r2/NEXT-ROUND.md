# Plan wejścia w r3 po zamknięciu r2

Nowe źródło: main 3ebd95d4 i REVIEW-2026-11-12-s11-0125.md. Nie jest to wynik nowego renderu SBS. Przed próbami: merge najnowszego main, regeneracja bez fallback, import i bazowe obrazy z tej samej epoki.

Najpierw 837235 i 275528: warianty cofnięcia wzdłuż własnego kierunku patrzenia o 0/12/16/20 m. Bez arbitralnego wspólnego przesunięcia E/N. Portal ADR 0125 jest pierwszą kotwicą, ale potrzebna jest też zgodność nosa wyspy albo trwałego narożnika jezdni. Szewron oparty na wygenerowanym nosie może zawierać osobny błąd świata.

Następnie 328135 i 297817: ich kierunki patrzenia są przeciwne do grobina. Hipoteza przesunięcia sekwencji około 45 m wymaga kontroli znaku i osi; nie przenosić liczby automatycznie na oba zdjęcia. Porównać układ tyłu portalu, jezdni i hali w obu fotografiach, zanim wybierze się nowe miejsce.

180137: test przesunięcia w stronę jazdy 0/10/15/20 m względem początku przeszklonego ekranu i włączenia łącznicy. Utrzymać wysokość pokładu zgodną z właściwą jezdnią, nie używać w ciemno NMT na wiadukcie. 494288: kurs względem osi pomostu, bez uzasadniania samą krzywizną jezdni w świecie.

Każda hipoteza wyłącznie w diagnostyce C do przeglądu własnego i niezależnego. Zachować oryginalne obrazy i negatywne kadry. Zmiana maski/pozy unieważnia zgodny trend; nie przenosić historycznej oceny D51 na nowe piksele.

Ranking docs/refs/sbs-priorities.md powinien jawnie oddzielać aktualny render r3 od starszych recenzji. Poprawione na main obiekty oznaczyć jako oczekujące potwierdzenia, nie nadal brakujące. Świat pozostaje poza zakresem SBS.

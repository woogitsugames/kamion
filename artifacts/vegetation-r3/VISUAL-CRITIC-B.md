# Niezależna ocena odrzuconych prób r3

Krytyk vegetation_critic obejrzał rejected-comparison.jpg, rejected-comparison.json, probe-b-comparison.json, diagnostic-maple-height/input-change.json i migawkę producenta B. Ocena tylko do odczytu, bez dodatkowych renderów i telefonów.

Werdykt: odrzucenie B1 i diagnostyki wysokości klonu jest uzasadnione wizualnie. B8 pozostaje otwarte. B1 nie odtwarza zespołu szerokich, gęstych koron, które na fotografii przesłaniają zabudowę. Nadal dominują odsłonięte hale, a drzewa mają małe, rozczłonkowane korony. Poza klasy B ogranicza dokładność pozycji i skali, lecz nie uzasadnia zamknięcia B8.

B1 jest wynikiem pełnego producenta: jedna zamiana syntetycznej brzozy wariantu 2, trzy propozycje odłożone, zero nowych rekordów. Obraz różni się od baseline 5307 pikselami. Równe 5516 trafień maski koloru oznacza tylko równą liczebność progu w ROI, nie identyczny obraz ani biomasę. Odrzucenie wynika z obejrzanej kompozycji.

Diagnostyka klonu zmienia wyłącznie h z 8 do 13,8 m w wejściu renderera. Nie jest wynikiem producenta B2. Różni się 11 565 pikselami od baseline. Większa sylwetka zachowuje odseparowane skupiska liści; powiększenie uwydatnia słabość modelu zamiast odtwarzać gęstą koronę.

Obie próby w tej jednej kamerze Low mają 665 wywołań, czyli 460 statycznych i 205 instancji, oraz raportowane 575 tys. trójkątów, czyli 547 i 28 tys. Precyzja trisK nie wyklucza mniejszych różnic geometrii. A wcześniej dodało cztery wywołania. Brak wzrostu kosztu nie akceptuje wyglądu ani całej macierzy kamer.

Krytyk wskazał niejednoznaczne globalne producer_generated:false. Poprawiono je na osobne pola każdego wariantu; false dotyczy tylko diagnostyki klonu. Nie oceniono jeszcze przywróconego świata po końcowej regeneracji i imporcie. Oczekujące testy nie potwierdzają przywrócenia.

# Ikony Low — izolowane porównanie r4

Porównano ten sam fragment lewego panelu kierownicy (240 × 200 pikseli oryginalnego kadru 1920 × 1080). Arkusze 960 × 440 powiększają go dokładnie dwukrotnie najbliższym sąsiadem; nie są nowym renderem o większej rozdzielczości. Obejrzano warianty 512/0 oraz 256/−0,75 przy overcast i wariant bias przy clear oraz dusk.

Samo przełączenie Low 256 → istniejący Medium 512 niemal nie zmienia ikon: w ROI overcast zmieniło się 16/48 000 pikseli. Odrzucamy zwiększenie atlasu bez potwierdzonego efektu. Zostaje pierwotny Low 256.

Bias −0,75 daje miejscowo wyraźniejszy obrys symboli telefonu i głośnika. Zmieniło się odpowiednio 332/48 000 pikseli overcast, 331 clear i 329 dusk. Liczby opisują różnicę obrazu, nie skalę poprawy. Nie wszystkie małe symbole stają się jednoznaczne; brak dowodu, że cały P1 czytelności jest zamknięty. Dusk nie jest pełną nocą.

Wartość −0,75 jest WORKING_VALUE. Dane wybierają oddzielny Low atlas, importer zmienia tylko jego mipMapBias. Mipy pozostają włączone, rozmiar 256² i liczba dziewięć bez zmian. High 1024² i Medium 512² nie mają bias. Nie dodano próbek shadera, przebiegów, materiałów, geometrii ani pól QualityProfile.

Ostrzejsze filtrowanie wymaga dalszej oceny migotania w ruchu na urządzeniu; statyczne PNG nie rozstrzygają tego. Sesja nie używa telefonu. Wariant pozostaje wybranym kandydatem do pełnej macierzy i kontroli budżetu, nie niezależnie zaakceptowaną naprawą.

Wyniki i hashe: legend2x-roi-check.json, legendbias-roi-check.json, legendbias-clear-roi-check.json, legendbias-dusk-roi-check.json. Artefakty materiału Plastic nadal oddzielne; przy tych renderach jego mapy były niezmienione.
Ważne doprecyzowanie rozdzielczości: źródłowe PNG mają 1920×1080, ale stats Low potwierdza renderScale=0,75 i MSAA=2 (wewnętrzny render około 1440×810, następnie upscale). „Natywny ROI” oznacza nieprzeskalowany wycinek zapisanego PNG, nie 1:1 piksele wewnętrznego RT. Baseline i oba warianty mają identyczne ustawienia. Nie podnoszono skali ani rozdzielczości Low; High ma renderScale=1.
Próba ogólnego _Cutoff 0,4 została odrzucona: ROI Clear względem hp15 ma 0 różniących się pikseli; kod forward używał już odrębnego stałego progu 0,16 w paśmie ikon. To przeoczona wcześniej zależność, nie dowód dobrej jakości ikon. Przywrócono ogólny próg 0,5. Kolejna izolowana próba zastępuje wyłącznie tę stałą właściwością _LegendCutoff (domyślnie 0,16), ustawia Low 0,28 za danymi, Medium/High nadal 0,16. Nowych wyników jeszcze nie oceniono. A/B tej próby musi używać result-0112-hp15 (te same normalne), a nie legendbias sprzed integracji Plastic.

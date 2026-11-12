# Nocna referencja fotograficzna do r3

Volvo Trucks Magazine: Easier, safer night driving with night mode, 2017-03-24.
Fotograf: Jonatan Fernström. Tekst: Nic Townsend.
Strona pierwotna: https://www.volvotrucks.sg/en-sg/news/magazine-online/2017/mar/easier-safer-night-driving.html
Plik na serwerze producenta: https://www.volvotrucks.hu/content/dam/volvo-trucks/markets/master/classic/magazine/night-mode/VTM_GLO_Nightmode_0_1860x1050.jpg
Lokalnie: reference-volvo-night.jpg. Prawa autorskie Volvo / autor zdjęcia; NIE CC0, NIE materiał do gry. Wyłącznie referencja diagnostyczna z atrybucją, brak kopiowania brandingu do modelu.

Obejrzano pełne zdjęcie. Analogowy panel i funkcja black-panel różnią się od fikcyjnego cyfrowego TRAKT; nie kopiować układu i zielonego koloru jako obowiązkowego. Zdjęcie pokazuje rozdział podświetlonych legend przycisków od ciemnych korpusów. Nie znamy ekspozycji ani nie mamy tej samej sceny/pozy, więc nie wyprowadzać cd/m2 ani dokładnego docelowego RGB.

Preflight cab-dash Low/High dusk zachowuje nocne palety ekranów. Aktualny CabInterior.shader ma dla legend (pas atlasu v<0,5) podniesione albedo i częściowe AO, lecz brak emisji. W r3 warto sprawdzić wydzielone podświetlenie wyłącznie legend, za flagą danych i bez nowego pass/draw/fetch tekstury. Dzień powinien zachować dotychczasowy obraz. Najpierw nowy baseline po merge main, diagnostyka wyłączonego światła otoczenia wyłącznie w scenie QA, potem A/B i budżety całej trasy. Nie zmieniać globalnego światła świata.

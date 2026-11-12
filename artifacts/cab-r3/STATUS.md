# Kabina r3 — nocne podświetlenie

Start od zamkniętej r2 d04feba0, następnie merge main bez konfliktów. R2 artifacts skopiowane do main: 565 plików, 582,68 MB, failed 0. Bez merge do main i push.

Cel: ocenić i poprawić podświetlenie legend przycisków względem rzeczywistego zdjęcia nocnego, zachowując działające nocne palety ekranów, czytelność dnia i budżety Low. Źródło i ograniczenia zdjęcia: artifacts/cab-r2/NIGHT-REFERENCE.md. Nie kopiować oznaczeń marki. Wstępne kadry r2 nie zastępują baseline r3 po merge.

Nowy backlog recenzji: okluzja prawego wide-angle kanałem drzwi wymaga pomiaru z DriverEyePoint; kremowa powierzchnia przodu w Front należy do zewnętrza poza własnością cab. K4 szerokie pasmo AO i K6 macro zużycia pozostają otwarte.

Następny krok: świeże baseline Low/High clear/overcast/dusk, inspekcja nocna z odciętym otoczeniem wyłącznie w QA; dopiero potem flaga danych i wariant podświetlenia. Każde Unity owner gpt-cab, heavy owner gpt-cab-r3. Pojedynczy własny heavy, mutex wrappera; pełny GIS dopiero na końcu rundy.
Przygotowano wrappery r3: baseline obejmuje sześć stanów (Low/High × clear/overcast/dusk), siedem kamer i sześć natywnych RT w każdym stanie. Pojedyncze własne Unity; produkcyjne shadery i materiały nadal bez zmian r3. Kopia wrappera heavy zachowuje mutex.
Zapisano baseline Low clear, siedem kamer i sześć natywnych RT z identyfikatorem wnętrza. Następny krok: kontynuować macierz lub porównać PNG.
Zapisano baseline Low overcast, siedem kamer i sześć natywnych RT z identyfikatorem wnętrza. Następny krok: kontynuować macierz lub porównać PNG.
Porównywarka r3 uwzględnia także dusk i oddzielne statystyki regular/instanced. Wrapper BuildBatch/InstallBatch ograniczony do gałęzi r3. Trwa baseline, brak zmian kodu gry w czasie jego zapisu.
Zapisano baseline Low dusk, siedem kamer i sześć natywnych RT z identyfikatorem wnętrza. Następny krok: kontynuować macierz lub porównać PNG.
Zapisano baseline High clear, siedem kamer i sześć natywnych RT z identyfikatorem wnętrza. Następny krok: kontynuować macierz lub porównać PNG.
Zapisano baseline High overcast, siedem kamer i sześć natywnych RT z identyfikatorem wnętrza. Następny krok: kontynuować macierz lub porównać PNG.

Przygotowanie r5: rzeczywiste wyrównanie odpowiedzi Low/High, jeszcze bez wdrożenia.

Plansza v2 potwierdza, że sama korekta EV nie wystarczy. Lokalny URP LutBuilderHdr wykonuje LumVsSat i globalną saturację przed krzywymi YRGB w przestrzeni FastTonemap, a na końcu FastTonemapInvert. Mapowanie kolorów nie jest prostą niezależną krzywą szarości.

Możliwy eksperyment: mała CPU-generowana tekstura3D za domyślnie wyłączoną flagą danych LightingPreset, próbkowana w istniejącym przebiegu Low. Nie nowy fullscreen lub kamera. Rozdzielczości16/32 wymagają porównania błędu gradientów i ciemnych kolorów; jedna próbka3D nadal ma realny kosztGPU i pamięci, bez zgody na twierdzenie o zerowymkoszcie.

Nie kopiować bezmyślnie funkcji Display(gray) na kanałyRGB: w FastTonemap operacje mogą zależeć od największego kanału, a LumVsSat od luminancji. Własny lookup powinien być sprawdzony względem aktywnego rzeczywistego High, najpierw laboratoryjnie, potem na światowych materiałach.

Metoda musi ominąć fizyczny capture jak istniejący toe. Nie może dodawać drugiej prezentacji do już zmapowanych odbić. Sky cap jest dziś kalibrowany oddzielnie dla Low i High, więc nowe mapowanie Low wymaga spójnej odwrotności capu, a nie przypadkowego przepalenia chmur.

Szkło premultiplikowane i kabina wymagają oddzielnej oceny. Stosowanie nowej krzywej tylko na WorldSurface nie dowodzi zgodności całego kadru, a zmiana shaderów innych dziedzin pozostaje poza sesjąlight. Korzystać ze wspólnego punktu KamionTone tam, gdzie już istnieje.

Wejście planszy jest eksponowanym liniowym RGB, nie luksami; najpierw weryfikować faktyczny grading stack i preset/global. Zachować test prawdziwego assetu: tekstYAML nie jest dowodem wczytanej wartości. Nie wybierać korekty z pierwszej odrzuconej planszy lub final-v1Night.

R5 zaczyna się dopiero poREPORT/robocopy r4, nowejgałęzi i mergeaktualnego main. Aktualne otwarte P1Night: źródła/halo/okna/doki, mokro nadalFAIL. Nie zastępować tych wymagań kosmetyczną korektą tonów.

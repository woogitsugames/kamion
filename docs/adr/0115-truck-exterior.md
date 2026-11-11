# 0115 — Zewnętrze TRAKT-a i naczepy

## Runda 1 — lakier, szkło i światła dzienne

Status: praca w toku. Start 11 listopada 2026, 21:31 CET. Gałąź `gpt-truck-r1`.

Punktem wyjścia jest main `5f2aa277` oraz recenzja `REVIEW-2026-11-11-s10-gpt-0087-0090.md`. Dawne pomiary 0087 nie stanowią pomiaru tej rundy. Obowiązują D30, D34, D35 i D44, a także budżet Low bez dodatkowych przebiegów i wzrostu liczby wywołań rysowania. Czas GPU na telefonie pozostanie UNVERIFIED, ponieważ telefony należą do zakresu lidera.

Najpierw zapisujemy aktualny baseline Low i High, przy zachmurzeniu i słońcu. Ocenę lamp opieramy na tej samej masce i rozkładzie jasności, ocenę szyby na jej górnej i dolnej części oraz widoczności wnętrza, a lakieru na drzwiach i deflektorze. Zdjęcia Commons są wyłącznie odniesieniem do zachowania materiału, nie projektem do skopiowania. Przesłane obrazy AI nie są zdjęciami ani źródłem tekstur.

Pierwsza uzasadniona poprawka techniczna dotyczy mgły w `FragFast`: szkło używa mieszania premultiplied, więc jego wkład rozproszonego światła atmosfery powinien być pomnożony przez alfę. W szybkim wariancie wierzchołek już oblicza transmitancję atmosfery, dlatego fragment nie może ponownie liczyć wykładnika. Osobno należy zachować zgodność filtrowania capture z pełną ścieżką.

DRL zachowuje kodowanie 1000 nitów na jednostkę RGBAHalf. Luminancja jest WORKING_VALUE i wymaga porównania przed i po. Nie zmieniamy ekspozycji całej sceny ani presetów oświetlenia należących do innej sesji. Lakier wymaga aktualnego dowodu rozdzielającego refleks od jasności białego pigmentu; nie przyjmujemy z góry, że capture nie zawiera podłoża.

Wyniki, porównania, ograniczenia i konflikty zostaną wpisane po walidacji. Na tym etapie nie ogłaszamy PASS wyglądu.

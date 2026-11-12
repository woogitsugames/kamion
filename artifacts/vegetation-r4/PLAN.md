# R4 — liściasta pokrywa berberysu

Przeczytano nowy HANDOVER i feedback po merge main 7c9b4ca6. Najpierw pełny świeży baseline na stanie zintegrowanym, ponieważ zmieniły się światło i materiały innych dziedzin. Nie przenosić pomiarów ani obrazów r3 jako świeżego before.

Kandydat z next-round-proposal w r3 zmienia wyłącznie posiadany plantings.py: berberis_red wykorzystuje istniejący materiał liści dla wewnętrznej warstwy, w skali HEDGE_TILE_M i z osobną fazą UV. Ma usunąć płaski pełny rdzeń wyglądający jak drewno. W małej analizie czterech obrysów pozostało 18 402 trójkąty i te same pozycje/indeksy na płaskim terenie; pozostałe gatunki są niezmienione. Nie ma jeszcze renderu ani akceptacji tej propozycji. Po baseline ponownie sprawdzić hash źródła przed użyciem patcha.

Porównanie z rzeczywistym CC0 zdjęciem Rakoon: niski, gęsty pas, drobne listki i nierówność powierzchni. Nie tworzyć wielkich losowych przerw ani wracać do grubych kiełbas odrzuconych we wcześniejszych iteracjach. Brak pokrywy, jasna pusta siatka lub większy koszt Low oznaczają odrzucenie.

Próba najpierw w kilku bliskich i trasowych kadrach ronda Low/High clear/overcast. Zachować 18 402 trójkąty albo mniej, wywołania Low bez wzrostu, pozostałe gatunki oraz kolizje bez zmian. Analiza geometrii nie potwierdza kosztu alpha overdraw. Hedge shell/sprig to URP Lit chunków, nie runtime WorldInstances.simpleFoliage. Nie edytować importera, WorldInstances ani plików Claude.

Po obiecującej próbie: generator w heavy, import, pełna macierz wszystkich kamer przed/po, oglądanie arkuszy i niezależny krytyk. Sprawdzić rzeczywiste pozycje i indeksy road_collision oraz terrain_lod2 w GLB, zamiast hashy całych assetów Unity. Testy celowane przez heavy; pełny GIS i EditMode dopiero na końcu. REPORT normalnym polskim tekstem, ADR0109 r4, robocopy artefaktów do main, natychmiast kolejna runda. Bez push, merge do main i telefonów.

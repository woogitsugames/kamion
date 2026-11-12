# Próba czerni po ocenie A — jeszcze bez zmiany produkcji

Nowe ROI w life3_black_side5: clear drzwi/asfalt 0,9703 Low i 0,9769 High; overcast 0,7252/0,7433. Kadr i ROI są inne od zamkniętego historycznego celu 30–40, więc tych liczb nie porównuje się bezpośrednio. A zmienia też dolny nalot; przy ocenie czerni oddzielić czysty pigment od jaśniejszej soli.

Hipoteza do ograniczonej ablacji: zmniejszyć wyłącznie dodatkowe podbicie odbicia płatków _CarFlake.z czarnego lakieru, obecnie 0,08. To parametr warstwy metalicznej, nie całość F0 ani ekspozycja. Pozostawić pigment, Pearl, roughness, rozkład zabrudzenia i statyczne kabiny bez zmiany.

Ewentualny kontrakt danych: opcjonalne flake_lift w car_paint_black; fabryka czyta tylko dla car_paint_ i ogranicza do 0…0,08, domyślnie 0,08. Istniejący wektor _CarFlake, bez nowego keywordu, próbki ani przebiegu. Pierwsza próba 0,025 jako WORKING_VALUE; decyzja po pomiarze i obrazie w czterech warunkach, nie z teorii.

Dowód wymagany, jeżeli próba zostanie wykonana: kanoniczny World/import, natywne _CarFlake.z tylko czerni zmienione, wszystkie inne lakiery/kabiny i _PearlTint zachowane, porównanie tych samych ROI i pełnych kamer. Jeżeli znika materiał lakieru albo zbyt ciemny overcast, odrzucić/zmienić parametr. Nie wymuszać celu 0,4–0,7 kosztem obrazu; jakość może pozostać PARTIAL.

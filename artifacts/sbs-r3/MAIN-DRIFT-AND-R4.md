# Zmiana main podczas zamykania r3

12 listopada, około 10:39. Main przeszedł z 14ccbaf1 na f560cbd1: nowe scalenia edge r3, landmarks r2, light r2 i truck r2 oraz wspólna regeneracja. Nie są to źródła renderów r3. Nie przypisuję im wyniku 13/11/1 ani obrazu klina z naszej wcześniejszej bazy.

R3 zachowuje zamrożony, spójny świat do audytu i końcowych testów. R4 zacznie od merge aktualnego main, ponownego sprawdzenia produktów i pełnej nowej serii, zamiast mieszania nowych wejść z istniejącymi capture.

Przeczytana recenzja s12 pakietu B potwierdza PASS narzędzia SBS r2 i warunki używania heavy dla ComposeOnly. Podtrzymuje wymóg dwóch niezależnych kotwic dla korekty pozy. W szczególności 297817 blokuje ocenę koron vegetation; kolejny krok SBS musi rozdzielić zbieżność jezdni, pitch i geometrię otoczenia. Nie przesuwamy koron w celu dopasowania niepotwierdzonej kamery.

Nowa recenzja nie zastępuje obrazów r3 ani nie akceptuje prób C. Po r3 kandydatury 328135-21 i 297817-26 mają portal i powierzchnię jezdni, lecz konflikt pionowej projekcji pozostaje. Kontrolowana próba pitch przy stałym XY jest zapisana w ROAD-PROJECTION-NOTES.md.

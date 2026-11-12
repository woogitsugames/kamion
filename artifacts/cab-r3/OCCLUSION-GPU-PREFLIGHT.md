# Maska GPU prawego szerokokątnego — preflight

Użyto istniejącego CabBezelInspection i standardowego qaMask MIRROR_WideR_LOD0. Kamery są w DriverEyePoint. W after jest bieżący model; before jest wyłącznie tymczasową ablacją obrzeża z istniejącego narzędzia, nie nową poprawką. Nie zapisano scen ani zmian geometrii.

Obejrzano normalny obraz i maskę after Low oraz maskę after High. Jednolita magenta zajmuje powierzchnię szkła także tam, gdzie w normalnym obrazie jest szeroki ciemny prostokąt. W badanej pozycji ciemny obszar pochodzi z treści odbicia RT, a nie z szerokiego fizycznego przesłonięcia przez kanał drzwi. Nie zidentyfikowano tu dokładnego odbijanego obiektu i nie zgłaszamy pełnej widoczności we wszystkich pozycjach głowy.

Dodatnia kontrola: log wskazuje dokładnie jeden slot na jednym rendererze MIRROR_WideR_LOD0. W ograniczonym, wspólnym ROI (800,650,320,350) maska ma 35 727 pikseli magenta Low i 35 949 High. To liczba widocznych pikseli w ROI, nie procent okluzji; brak osobnego renderu idealnie niezasłoniętej powierzchni. Wspiera to wcześniejsze promienie geometryczne: brak trafień centralnie dla przednich stron, małe trafienia przy dolnym brzegu.

Low: exit 0, komplet plików i marker CAB_BEZEL_INSPECTION_RESULT: OK. High: osiem świeżych PNG i ten sam marker OK, po czym exit -1073741819 przy zamykaniu. Nie opisujemy High jako czystego zakończenia procesu. Obraz after High został odczytany i maska jest niezerowa, ale błąd zamykania pozostaje ograniczeniem tego dodatkowego pomiaru. Slot Unity zwolniony w finally.

Wniosek: nie przesuwać okna, oka, FOV ani lustra w celu usuwania ciemnego odbicia. Pozostają drobne przecięcia przy brzegu i inne pozycje oka, niepotwierdzone w tym renderze. FOV i testy optyczne zachowano. Do kolejnej rundy wybrać rzeczywiste odstępstwo wnętrza, a nie wymuszać poprawkę geometrii według błędnie rozpoznanego fragmentu obrazu.

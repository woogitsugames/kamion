# Następny audyt okluzji prawego szerokokątnego

Dowód źródłowy: artifacts/cab-r1/audit-supports.py buduje BVH wyłącznie z obiektów o nazwie zaczynającej się od mirror_arm_. Jego 2400 promieni z oka kierowcy na lustro potwierdza cofnięcie podpór, ale nie obejmuje kanałów okna, słupków ani reszty kabiny. Nie używać wyniku 0 jako dowodu całkowitej widoczności szkła.

Nowy pomiar powinien użyć rzeczywistego zaimportowanego modelu po builderze, DriverEyePoint i faktycznej powierzchni szkła. Zliczyć pierwszy nieprzezroczysty obiekt na odcinku oko→szkło, z nazwą renderera, slotem materiału i trójkątem/obszarem. Rozdzielić podpory, kanał okna i słupek. Szyby przezroczyste, samo szkło lustra i maskowane dekale nie są pełnymi nieprzezroczystymi przeszkodami. Próbki przy krawędziach ramki oznaczyć osobno, by nie pomylić zamierzonego obrzeża z zasłanianiem środka.

Ostateczny dowód ma również pochodzić z renderu z oka kierowcy: powierzchnia szkła widziana przez kabinę, a nie zawartość jego RT. Źródłowy BVH i identyfikator wnętrza w RT odpowiadają na inne pytania. Własny test na gotowym modelu eliminuje także ryzyko różnicy ram współrzędnych i korekt buildera.

Nie łączyć naiwnie importów geom/materials generatorów interior i exterior: obie biblioteki używają tych samych nazw modułów. Audyt gotowego modelu Unity omija ten problem. Do czasu wskazania konkretnego occludera nie zmieniać grubości kanału, pozycji oka, lustra lub jego FOV. Zachować testy optyczne i budżety. Przód kabiny widoczny w Front nadal należy do sesji zewnętrza.

To przygotowanie do kolejnej rundy po zamknięciu r3, nie wykonany pomiar ani zgłoszona poprawka.

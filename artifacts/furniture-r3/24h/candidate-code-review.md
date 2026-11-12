# Przegląd kodu kandydata wiat — wynik i poprawka

Niezależny reviewer wykrył szczelinę między słupkami kończącymi się na2,5m
oraz spodem łukowego dachu. Poprawiono podpory:ich wysokość wynika teraz
z interpolacji rzeczywistego segmentowanego spodu dachu danegoLOD, bez nowych
tris i slotów. Maksymalny wierzch obniżono z roboczego2,69m do poprzedniego
maksimum2,60m. Test sprawdza połączenie wszystkich pięciu podpór dlaLow/High.
To poprawka własnego modelu, nie pomiar wymiarów obiektu ze zdjęcia.

Reviewer potwierdził wybór tylko dwóchOSM, zachowanie pozycji/yaw/src i seeda
kotwicFab, niezmienność generic oraz starej pełnej kolizji. Pozostają ryzyka:
URPLit przyroughness0,4 może dać mleczne odbicie nieba, a wspólny przezroczysty
prymityw bezZWrite może źle sortować ściany w widoku narożnym. Winding szyb
jest poprawny. Oględziny clear/overcast z obu stron są obowiązkowe.
Trzy sloty nowej rodziny nie dowodządraws+0 po podziale instancji.
Review wyłącznie do odczytu, bez Unity/Python i edycji przez reviewera.

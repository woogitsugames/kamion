# Plan konstrukcji palet r5 przed oględzinami baseline

Obejrzano oba zdjęcia W.carter CC0 w refs (960 px). Konstrukcja ma duże otwarte wejścia z obu osi, rozdzielone klockami; warstwy lekko przesunięte, drewno różnie postarzone. Zdjęcia nie dokumentują rozmieszczenia w Białymstoku. Źródła/licencje i oficjalne wymiary w PALLET-PREFLIGHT.md. Bez logo/pieczęci.

Pierwszy kandydat, do zastosowania dopiero po świeżym baseline: LOD0 pięć desek górnych, trzy poprzeczki, trzy płozy dolne i dziewięć klocków. Wysokość warstwy 144 mm, obrys 1200×800 mm; grubość desek 22 mm. Pozostałe proporcje, szczeliny i szerokości to WORKING_VALUE. Zachować deterministyczny seed n i dotychczasowe przesunięcia warstw ±30 mm, jedną istniejącą grupę pallet_wood, kolizję bez zmian. Nie zmieniać wspólnych progów LOD.

Klocki bez całkowicie zasłoniętych górnych/dolnych ścian: tylko cztery ściany pionowe. Każda dotyka istniejącej deski/poprzeczki na obu końcach. Nie otwiera to powierzchni widocznej przez widły. LOD0 wstępnie 204 trójkąty na warstwę, 3264 dla 16. To rachunek projektu, nie pomiar natywnego modelu ani trasy.

LOD1 powinien zachować klocki i dolne płozy, górę uprościć do pełnego pokładu. Wstępnie 120 trójkątów na warstwę (1920 dla 16). Rozważyć dalsze uproszczenie tylko na podstawie obrazów i rzeczywistych liczników; nie wracać do pełnego bloku bez ujawnienia utraty prześwitów. Jeśli koszty przekroczą +2% na dowolnej kamerze trasy, poprawić geometrię/LOD, nie podnieść limitu trasy.

Materiał obecnego cache ma WorldSurface GUID 3bdc254b264039f44854f125dcb313b3, BaseMap e89c272fd8769524ba7dcd43e0a57935. To odczyt przed nowym importem, bez potwierdzenia wyglądu. Pełna kontrola po świeżym imporcie.

Przygotowano audit-pallet-scope.py: porówna payload wszystkich węzłów GLB, dopuszcza wyłącznie LOD0/LOD1 czterech pustych stosów, chroni kolizje i całą resztę świata, materiał/grupy i 192 produkty instancji. Nieuruchomiony; wynik będzie ważny dopiero po generacji kandydata pod heavy. Oddzielnie potrzebne promienie przez faktyczne wejścia, PNG, natywny LOD i budżet wszystkich kamer.

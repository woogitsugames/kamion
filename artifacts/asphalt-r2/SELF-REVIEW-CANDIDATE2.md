# Samokontrola r2 / candidate2

Obejrzano 16 par materiałowych (osiem pełnych kadrów i osiem natywnych wycinków), 12 par kontekstu Kwadrat i cztery zestawienia zdjęcie/render. Publiczne zbliżenia zachowują czytelne fugi i kruszywo przy mniejszych plamach wilgoci. Obrzeże ma bardziej czytelne podziały; Low pozostaje miększy niż High, High ma nadal silne jasne punkty. W kadrach Kwadrat lokalnie nie dostrzegam zmiany materiału; nie twierdzę jeszcze, że całe pliki są pikselowo identyczne. Zdjęcia SBS jawnie ujawniają rozbieżną pozę/model i nie służą do dopasowania jasności.

Audyt 328 rzeczywistych snapshotów: pozy, FOV, view, projection i rootToWorld identyczne z baseline; wszystkie flagi zakresu i współczynniki bazowego grime poprawne, yardGrime bez zmiany. GPU readback rzeczywistego fragmentu zakresu potwierdził ochronę punktu Kwadrat i aktywny publiczny probe również po przesunięciu obiektu; EditMode 312/312, bez pominiętych testów. Źródła importera potwierdzają zachowanie lokalnych E/N w chunkach.

Lekki audyt 2952 liczników ze wszystkich 328 kamera/warunków: zero różnic, instancje osobno. Geometria 128 GLB/7315 prymitywów dokładnie identyczna z baseline. Import: 22 kategorie bajtów bez zmiany, ASTC 40 910 657 B, 126 992 instancji, 2674 collidery props. Te dane nie są pomiarem GPU. Trzy float4 zwiększają deklarację stałych o 48 B przed wyrównaniem, dodają kontrolę zakresu i ALU; brak nowych fetchów, przebiegów, UV i wariantów keyword. Koszt A16 UNVERIFIED.

Niezależny krytyk dał PASS przyrostu materiałowego candidate2 z ograniczeniami P2. Pełne arkusze wszystkich kamer i testy końcowe wymagają jeszcze odczytania. D51: ocena materiału nie jest blokadą route Gate3. Wycofane proporcje renderu r1 nie są używane.

# gpt-s16 r1 — ADR 0153 — raport roboczy

Gotowe do recenzji: **NIE**. Gałąź `gpt-s16-r1`, baza `421f1b4fb`.

Przygotowano odtwarzalny atlas BaseColor/MaskMap dla detali LOD1/LOD2 aut i
pojazdów placowych. Lakier / główne poszycie zachowuje istniejący materiał.
Próba na wszystkich 41 prototypach daje najwyżej dwie podsiatki; trójkąty
po konsolidacji nie zmieniają się. To wynik generatora, nie pomiar klatki.
8 testów atlasu oraz testy deposition/yard razem: **37 passed**.

Baseline świata: generator **595,7 s**, bez `fallback=True`; bazowe materiały
**474 s**. Brakujące lokalne zdjęcie asfaltu uzupełniono z main poza gitem;
dwie starsze mapy detalu odtworzono osobno w **1 s**. Log nieudanej, przerwanej
nadmiarowej przebudowy zachowano. Bazowy import Unity zakończył się poprawnie.
Wykonano **114 kamer × 4 warunki**: 48 bazowych + 30 G3 + 36 ujęć rzeczywistych
pojazdów przy progach LOD. Start Unity respektuje PHONE_RUN.

Audyt bazowego GLB obejmuje 420 chronionych węzłów i 68 odległych LOD.
`baseline-budget-audit.json` wykazuje przekroczenia docelowych dwóch podsiatek
w bazie. Wariant A (613,3 s): wszystkie 420 chronionych węzłów oraz geometria
68 odległych LOD bez błędów, 14 nowych aliasów zgodnych. Poprawiony wariant B
wymaga powtórnego audytu rzeczywistych buforów po eksporcie; samo przejście
testu źródeł nie stanowi dowodu niezmienności LOD0.

Wspólne pliki: `materials.py` oraz `WorldPbrMaterials.cs` wyłącznie addytywnie
za polem `vehicle_lod_atlas`. `InstanceImporter.cs` addytywnie obsługuje końce
LOD z jawnych extras oraz alias istniejącego mesh/material LOD1 dla LOD2
pojazdów placowych. Pozostałe definicje materiałów i stare polityki pozostają
bez zmian. Drugi poziom placowych 276–316 tris jest już mały; nie usunięto
kół ani podpór. Próba cięcia mikrodetali była NO-OP i została wycofana.
Nowy trzeci poziom placowych współdzieli natywny mesh i materiały LOD1.
Po niezależnym preflight poprawiono zachowanie żaluzji chłodni, efektywną
metaliczność detali i walidator tablic. LOD0 zachowuje rygory walidacji rogów
UV i ma test aktywnego remapu tablic po imporcie. Potwierdzenie statyczne
recenzenta jest w `REVIEW-PREFLIGHT.md`; ocena wizualna nadal otwarta.

Otwarte: pełne before/after wszystkich kamer, metryki draws/batches/tris osobno
dla każdej kamery, oględziny PNG i lokalnych zdjęć, kalibracja progów w edytorze,
pełny GIS, EditMode, niezależna recenzja, końcowy ADR, sprzątanie dowodów i push.
Nie wykonano pomiaru A16; oczekiwany zysk ms jest **UNVERIFIED**.

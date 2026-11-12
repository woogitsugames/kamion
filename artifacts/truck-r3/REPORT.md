Runda 3 zakończona na gałęzi gpt-truck-r3; kod poprawki jest zapisany w d01382a5, baza main 9874d98c, merge f92690f3.
Naprawiono otwarte osie Low ciągnika i naczepy oraz mostkowanie wysp atlasu opon i rantów. Mapy mają dotychczasowe rozdzielczości; nie dodano przebiegów shaderów ani draws.
Pełne bake obu pojazdów i natywne walidatory przeszły. Końcowy LOD2: ciągnik 17 690/17 900, naczepa 7 849/8 000 trójkątów. Mapy oraz LOD0/1 są identyczne bajtowo z pełnym wariantem v2.
Przednia tarcza Low jest wyraźnie pełniejsza niż w v2; krytyk potwierdza poprawę poza samą piastą. Nadal P1: nieregularne otwory, ząbkowany rant i wnętrze felgi naczepy. Bez pełnego PASS wyglądu.
Reprezentatywne przednie koło Low: UV-wide 47→0, trójkąty 907→1186, wierzchołki 1086→1124. Naczepa 511→709 trójkątów i 849→967 wierzchołków. Globalne budżety nie wzrosły.
Cztery reprezentatywne koła LOD0/1 zachowały geometry+normal hash, przy celowej zmianie UV i mniejszej liczbie wierzchołków. To nie pomiar pamięci lub czasu GPU.
Własne i niezależne oględziny 12 zbliżeń oraz 28 całych kadrów Low/High w obu pogodach nie wykazały nowej większej regresji poza kołami; szczegóły REVIEW-WHEELS-V3.md i REVIEW-WHOLE-LOW.md.
[Zdjęcie|render Low](photo-wheel-detail-wheels-v3-fleet-Low.jpg), [Low przed|po](detail-wheels-v3-fleet-pairs/Low-overcast-truck-wheel-detail.jpg), [cały Low](whole-low-v3-pairs/Low-clear-contact.jpg), [High](maps-high-v2-pairs/High-overcast-contact.jpg) — wszystkie ≤960 px, zdjęcie Matti Blume CC BY-SA 4.0. Różne pojazdy i światło, bez kalibracji chromu.
Wszystkie 96 wierszy kamer: draws rendererów i osobno instancji bez wzrostu, trójkąty bez wzrostu; dziesięć Low spadło o 1–2 tysiące w zaokrąglonym liczniku. To estymaty CPU, nie GPU telefonu.
Testy geometrii 12/12, pełny EditMode 326/326, zero failed/skipped. Czerwony baseline potwierdzał odsłonięte osie wyłącznie w LOD2.
Audyt 580 plików i dwóch prefabów: pozycje identyczne. Dwa renderery drzwi Low zmieniły kolejność Paint/Trim, rozwiązywaną po nazwach przez importer; jawny diff w fixture-final-semantic-diff.json.
Android Low+High: Succeeded, 0 błędów, 12 ostrzeżeń, 162 s. APK 389093741 bajtów, SHA256 AC52927339EC9DDA4CB4519591FC985D11E24E12682F125081CB5631AF7C0F14, źródło f3e79869dcea5b04ad03af0a9b93591e515508d5. Bez instalacji i uruchamiania.
Końcowy GIS pod heavy: 617 passed, 1 failed, 1 xfailed, 814,39 s. Jedyny błąd: nieaktualny fidelity_qa względem overrides.yaml i roads/meshing.py. Deterministyczność świata przeszła na świeżym manifeście; siedem plików ubocznych zachowano i przywrócono.
Nie rozwiązano pozostałego P1 felg, lakieru/dachu, mleczności szyby ani pełnego brudu naczepy. A16 i ruch pozostają UNVERIFIED; telefonów nie używano.
Przewidywane konflikty: własne generatory eksportu kół, źródłowe mapy/FBX i testy TruckWheelLodGeometryTests; ADR 0115. Bez merge do main i bez push.

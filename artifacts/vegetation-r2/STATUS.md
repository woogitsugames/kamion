# Vegetation r2 — ADR0088 — gpt-vegetation-r2

- Krok1: przeczytano pełny kontrakt S10/B, HANDOVER s9, CLAUDE, AGENT-RULES i skill visual-qa; branch z main4f7da66c. Praca wyłącznie w tym worktree; bez telefonów, main, dróg, scen/ustawień i innych worktree. Materiały Fab tylko w ignorowanych wynikach.
- NASTĘPNY KROK: `git lfs checkout` i bootstrap kopii danych oraz produktów Fab/Unity według GPT-TASK-02-S10.md.

- Krok2: git-lfs checkout + fyzické kopie derived/cc0/Fab produktů/_Generated/materialcache/Library; vstupy gugik/osm/refs/mapillary/fab junction pouze pro čtení. NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q` po auditu výchozího stavu a s9recenzí.


- Krok3: odtworzono baseline świata z HEAD, nie użyto starej sceny main; build bez fallback=True, zapisano SHA surowych produktów. NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` i4zestawy kontrolne.


- Krok4: przygotowano spójne okna koron, stabilny podzbiór kart LOD1 z LOD0, fotograficzną korę sosny CC0 oraz paletę liści WORKING_VALUE. Wyjścia tylko w artifacts/vegetation-r2/tree-products, scena baseline nietknięta; zachowano3pasmaLOD0/1+impostorLOD2. NASTĘPNY KROK: `blender -b --factory-startup -P tools/blender/world/make_trees.py -- --out artifacts/vegetation-r2/tree-products`.


- Krok5: w generatorze masek trawy dodano pola przestrzenne6m/3,5m zakotwiczone we współrzędnych, ograniczone do klas BDOT/OSM; zachowano kanałR odległości iG lasu. OSM species/genus wybiera istniejące gatunki zamiast zawsze lipy. Testy5PASS. NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/tree-bake.log -Tail 8` i dokończenie czterech59kamerowych baseline z prawdziwym WorldC_High.


- Baseline Low-overcast wyrenderowany i zapisany; NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/Low-overcast/stats.txt` i pomiar koron/ref.


- Baseline Low-clear wyrenderowany i zapisany; NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/Low-clear/stats.txt` i pomiar koron/ref.


- Baseline High-overcast wyrenderowany i zapisany; NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/High-overcast/stats.txt` i pomiar koron/ref.


- Baseline High-clear wyrenderowany i zapisany; NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/High-clear/stats.txt` i pomiar koron/ref.


- Baseline59 WorldC Low-overcast: rzeczywista scena profilu, kontrolne+s9Gate3; zastępuje wcześniejszy28kamerowy zestaw. NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/Low-overcast/stats.txt` oraz pomiar koron.


- Baseline59 WorldC Low-clear: rzeczywista scena profilu, kontrolne+s9Gate3; zastępuje wcześniejszy28kamerowy zestaw. NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/Low-clear/stats.txt` oraz pomiar koron.


- Baseline59 WorldC_High High-overcast: rzeczywista scena profilu, kontrolne+s9Gate3; zastępuje wcześniejszy28kamerowy zestaw. NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/High-overcast/stats.txt` oraz pomiar koron.


- Baseline59 WorldC_High High-clear: rzeczywista scena profilu, kontrolne+s9Gate3; zastępuje wcześniejszy28kamerowy zestaw. NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/before/High-clear/stats.txt` oraz pomiar koron.


- Krok6: pełny baseline59×4 gotowy (WorldC Low, WorldC_High High, overcast+clear). Dopiero teraz zmieniono shader liści (lokalne rozpraszanie półkulowe, mniej podwójnej okluzji), warunkową obwódkę gruntu8–55cm i sylwetkę istniejących żywopłotów bez nowych materiałów/trójkątów. NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` po zatwierdzeniu nowego bake drzew; następnie import i pomiary.


- Krok7: pomiar rzeczywistych ROI koron zachowuje piksele<16 i odrzuca niebo; DK8 Low p10/p50 18,64/31,15,5,43%<16. Zdrowe Andersa/Putry p50 64–73 pozostają granicą regresji. Przywrócono bazowe palety liściastych; korekcja rozpraszania dotyczy sosny/HLOD iglastego i mieszanego. Zdjęcia referencyjne mają inne ekspozycje/sezon, służą granicom orientacyjnym, nie dopasowaniu globalnemu. Testy16PASS. NASTĘPNY KROK: `Get-Content artifacts/vegetation-r2/tree-final-bake.log -Tail 5`; potem kopia legalnych proc/CC0 produktów i build_world.


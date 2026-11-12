# gpt-s16 r1 — ADR 0153
Gałąź `gpt-s16-r1`; kod/audyt `6b06b4d25`, baza `421f1b4fb`. Gotowe do recenzji: NIE — trwa końcowy GIS.
41 prototypów aut/pojazdów placowych: LOD1/LOD2 mają najwyżej 2 podsiatki, wspólny atlas detali i dotychczasowy lakier/poszycie; LOD0 bez zmian.
Końcowy audyt GLB: 420 chronionych węzłów identycznych, 68 dalekich LOD z tą samą geometrią, 14 nowych aliasów LOD1→LOD2, zero błędów (`glb-audit.json`).
456 wcześniejszych materiałów natywnych identycznych SHA256 po cofnięciu 7 ubocznych zapisów Unity; tylko 1 nowy atlas (`native-material-audit.json`, `native-cleanup-ledger.json`).
114 kamer × 4 warunki: Low batche instancji delta −312..0, High −395..0; dalsze 40 × 4: Low −310..−34, High −381..−97; draws/tris Low nigdzie nie rosną.
Cab-dash Low: instancje 122→122, batche 307→190, tris 17k→17k; osobne estymaty sceny 388 draws i 344k tris bez zmian.
Każda kamera osobno: `CAMERAS.md`, `camera-counts.json`, `clear/CAMERAS.md`, `clear/camera-counts.json`. SceneStats to CPU estimate; trisK są ucięte, batche GPU/SRP niezmierzone.
72 natywne pomiary pasm: auta Low 16/42,5 m i High 37,5/127,5 m; placowe Low 20/50 m i High 60/150 m; alias placowych nie zmienia mesh/material przy drugim progu.
Generator B 647,7 s bez fallback; import po dodatkowym baseline przywrócony. Odtwarzanie: `uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c`, następnie `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` (z blokadą Unity).
616 par przed/po ≤960 px: `pairs/`, `clear/pairs/`, zbliżenia `clear/target-crops/`; autor obejrzał wszystkie, niezależny critic PASS dla statycznego edytora (`REVIEW-VISUAL.md`).
Porównano lokalne zdjęcia aut/kół z istniejących referencji. Zachowana kratka chłodni i aktywny remap tablic LOD0; istniejące wielokątne koła LOD1 nadal obecne także w baseline.
Szczegóły SUV przy High 127,5 m są za małe do oceny koloru; oceniono brak widocznego artefaktu. Ruch, ASTC, GPU p95 A16 oraz zysk 0,7 ms pozostają UNVERIFIED.
Testy celowane 37 passed; końcowy EditMode 452 passed, 0 failed/skipped. Pierwszy GIS 926 passed/3 xfailed/1 fail starego fidelity; raport odświeżony, ponowny pełny GIS w toku.
Wspólne pliki zmieniono addytywnie za `vehicle_lod_atlas`: `materials.py`, `WorldPbrMaterials.cs`, `InstanceImporter.cs`; walidator tablic zachowuje ścisły LOD0 i stare biblioteki. Bez nowych shaderów/przebiegów.
Możliwe konflikty: powyższe pliki, `streetscape/export.py`, wygenerowane manifesty/GLB/meta. Przy integracji unia kodu, regeneracja świata i import; main scala wyłącznie lider.
Sprzątnięto zastąpioną diagnostykę i efekty uboczne Unity; pełne PNG pozostają tylko lokalnie. Automatyczny przegląd odrzucił usunięcie własnych `clear-rejected` (0,412 GB) — DECYZJA: ręczne usunięcie po recenzji; nie obchodzono blokady.
Następny krok: zakończyć GIS, zapisać wynik i push wyłącznie `gpt-s16-r1`; potem `git switch -c gpt-s16-r2; git merge origin/main` i baseline ADR 0154. Telefonów i main nie dotykano.

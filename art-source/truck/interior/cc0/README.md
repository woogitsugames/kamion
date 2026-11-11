# Skany materiałów wnętrza

Manifest `../cab_material_scans.json` wskazuje źródło, autora, licencję, fizyczny rozmiar oraz rozmiary plików i MD5. Brown Leather: Rob Tuytel / [Poly Haven](https://polyhaven.com/a/brown_leather), [CC0](https://polyhaven.com/license), 40 × 40 cm. `_raw/` jest ignorowany; żaden zasób Fab/Megascans nie jest częścią tego zestawu.

Flaga `leather.enabled` steruje nadpisaniem dwóch istniejących map Leather w eksporterze `a6_export.py` oraz korektą UV obręczy w `TruckAssetBuilder`. Brak lub uszkodzenie źródła przy aktywnej fladze przerywa eksport. Nie ma cichego zastępowania skanu teksturą proceduralną.

Konwerter `tools/blender/truck/interior/cc0_leather.py --output <katalog> --fetch` pobiera brakujące pliki i przygotowuje kandydat. Uruchamiać wyłącznie wewnątrz slotu `heavy` z nazwą gałęzi, zwalnianego w `finally`; gotowy wrapper rundy: `artifacts/cab-r2/convert-cc0.ps1` (zakłada już pobrane pliki). Samo przygotowanie kandydata nie włącza go w grze.

Fizyczny crop ma około 12 cm i zachowuje dotychczasowe rozdzielczości High 1024, Medium 512, Low 256. R to neutralna wariacja luminancji skanu (barwa pozostaje w wierzchołkach), G to AO skanu, B to wariacja roughness przy dotychczasowej bazie wierzchołkowej. A zachowuje istniejącą perforację. Normal OpenGL jest normalizowany po resamplingu. Opposite-edge crossfade obejmuje po 6% krawędzi; te fragmenty skanu są zmienione dla ciągłości kafla.

Obręcz kierownicy ma w źródłowym FBX kafel 5 cm. Pod flagą CC0 builder mnoży jej UV przez 5/12, pozostawiając piastę, pozostałe materiały i atlas AO bez zmian. Granice promienia 0,19–0,27 m są WORKING_VALUE i wymagają weryfikacji na wszystkich LOD; niejednoznaczny wybór kończy się błędem. Blenderowy podgląd samego źródłowego FBX nie uwzględnia tej korekty Unity.

Skan skóry nie jest skanem tworzywa deski. Akceptacja materiału wymaga obejrzenia świeżych kadrów Low/High oraz sprawdzenia budżetu, niezależnie od zgodności hashów.

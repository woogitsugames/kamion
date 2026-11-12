Sprawdzenie surowych lamp przed regeneracją R6

inspect-lamp-glb.ps1 odczytuje tylko metadata JSON GLB, z limitem4 MiB. W aktualnym pliku przed build_world nie brak soczewki w żadnym z16 renderowanych węzłów lamp (8 rodzin z LOD0/LOD1). Zapisano hash pliku, każdy submesh, materiał, liczbę wierzchołków i indeksów oraz bounds. To nie dowód zaimportowanego bindingu, faktycznego LOD lub widoczności piksela; po regeneracji plik może się zmienić.

Dla lamp_10m/LOD1 tafla jest naY9.91899967, a dolna granica obudowy naY9.92000008: różnica około1 mm. Nie ma podstaw, by nazywać taflę brakującą lub położoną wewnątrz prostokątnej obudowy na podstawie tych bounds. Nie oceniono wszystkich przesłonięć i głębokości kamery.

Dwie hipotezy sprawdzone w kodzie: WorldMeshBake.Compact zachowuje pozycje Float32, więc nie rzutuje tej szczeliny do Float16 pozycji. WorldSurface Forward używa Cull[_Cull], czyli zarejestrowane Cull0 nie jest tylko nieużywaną właściwością. DepthOnly ma CullBack, lecz zapisane Mobile_Renderer/Mobile_Renderer_SSAO mają m_DepthPrimingMode0 i nie potwierdzają tezy, że Equal depth priming usuwa soczewkę w oglądanych kadrach. Aktualnego formatu bufora głębokości nie mierzono.

Nie zmieniono generatora, meshów, importerów, rendererów ani shaderów innych właścicieli. Następny rozstrzygający dowód nadal wymaga aktualnego renderu i identyfikacji konkretnej soczewki.

# Następny krok po przekazaniu r1

Gałąź gpt-vegetation-r2 jest używana przez dawny worktree. Zachować ją i wybrać pierwszy wolny numer. Nie pomijać przez to otwartych problemów z pierwszego wpisu backlogu.

Najbliższy cel: korony liściaste Putry na High za jasne (stały ROI p50 76,57 overcast; Low 58,11). Poprawkę badać w danych leaf_textures.py, bez globalnego przyciemniania światła i bez zmiany nieprzydzielonego VegetationCanopyPolicy.cs. Sosna DK8 pozostaje kontrolą regresji. Palety są robocze, zdjęcia oraz te same ROI rozstrzygają o kierunku.

Audyt next-round-leaf-input-audit.json potwierdza, że bieżące generowane klon, lipa i sosna odpowiadają istniejącym PNG piksel w piksel (RGB i alfa). Można zachować maskę, liczbę liści i topologię. Samocień kart został odrzucony; Putry korzysta z innego LOD, więc próba musi obejmować też ponowny wypiek impostorów. Importer InstanceImporter.ProtoMaterial czyta tekstury z art-source/world/vegetation po nazwie obrazu GLB. Nie wystarczy poprawić samej bliskiej karty.

W main od baseline zmieniły się w obrębie wejść świata tylko dane SBS. Po merge sprawdzić to ponownie. Nowy zestaw ma 25 póz B i 17 C, brak A. Odrzucić C z porównań kalibracyjnych; B nadal pozostaje niepotwierdzoną pozą. Kamery kontrolne można ponownie wykorzystać jako baseline wyłącznie po sprawdzeniu zgodności wszystkich rzeczywistych wejść, nie samej nazwy pliku.

Każdy ciężki wypiek Python/Blender objąć pulą heavy. Każdy Unity osobnym acquire/finally release. W trakcie tylko testy pojedynczych plików. Pełny GIS na końcu nowej rundy. Nie zmieniać źródeł następnej próby przed zamknięciem bieżących testów i utrwaleniem dowodów r1.

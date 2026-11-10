# Zasady dla agentów — sesja 5 (lider = jedyny integrator)

Repo główne: `C:\Users\matma\Documents\Claude\kamion` (Unity 6000.3.28f1 URP, projekt w `game/`). Przeczytaj `CLAUDE.md` i `docs/06` (anti-slop).

1. **Ciągły WIP:** po każdym kroku `git add` + commit `wip(<obszar>): ...` na SWOJEJ gałęzi i dopisz 2–4 linie do swojego `STATUS.md` (co zrobione, liczby, NASTĘPNY KROK jako gotowa komenda). Limit sesji może Cię zabić w każdej chwili.
2. **Nie scalaj na main, nie pushuj.** Nie zmieniaj `ProjectSettings/`, `Packages/`, asmdef (jeśli musisz — opisz w STATUS, lider zrobi). Po każdym uruchomieniu Unity cofnij efekty uboczne: `game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat`, `game/ProjectSettings/QualitySettings.asset`, `ProjectSettings.asset` (preloadedAssets), pusty `game/Assets/Resources(.meta)`.
3. **Blokada telefonu:** przed KAŻDYM startem Unity sprawdź, czy istnieje `C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN`; jeśli tak — czekaj (pętla co 60 s), nie startuj Unity. Nie używaj adb, nie dotykaj telefonów.
4. **Dowody** zapisuj w swoim worktree pod `artifacts/<twój-katalog>/` ORAZ na końcu skopiuj je do `C:\Users\matma\Documents\Claude\kamion\artifacts\<twój-katalog>\`. PNG do oglądania zmniejszaj do ≤ 960 px (ImageMagick `magick in.png -resize 960x out.jpg`).
5. **Referencje tylko z otwartych źródeł** (D43): Mapillary (`tools/refs`, token czyta skrypt — nigdy go nie wypisuj), KartaView, Panoramax, Wikimedia Commons, Openverse (CC0/BY/BY-SA), GUGiK (ortofoto, LoD), OSM, otwarte dane Białegostoku, skany CC0 Poly Haven/ambientCG. Lokalnie: `Data/raw/refs`, `Data/raw/mapillary`, `artifacts/refs*`. **Zakaz Google Maps/Street View/Earth/3D Tiles** (także przez Gemini/Composio). Bez cudzych marek/logo.
6. **Nie zmyślaj liczb** — mierz albo `UNVERIFIED`/`WORKING_VALUE`. Pętla wizualna: render → obejrzyj → porównaj z referencją → popraw.
7. Worktree z junctionami `Data/raw/*` do main — NIE kasuj ich zawartości (to dane main). Library: możesz skopiować `game/Library` z main (robocopy) zamiast pełnego importu.
8. Blender: `C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe -b` (nigdy `Mesh.materials.clear()`).
9. Raport końcowy ≤ 20 linii: gałąź + ostatni sha, co zrobione (liczby), co otwarte, komendy dla lidera do scalenia/integracji.

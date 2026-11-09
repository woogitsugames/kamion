---
name: blender-hero-asset
description: Pipeline wysokiej jakości assetu 3D w Blenderze (blockout → high → low → UV → bake → materiały → LOD → eksport → render kontrolny → import do Unity). Używaj przy ciężarówce, naczepie i obiektach charakterystycznych świata.
---
# Hero asset w Blenderze

## Organizacja
- Źródła: `art-source/<asset>/<asset>.blend` (LFS), skrypty: `tools/blender/<asset>/*.py`, referencje: `art-source/<asset>/refs/`.
- Uruchamianie odtwarzalne: `blender -b art-source/<asset>/<asset>.blend -P tools/blender/<asset>/<step>.py -- <args>`. Blender MCP — do interaktywnego podglądu i szybkich poprawek, ale wynik zapisuj jako skrypt/zmiany w .blend z commitem.
- Skala: metry, osie zgodne z Unity po eksporcie (test transformacji), zastosowane transformacje, pivoty w miejscach funkcjonalnych (koła w osi, drzwi w zawiasach, kierownica w osi kolumny).

## Kroki z bramkami
1. Referencje i wymiary → plik `dims.json` (źródła).
2. Koncepcje/blockout → render kontrolny (`tools/blender/common/render_turntable.py`: 8 widoków + kabina, studio HDRI + plener) → obejrzyj → akceptacja.
3. High-poly: hard-surface, kontrolowane bevele (różne promienie wg funkcji), szczeliny, śruby, uszczelki; unikaj idealnej symetrii tam, gdzie świat jej nie ma (zużycie, detale).
4. Low-poly: retopologia, sylwetka zachowana, trójkąty tam, gdzie nie widać; budżet.
5. UV: bez rozciągania (sprawdź checkerem w renderze), texel density z ADR, wyspy proste, padding pod mipmapy.
6. Bake: normal/AO/curvature/ID; sprawdź szwy i artefakty w renderze.
7. Materiały PBR: bazowe wartości z tabeli referencyjnej, warstwy zużycia na maskach (krawędzie, krzywizna, ekspozycja), eksport tekstur do PNG → ASTC w Unity.
8. LOD0–3 (+ impostor), kolizje uproszczone, punkty (empties) dla kamer/świateł/osi/siodła/dźwięku.
9. Eksport (format z ADR) → import Unity skryptem → prefab generowany → walidator assetu.
10. Render kontrolny w Unity i zrzut z telefonu → skill `visual-qa` → `visual-critic`.

## Zakazy
Logo i kształty prawdziwych marek; zasoby niejasnego pochodzenia; obraz 2D z generatora jako tekstura bez obróbki; siatka z generatora 3D jako finalna (tylko punkt wyjścia do pełnej przebudowy).

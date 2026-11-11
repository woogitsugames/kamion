"""One-off: final numbers and addenda in ADR 0070 and STATUS.md."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
p = REPO / "docs/adr/0070-hero-fire-station.md"
s = p.read_text(encoding="utf-8")
s = s.replace("LOD0 8 246 trójkątów", "LOD0 8 240 trójkątów").replace("LOD1 2 956", "LOD1 2 950")
if "Dodatek: `_Tile`" not in s:
    s += """
## Dodatek: `_Tile` w Kamion/World PBR
`WorldPbrMaterials.Create` wyliczał `tile` z `tile_m` zestawu, ale nigdy nie zapisywał go do materiału: wszystkie zestawy
są próbkowane z domyślnym kaflem shadera 4 m (np. `plaster` 2 m, `brick` 1,04 m, beton 10 m). Dla atlasu to błąd
krytyczny (pierwszy render: atlas powielony co 4 m), więc zestaw z `"atlas": true` w `materials_spec.json` dostaje
`_Tile` = `tile_m`. Pozostałych zestawów ta zmiana nie dotyka: naprawa ogólna zmienia wygląd całego świata i wymaga
osobnej decyzji lidera (dotyczy też atlasu wiaduktu z ADR 0067, który trzeba oznaczyć `atlas`).

## Dowody
`artifacts/firestation-r9/`: `blender/it{1,2,3}/` (3 iteracje, `compare_it3.jpg` obok referencji),
`unity/r2/{High,Low}-{overcast,lowsun}/` (`compare_unity_r2.jpg`), `plan_overlay.jpg` (rzut na ortofoto), logi `logs/`.
pytest `tests/gis`: 173 passed; EditMode: 164 passed, 0 failed (5 inconclusive: brak prefabrykatu TRAKT w worktree).
Przegląd `visual-critic`: do zrobienia przez lidera (subagent nie tworzy subagentów).
"""
p.write_text(s, encoding="utf-8", newline="\n")
q = REPO / "artifacts/firestation-r9/STATUS.md"
t = q.read_text(encoding="utf-8")
t += """- Unity: pierwszy render pokazał atlas powielony co 4 m (WorldPbrMaterials nie zapisywał `_Tile`); naprawa tylko dla zestawów `"atlas": true`. Runda r2 OK: `unity/r2/{High,Low}-{overcast,lowsun}/`, montaż `unity/r2/compare_unity_r2.jpg`. pytest tests/gis 173 passed (359 s); EditMode 176: 164 passed, 0 failed, 5 inconclusive (brak prefabu TRAKT w worktree), 7 skipped.
- Efekty uboczne Unity cofnięte (M_Sky.mat, QualitySettings, ProjectSettings; brak Assets/Resources).
- UWAGA: `Data/raw` to junction do main, więc `build_world` z tej gałęzi nadpisał `Data/raw/derived/bialystok-industrial-c/world/*` w main (instancja `landmark_fire_station_jrg2`, brak generycznej bryły remizy). Main bez tej gałęzi: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`.
- OTWARTE: visual-critic (lider); dach w Unity jaśniejszy / mniej nasycony niż na zdjęciach (zmniejszyć `chalk`, szorstkość ok. 0,6 w `sets_fire_station.py`, przebudować atlas); okna szczytu płaskie; elewacje podwórza WORKING_VALUE; kadr `fire_station_ref7197` szerszy niż zdjęcie; po scaleniu wiaduktu `git merge main` i oznaczyć `viaduct_concrete` jako `atlas`.
- NASTĘPNY KROK: `git merge main` (po scaleniu ADR 0067), konflikty w build_all.py / materials.py / InstanceImporter.cs / build_world.py, potem `pwsh artifacts/firestation-r9/scripts/unity_round.ps1 -Tag r3`.
"""
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")

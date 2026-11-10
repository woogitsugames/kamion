# Wiadukt Bieżeństwa (hero, ADR 0067) — STATUS

Worktree: `.claude/worktrees/agent-a1ec6028c4e13f527` (gałąź `worktree-agent-a1ec6028c4e13f527`, od main fb0fee5).

## Ustalenia
- Obiekt: wiadukt Andersa nad Rondem Pamięci Bieżeństwa 1915 r., OSM way 175157461 + 177895177 (dwie jezdnie,
  dwa pomosty po 11,3 m, część na filarach ok. 200 m, rampy na murach 45–65 m). Kamery: `stretch_04`,
  `photo_biezenstwa_ground`, `g3a_rondo_bie_approach`, `g3a_eye_s0362`, `biezenstwa_above`.
- Baseline (przed zmianą): `stretch_04` High 1 997 615 / Low 962 150 trójkątów (szacunek generatora).
  Generyczna geometria do zastąpienia na tych łańcuchach: soffit 406 + fascia 1 208 + balustrada 15 744 = 17 358.
- p42/p45/p47 to Rondo Putry (inny wiadukt) — tylko wzór sufitu z kamerą.

## Architektura (decyzje)
- Override `kind: hero_bridge` w `overrides.yaml` → `tools/worldgen/streetscape/hero_bridge.py`:
  `plan()` pisze spec `Data/Regions/<id>/generated/landmarks/<asset>.spec.json` (szyny krawędzi pomostu z tych samych
  wzorów co generyczny pomost, linie filarów omijające jezdnie, cięcia segmentów) i sprawdza sha256 specu w
  `<asset>_meta.json`; asset nieaktualny → automatyczny Blender (`KAMION_BLENDER`/PATH) albo fallback do generyka +
  `overrides_stale`. `apply()` usuwa generyczny soffit/fascia/balustradę (przebudowa wstęgi łańcucha, `c.meta["hero"]`),
  pomija generyczne podpory, dodaje instancje segmentów `landmark_viaduct_biezenstwa_NN` (LOD0/1/2), kolizję filarów
  i przyczółków, liczby trójkątów do budżetu.
- Materiały: jeden atlas-pas `viaduct_concrete` (24 × 12 m, UV0 w metrach, Kamion/World PBR bez zmian shadera) na
  bazie skanu CC0 Poly Haven „Concrete Wall 008”; `viaduct_steel` (tekstura alfa balustrady + stal).
- Żwir: `plantings` island `fill: gravel` (wyspa środkowa ronda), zamiast soil + berberys.

## Zrobione
- [x] junctiony Data/raw, kopia Library z main, baseline build_world (log `logs/build_world_baseline.log`)
- [x] `hero_bridge.py` (spec/plan/apply) — napisany, NIEURUCHOMIONY jeszcze
- [x] `roads/meshing.py`: `c.meta["hero"]` pomija soffit/fascia/ekran/balustradę
- [x] `art-source/world/materials/_src/sets_viaduct.py` + rejestracja w `build_all.py`; zbudowany zestaw
  `viaduct_concrete` (44 s), `art-source/world/textures/viaduct_steel.png`, `atlas_layout.json`

## Do zrobienia (kolejność)
1. Obejrzeć atlas (`art-source/world/materials/viaduct_concrete/Medium/*BaseColor.png`, zmniejszony).
2. `tools/blender/world/landmarks/make_viaduct.py` (spec → GLB LOD0/1/2 + `.collision` + `_meta.json` z
   `spec_sha256`, `glb_sha256`, `segments[{name, anchor, tris[3]}]`, `materials`; osie glTF (−E, U, N) względem
   kotwicy segmentu; render kontrolny Blendera).
3. Hook w `roads/build_world.py` (po `SS.run`: `HB.plan` → pominąć `build_bridge_supports` dla hero → `HB.apply`;
   `props_meta.update(tris)`; `instance_ends`: `landmark_viaduct` → [90, 300, 20000]; QA `hero_bridges`).
4. `streetscape/materials.py`: `viaduct_concrete` (color = średnia atlasu ze specu), `viaduct_steel`
   (`texture`, `alpha_cutoff`), `island_gravel`; `plantings.py` `fill: gravel`; `overrides.yaml` (hero_bridge +
   ring-centre → gravel).
5. Unity: `InstanceImporter` — prototypy także z `art-source/world/landmarks/*/*.glb`, Policy `landmark_viaduct`
   3 LOD-y, cienie LOD0+LOD1.
6. build_world → import-region (sprawdzić `artifacts/locks/PHONE_RUN` w main przed Unity) → visual-qa WorldC
   Low/High overcast/lowsun, kamery G3-A z `-Gate3`, montaże przed/po obok Mapillary w `artifacts/viaduct-r9/`.
7. pytest `tests/gis` + nowy test hero_bridge; EditMode; ADR 0067; `docs/LICENSES.md`; `docs/WORLD_GENERATION.md`.

## Komendy
```
uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only viaduct_concrete
uv run --project tools/worldgen python art-source/world/materials/_src/sets_viaduct.py --railing --layout
blender -b --factory-startup -P tools/blender/world/landmarks/make_viaduct.py -- --spec Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_biezenstwa.spec.json
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -Cameras stretch_04,... -OutputDir artifacts/viaduct-r9/after/High-overcast
```
Uwaga: baseline build_world zmienia bajty `world_manifest.json` i kilku PNG/GLB w `art-source/world` (różnice
środowiska) — nie commitować tych plików bez potrzeby.

## Dziennik (najnowsze na dole)
- 20:xx atlas `viaduct_concrete` przebudowany z neutralniejszym odcieniem (beton lin. 0.373/0.359/0.306, średnia atlasu 0.369/0.324/0.276). OK wizualnie (pasy: gzyms czerwony, dźwigar, filar z czerwonym pasem, ściana, próbki).
- Napisany `tools/blender/world/landmarks/make_viaduct.py` (NIEURUCHOMIONY). Hooki gotowe: `build_world.py` (HB.plan/apply, instance_ends `landmark_viaduct` [90,300,20000], QA `hero_bridges`), `materials.py` (viaduct_concrete, viaduct_steel, island_gravel), `plantings.py` (`fill: gravel`), `overrides.yaml` (`andersa-viaduct-biezenstwa-hero`, ring-centre → gravel).
- W toku: `KAMION_NO_BLENDER=1 uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (ma zapisać spec; asset jeszcze nie istnieje → fallback generyczny). Log: `artifacts/viaduct-r9/logs/build_world_spec.log`.
- Następny krok: `blender -b --factory-startup -P tools/blender/world/landmarks/make_viaduct.py -- --spec Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_biezenstwa.spec.json --render <abs>/artifacts/viaduct-r9/blender` → obejrzeć PNG → potem bez `--render` (eksport GLB + meta) → ponownie build_world (bez KAMION_NO_BLENDER).
- Blender: render kontrolny OK (artifacts/viaduct-r9/blender/*.png). Asset: art-source/world/landmarks/viaduct_biezenstwa/viaduct_biezenstwa.glb, 6 segmentow, trojkaty LOD0/1/2 = 10544/4592/1396 (usuwany generyk 17358); spec: 7 linii filarow. Nastepny krok: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c (oczekiwane hero bridges applied), potem pytest tests/gis/test_hero_bridge.py, potem import Unity.

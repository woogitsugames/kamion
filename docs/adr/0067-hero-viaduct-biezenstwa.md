# ADR 0067: Wiadukt nad Rondem Pamięci Bieżeństwa jako hero asset (override `hero_bridge`)

Status: przyjęty (world-builder / obiekt charakterystyczny), 2026-11-10. Źródło: `docs/reports/visual/REFS-MAPILLARY-FINDINGS-2026-11-10.md`
(#1, #2, #9). Uzupełnia ADR 0011/0012 (import, instancje), ADR 0022 (zestawy PBR), ADR 0065 (Mapillary jako referencja).

## Kontekst
Generyczny pomost (`roads/meshing.build_bridge_extras`: płaski spód, pas fascia, balustrada, okrągłe podpory) nie
przypominał wiaduktu ul. Andersa nad rondem (OSM way 175157461 + 177895177). Kadry Mapillary p13, p21 i
`sheet_g3a_eye_s0362` (CC BY-SA 4.0, tylko referencja, nic z nich nie trafia do gry) pokazują: dźwigar skrzynkowy ze
skośnymi wspornikami, czerwony gzyms na całej wysokości krawędzi, pary prostokątnych słupów z czerwonym pasem, szary
kolektor odwodnienia pod wspornikiem, cienki czerwony przewód wzdłuż dźwigara, ciemną balustradę z dwoma pochwytami,
jasny żwir z krawężnikiem na wyspie.

## Decyzja
1. **Override `kind: hero_bridge`** (`Data/Regions/<id>/overrides.yaml`, moduł `tools/worldgen/streetscape/hero_bridge.py`).
   `plan()` zapisuje spec `generated/landmarks/<asset>.spec.json` z wygenerowanej drogi (szyny krawędzi pomostu co
   stację, linie podpór omijające jezdnie, cięcia segmentów ok. 50 m) i porównuje sha256 specu z `<asset>_meta.json`.
   Asset nieaktualny → Blender headless (`KAMION_BLENDER` / PATH; `KAMION_NO_BLENDER=1` wyłącza) albo powrót do generyka
   i wpis w `overrides_stale`. `apply()` usuwa generyczny spód, fascia, balustradę i podpory łańcucha
   (`c.meta["hero"]`), wstawia instancje `landmark_<asset>_NN` (LOD0/1/2, końce 90 / 300 / 20000 m) oraz pudełka kolizji
   słupów i przyczółków. Jezdnia, krawężniki, bariery, latarnie, mury ramp i kolizja drogi pozostają generowane.
2. **Generator** `tools/blender/world/landmarks/make_viaduct.py` (spec → GLB + meta, deterministycznie, nic ręcznie).
   Osie glTF (−E, U, N) względem kotwicy segmentu. Wymiary konstrukcji (`params` w specu) to WORKING_VALUE z kadrów
   „na oko”: dźwigar 1,55 m, gzyms 0,57 m, słupy 0,8 × 1,0 m, rozpiętości ok. 25 m.
3. **Materiały**: `viaduct_concrete` = atlas-pas 24 × 12 m (UV0 w metrach atlasu: gzyms, rozwinięty półprzekrój
   dźwigara, rozwinięty słup, ściana przyczółka, próbki) na bazie skanu CC0 Poly Haven „Concrete Wall 008”
   (`art-source/world/materials/_src/sets_viaduct.py`, md5 plików w kodzie, skan poza repo w `Data/raw/cc0`); szalunki,
   zacieki, wylewki, sadza i farba generowane. `viaduct_steel` = tekstura alfa przęsła balustrady + próbka stali
   (malowana, ciemny grafit). Rury malowane z atlasu betonu (szara / czerwona). `island_gravel` (zestaw
   `gravel_compacted`) dla `plantings` `fill: gravel` — wyspa środkowa ronda zamiast gleby z berberysem.
4. **Unity**: `InstanceImporter` czyta prototypy także z `art-source/world/landmarks/*/*.glb`; polityka
   `landmark_viaduct` (3 LOD-y, cienie LOD0 + LOD1). `WorldPbrMaterials`: materiał z `"set_tile": true` dostaje `_Tile`
   z `tile_m` zestawu.

## Liczby (zmierzone, 2026-11-10)
- Asset: 6 segmentów, 7 linii podpór, trójkąty LOD0/1/2 = 11 440 / 4 964 / 1 396; usunięty generyk 17 358.
- `stretch_04` (szacunek generatora): High 1 997 615 → 1 958 325, Low 962 150 → 918 564 (limit 2 000 000).
- Prześwit pod dźwigarem w środkowej części: 3,27–4,99 m (niweleta generatora: 4,5 m nad jezdniami pierścienia).

## Znane
- **`_Tile` nie był dotąd nigdzie ustawiany** (`WorldPbrMaterials.cs` liczył `tile` z `tile_m` i go nie zapisywał): wszystkie
  zestawy są próbkowane co 4 × 4 m (krawężnik 2 × 0,5 m, żwir 3 m, beton 10 m, płyty 6 m). Tu naprawione tylko dla
  materiałów z `set_tile` — zmiana globalna przestawi wygląd całego świata i wymaga osobnego przeglądu (decyzja lidera).
- Wiadukt w grze jest niższy niż na zdjęciach (słupy 2,4–4,6 m wobec ok. 6 m „na oko”): wynika z niwelety drogi i
  kopca wyspy w terenie, poza zakresem assetu (`roads/` + teren).
- Balustrada bez skośnych zastrzałów słupków; kamera CCTV wg Ronda Putry (#9), nie z tego obiektu.
- Latarnie na pomoście: stoją generyczne latarnie drogowe (są na zdjęciach), asset ich nie dubluje.
- `tools/blender/world/render_control.py` nie zna prototypów z `landmarks/`.

## Dowody
`artifacts/viaduct-r9/` (rendery Blendera, kadry WorldC High/Low × overcast/lowsun, montaże przed / po / Mapillary).
Testy: `tests/gis/test_hero_bridge.py`.

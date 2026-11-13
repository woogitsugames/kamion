# ADR 0174 — import regionu Dojlidy/Krywlany do Unity: biblioteka ulicy per region, trasa i kamery foto
Status: Proposed (agent world-builder, s17, gałąź `dojlidy-import-0174`), 2026-11-13. Do scalenia przez lidera.
Poprzednik: ADR 0166 (dane regionu `bialystok-dojlidy`), ADR 0011/0012 (import glTFast, warstwy treści).

## Kontekst
ADR 0166 wygenerował region `bialystok-dojlidy`, ale import do Unity był otwarty: `InstanceImporter` (i 6 innych miejsc
importu) czytał bibliotekę ulicy (`street_props.glb`, `props_meta.json`, lica znaków, tekstury mebli/`plot_kit`) tylko
z `art-source/world`, która należy do regionu C (`SHARED_LIBRARY_REGION`), a region ≠ C ma własną bibliotekę
w `Data/raw/derived/<id>/{props,signs,textures}` (poza gitem). Import dojlidy z biblioteką C dałby prototypy i znaki
regionu C (inne kody znaków i tablice), a brakujące prototypy byłyby po cichu pomijane.

## Decyzja
1. **`Game.World.Import.WorldLibrary`** — jedna funkcja `Resolve(region, kind, file)`, lustro
   `build_world.props_library_dir()`: region C (`SharedRegion`, zgodność z Pythonem sprawdza test) czyta wyłącznie
   `art-source/world/<kind>/`; inny region czyta `Data/raw/derived/<id>/<kind>/<file>` dla `kind ∈ {props, signs,
   textures}`, a plik, którego biblioteka regionu nie ma (np. `vehicle_lod_details_*`), bierze ze wspólnej. Roślinność,
   landmarki, zestawy PBR i Megascans pozostają wspólne. Przełączone wywołania: `InstanceImporter.Build` (street_props),
   `InstanceImporter` (lica `sign_*`), `RegionImporter` ×2 (tekstury materiałów), `WorldPbrMaterials` ×3 (props_meta,
   lica znaków mebli, plinth), `WorldCarPlateMaterials` (walidacja biblioteki tablic), `VehicleLodAtlasMaterials` ×2.
   Region C: ścieżki znak w znak jak w main (test `WorldLibraryTests.ReferenceRegion_ReadsOnlyArtSource`).
   Alternatywa odrzucona: biblioteka-suma C+region — wymaga scalania GLB i `props_meta`, a kolizje nazw prototypów
   (te same nazwy, inna geometria tablic) nie mają jednoznacznego zwycięzcy.
2. **`scripts/export-route.py` czyta `route_endpoints.json`** (authored_override ADR 0166), tak jak już robi to
   `build_world.route_polyline`; bez niego kandydat D4 (region C). Wcześniej import dojlidy padał (`StopIteration`).
   Region C: `route_start.json` bajt w bajt (sprawdzone `git diff` po ponownym eksporcie).
3. **Kamery dopasowane do zdjęć** (krok importu z ADR 0166 §5): `Data/Regions/<id>/control_cameras_photo.authored.json`
   (authored_override) → `cameras_generic` dopisuje `photo_<id>` do `generated/control_cameras.json`. Pozycja = GPS
   Commons (zweryfikowany 31/31), oko 1,6 m, vFOV 40° (WORKING_VALUE dla 16:9, hFOV ~65°). Kierunek: `kierunek_deg` P11
   jest UNVERIFIED, więc azymut = namiar na obiekt widoczny w kadrze poprawiony o jego przesunięcie w pikselach
   (P11-001 Kontri, P11-063 Bravilor) albo wzdłuż ulicy z kadru (P11-056); P11-094 i P11-129 UNVERIFIED (129 w dwóch
   kierunkach, wybór z renderu). Region C nie ma pliku — jego zestaw kamer bez zmian.
4. **Scena osobna**: `WorldSceneBuilder.SceneNameFor` → `World_bialystok-dojlidy(.unity|_High.unity)` w
   `game/Assets/_Generated/World/bialystok-dojlidy/` (poza gitem); `BuildScenes` zna tylko WorldC — region nie trafia do
   APK. Plik GPS `bialystok-dojlidy_route.bytes` generowany przez build_world jest usuwany z `Resources` (nie do APK).

## Wyniki (worktree, 2026-11-13)
- `build_world --region bialystok-dojlidy` na main 3a60019ff: 64 GLB, 418 MiB High / 124 MiB Low, 441 s.
- Import: `IMPORT_RESULT: OK chunks=64 corridor=31 tiers=Low+High`, 0 ostrzeżeń „prototype not in the library”,
  `car_plate` remap włączony (walidacja biblioteki regionu przeszła).
- Pamięć (`artifacts/world/<id>-import.json`, ta sama metoda): meshe Low **68,8 MB** (C 83,1), High **197,2 MB**
  (C 226,0), instancje 18,3 MB / 112 964 (C 22,5 MB / 126 861), kolizja 16,7 MB (C 17,1), PBR ASTC 39,4 MB (C 39,7).
- Spójność nawierzchni: dopiero teraz istnieje `route_start.json`, więc QA widzi trasę kontrolną: **5 przypadków na
  trasie** (ADR 0166 podawał 0, bo trasy nie było): `arrow_no_exit` Kuronia × łącznik (69,8; 384,8),
  `lane_blind_end` (94,2; 409,4) i (452,4; 424,1), 2× `lane_blind_end` na wschodniej krawędzi kafla (1024; 280–283) —
  artefakt granicy.
- Kamery kontrolne Low i porównanie z kadrami: patrz „Wizualnie”.

## Wizualnie
(uzupełniane po renderze)

## Testy
- pytest: `tests/gis/test_region_generic_0166.py` 3/3, nowy `tests/gis/test_photo_cameras_0174.py` 2/2.
- EditMode: nowy `WorldLibraryTests` (3; refleksja, bo asmdef testów nie referuje `Game.World.Import.Editor` — zmiana
  asmdef należy do lidera).

## Konsekwencje
- `build_world.py` zmieniony (kamery foto) → po scaleniu lider: `fidelity/run.py --region bialystok-industrial-c`
  (raport C liczy sha256 `build_world.py`; wynik C bez zmian).
- Nowy region = katalog `Data/raw/derived/<id>/{props,signs,textures}` musi istnieć przed importem (tworzy go
  build_world); bez niego import po cichu użyje biblioteki C — `WorldLibrary.HasRegionProps` do ewentualnej bramki.

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy
Remove-Item game/Assets/_Project/UI/Resources/CabDisplay/Nav/bialystok-dojlidy_route.bytes*
pwsh scripts/import-region.ps1 -Region bialystok-dojlidy
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting overcast -OutputDir artifacts/dojlidy-import-0174/Low-overcast
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting clear -Width 1920 -Height 1080 -Cameras photo_P11-001,photo_P11-063,photo_P11-056,photo_P11-094,photo_P11-129,photo_P11-129b -OutputDir artifacts/dojlidy-import-0174/Low-clear-photo
```

# REPORT — integracja stanu main po sesji 9 (integration-s9)

- Gałąź `worktree-integration-s9`, baza main `fa83f577`; APK zbudowany z `ad4062539c` (czyste drzewo).
- Maszyna: Windows 11, Unity 6000.3.28f1, RTX 5070 (rendery edytora). Telefon: NIE dotykany — brak pomiaru na urządzeniu, bramka niezaliczona (emulator/edytor nie zastępuje telefonu).

## Wyniki kroków
| krok | wynik | dowód |
|---|---|---|
| 1 build_all | exit 0 (7 min 51 s); `asphalt_detail_photo` SKIP — w worktree brak `Data/photos` | `logs/step1.log` |
| 1 build_world / export-route | exit 0 / exit 0 | `logs/step1.log` |
| 1 pytest tests/gis | 345 passed, 2 xfailed (369 s) | `logs/step1.log` |
| 2 import-region | IMPORT_RESULT OK, chunks=64, corridor=41, Low+High; WORLD_MEMORY Low 110,0 MB, High 237,9 MB | `artifacts/logs/import-region-bialystok-industrial-c-20261111-060219.log` |
| 3 TruckAssetBuilder / TrailerAssetBuilder / WorldTruckInstaller | exit 0 ×3; `MI_Ext_DoorGlassL/R.mat` w `_Generated/Truck` (3 tiery) | `logs/step3-*.log` |
| 4 EditMode | 212/212 (TruckDoorGlassTests ×3 zielone) | `artifacts/tests/editmode-20261111-060543.xml` |
| 4 PlayMode (pełny) | 117: 109 passed, 0 failed, 8 skipped; WorldCBarrier/DepotBarrier/WorldCRoute/WorldEdgeRecovery 9/9 | `artifacts/tests/playmode-20261111-060607.xml` |
| 4 pytest tests/physics + tests/gate3 | 40 passed, **8 FAILED** | `logs/step4-pytest-physics-gate3.txt`, `swept/` |
| 5 rendery | 3 × 59 kamer + `r10b_black_05`, VISUALQA_RESULT OK ×6 | `merged/<tier-light>/` (PNG, `view/*.jpg` 1280 px, `sheet-*.jpg`, `stats.txt`) |
| 6 APK Low | BUILD_RESULT Succeeded, errors=0, warnings=12, 179,5 MB, 245 s | `artifacts/apk/kamion-0.1.0-ad4062539c.apk` |

SHA256 APK: `ad514a8bf6e6bfd795a72b2fcf5c645106e21fccc45682814789a7e1faffbf82`
(poprzedni czysty Low `e3671b4309`: 166,2 MB → +13,3 MB; skład: `artifacts/apk/kamion-0.1.0-ad4062539c.content.json`).

## Porażki testów — diagnoza
1. `tests/physics/test_swept_path_gate3.py` — 7 czerwonych. **Regresja ze scalenia 0076** (linia trasy = środek skrajnego prawego pasa), nie geometrii ronda: raster jezdni na wykresie jest taki sam jak 10.11, przesunęła się linia trasy na wyjeździe z ronda Bieżeństwa (E 559, N −689) i Putry (E −535, N 52). Min. prześwit opon naczepy [m], baza `artifacts/swept/run2` (10.11) → teraz: G3-A wide −0,10/czysto → −1,92; G3-A lane −1,10 → −2,94 (także oś kierowana −0,57, napędowa −1,00); G3-B wide czysto → −0,63; G3-B lane czysto → −0,98. Kierowca testowy jadący po linii trasy ścina narożnik. PlayMode WorldCRouteTests (solo i 40 t) przechodzi. Nie naprawiałem (`tests/physics` i `roads/route` poza moją własnością) — do decyzji: poprawić linię trasy na wyjazdach z rond albo tor kierowcy testowego.
2. `tests/physics/test_scenario_strictness.py::test_generator_reproduces_committed_scenarios` — znane sprzed s9: `top_speed_flat_comb.json` zaostrzony ręcznie w `fadddda5` (0082: min 87 → 88, opis źródła), generator nieuaktualniony. Nie regresja scaleń s9.
3. PlayMode skipped 8: 7 × „visual capture, run on demand”, 1 × `AudioLayersTests` (VehicleAudioLibrary nie wygenerowana w chwili testu; build APK wyrenderował audio).

## Regresje wizualne integracji
Obejrzane: 12 arkuszy (wszystkie kamery × 3 warianty) + pełne kadry High-overcast: fire-station-ref7197, stretch-05-docks, kwadrat-park-gate, truck-at-gate, r10_block_2, r10b_black_05, dk8-dk19-exit, chase, trailer-34; Low-overcast: fire-station-ref7197, chase.
- **Nie znaleziono**: różowych materiałów, brakujących tekstur, czarnych obiektów, dublowanych obiektów (kontrola danych: 1014 pojazdów, 0 par bliżej niż 1,9 m), błędnej skali kostki (kwadrat-park-gate, truck-at-gate).
- Sprzed integracji (identyczne w `buildings-r11/r3`): rozciągnięte UV na koronie muru — `g3b-rondo-putry-approach`; ekran akustyczny zasłania pół kadru — `r10_shed_2`.
- Znane otwarte: bok czarnego auta bardzo ciemny (`r10b_black_05`, 0089); pikselowe odbicie w szybie czołowej (`truck-at-gate`, 0087).
- Zmiana układu: linie stanowisk i auta przy starcie przesunięte względem `buildings-r11/r3` (`chase`) — skutek regeneracji po 0092/0093, nie błąd.

## Low — draws/tris na kamerę
Pełna tabela 59 kamer: `stats-low-compare.md` (odniesienie: `artifacts/buildings-r11/r3/Low-overcast/stats.txt`, stan po 0091). Suma: draws 17 247 → 17 332 (+0,5 %), tris 15 403k → 15 440k (+0,2 %). Maks. wzrost draws +2,0 % (cab-left, r10_hall_1); `route-onramp-andersa-above` −3,6 % draws / −7,9 % tris. Wartości = szacunek edytora przed SRP batching; telefon UNVERIFIED.

## Inne ustalenia
- **Regeneracja nie jest identyczna z main**: ten sam kod, a wynik różny od zacommitowanego w `95f49598` (stanowiska 1526 → 1500, auta 908 → 900, kerb_tris 84 942 → 84 705, footprint_nodes +4). Przyczyna nieustalona (UNVERIFIED: starsza kopia `Data/raw/derived` w worktree albo niedeterminizm generatora). APK i rendery pochodzą z regeneracji worktree.
- Megascans (0084) nieaktywny w świecie: `megascans: available=[], fallback=True` — tak samo w logach regeneracji main.
- W worktree brak `Data/photos` → `asphalt_detail_photo` nie odbudowuje się; PNG skopiowane z main, w Unity tekstury z kopii `_Generated`.
- Efekty uboczne Unity cofane po każdym uruchomieniu (`Rendering/Settings`, `ProjectSettings`); po buildzie także `URP_Ultra.asset` i `UniversalRenderPipelineGlobalSettings.asset`.

## Następny krok (lider, gdy żaden Unity nie działa)
`pwsh scripts/build-android.ps1 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-ad4062539c.apk -Install -Run -Serial <A16> -Tier Low -LogcatSeconds 60` → `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Serial <A16>`

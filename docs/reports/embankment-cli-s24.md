# Skarpy i pylony — embankment-cli, s24

Zakres: P3 #13 / #15 z raportu drive-review-s24. Obejrzano wskazane
`shot_t1930.png`, `shot_t2250.png`, `shot_t0310.png`. Wszystkie zapisy,
testy i commity wykonano w worktree `embankment-cli`. Bez Unity, `build_world`
i pushowania. Dane NMT nie były dostępne w tym worktree; kontrola rzeczywistej
drogi używa siatki z danych repozytorium i syntetycznego nasypu.

## Przyczyny i zmiany

- `tools/worldgen/terrain_mesh/conform.py:217`: EDT wyznaczało odległość od
  węzłów rastrowej maski nawierzchni. Wzdłuż ukośnej drogi położenie krawędzi
  przeskakiwało pomiędzy rzędami siatki. Zwiększenie gęstości samego NMT
  pozostawiłoby ten mechanizm. Siatka źródłowa ma już krok 1 m;
  `game/Assets/_Project/World/Import/RegionImporter.cs:689` utrzymuje gęsty pas
  przy drodze w High. Konformowanie otrzymuje teraz ciągły obrys powierzchni
  (`streetscape/stage.py:191`), a `terrain_mesh/conform.py:175` liczy dokładną
  odległość w pasie 16 m, interpoluje przedłużenie wysokości i płynnie wraca
  do starej metryki poza pasem. Nie zmieniono V/T jezdni ani ilości geometrii terenu.
- `tools/worldgen/terrain_mesh/conform.py:164`: końcowy filtr stoków obejmował
  również zakopany teren pod nawierzchnią, po czym włączał się skokowo przy
  granicy pasma. `streetscape/stage.py:202` pomija ten filtr dla nowego obrysu;
  harmoniczne wyrównywanie wysepek nadal działa. Tę poprawkę wskazało review.
- `tools/worldgen/streetscape/far_field.py:1628`: opisane jako „lattice” pylony
  miały dwie pełne, skrzyżowane płaszczyzny trzonu. Na tle nieba wyglądały jak
  szare stożki. Nowa ażurowa konstrukcja ma nogi, przekątne, poziome belki
  i podparte poprzeczniki, po **204 tris/słup** zamiast 12. Pierwszy wariant
  420 tris ograniczono po review. Bez nowych materiałów i submeshy. Dla
  179 słupów z QA dw671-tykocin-09 koszt maksymalny rośnie o 34 368 tris;
  rzeczywista liczba Low zależy od istniejącego odsiewu. FPS nie mierzono.

Decyzja: [ADR 0311](../adr/0311-ciagly-obrys-skarpy-i-kratownice-far-field.md).

## Walidacja

`uv run --project tools/worldgen pytest tests/gis/test_embankment_pylons_s24.py tests/gis/test_unit_meshing_chunks.py tests/gis/test_terrain_walls.py tests/gis/test_far_field.py tests/gis/test_far_field_boundary.py tests/gis/test_far_field_lod1.py tests/gis/test_far_field_industrial_facade.py tests/gis/test_tunnel_0211.py -q --tb=short`

**91 PASS, 1 SKIP**, 21,63 s. Log: `artifacts/embankment-cli/pytest.log`.
Pominięto kontrolę ekstrakcji far-field wymagającą niedostępnego cache danych surowych.
Nowy plik zawiera 19 przypadków: cztery kąty × nasyp/wykop, droga ze spadkiem,
pusty obrys, siatka DK65-10 i osiem wariantów sylwetki Low/High.
Testy obejmują wynik po `tidy`, maksymalny skok między sąsiadami skarpy
≤ 1 / EMBANKMENT_SLOPE m na 1 m, zgodność z profilem analitycznym, brak
NaN/degeneracji, budżet geometrii i prześwity pylonu w dwóch rzutach.
Hash V/T rzeczywistej jezdni DK65-10 przed/po pozostaje identyczny.

Podgląd: `artifacts/embankment-cli/comparison.png` (960×640), obejrzany przez
autora i niezależnego recenzenta. Odtworzenie bez Unity:

`uv run --project tools/worldgen python tools/worldgen/qa/preview_embankment_s24.py --baseline 8ad119ad969f080e4e8dc2c397851723341dac83 --output artifacts/embankment-cli`

Na syntetycznym nasypie pod kątem 23°, w pasie 2,5–5 m od obrysu, maksymalny
błąd końcowego profilu spada z 0,819 m do 2,84e-14 m (dokładność obliczeń).
To pomiar geometrii syntetycznej, **nie wynik przejazdu ani ocena obrazu gry**.
Review końcowego kodu i podglądu: bez blokujących uwag.

## Kafle do przebudowy i kontrola po integracji

- Minimum dla zgłoszeń: **`dk65-10`** (teren) oraz **`dw671-tykocin-09`**
  (far-field). Sam reimport starych GLB nie zastosuje poprawki generatora.
- Do kontroli spójności szwów także `dk65-09`, `dk65-11`,
  `dw671-tykocin-08` i `tykocin`. Pylony są własnością tła danego kafla,
  więc należy regenerować także tła sąsiadów używanych w przejeździe.
- Do pełnego wdrożenia na obecnym korytarzu: cały zestaw **`d67-full`**
  z `region_catalog.json`; poprawki są wspólne dla wszystkich regionów.

Następna, osobno autoryzowana sesja: generacja świata dla powyższych kafli,
reimport wariantów Low i High, przejazd DK65-10 i DW671-09 w obu kierunkach.
Sprawdzić szwy, przełączenia terenowych LOD i czytelność słupów w ruchu.
Przerzedzanie dalszych LOD oraz filtr minimum pod drogą nie zostały zmienione;
wynik wizualny po przebudowie pozostaje **UNVERIFIED**. Pozostałe P1 z raportu
(kurtyny lasu, płyty przecinające drogę) są poza zakresem tej poprawki.

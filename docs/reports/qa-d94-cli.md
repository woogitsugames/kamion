# QA D94 — testy przekrojów i szwy (2026-11-20)

Gałąź `qa-d94-cli`. Bez Unity, przebudowy kafli i push. Wszystkie zapisy w tym worktree.

## Przyczyny i zmiany

1. `tests/gis/conftest.py:133,146`: zerowanie D94 w drugim `pytest_configure` zastąpiono odwracalnymi fixture. Domyślna fixture sesyjna zachowuje 0 dla sieci `piers_check`/`world`, tworzonych przed fixture modułowymi. Fixture modułowa następnie wybiera konfigurację danego modułu. Domyślnie testy pomiarowe nadal otrzymują 0, także fixture modułowe; marker `generated_world` wybiera `GAMEPLAY_LANE_WIDEN_DEFAULT_M` generatora. `tests/gis/test_route_links_s23.py:17` używa tego markera. Test kontroluje jednocześnie pomiarowe 0 w fixture sesyjnej i aktywne D94 w module tras. Usunięcie drugiego hooka przywraca rejestrację `unit`.
2. `tools/worldgen/qa/seams.py:586`: zakresy pomiarowe K1/ADR 0212 pozostają w `REFERENCE`, podczas oceny są przesuwane o `2 * GAMEPLAY_LANE_WIDEN_M` dla dwóch pasów. Dla D94 zakresy 6,0–6,4 i 6,6–7,0 stają się 6,5–6,9 i 7,1–7,5 m; nominalne 6,2/6,8 dają 6,7/7,3 m. Źródło wiersza jawnie podaje D94. Nie zmieniono tolerancji geometrii ani szerokości zakresu. Regresje sprawdzają 0/0,1/0,25 oraz błędną szerokość +0,5 m.
3. Zgłoszone urwania są skutkiem odrzucania przesuniętych ukośnych końców przez test płaszczyzny szwu (5 cm), a nie dowodem wycięcia asfaltu. D94 przesuwa oś w `tools/worldgen/roads/network.py:760`; dla w261104557 szew X=772875, prawa oś X=772874,88 (około 12 cm poza); dla w1560819273 szew Y=603391, lewa oś Y=603390,84 (około 16 cm poza). Graniczne węzły grafu nadal leżą na szwach.
4. Poprawka generatora jest już w historii tej gałęzi: `ad6f732d2` (`dk8-seam-cli`). `tools/worldgen/roads/seam_taper.py:112,155,299,305` używa `End.boundary_xy`/`End.on_seam` po obu stronach; `tools/worldgen/qa/seams.py:303` robi to samo w QA. Nie dublowano poprawki i nie zmieniano przycinania. Nowe regresje (`tests/gis/test_dk8_seam_cli.py:105`) sprawdzają oba rzeczywiste szwy, odtwarzają odrzucenie starego filtra, uruchamiają dyskowy loader sąsiada w obu kierunkach oraz sprawdzają zgodną szerokość i symetrię taperu.
5. Niezależny błąd starego testu linków: zamknięta lista `replacesRoute` nie uwzględniała istniejącego linku `wasilkow-01-to-02` (ADR 0315). Dodano dokładnie `dk8-wasilkow-01` oraz kontrolę, że link zastępuje wyłącznie trasę własnego kafla. Nie rozszerzano progów geometrii.

6. `tests/gis/test_seams_p3_0304.py:30`: test pobocza mieszał sieć pomiarową (0) z zapisanymi szerokościami buildu D94 (8,0/8,5 m). Przy 0 nie ma tego taperu i wiersz historycznego buildu dawał FAIL. Test ładuje te same rzeczywiste dane sieci i kontekstu, ale nie dołącza archiwalnych `roads_qa` z innej konfiguracji. Wszystkie bieżące wiersze geometrii, położenia i poboczy nadal muszą przejść. Produkcyjne QA z D94 nadal ocenia metadane buildu (tu prawidłowo PRZEJŚCIE).

## Dowody i ograniczenia

`artifacts/qa-d94-cli/seams.{json,md,log}`: oba szwy, 16 dróg, zero wierszy urwania i zero FAIL referencji K1. Pozostają 4 FAIL położenia osi po 0,25 m: w76084085, w261104557, w281813932 na Kleeberga/Knyszyńska oraz w1560819273 na dk65-05/06. Są raportowane bez maskowania. Wysokość powierzchni GLB i wizualny stan po imporcie nie zostały w tym przebiegu zweryfikowane; QA używa sieci generatora, nie nowych siatek.

`artifacts/qa-d94-cli/references.{json,md,log}`: wszystkie 15 szwów korytarza DK65, 57 dróg, **30/30 referencji OK**, zero fałszywych FAIL referencji. Ten dodatkowy przebieg używa `--pass1` do kontroli rozstawów; jego 8 innych FAIL nie stanowi globalnego PASS geometrii.

Pierwszy pełny przebieg (`pytest.log`): 94 passed, 3 skipped, 2 failed (stara lista zastępowanych tras i metadane D94 w teście pomiarowym, oba poprawione). `test_links_json_fresh` przeszedł przy D94; porównanie JSON z generatorem jest niezmienione. Końcowy przebieg po korektach (`pytest-final.log`, `-k 'not links_json_fresh'`): **110 passed, 3 skipped, 1 deselected, 492,85 s**. Pominięty selektorem test świeżości JSON przeszedł w pierwszym przebiegu; razem **111 passed, 3 skipped** w dotkniętych modułach, bez FAIL. Nie powtarzano kosztownego niezmienionego porównania JSON. Trzy SKIP wynikają z braku gotowych GLB w tym worktree.

Po doprecyzowaniu sesyjnej konfiguracji wykonano dodatkowo `pytest-session-config.log`: 13 passed (test sesyjnego 0 i modułowego D94 oraz wszystkie przypadki zakresów).

Testy kontrolne: `pytest-reference.log` 12 passed; `pytest-boundaries.log` 2 passed; `pytest-config.log` 13 passed; `pytest-route-config.log` 2 passed; `pytest-session-config.log` 13 passed (częściowo te same testy, nie sumować).

Dodatkowa kontrola `test_road_fidelity.py test_road_consistency.py`: 16 passed, 1 istniejący xfailed, 1 failed (`test_report_not_stale`). Tracked `fidelity_qa.json` ma nieaktualne hashe ośmiu modułów generatora. Świeżość nie została wyłączona ani sztucznie odświeżona; podobny FAIL występuje w wejściowym `regen-wave-2-s24/logs/pytest-final.log`.

## Integracja

Same zmiany fixture i referencji QA nie wymagają przebudowy kafli. Jeśli dane pochodzą z generatora sprzed `ad6f732d2`, przebudować po jednym w tle obie strony: **bialystok-kleeberga, bialystok-knyszynska, dk65-05, dk65-06**, następnie export-route i zależne route_links. Dotyczy to symetrii taperu; przebudowa nie jest naprawą pozostawionych FAIL bocznego położenia osi. Jeśli kafle już zbudowano po tej poprawce, nie ma nowej zmiany generatora wymagającej ponownego build_world.

Polecenia walidacji:

```powershell
uv run --project tools/worldgen python -m pytest -q tests/gis/test_route_links_s23.py tests/gis/test_seams_p3_0304.py tests/gis/test_seams_0224.py tests/gis/test_seam_taper_0275.py tests/gis/test_dk8_seam_cli.py tests/gis/test_road_widen_0306.py
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --tiles bialystok-kleeberga,bialystok-knyszynska,dk65-05,dk65-06 --json artifacts/qa-d94-cli/seams.json --md artifacts/qa-d94-cli/seams.md
```

# Przegląd #93 (`putry-ring-0198b`, ADR 0226) i #82 (`piers-0198`, ADR 0198) — rondo Putry i podpory estakady A

Sesja s21 „cloud D”, 2026-11-15. Bez Unity, `Data/raw`, ortofoto i GPU: przegląd kodu i danych w gicie, testy czystego
Pythona. Stan gałęzi: `origin/piers-0198` = `51f89f4c0`, `origin/putry-ring-0198b` = `a7066e7b7` (przed tym raportem).

## 1. Przenumerowanie ADR (wykonane)
- ADR #93 `0216` kolidował z `origin/summer-led-0216` (latarnie LED Knyszyn). Teraz **0226**
  (`docs/adr/0226-rondo-putry-wyspa-z-ortofoto-apron-width.md`, test `tests/gis/test_putry_ring_0226.py`, oba `git mv`).
  Zmienione odwołania: `tools/worldgen/roads/{network,junctions}.py`, `streetscape/hero_bridge.py`, `tests/gis/{conftest,
  test_piers_vs_roads_0198}.py` (asercja na tekst `ADR 0226` w notatce `viaduct_underdeck.json`), `overrides.yaml`
  regionu C (4 komentarze), `viaduct_underdeck.json` (2), ADR 0198 (link), `docs/WORLD_GENERATION.md`, PR-BODY, live.
  Liczby `0.0216` (`max_grade`) nietknięte; odwołań do LED 0216 na gałęzi brak. Tytuł i opis PR #93 poprawione.

## 2. Relacja #82 ↔ #93
- **#93 zawiera #82 w całości**: `git merge-base --is-ancestor origin/piers-0198 origin/putry-ring-0198b` = prawda;
  baza PR #93 na GitHubie to `piers-0198` (PR ułożone w stos). 3 commity #82 + 5 (teraz 6–7) commitów #93.
- `docs/adr/0198-…md`: 71 linii w #82, 77 w #93 — różnica to wyłącznie dopisana sekcja „Runda 2” (6 linii, link do
  0226). Nie ma rozbieżnych wersji tej samej treści — **dubel, nie konflikt**.
- Te same pliki/klucze z różnymi wartościami: `viaduct_underdeck.json` (`pier_lines_en["173956078"]` 6 → 8 rzędów,
  `pier_lines_en_held` usunięte, notatki), `overrides.yaml` (`putry-ring-s-placement`: stały `center_offset 2.9` → profil),
  `test_piers_vs_roads_0198.py` (`test_sw_deck_conflict_is_explicit` → `…_is_resolved`). To zamierzona ewolucja
  (#82 sam przewidział: „when the ring geometry is corrected this assertion fails on purpose”), nie konflikt.
- Scalanie z `origin/main` (214 commitów do przodu, m.in. `roads/junctions.py`, `build_world.py`, `overrides.yaml`):
  `git merge-tree` czysto; scalenie próbne main + #93 → testy `-k "putry or 0226 or 0198 or roundabout or ronda or
  override"` **71 passed, 1 skipped**.
- Z `origin/budget-fix-s21` (ADR 0221, stan wypchnięty `220d61bae`: `build_world.py`, `streetscape/cycleways.py`):
  `merge-tree` czysto. #93 ponad #82 nie zmienia `build_world.py`; #82 zmienia go o 7 linii (hero bridge). #93 zmienia
  generator dróg C w `roads/network.py` (pole `apron_width`, szerokość strony ISLAND w `assign_sides`) i
  `roads/junctions.py` (`island_curb_radius` w `compute_corners`) — **to ten sam generator, który budget-fix-s21 stroi
  lokalnie**; lokalnej pracy nie widzę, więc ryzyko konfliktu tekstowego w tych dwóch funkcjach istnieje, a semantycznie
  #93 zmienia trójkąty tylko na rondzie Putry (mniej opaski `apron_sett`: −313,8 m², +4 kolumny).

**Kolejność:** (a) zalecana — przestawić bazę #93 na `main`, scalić #93 (wnosi #82), zamknąć #82 jako zawarty w #93;
(b) alternatywa — scalić #82, potem #93 (baza przełączy się na main). Stanu #82 samego (przęsło 79 m, rzędy „held”)
nie ma sensu utrwalać na main, skoro właściciel zdecydował o poprawie ronda.

## 3. Liczby i źródła
| Liczba | Wartość | Źródło / oznaczenie | Ocena |
|---|---|---|---|
| krawężnik wyspy, 38 pkt | `KERB` w teście | ortofoto GUGiK WMS HighResolution 0,05 m/px, 2026-11-15, odczyt na oko ±0,3 m, **WORKING_VALUE** | dane w gicie, odtwarzalne; data nalotu UNVERIFIED — uczciwie oznaczone |
| `apron_width` | 0,4 m | średnia zakresów W/N/E (0–0,7 m), WORKING_VALUE | OK; jasny pas = krawężnik czy krawężnik + pas: UNVERIFIED |
| `island_curb_radius` NW | 10,0 m (pomiar 12,0) | LSQ 12 pkt, reszty ≤ 0,13 m; 10 = największy mieszczący się | OK, błąd 1,4 m zostaje jawnie |
| profil osi drogi S | 1,2 / 0,25 / 0,15 / 2,9 m; szer. 7,2 / 6,0 / 7,0 m | odczyt ortofoto, WORKING_VALUE | patrz F1 |
| rzędy SW | 89,0 i 109,0 m | okno wolne 88–110 m ze skryptu keep-out, ±1 m zapasu; WORKING_VALUE (słupy zasłonięte pomostami) | sprawdziłem geometrię punktów: odległości 32,49 / 20,00 / 26,49 m = deklarowane przęsła |
| max przęsło SW | 32,5 m (było 79,0; reguła 94,8) | 135,5 − 56,5 = 79,0; 89,0 − 56,5 = 32,5 — pochodne | zgodne |
| rozstaw kolumn od jezdni | 3,06 / 2,84 m; min 2,53 m | `check_piers_vs_roads.py` na płaskim modelu | pełny keep-out (place, działki) dopiero po `build_world` |
| liczba rzędów 7–9 na pomost | 8 + 8 | zdjęcia P13-030/031 ESTIMATED, Panoramax tylko referencja | OK |
- Licencje: podglądy `artifacts/putry-ring-0198b/ortho-overlay-*.jpg` (≤ 960 px) mieszczą się we wzorcu
  `artifacts/**/*ortho*` w `docs/LICENSES.md` (dane GUGiK, tylko referencja); atrybucja GUGiK w ADR i PR. Bez Google. OK.
- Brak liczb z PFU/projektów (rysunki obiektu niepubliczne, P13-032/033 UNVERIFIED) — poprawnie zaznaczone.

## 4. Kod — uwagi
- **F1 (średnia, do weryfikacji w Unity przed scaleniem):** droga S ronda — między t 0,42 a 0,62 oś przesuwa się o
  2,75 m na ok. 9 m (≈ 17° względem osi), a szerokość 6,0 → 7,0 m. Linie pasów i tor jazdy po pierścieniu mogą dostać
  „schodek”; dla ciągnika z naczepą to odczuwalny esik na rondzie. Autor zgłosił to jako otwarte. Warunek: render
  `putry-above` + kadr MA-010 `au_r_s1160`; jeśli linia pasa jest skośna/łamana — wydłużyć przejście profilu
  (np. t 0,42 → 0,75) albo przesunąć tylko prawą krawędź (wyspa dzieląca), a nie oś pasów.
- **F2 (mała):** `island_curb_radius` w `junctions.py` nie ma walidacji: wartość tekstowa → `ValueError` i przerwany
  build; `nan`/≤ 0,75 → po cichu narożnik ostry; brak `overrides_stale`, gdy węzeł nie ma narożnika ring–ring albo gdy
  promień nie mieści się i pętla zmniejsza go ×0,7 (wtedy autorska wartość jest cicho ignorowana). Proponuję: zakres
  jak `apron_width` (np. 1–40 m) + wpis do `j.notes`/`overrides_stale`, gdy użyty promień ≠ autorski.
- **F3 (mała):** `apron_width` na celu z listą dróg: jeśli choć jedna droga nie jest rondem, całe `id` trafia do
  `overrides_stale`, choć na pozostałych zostało zastosowane (półprawda w QA). Dziś nieaktywne (4 drogi = ring).
- **F4 (kosmetyka):** pętla po `j.nodes` — wygrywa ostatni węzeł z polem; deterministyczne przy stałej kolejności
  węzłów, ale warto przerwać na pierwszym trafieniu i udokumentować.
- Determinizm: brak losowości, brak zależności od kolejności słowników poza F4. Inne ronda bez zmian (test
  `test_only_the_putry_ring_has_an_authored_apron_width`, `test_default_apron_is_unchanged`). Degeneracja pasa 0 m
  zablokowana (`APRON_W_MIN` 0,2, test profilu). Testy sensowne; `test_north_west_island_corner…` z twardą listą
  promieni (12 / 8,4 / 5,88) jest kruchy przy zmianie reguły — akceptowalne.
- Fixture `piers_check` (sesyjny, ~100 s) współdzielony — dobra zmiana względem #82 (jeden przebieg zamiast dwóch).

## 5. Testy (uruchomione tutaj)
- `pytest tests/gis -k "putry or 0226 or 0198" -q` → 27 passed (po przenumerowaniu).
- `pytest tests/gis -k "piers or viaduct or underdeck or hero_bridge or roundabout or ronda or override" -q` → 63 passed,
  5 skipped (4 × `viaduct_biezenstwa.glb` = wskaźnik git-lfs, 1 × heightmap wymaga `Data/raw`).
- Scalenie próbne `origin/main` + #93: `-k "putry or 0226 or 0198 or roundabout or ronda or override"` → 71 passed, 1 skipped.
- Nieuruchomione: `build_region`, `build_world`, `fidelity/run.py` (`test_report_not_stale` pada do regeneracji —
  wymaga `Data/raw`), import, rendery, SBS, budżet, EditMode, swept path.

## 6. Werdykt
- **#93: FIX (lekki) → SCAL po weryfikacji lidera.** Blokuje tylko F1 (render; poprawka danych tylko gdy linia pasa
  łamie się). F2 zalecane przed scaleniem (kilka linii), F3/F4 mogą iść później. Przed scaleniem: baza → `main`.
- **#82: ZAMKNIJ jako zastąpiony przez #93** (cała zawartość w #93; pośredni stan z przęsłem 79 m nieaktualny po
  decyzji właściciela). Jeśli lider woli zachować historię PR — scalić #82 bezpośrednio przed #93, bez zmian.

## 7. Komendy dla lidera (PowerShell 7, katalog repo, po checkout `putry-ring-0198b` / scaleniu)
```
uv run tools/worldgen/build_region.py --region bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
#  oczekiwane: streetscape_qa.json hero_bridges.pier_cols_on_carriageway == [], spec podpór 8 + 8, pier_lines_skipped 0,
#  overrides_stale bez putry-ring-*
uv run --project tools/worldgen python tools/worldgen/qa/check_piers_vs_roads.py --region bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low  -Lighting overcast -OutputDir artifacts/putry-ring-0198b/low
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear    -OutputDir artifacts/putry-ring-0198b/high
#  kadry: putry-above, au_r_s1160 (F1), g3b_eye_s1582, g3b_eye_s1632, route-putry-approach, driver-andersa-to-putry
uv run --project tools/worldgen python -m pytest tests/gis -q
pwsh scripts/test.ps1 -Platform EditMode
```
Kolejność względem budget-fix-s21 (ADR 0221): najpierw scalić to, co lider ma lokalnie w generatorze dróg C, potem
#93 i jedna regeneracja + jeden pomiar budżetu stretch_04 (żeby nie mierzyć dwa razy).

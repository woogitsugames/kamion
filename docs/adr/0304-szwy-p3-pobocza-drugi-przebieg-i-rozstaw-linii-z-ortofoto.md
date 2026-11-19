# ADR 0304 — Szwy P3: qa.seams porównuje 2. przebieg pobocza, rozstaw linii DK65 / Szosy Knyszyńskiej z ortofoto 0,1 m (seams-p3-s24)

Status: Proposed (agent seams-p3-s24, gałąź `seams-p3-s24`), 2026-11-19. Do scalenia przez lidera.
Powiązane: ADR 0224 (qa szwów), 0275 (`seam_taper`), 0289 (16 FAIL „baseline”), 0205 / 0208 (Szosa Knyszyńska na szwie
`bialystok-knyszynska` | `dk65-01`), 0212 (linie krawędziowe DK65 w Knyszynie, 7,1 m `WORKING_VALUE`), 0220 (K1,
`edge_line_spacing`), 0076 (`_tight_side`, krawędź zlicowana przy drugiej jezdni), 0301 (lanes-audit-s24 — tu bez zmian
w `standards.py` / `markings.py`).

## Kontekst
`qa.seams` na korytarzu (main 11e22c1ff, raport `artifacts/regen-wave-s24/seams.md`): 16 FAIL na 20 szwach, w tym 10 na
trasie: 2 × „pobocze krawężnik vs krawężnik (płasko)” na DK8 (`kleeberga` | `knyszynska` w261104557, C | Maczka
w257367422) i 8 × „referencja rozstawu linii” (`knyszynska` | `dk65-01` 5,6 m przy 6,0–6,4; trzy szwy Knyszyna 7,1 m przy
6,6–7,0).

## Ustalenia (zmierzone)
1. **Pobocze DK8 na szwach = artefakt narzędzia, nie geometrii.** `qa.seams.add_sides` wołał tylko 1. przebieg
   `assign_sides` (bez przycięć skrzyżowań). W 1. przebiegu `_tight_side` pomija drugą jezdnię w promieniu
   `ADJ_NODE_SKIP_M = 30 m` od wspólnego węzła: w `knyszynska` łańcuch DK8 ma 25,9 m do węzła włączenia pasu
   `w561326924`, więc cały jest „przy węźle” → krawężnik 0,13 m; `kleeberga` węzła nie ma → zlicowana (107,5 m).
   Generator (`pipeline.build`) meshuje **2. przebieg** (`trims=True`, pominięcie = przycięcie + 1 m): w nim
   `knyszynska` daje krawędź zlicowaną na całych 26 m po stronie pasu, `kleeberga` 133,5 m — oba kafle to samo
   (`qa/seam_side_probe.py --trims`). Tak samo C | Maczka w257367422: w 2. przebiegu OK.
2. **Rozstaw linii: referencje mają rację, generator nie.** Nowe narzędzie `qa/seam_line_ortho.py`: oś drogi z sieci
   generatora obu kafli, przekrój jasności co 0,5 m na ±40 m od szwu (ortofoto GUGiK WMS HighResolution 0,1 m, 2025),
   najsilniejszy pik farby 2,4–4,2 m od osi po każdej stronie, mediany z przekrojów o kontraście ≥ 15:

   | szew | droga | ortofoto (kafel A / B) | generator przed | referencja |
   |---|---|---|---|---|
   | bialystok-knyszynska / dk65-01 | w234919333 | 6,45 (n 45) / 6,40 (n 49) | 5,6 | K1 6,0–6,4 (km 8,8 = 6,3) |
   | knyszyn-s / knyszyn | w286990127 | 6,80 (79) / 6,75 (79) | 7,1 | 6,6–7,0 |
   | knyszyn / knyszyn-w | w232511646 | 6,75 (58) / 6,75 (73) | 7,1 | 6,6–7,0 |
   | knyszyn-w / dk65-monki-01 | w232511647 | 6,75 (45) / 6,75 (40) | 7,1 | 6,6–7,0 |

   Szosa Knyszyńska: asfalt na pasku ~7,8 m (K1: 7,9–8,4 m), nie 6,1 m z odczytu ortofoto 0,25 m 2024 (ADR 0205).
   Paski: `artifacts/seams-p3-s24/ortho/*/strip_w*.png` (oś generatora = środek, podziałka 1 m, linia szwu na niebiesko).

## Decyzja
1. **`qa.seams` domyślnie porównuje 2. przebieg** (`add_sides(trims=True)`: `ST.apply_shoulders`, potem
   `junctions.build_junctions` na punktach `osm_context` jak `pipeline.build`, potem `assign_sides(..., trims=True)`).
   `--pass1` daje stary raport; źródło wiersza pobocza mówi, który przebieg (`assign_sides, 2. przebieg`); JSON ma
   `sides_pass`. Kod generatora bez zmian.
2. **Override zamiast stałej** (zmiana `EDGE_LINE_INSET_MINOR` przebudowałaby dk65-01…05 i łamała ADR 0220):
   - `dk65-edge-line-spacing-0304` `{edge_line_spacing: 6.8}` w `knyszyn`, `knyszyn-w`, `knyszyn-s`, `dk65-monki-01`
     (osobny wpis — `set` przekroju `dk65-carriageway-width` zostaje ten sam, test ADR 0212). W `knyszyn-s` bez
     w27718745: jego profil szerokości 6,6 → 7,5 m zostaje z wcięciem 0,20 m (6,2 m zmierzone na wąskim odcinku).
   - Szosa Knyszyńska w234919333: `width 6.0 → 6.7` w `knyszynska-seam-w-xsec` (`bialystok-knyszynska`) i
     `knyszynska-xsec-main` (`dk65-01`), ten sam `set` w obu kaflach; linie z reguły 0,20 m od krawędzi = 6,3 m
     (środek między 6,4 przy szwie i K1 6,2–6,3 dalej). ADR 0220 zostawiał ten way bez `edge_line_spacing` — zostaje.
   Wszystkie wartości `WORKING_VALUE` (±0,1 m = 1 px), `verify: owner drive / taśma`.

## Wynik (`artifacts/seams-p3-s24/`)
| raport | FAIL | na trasie | poza trasą |
|---|---|---|---|
| przed, 1. przebieg (`seams_before.md`, = raport regen-wave) | 16 | 10 | 6 |
| przed, 2. przebieg (`seams_pass2.md`) | 15 | 8 | 7 |
| po (`seams_after1.md`, 2. przebieg + override) | **7** | **0** | 7 |

Pozostałe 7 (wszystkie poza trasą, przyczyna = dane kontekstu kafla albo geometria przy węźle po jednej stronie):
- `kleeberga` | `maczka` w257355872 trunk (2 wiersze) + w227027719 trunk_link: łącznica włącza się w DK8 18 m za
  szwem w `maczka`; po stronie `maczka` szczelina 0,4–0,8 m → krawędź zlicowana, po stronie `kleeberga` łącznica jest
  2,4–3,2 m od DK8 (bez wspólnego węzła) → pobocze wiejskie z rowem / krawężnik.
- `kleeberga` | `maczka` w25899482, w25899483 (plac BDOT10k tylko w kontekście `kleeberga`, okno ±12 m reguły placu
  ucięte szwem) i w305072031, C | `maczka` w606396470 (chodnik z ciągu pieszego widocznego tylko w kontekście jednego
  kafla). Naprawa wymaga reguły symetrycznej na kontekście sąsiada (jak `seam_p2a`) — otwarte.

## Budżet
Linie: te same siatki `markings`, 0 draw calls. Szosa Knyszyńska +0,7 m jezdni na ~650 m (2 kafle) — ESTIMATED < 1 tys.
tris. Narzędzie qa: 2. przebieg buduje skrzyżowania wszystkich kafli korytarza (≈ 2× dłużej, 21 kafli ~ 15 min).

## Odtworzenie
```
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --md out.md          # [--pass1]
uv run --project tools/worldgen python -m tools.worldgen.qa.seam_side_probe bialystok-kleeberga bialystok-knyszynska 261104557 --trims
uv run --project tools/worldgen python -m tools.worldgen.qa.seam_line_ortho knyszyn knyszyn-w 232511646 artifacts/seams-p3-s24/ortho/knyszyn-knyszyn-w --along 40
uv run --project tools/worldgen python -m pytest tests/gis/test_seams_p3_0304.py tests/gis/test_region_knyszyn_edges_0212.py -q
```

## Kafle do przebudowy w main po scaleniu
`bialystok-knyszynska`, `dk65-01`, `knyszyn-s`, `knyszyn`, `knyszyn-w`, `dk65-monki-01` (overrides; generator bez zmian,
więc `bialystok-industrial-c` / `bialystok-maczka` / `bialystok-kleeberga` nie wymagają przebudowy).

## Otwarte
1. 7 FAIL poza trasą (wyżej).
2. w27718745 (`knyszyn-s`): szeroka końcówka profilu (km 25,32–25,49) ma linie 7,1 m; ortofoto: przerywane 7,1–7,5 m
   do km 25,49, potem 6,7–6,8 m — reszta poza szwem, bez zmian.
3. Ocena `visual-critic` niewykonana (subagent nie tworzy subagentów) — do lidera. Na kadrze `seam_w_back_into_tile` (knyszynska) przed i po: pognieciona płyta kostki po lewej (plac) — istniejąca usterka, nie z tej zmiany.

## Weryfikacja (prywatna kopia derived, przebudowa 6 kafli exit 0; import Win64 + visual-qa High clear, edytor)
- Rendery `artifacts/seams-p3-s24/vqa/{before,after}/{bialystok-knyszynska,knyszyn-w}/*.jpg`: DK8 przy szwie z kleeberga
  (`seam-e-into-tile`) — pas dodatkowy zlicowany z DK8 bez krawężnika między nimi (jak w kleeberga); Szosa Knyszyńska
  (`seam-w-*`) — jezdnia szersza, linie dalej od siebie; DK65 knyszyn-w (`dk65-seam-east-out`) — linie odsunięte od
  krawędzi 7,5 m. Kadr „przed” knyszyn-w ma różowy budynek: import starego snapshotu derived bez materiału — artefakt
  porównania, nie zmiany.
- `pytest tests/gis` (na przebudowanych kaflach): 2510 passed, 5 failed → po poprawce `test_edge_lines_0205` (6.0 → 6.7)
  zostają 4 testy świeżości, które lider odświeża po przebudowie w main: `test_region_catalog_0267` /
  `test_start_clear_0262` (routeLengthM knyszynska 2961,35 → 2961,34, dk65-01 631,76 → 631,54 —
  `scripts/export-region-catalog.py`), `test_route_links_s23::test_links_json_fresh` (`streaming/route_links.py`),
  `test_world_roads::test_export_is_deterministic` (bialystok-industrial-c — stan C w tym worktree sprzed d39c96bca, bez związku).

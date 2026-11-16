# STATUS int-world3-s23 (integracja world3, s23)
Gałąź `int-world3-s23` z origin/main 64e54592e; worktree `.claude/worktrees/int-world3-s23` (derived = junction do main).
- krok 1 (scalenia, wszystkie bez konfliktów kodu; STATUS.md = ours; README ADR z adr_index.py; LICENSES = suma):
  #147 (pełny gis: 2074 pass / 2 fail = stale: fidelity C + determinizm eksportu C, znikają po przebudowie),
  #154 (-k signs/rail/junction/... 802 pass), #158 (189 pass), #153 (187 pass + navgraph/tests 53 pass),
  #150 (268 pass + 1 fail CRLF hash → fix `.gitattributes Data/Plans/** eol=lf`, 19/19), #164 (203 pass + tools/worldgen/tests 21),
  #165, #169, origin/main (01fa8691a; world2 jeszcze NIE w main).
- krok 1b: pavement_rules knyszyn-w (`knyszyn-w-pavement-rules-d38`), OD-005 `dk8-seam-kerb-od005-c` z powrotem w overrides C, plik pending usunięty.
- visual-qa.ps1: nowy parametr -BuildTarget (Win64 bez przełączania platformy).
- NASTĘPNY KROK: łańcuch world+unity: `artifacts/int-world3-s23/tools/chain.ps1` (status `artifacts/int-world3-s23/logs/chain-*.status`, czytać `exit=`).
- Kafle world2 (dk65-11, knyszyn-s, dk65-06, dw671-tykocin-01, knyszynska, maczka, kleeberga + 18 pierścienia) NIE przebudowywane do scalenia world2 w main.
- 19:3x łańcuch próbny t1 (knyszyn-w, world PID 65404 + unity PID 39788) — czeka w kolejce heavy (4/4 zajęte: dk19-tiles ×3, crash-diag).
- Znany czerwony po scaleniu #153×#169: `test_effective_graph_readers::test_knyszyn_route_graph_has_the_dk65_splits_and_consistent_geometry` (luka węzeł↔oś 1,73 m na 8 krawędziach pierścienia; = review #169 P2-7: pierścień na r 10,5 m z `outer_diameter_m`, węzły KRTG na r OSM 8,65 m). Przy #165 zielony. Do decyzji lidera.
- Sonda uskoku DK65 płd. (`tools/worldgen/qa/knyszyn_s_kerb_step.py`) na derived sprzed #169: W max 0,506 / E max 0,652 m.
- 20:57 łańcuch r1 KOMPLET (exit=0 wszystkich kroków): build_region knyszyn/dojlidy/dk65-04/C; build_world + export-route + katalog 13 kafli (knyszyn, bialystok-dojlidy, dk65-01..05, 07..10, dk65-monki-01, bialystok-industrial-c) + knyszyn-w (t1); fidelity C exit=0; catalog --check exit=0; import Win64 14 kafli exit=0; VQA High: knyszyn 72 PNG, knyszyn-w 47, dojlidy 47, C 53 (`artifacts/int-world3-s23/vqa/<kafel>/<tag>/High-clear/`).
- Chodniki domniemane: knyszyn 0 → 41 925 m², knyszyn-w 0 → 11 464 m² (sidewalk_paving); C i Dojlidy bez zmian (24 459 / 21 103 m²).
- Oględziny: Południowa×Szkolna — łezka znikła, 4 przejścia P-10, chodniki obustronne z kostki; Tykocka (knyszyn-w) chodniki obustronne. Pawilon Rynku w r1 ma żółte ściany i dach namiotowy (P1-1 kolor OK; obok jasny trójkąt nawierzchni — do sprawdzenia; parkingu z płyt brak). Lipy: płaskie karty + ciemny pionowy szew nadal (P1-2 OPEN). Uskok DK65 płd. przy rondzie NADAL widoczny (rondo-dk65-from-south: ściana betonowa po prawej); sonda GLB: W max 0,499 m, E max 0,654 m (przed #169: 0,506 / 0,652) → poprawka (e) z #169 w integracji nie działa (prawdop. #165 zmienia narożnik).
- 23:4x pełne testy po przebudowie w tle: `artifacts/int-world3-s23/logs/final-tests.status`.
- 00:05 pełne testy po przebudowie: tests/gis 2228 pass / 3 fail / 2 xfail / 1 skip (fidelity i determinizm C ZIELONE); tools/worldgen/tests + navgraph/tests 74 pass. Faile: (1) `test_knyszyn_route_graph_…` luka KRTG 1,73 m (#153×#169, ADR 0274 notka); (2) `test_every_graph_reader_is_classified` → naprawione (map_plan_0278, sonda, streaming/*); (3) `test_dk65_seam_knyszyn_0233[dk65-11-knyszyn-s-pt1]` 0,12 > 0,10 m — kafle world2 (nie przebudowywane tu).
- 00:1x merge origin/main (int-ui, #162 eps): konflikty build_route_graph.py (obie strony), visual-qa.ps1 (-BuildTarget + -Pc), knyszyn_route.bytes (przeliczony; pozostałe 13 KRTG bajt w bajt = main), route_links.json przeliczony, katalog --check exit=0.
- Znaki (streetscape_qa, przed→po): knyszyn A-8 0→1, B-18 1→3, B-20 2→3, D-42/43 0→3; knyszyn-w A-7 1→7, D-42/43 0→2; dk65-04 A-7 1→3; dk65-07 A-7 1→3, D-42/43 0→2; dk65-10 A-7 1→6, D-42/43 0→5; dk65-monki-01 A-7 1→5; C i Dojlidy 0 zmian.
- NASTĘPNY KROK (lider): po scaleniu world2 do main → `git merge origin/main` + chain.ps1 -Mode world/unity dla 25 kafli world2 (+ ponowny VQA knyszyn-s/dk65-11), potem decyzja ws. luki KRTG pierścienia i uskoku (e).

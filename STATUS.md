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

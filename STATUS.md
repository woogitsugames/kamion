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

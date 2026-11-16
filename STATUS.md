# STATUS — import-pbr-stale-s23 (D43)
- Krok 1: freshness PBR przeniesiony do `build_all.py --check/--list-outputs` (pomija pliki nieprodukowane: asphalt_detail_photo bez zdjęcia, scan-only bez skanów); import-region.ps1 woła check (exit 0/3). pytest 6/6.
- NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region knyszyn` (lider; oczekiwane: „PBR Medium: … skipped”, bez build_all).
- Krok 2: zasada junction `Data/raw/derived` w docs/09 §5 i AGENT-RULES p. 7a; `new-agent-worktree.ps1` robi teraz junction dla derived (`-CopyDerived` = stara kopia). README materiałów: --check. Nieuruchomione (brak pwsh).
- NASTĘPNY KROK: lider `pwsh scripts/import-region.ps1 -Region knyszyn`; przy nowym worktree `pwsh scripts/new-agent-worktree.ps1 -Name test-junction -NoLibrary` → `(Get-Item .claude/worktrees/test-junction/Data/raw/derived).LinkType` = Junction.

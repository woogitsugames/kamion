# c-regen-s22 — live
- 15.11 20:5x: worktree `.claude/worktrees/c-regen-s22` (gałąź c-regen-s22 z main a7a704287). Kopie generated/*.json sprzed regeneracji: artifacts/c-regen-s22/before/data. Merge-tree obu gałęzi (qa-tools-0219, summer-cd-0216b) czysty.
- W TLE: `artifacts/c-regen-s22/tools/vqa.ps1 -Tag before` (rendery „before” z kodu main, C + Dojlidy, Low/High × clear/dusk). Status: artifacts/c-regen-s22/before/vqa.status, koniec: before/vqa.done.
- NASTĘPNY KROK: po before/vqa.done → `git merge origin/qa-tools-0219 origin/summer-cd-0216b` (osobno), re-checkout Data/Admin/powiaty_prg.geojson, potem `Start-Process pwsh -ArgumentList '-NoProfile','-File','artifacts/c-regen-s22/tools/regen.ps1'` (do napisania: build_region+build_world+fidelity C i Dojlidy pod heavy).

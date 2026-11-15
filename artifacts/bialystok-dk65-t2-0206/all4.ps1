# ADR 0206 round 4: tunnel cut kept open in terrain conform -> rebuild -> probe -> import -> topview -> visual-qa Low, High
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'; $st = "artifacts/$n/all4.status"
"all4 start $(Get-Date -Format s)" | Add-Content $st
Remove-Item "artifacts/$n/chain.status" -ErrorAction SilentlyContinue
pwsh "artifacts/$n/chain.ps1" *> "artifacts/$n/chain4.out"
Get-Content "artifacts/$n/chain.status" -Tail 1 | Add-Content $st
tools/worldgen/.venv/Scripts/python.exe "artifacts/$n/probe_lod2.py" 76073122 23982181 *> "artifacts/$n/probe_lod2_r4.txt"
"probe done" | Add-Content $st
if ((Get-Content "artifacts/$n/chain.status" -Tail 1) -like 'CHAIN DONE*') {
    uv run --project tools/worldgen python tools/worldgen/qa/junction_topview.py --region bialystok-kleeberga --out "artifacts/$n/junctions-r4" *> "artifacts/$n/topview4.log"
    pwsh "artifacts/$n/vqa.ps1" -Tag r4 -Tiers Low *> "artifacts/$n/vqa-r4-low.out"
    pwsh "artifacts/$n/vqa.ps1" -Tag r4 -Tiers High *> "artifacts/$n/vqa-r4-high.out"
}
git checkout -- Data/Regions/bialystok-industrial-c Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json
"ALL3 DONE $(Get-Date -Format s)" | Add-Content $st

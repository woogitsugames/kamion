$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'; $st = "artifacts/$n/r1.status"
"r1 start $(Get-Date -Format s)" | Add-Content $st
pwsh "artifacts/$n/chain.ps1" *> "artifacts/$n/chain1.out"
Get-Content "artifacts/$n/chain.status" -Tail 1 | Add-Content $st
if ((Get-Content "artifacts/$n/chain.status" -Tail 1) -like 'CHAIN DONE*') {
    uv run --project tools/worldgen python tools/worldgen/qa/junction_topview.py --region bialystok-kleeberga --out "artifacts/$n/junctions" *> "artifacts/$n/topview.log"
    "topview exit=$LASTEXITCODE" | Add-Content $st
    pwsh "artifacts/$n/vqa.ps1" -Tag r1 -Tiers Low *> "artifacts/$n/vqa-r1.out"
}
"R1 DONE $(Get-Date -Format s)" | Add-Content $st

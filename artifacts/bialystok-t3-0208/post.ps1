$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-t3-0208'; Set-Location $wt; $A='artifacts/bialystok-t3-0208'
"post start $(Get-Date -Format s)" | Set-Content $A/post.status
uv run --project tools/worldgen python tools/worldgen/qa/junction_topview.py --region bialystok-knyszynska --out $A/junctions-r2 *> $A/topview-r2.log
uv run --project tools/worldgen python $A/route_sweep.py sweep bialystok-knyszynska *> $A/route_sweep_r2.txt
uv run --project tools/worldgen python $A/route_sweep.py seam bialystok-knyszynska bialystok-kleeberga C:\Users\matma\Documents\Claude\kamion\Data\raw\derived\bialystok-kleeberga\world *> $A/seam_e_r2.txt
uv run --project tools/worldgen python $A/route_sweep.py seam bialystok-knyszynska dk65-01 C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk65-corridor-0205\Data\raw\derived\dk65-01\world *> $A/seam_w_r2.txt
"sweep done $(Get-Date -Format s)" | Add-Content $A/post.status
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner bialystok-t3-0208-pytest | Out-Null
uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> $A/pytest-r2.log
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $A/post.status
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner bialystok-t3-0208-pytest | Out-Null
git status --short | Add-Content $A/post.status
"POST DONE $(Get-Date -Format s)" | Add-Content $A/post.status

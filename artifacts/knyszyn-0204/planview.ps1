param([string]$Region='knyszyn',[string]$Tag='r1',[string[]]$At,[switch]$Rebuild)
Set-Location $PSScriptRoot\..\..
$A="artifacts/knyszyn-0204"; $st="$A/plan_${Region}_$Tag.status"; "start" | Set-Content $st
$env:PYTHONUNBUFFERED='1'
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-0204-plan | Out-Null
$env:PLAN_CACHE="$A/plan/${Region}_cache.pkl"; New-Item -ItemType Directory -Force "$A/plan" | Out-Null; $args2=@('--region',$Region,'--out',"$A/plan/$Region/$Tag",'--route','--px','700'); if($Rebuild){$args2+='--rebuild'}
foreach($a in $At){$args2+=@('--at',$a)}
uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py @args2 *> "$A/plan_${Region}_$Tag.log"
"exit=$LASTEXITCODE" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-0204-plan | Out-Null
"DONE" | Add-Content $st

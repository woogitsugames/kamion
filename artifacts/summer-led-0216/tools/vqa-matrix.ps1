param([string]$Tag = 'before', [string[]]$Regions = @('knyszyn','bialystok-knyszynska'))
# visual-qa matrix for ADR 0216: day/dusk/night x Low/High. Sequential, one unity slot per run.
$wt = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Set-Location $wt
$out = "artifacts/summer-led-0216/$Tag"
New-Item -ItemType Directory -Force $out | Out-Null
$status = "$out/vqa.status"; Remove-Item "$out/vqa.done" -ErrorAction SilentlyContinue
foreach ($r in $Regions) { foreach ($t in 'Low','High') { foreach ($l in 'clear','dusk','night') {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    "$(Get-Date -f HH:mm:ss) start $r $t $l" | Add-Content $status
    pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner summer-led-0216 | Out-Null
    try { pwsh scripts/visual-qa.ps1 -Scene "World_$r" -Tier $t -Lighting $l -OutputDir "$out/$r/$t-$l" *> "$out/vqa-$r-$t-$l.log"; $c = $LASTEXITCODE }
    finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner summer-led-0216 | Out-Null }
    "$(Get-Date -f HH:mm:ss) done $r $t $l exit=$c" | Add-Content $status
    git checkout -q -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
} } }
"done" | Set-Content "$out/vqa.done"

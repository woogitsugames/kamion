param([ValidateSet('before','after')][string]$Phase='before',
    [ValidateSet('Low','High')][string]$Tier='Low',
    [ValidateSet('clear','overcast','dusk')][string]$Lighting='overcast')
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r2/24h'
. "$root/scripts/env.ps1"
$source="$root/$ev/FurnitureExactStats.cs"
$target="$root/game/Assets/_Generated/FurnitureExactStats/Editor/FurnitureExactStats.cs"
New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
if ((Test-Path $target) -and (Get-FileHash $target).Hash -ne (Get-FileHash $source).Hash) { throw 'Different owned diagnostic already exists' }
Copy-Item $source $target
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-furniture -StaleHours 876000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'No Unity slot' }
$ok=$false
try {
    $scene=if($Tier -eq 'High'){'WorldC_High'}else{'WorldC'}
    $out=[IO.Path]::GetFullPath("$ev/exact-$Phase/$Tier-$Lighting",$root)
    $log=[IO.Path]::GetFullPath("$ev/exact-$Phase-$Tier-$Lighting.log",$root)
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.FurnitureQA.FurnitureExactStats.Run',
        '-qaScene',$scene,'-qaTier',$Tier,'-qaLighting',$Lighting,'-qaOutput',$out,
        '-qaGate3',"$root/$ev/cameras.json",'-furniturePhase',$Phase)
    if ($code -ne 0 -or !(Select-String $log -SimpleMatch 'FURNITURE_EXACT_STATS_OK cameras=')) { throw 'Counter capture failed' }
    # Small JSON-only verifier, not a heavy generator/test/image job.
    & uv run --project tools/worldgen python "$ev/verify_exact_stats.py" $Phase $Tier $Lighting *> "$ev/exact-$Phase-$Tier-$Lighting-validation.log"
    if ($LASTEXITCODE -ne 0) { throw 'Exact counters did not match frozen output' }
    $ok=$true
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-furniture
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): dokładny licznik CPU $Phase $Tier $Lighting; sukces=$ok, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU."
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
    git add -f "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
    git commit -m "wip(furniture): checkpoint exact $Phase $Tier $Lighting counters"
}

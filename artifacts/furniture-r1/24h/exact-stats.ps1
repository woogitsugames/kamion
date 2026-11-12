param([ValidateSet('Low','High')][string]$Tier='Low',[ValidateSet('clear','overcast')][string]$Lighting='overcast')
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r1/24h'
. "$root/scripts/env.ps1"
$generated="$root/game/Assets/_Generated/FurnitureExactStats/Editor"
New-Item -ItemType Directory -Force $generated | Out-Null
$source="$root/$ev/FurnitureExactStats.cs"
$target="$generated/FurnitureExactStats.cs"
if ((Test-Path -LiteralPath $target) -and (Get-FileHash -LiteralPath $target).Hash -ne (Get-FileHash -LiteralPath $source).Hash) {
    throw 'Existing diagnostic source differs; inspect it before replacing'
}
Copy-Item -LiteralPath $source -Destination $target
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-furniture -StaleHours 876000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Could not acquire Unity slot' }
$ok=$false
try {
    $scene=if ($Tier -eq 'High') {'WorldC_High'} else {'WorldC'}
    $out=[IO.Path]::GetFullPath("$root/$ev/exact-after4/$Tier-$Lighting")
    $log="$root/$ev/exact-$Tier-$Lighting.log"
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.FurnitureQA.FurnitureExactStats.Run',
        '-qaScene',$scene,'-qaTier',$Tier,'-qaLighting',$Lighting,'-qaOutput',$out,
        '-qaGate3',"$root/$ev/cameras.json",'-furniturePhase','after4')
    if ($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'FURNITURE_EXACT_STATS_OK cameras=55')) {
        throw "Exact counter run failed ($code); inspect log"
    }
    & uv run --project tools/worldgen python "$ev/verify_exact_stats.py" $Tier $Lighting *> "$ev/exact-$Tier-$Lighting-verification.log"
    if ($LASTEXITCODE -ne 0) { throw 'Exact counter validation failed; no budget claim may use it' }
    $ok=$true
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-furniture
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): dokładniejszy licznik CPU $Tier $Lighting; sukces=$ok. Slot Unity zwolniony. NASTĘPNY KROK: odczytać zweryfikowane granice budżetu; to nie pomiar GPU."
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r1/STATUS.md
    git add -f "$ev/STATUS.md" artifacts/furniture-r1/STATUS.md
    git commit -m "wip(furniture): checkpoint unrounded CPU counters $Tier $Lighting"
}

param([string]$Round = 'base', [string]$Configs = 'High:overcast', [switch]$SkipImport, [string]$Cameras = '')
# One visual round: (PHONE_RUN lock) -> import-region -> visual-qa per Tier:Lighting -> 960 px JPGs. Run from the worktree root.
$ErrorActionPreference = 'Continue'
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$lock2 = $lock -replace 'PHONE_RUN','GPT_UNITY_HOLD'
# machine-wide Unity limit (scripts/unity-slot.ps1, max 4 at once; also waits for PHONE_RUN): acquire before EVERY Unity run
function WaitLock { while (Test-Path $lock2) { Start-Sleep 60 }; pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Owner claude-buildings-r7 | Out-Host }
function FreeSlot { pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Release -Owner claude-buildings-r7 | Out-Host }
$out = "artifacts/buildings-r15/$Round"
New-Item -ItemType Directory -Force $out | Out-Null
if (-not $SkipImport) {
    WaitLock
    $t = Get-Date
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$out/import.log"
    FreeSlot
    "import exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
}
$camFile = 'Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json'
foreach ($cfg in $Configs.Split(',')) {
    $tier, $light = $cfg.Split(':')
    WaitLock
    $t = Get-Date
    $dir = "$out/$tier-$light"
    $args2 = @('-Scene', 'WorldC', '-Tier', $tier, '-Lighting', $light, '-Gate3', $camFile, '-OutputDir', $dir)
    if ($Cameras) { $args2 += @('-Cameras', $Cameras) }
    pwsh scripts/visual-qa.ps1 @args2 *> "$out/qa-$tier-$light.log"
    FreeSlot
    "qa $cfg exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
    New-Item -ItemType Directory -Force "$dir/960" | Out-Null
    Get-ChildItem "$dir/*.png" | ForEach-Object { magick $_.FullName -resize 960x "$dir/960/$($_.BaseName).jpg" }
}
# Unity side effects (AGENT-RULES 2)
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
if ((Test-Path game/Assets/Resources) -and -not (Get-ChildItem game/Assets/Resources -Force)) { Remove-Item game/Assets/Resources, game/Assets/Resources.meta -Force -ErrorAction SilentlyContinue }
'round done' | Tee-Object -Append "$out/round.log"

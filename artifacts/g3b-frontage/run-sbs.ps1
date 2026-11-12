# Renders the SBS photo-pose cameras (Low overcast by default) under a Unity slot and moves the result to artifacts/g3b-frontage/<Name>.
param([string]$Name = 'baseline', [string[]]$Tiers = @('Low'), [string[]]$Lighting = @('overcast'))
$ErrorActionPreference = 'Stop'
$Tiers = @($Tiers | ForEach-Object { $_ -split ',' }); $Lighting = @($Lighting | ForEach-Object { $_ -split ',' })   # pwsh -File passes 'a,b' as one string
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-g3b-frontage
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/sbs-gate3.ps1 -Tiers $Tiers -Lighting $Lighting
    $code = $LASTEXITCODE
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-g3b-frontage
    Pop-Location
}
$dst = Join-Path $root "artifacts\g3b-frontage\$Name"
if (Test-Path (Join-Path $root 'artifacts\sbs-gate3\renders')) {
    New-Item -ItemType Directory -Force $dst | Out-Null
    robocopy (Join-Path $root 'artifacts\sbs-gate3') $dst /E /NFL /NDL /NJH /NJS /NP | Out-Null
}
"sbs exit=$code -> $dst"

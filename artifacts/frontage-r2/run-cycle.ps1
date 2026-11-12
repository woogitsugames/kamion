# build_world -> import -> SBS G3-B render (Low overcast + clear) -> control cameras -> artifacts/frontage-r2/<Name>; writes cycle-<Tag>.done
param([string]$Name = 'baseline', [string]$Tag = '0', [switch]$SkipBuild)
$log = Join-Path $PSScriptRoot "cycle-$Tag.log"
if (-not $SkipBuild) { & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-build.ps1') -Log "build-world-$Tag.log" *> $log }
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-import.ps1') -Log "import-$Tag.log" *>> $log
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-sbs.ps1') -Name $Name -Lighting overcast *>> $log
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-control.ps1') -Name $Name -Lighting overcast *>> $log
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-sbs.ps1') -Name $Name -Lighting clear *>> $log
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-control.ps1') -Name $Name -Lighting clear *>> $log
'done' | Set-Content (Join-Path $PSScriptRoot "cycle-$Tag.done")

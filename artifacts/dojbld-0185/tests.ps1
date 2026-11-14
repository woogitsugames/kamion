$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot\..\..
$n = 'dojbld-0185'; $a = "artifacts/$n"; $st = "$a/tests.status"
Remove-Item "$a/tests.done" -ErrorAction SilentlyContinue
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n | Out-Null
"pytest start $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider *> "$a/pytest-gis.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n | Out-Null
pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
"editmode start $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/test.ps1 -Platform EditMode *> "$a/editmode.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"done $(Get-Date -Format s)" | Set-Content "$a/tests.done"

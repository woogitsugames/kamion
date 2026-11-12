param([ValidatePattern('^wet-cube-lab(?:-v\d+)?$')][string]$OutputName='wet-cube-lab')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
. "$repo/scripts/env.ps1"
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$output="$PSScriptRoot/$OutputName"
$log="$PSScriptRoot/$OutputName.$(Get-Timestamp).log"
& pwsh $slot -Acquire -Owner gpt-light -PollSeconds 1 -StaleHours 87600
if($LASTEXITCODE){throw 'No Unity slot'}
try {
    git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    if($LASTEXITCODE){throw 'Uncommitted settings before lab'}
    $start=Get-Date
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Rendering.Editor.WetCubeLab.Run','-wetCubeLabOut',$output)
    $result=Select-String -Path $log -SimpleMatch 'WET_CUBE_LAB_RESULT: OK images=16'|Select-Object -Last 1
    $files=@(Get-ChildItem -LiteralPath $output -Filter '*.png' -ErrorAction SilentlyContinue|Where-Object {$_.LastWriteTime -ge $start -and $_.Length -gt 0})
    $complete=$result -and $files.Count -eq 18 -and @($files|Where-Object Name -Like '*_envcube.png').Count -eq 2
    if($code -ne 0 -and $complete){
        $mono=Select-String -Path $log -SimpleMatch 'Cleanup mono'|Where-Object LineNumber -GT $result.LineNumber
        $abort=Select-String -Path $log -SimpleMatch 'abort_threads: Failed aborting'|Where-Object LineNumber -GT $result.LineNumber
        $fatal=Select-String -Path $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
        if($mono -and $abort -and -not $fatal){Write-Warning "Known Mono shutdown after complete lab, original exit=$code";$code=0}
    }
    if($code -ne 0 -or -not $complete){Show-UnityLogErrors $log;throw "Incomplete wet lab code=$code log=$log"}
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-light
}
Add-Content "$PSScriptRoot/STATUS.md" "Lab kostki16/16 +2cube zakończony, log=$log; wynik obrazu nadal wymaga oceny."
git add -f artifacts/light-r3/STATUS.md
git commit -m 'WIP light r3: record completed controlled reflection laboratory'

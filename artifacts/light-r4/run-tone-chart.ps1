param([ValidatePattern('^tone-chart(?:-[a-z0-9]+)?$')][string]$OutputName='tone-chart')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
. "$repo/scripts/env.ps1"
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$output="$PSScriptRoot/$OutputName"
$log="$PSScriptRoot/$OutputName.$(Get-Timestamp).log"
& pwsh $slot -Acquire -Owner gpt-light -PollSeconds 1 -StaleHours 87600
if($LASTEXITCODE){throw 'No Unity slot'}
git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
if($LASTEXITCODE){& pwsh $slot -Release -Owner gpt-light;throw 'Commit own settings before chart'}
try {
    $start=Get-Date
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Rendering.Editor.LightToneChart.Run','-lightToneChartOut',$output)
    $result=Select-String -Path $log -SimpleMatch 'LIGHT_TONE_CHART_RESULT: OK images=8'|Select-Object -Last 1
    $files=@(Get-ChildItem -LiteralPath $output -Filter '*.png' -ErrorAction SilentlyContinue|Where-Object {$_.LastWriteTime -ge $start -and $_.Length -gt 0})
    $complete=$result -and $files.Count -eq 8
    foreach($tier in @('Low','High')) {foreach($preset in @('Clear','Overcast','Dusk','Night')) {
        $proof=Get-Content "$output/$tier-$preset.json" -Raw|ConvertFrom-Json
        if($proof.patches.Count -ne 24 -or $proof.tier -ne $tier -or $proof.preset -ne $preset -or $proof.postProcessing -ne ($tier -eq 'High') -or -not $proof.gradingVerified){$complete=$false}
    }}
    if(Select-String -Path $log -Pattern 'Shader error|error CS\d+' -Quiet){$complete=$false}
    if($code -ne 0 -and $complete){
        $mono=Select-String -Path $log -SimpleMatch 'Cleanup mono'|Where-Object LineNumber -GT $result.LineNumber
        $abort=Select-String -Path $log -SimpleMatch 'abort_threads: Failed aborting'|Where-Object LineNumber -GT $result.LineNumber
        $fatal=Select-String -Path $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error' -Quiet
        if($mono -and $abort -and -not $fatal){Write-Warning "Known Mono shutdown after complete chart, original=$code";$code=0}
    }
    if($code -ne 0 -or -not $complete){Show-UnityLogErrors $log;throw "Incomplete chart code=$code log=$log"}
}
finally{git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings;& pwsh $slot -Release -Owner gpt-light}
Add-Content "$PSScriptRoot/STATUS.md" "Plansza tonów8/8, metadata24pól i postLow=false/High=true; log=$log. Wynik obrazu i różnice wymagają analizy."
git add -f artifacts/light-r4/STATUS.md
git commit -m 'WIP light r4: record actual tier tone-chart capture'


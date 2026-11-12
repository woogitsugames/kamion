param([ValidatePattern('^grade-lab(?:-v\d+)?$')][string]$OutputName='grade-lab')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
. "$repo/scripts/env.ps1"
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$folder="$PSScriptRoot/$OutputName";$log="$PSScriptRoot/$OutputName.$(Get-Timestamp).log"
$source=(git rev-parse HEAD).Trim()
$sourcePaths=@('game/Assets/_Project/Rendering/Editor/LightGradeLutLab.cs','game/Assets/_Project/Rendering/Editor/LightGradeLutLab.shader','game/Assets/_Project/Rendering/Editor/LightGradeLutWorldProbe.cs','game/Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl')
$sourceHashes=@($sourcePaths|ForEach-Object {@{path=$_;sha256=(Get-FileHash -LiteralPath $_).Hash}})
& pwsh $slot -Acquire -Owner gpt-light -PollSeconds 1 -StaleHours 87600
if($LASTEXITCODE){throw 'No Unity slot'}
git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
if($LASTEXITCODE){& pwsh $slot -Release -Owner gpt-light;throw 'Commit own settings before lab'}
try{
    $start=Get-Date
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Rendering.Editor.LightGradeLutLab.Run','-lightGradeLabOut',$folder)
    $result=Select-String -Path $log -SimpleMatch 'LIGHT_GRADE_LAB_RESULT: OK images=33 cubes=6 holdoutPerPreset=192 gradientPerPreset=12288 physicalBypassMax=0'|Select-Object -Last 1
    $files=@(Get-ChildItem -LiteralPath $folder -Filter '*.png' -ErrorAction SilentlyContinue|Where-Object {$_.LastWriteTime -ge $start -and $_.Length -gt 0})
    $complete=$result -and $files.Count -eq 33
    if(-not $complete){Show-UnityLogErrors $log;throw "Incomplete lab before proof reading: exit=$code, freshPNG=$($files.Count), log=$log"}
    foreach($preset in @('Clear','Overcast','Night')){
        $proof=Get-Content "$folder/$preset-proof.json" -Raw|ConvertFrom-Json
        if($proof.captureBypassMaxRgb -ne 0 -or $proof.measurements.Count -ne 3 -or @($proof.measurements|Where-Object {$_.samples.Count -ne 192}).Count){$complete=$false}
        foreach($size in @(16,32)){
            $raw=Get-Item -LiteralPath "$folder/$preset-lut$size-RGBAHalf.raw"
            if($raw.Length -ne $size*$size*$size*8 -or $raw.LastWriteTime -lt $start){$complete=$false}
        }
        foreach($suffix in @('key.json','proof.json','gradient-proof.json')){
            if((Get-Item -LiteralPath "$folder/$preset-$suffix").LastWriteTime -lt $start){$complete=$false}
        }
        $gradient=Get-Content "$folder/$preset-gradient-proof.json" -Raw|ConvertFrom-Json
        if($gradient.measurements.Count -ne 3 -or @($gradient.measurements|Where-Object {$_.samples.Count -ne 12288}).Count){$complete=$false}
    }
    if(Select-String -Path $log -Pattern 'Shader error|error CS\d+' -Quiet){$complete=$false}
    if($code -ne 0 -and $complete){
        $mono=Select-String -Path $log -SimpleMatch 'Cleanup mono'|Where-Object LineNumber -GT $result.LineNumber
        $abort=Select-String -Path $log -SimpleMatch 'abort_threads: Failed aborting'|Where-Object LineNumber -GT $result.LineNumber
        $fatal=Select-String -Path $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error' -Quiet
        if($mono -and $abort -and -not $fatal){Write-Warning "Known Mono shutdown after complete lab, original=$code";$code=0}
    }
    if($code -ne 0 -or -not $complete){Show-UnityLogErrors $log;throw "Incomplete grade lab code=$code log=$log"}
    foreach($item in $sourceHashes){if((Get-FileHash -LiteralPath $item.path).Hash -ne $item.sha256){throw 'Lab source changed during render'}}
    $outputs=@(Get-ChildItem -LiteralPath $folder -File|Where-Object Name -ne 'manifest.json'|ForEach-Object {@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
    @{source_commit=$source;source_files=$sourceHashes;outputs=$outputs;started=$start.ToUniversalTime().ToString('o');log=$log}|ConvertTo-Json -Depth 8|Set-Content "$folder/manifest.json" -Encoding utf8
}
finally{git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings;& pwsh $slot -Release -Owner gpt-light}
Add-Content "$PSScriptRoot/STATUS.md" "Lab gradingu33PNG+6kostek,192holdout+12288gradientnaPreset zakończony; log=$log. To diagnostyka, bez wdrożenia lub GPU PASS."
git add -f artifacts/light-r5/STATUS.md
git commit -m 'WIP light r5: record actual High-baked LUT laboratory evidence'





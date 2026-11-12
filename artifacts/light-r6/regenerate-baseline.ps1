param([ValidateSet('Materials','World','Fidelity','Import','Baseline')][string]$StartAt='Materials')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $repo
if(Test-Path -LiteralPath "$PSScriptRoot/STOP-REQUESTED.txt"){throw 'User requested pause; read PRZEKAZANIE.md before explicitly resuming'}
if((git branch --show-current).Trim() -ne 'gpt-light-r6'){throw 'Expected round6'}
. "$repo/scripts/env.ps1"
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$phase=@('Materials','World','Fidelity','Import','Baseline').IndexOf($StartAt)
function RecordStep($message){Add-Content "$PSScriptRoot/STATUS.md" $message;git add -f artifacts/light-r6/STATUS.md;git commit -m "wip(light): $message"}
function HeavyStep($task){& pwsh -File "$PSScriptRoot/run-heavy.ps1" -Task $task;if($LASTEXITCODE){throw "Heavy $task failed; no subsequent phase"}}
function LatestLog($task){$files=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter "heavy-$task-*.log"|Where-Object Name -Match ('^heavy-'+$task+'-\d{8}-\d{6}\.log$')|Sort-Object LastWriteTime -Descending);if(-not $files.Count){throw "Missing $task log"};return $files[0].FullName}
function CheckWorldTree($checkpoint){if($checkpoint.worldgenTree -ne (git rev-parse HEAD:tools/worldgen).Trim()){throw 'World generator source changed since checkpoint'}}
function CheckMaterials {
    $checkpoint=Get-Content "$PSScriptRoot/materials-checkpoint.json" -Raw|ConvertFrom-Json
    if($checkpoint.sourceTree -ne (git rev-parse HEAD:art-source/world/materials/_src).Trim() -or $checkpoint.specSha -ne (Get-FileHash art-source/world/materials/materials_spec.json).Hash){throw 'Materials checkpoint source/spec changed'}
    foreach($f in $checkpoint.files){if(-not(Test-Path -LiteralPath $f.path) -or (Get-FileHash -LiteralPath $f.path).Hash -ne $f.sha){throw "Material output changed: $($f.path)"}}
}
if($phase -eq 0){
    HeavyStep BuildAll
    $spec=Get-Content art-source/world/materials/materials_spec.json -Raw|ConvertFrom-Json;$files=@()
    foreach($property in $spec.sets.PSObject.Properties){$tier=$property.Value.files.Medium;if(-not $tier){continue};foreach($name in $tier.files){$path="art-source/world/materials/$($tier.dir)/$name";if(-not(Test-Path -LiteralPath $path)){throw "Missing generated material: $path"};$files+=@{path=$path;sha=(Get-FileHash -LiteralPath $path).Hash}}}
    @{sourceTree=(git rev-parse HEAD:art-source/world/materials/_src).Trim();specSha=(Get-FileHash art-source/world/materials/materials_spec.json).Hash;files=$files;log=(LatestLog BuildAll)}|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/materials-checkpoint.json" -Encoding utf8
    RecordStep 'r6 materials and raw CC0 verification complete; heavy released'
}
CheckMaterials
if($phase -le 1){
    HeavyStep BuildWorld;$log=LatestLog BuildWorld
    if(-not(Select-String -LiteralPath $log -Pattern '\[world\s+\d+(?:\.\d+)?s\] done$' -Quiet) -or (Select-String -LiteralPath $log -SimpleMatch 'fallback=True' -Quiet)){throw 'World did not complete cleanly without fallback'}
    Copy-Item -LiteralPath $log -Destination "$PSScriptRoot/build-world.log"
    @{worldgenTree=(git rev-parse HEAD:tools/worldgen).Trim();manifestSha=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash;logSha=(Get-FileHash $log).Hash;log=$log}|ConvertTo-Json|Set-Content "$PSScriptRoot/world-checkpoint.json" -Encoding utf8
    RecordStep 'r6 world generated without fallback; heavy released'
}
$world=Get-Content "$PSScriptRoot/world-checkpoint.json" -Raw|ConvertFrom-Json;CheckWorldTree $world
if($world.logSha -ne (Get-FileHash -LiteralPath $world.log).Hash){throw 'World log changed'}
if($phase -le 2){
    if($world.manifestSha -ne (Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash){throw 'World manifest changed before fidelity'}
    HeavyStep Fidelity;$log=LatestLog Fidelity
    @{worldgenTree=$world.worldgenTree;worldLogSha=$world.logSha;manifestSha=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash;log=$log;logSha=(Get-FileHash $log).Hash}|ConvertTo-Json|Set-Content "$PSScriptRoot/fidelity-checkpoint.json" -Encoding utf8
    RecordStep 'r6 fidelity complete; heavy released before Unity acquisition'
}
$fidelity=Get-Content "$PSScriptRoot/fidelity-checkpoint.json" -Raw|ConvertFrom-Json;CheckWorldTree $fidelity
if($fidelity.worldLogSha -ne $world.logSha -or $fidelity.logSha -ne (Get-FileHash -LiteralPath $fidelity.log).Hash -or $fidelity.manifestSha -ne (Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash){throw 'Fidelity checkpoint changed'}
if($phase -le 3){
    if(-not(Test-Path Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb) -or -not(Test-Path Data/Regions/bialystok-industrial-c/route_start.json)){throw 'Missing import inputs; do not invoke un-slotted nested generation'}
    CheckMaterials
    # Refuse before entering the restore scope: pre-existing settings edits must survive a failed import precondition.
    git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    if($LASTEXITCODE){throw 'Settings dirty before import; preserve them and commit explicitly'}
    $log="$PSScriptRoot/import.$(Get-Timestamp).log"
    & pwsh $slot -Acquire -Owner gpt-light -PollSeconds 5 -StaleHours 87600
    if($LASTEXITCODE){throw 'No Unity slot; resume at Import after exact terminal failure'}
    try{
        # Same Unity entry point/arguments as import-region.ps1, after its Python preflight was completed above under heavy.
        $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
        if($code -ne 0 -or (Select-String -LiteralPath $log -Pattern 'Shader error|error CS\d+|\w+Exception:' -Quiet)){throw "Import failed: $code $log"}
        $scenes=@();foreach($name in 'WorldC','WorldC_High'){$path="game/Assets/_Generated/World/bialystok-industrial-c/$name.unity";$scenes+=@{path=$path;sha=(Get-FileHash -LiteralPath $path).Hash}}
        @{worldgenTree=$world.worldgenTree;manifestSha=$fidelity.manifestSha;scenes=$scenes;log=$log}|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/import-checkpoint.json" -Encoding utf8
    }finally{git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings;& pwsh $slot -Release -Owner gpt-light}
    RecordStep 'r6 import complete under Unity-only slot; no heavy slot held'
}
$import=Get-Content "$PSScriptRoot/import-checkpoint.json" -Raw|ConvertFrom-Json;CheckWorldTree $import
if($import.manifestSha -ne (Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash){throw 'Imported manifest changed'}
foreach($scene in $import.scenes){if($scene.sha -ne (Get-FileHash -LiteralPath $scene.path).Hash){throw 'Imported scene changed'}}
& pwsh -File "$PSScriptRoot/run-light-batch.ps1" -Jobs artifacts/light-r6/baseline.json -EnvDump
if($LASTEXITCODE){throw 'Baseline failed; inspect before new mutations'}

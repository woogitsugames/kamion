param([ValidateSet('Import','Capture','Test','Probe')][string]$Stage, [string]$Label = 'baseline',
    [string]$Cameras='', [ValidateSet('Low','High')][string]$ProbeTier='Low',
    [ValidateSet('clear','overcast')][string]$ProbeLighting='overcast',
    [ValidateSet('none','cracks_off','photo_off','grime_off')][string]$Ablation='none',
    [ValidatePattern('^[a-z0-9_]+([,;][a-z0-9_]+)*$')][string]$AblationMaterials='road_asphalt')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repo
$env:KAMION_ARTIFACTS_DIR = Join-Path $repo 'artifacts'
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$importStatePath='artifacts/asphalt-r3/current-import-state.json'
function Assert-ImportedWorld {
    if(-not(Test-Path $importStatePath)){throw 'No recorded fresh import; run Import first.'}
    $importState=Get-Content $importStatePath -Raw|ConvertFrom-Json
    if(-not $importState.complete){throw 'Import is incomplete; do not render the old scene.'}
    foreach($entry in @(
        @('manifest_sha256','Data/Regions/bialystok-industrial-c/generated/world_manifest.json'),
        @('factory_sha256','game/Assets/_Project/World/Import/WorldPbrMaterials.cs'),
        @('materials_spec_sha256','art-source/world/materials/materials_spec.json'))){
        if($importState.($entry[0]) -ne (Get-FileHash $entry[1]).Hash){throw "Import/source mismatch: $($entry[1])"}
    }
    return $importState
}
if($Stage -in @('Probe','Capture')){Assert-ImportedWorld|Out-Null}
function Write-CaptureContext([string]$OutputDir,[string]$Tier,[string]$Lighting,[string]$RequestedIds){
    # Run after acquiring the slot too: imports/sources may have changed during a long queue wait.
    $state=Assert-ImportedWorld
    New-Item -ItemType Directory -Force $OutputDir|Out-Null
    [ordered]@{schema=1;started_at=(Get-Date -Format o);label=$Label;tier=$Tier;lighting=$Lighting;
        requested_ids=$RequestedIds;ablation=$Ablation;import=$state;
        fixture_sha256=(Get-FileHash artifacts/asphalt-r3/cameras.json).Hash;
        qa_probe_sha256=(Get-FileHash game/Assets/_Project/Editor/VisualQA/AsphaltQaStateProbe.cs).Hash;
        world_root_sha256=(Get-FileHash game/Assets/_Project/World/Runtime/WorldRegionRoot.cs).Hash;
        shader_sha256=(Get-FileHash game/Assets/_Project/Environment/Shaders/WorldPBR.shader).Hash
    }|ConvertTo-Json -Depth 8|Set-Content "$OutputDir/capture-context.json"
}
if ($Stage -ne 'Probe' -and ($Ablation -ne 'none' -or $env:KAMION_ASPHALT_QA_ABLATION)) {
    throw 'Ablations are permitted only for explicit Probe captures, never import/test/full capture.'
}
function Invoke-Slotted([scriptblock]$Action) {
    & pwsh $slotScript -Acquire -Owner gpt-asphalt -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) { throw "Unity stage failed: $LASTEXITCODE" }
    } finally {
        & pwsh $slotScript -Release -Owner gpt-asphalt
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
if ($Stage -eq 'Import') {
    # import-region.ps1 can silently invoke Python builders. Require their outputs before taking a Unity slot.
    if (-not (Test-Path Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb) -or
        -not (Test-Path Data/Regions/bialystok-industrial-c/route_start.json)) {
        throw 'Run the world producer under a heavy slot before importing.'
    }
    $matRoot = 'art-source/world/materials'
    $spec = Get-Content "$matRoot/materials_spec.json" -Raw | ConvertFrom-Json
    $srcTime = (Get-ChildItem "$matRoot/_src" -Filter '*.py' | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    foreach ($p in $spec.sets.PSObject.Properties) {
        $files = $p.Value.files.Medium
        if (-not $files) { continue }
        foreach ($name in $files.files) {
            $png = Join-Path $matRoot "$($files.dir)/$name"
            if (-not (Test-Path $png) -or (Get-Item $png).LastWriteTimeUtc -lt $srcTime) {
                throw 'Run the required material producer under a heavy slot before importing.'
            }
        }
    }
    $importStarted=Get-Date
    $importState=[ordered]@{complete=$false;started_at=$importStarted.ToString('o');label=$Label;
        manifest_sha256=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash;
        factory_sha256=(Get-FileHash game/Assets/_Project/World/Import/WorldPbrMaterials.cs).Hash;
        materials_spec_sha256=(Get-FileHash art-source/world/materials/materials_spec.json).Hash}
    $importState|ConvertTo-Json|Set-Content $importStatePath
    Invoke-Slotted { & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c }
    $report='artifacts/world/bialystok-industrial-c-import.json'
    if(-not(Test-Path $report) -or (Get-Item $report).LastWriteTime -lt $importStarted){throw 'Fresh import report missing'}
    $importState.complete=$true
    $importState.finished_at=Get-Date -Format o
    $importState.report_sha256=(Get-FileHash $report).Hash
    $importState|ConvertTo-Json|Set-Content $importStatePath
} elseif ($Stage -eq 'Test') {
    Invoke-Slotted { & pwsh scripts/test.ps1 -Platform EditMode }
} elseif ($Stage -eq 'Probe') {
    if (-not $Cameras) { throw 'Specify the exact camera IDs for a pose probe.' }
    $out = "artifacts/asphalt-r3/$Label/$ProbeTier-$ProbeLighting"
    $env:KAMION_ASPHALT_QA_STATE = '1'
    $env:KAMION_ASPHALT_QA_DIRECTORY = [IO.Path]::GetFullPath($out, $repo)
    $env:KAMION_ASPHALT_QA_ABLATION = if ($Ablation -eq 'none') { $null } else { $Ablation }
    $env:KAMION_ASPHALT_QA_ABLATION_MATERIALS = $AblationMaterials
    try {
        Invoke-Slotted {
            Write-CaptureContext $out $ProbeTier $ProbeLighting $Cameras
            & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $ProbeTier -Lighting $ProbeLighting -Cameras $Cameras -Gate3 artifacts/asphalt-r3/cameras.json -OutputDir $out
        }
    } finally {
        $env:KAMION_ASPHALT_QA_STATE = $null
        $env:KAMION_ASPHALT_QA_DIRECTORY = $null
        $env:KAMION_ASPHALT_QA_ABLATION = $null
        $env:KAMION_ASPHALT_QA_ABLATION_MATERIALS = $null
    }
    if ($Ablation -ne 'none') {
        $evidence = Get-Content "$out/ablation-state.json" -Raw | ConvertFrom-Json
        if ($evidence.mode -ne $Ablation -or $evidence.materialSlots -le 0) { throw 'Ablation did not match an enabled material slot.' }
    }
    Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Zapisano próbę pozy $out dla $Cameras; nie jest to pełny baseline ani końcowy komplet kamer."
    git add -f artifacts/asphalt-r3/STATUS.md
    git commit -m "wip(asphalt): checkpoint selected-camera pose probe $Label"
} else {
    foreach ($tier in @('Low','High')) {
        foreach ($lighting in @('overcast','clear')) {
            $out = "artifacts/asphalt-r3/$Label/$tier-$lighting"
            $env:KAMION_ASPHALT_QA_STATE = '1'
            $env:KAMION_ASPHALT_QA_DIRECTORY = [IO.Path]::GetFullPath($out, $repo)
            try {
                Invoke-Slotted {
                    Write-CaptureContext $out $tier $lighting ''
                    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $lighting -Gate3 artifacts/asphalt-r3/cameras.json -OutputDir $out
                }
            } finally {
                $env:KAMION_ASPHALT_QA_STATE = $null
                $env:KAMION_ASPHALT_QA_DIRECTORY = $null
            }
            Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): zapisano $out. Następny krok: pozostałe serie lub porównanie wariantu."
            git add -f artifacts/asphalt-r3/STATUS.md
            git commit -m "wip(asphalt): checkpoint $Label $tier $lighting capture"
        }
    }
}

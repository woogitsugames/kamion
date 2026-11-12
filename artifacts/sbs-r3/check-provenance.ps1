$ErrorActionPreference='Stop'
$wrapper=Join-Path $PSScriptRoot 'render-gantry-probes.ps1'
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($wrapper,[ref]$null,[ref]$parseErrors)
if($parseErrors){throw ($parseErrors|Out-String)}
$definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-ProbeInputs'},$true)
if(!$definition){throw 'Missing production assertion function'}
Invoke-Expression $definition.Extent.Text
$taskRoot=Join-Path $PSScriptRoot ('contract-fixture-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskRoot | Out-Null
Push-Location $taskRoot
try {
    $world='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
    $material='art-source/world/materials/materials_spec.json'
    $prodCamera='Data/Regions/bialystok-industrial-c/sbs_cameras.json'
    $prodRefs='Data/Regions/bialystok-industrial-c/sbs_references.json'
    $cameraFile='probe-cameras.json';$planFile='plan.json';$importFile='import.json';$photoFile='comparison.png'
    foreach($file in @($world,$material,$prodCamera,$prodRefs,$cameraFile,$photoFile)){
        $directory=Split-Path $file -Parent
        if($directory){New-Item -ItemType Directory -Force $directory | Out-Null}
        Set-Content -LiteralPath $file -Value ('fixture '+$file) -Encoding utf8
    }
    function Hash($file){(Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant()}
    $import=[pscustomobject]@{exit_code=0;world_manifest_sha256=(Hash $world);materials_spec_sha256=(Hash $material)}
    $plan=[pscustomobject]@{world_manifest_sha256=(Hash $world);probe_cameras_sha256=(Hash $cameraFile);production_source_sha256=[pscustomobject]@{$prodCamera=(Hash $prodCamera);$prodRefs=(Hash $prodRefs)};probes=@([pscustomobject]@{photo=$photoFile;photo_sha256=(Hash $photoFile)})}
    $plan | ConvertTo-Json -Depth 5 | Set-Content $planFile -Encoding utf8
    $import | ConvertTo-Json -Depth 5 | Set-Content $importFile -Encoding utf8
    $loadedPlanHash=Hash $planFile;$loadedImportHash=Hash $importFile
    Assert-ProbeInputs
    $results=@([ordered]@{case='matching imported inputs';accepted=$true})
    $cases=@(
        @{file=$world;reason='Current inputs differ from imported scene'},
        @{file=$material;reason='Current inputs differ from imported scene'},
        @{file=$cameraFile;reason='Probe plan does not match world/cameras'},
        @{file=$planFile;reason='Plan/import receipt changed after loading'},
        @{file=$importFile;reason='Plan/import receipt changed after loading'},
        @{file=$prodCamera;reason='Production source changed since probe preparation'},
        @{file=$prodRefs;reason='Production source changed since probe preparation'},
        @{file=$photoFile;reason='Comparison photo changed since preparation'}
    )
    foreach($case in $cases){
        $full=(Resolve-Path $case.file).Path;$original=[IO.File]::ReadAllBytes($full)
        try {
            [IO.File]::WriteAllText($full,'changed after simulated wait')
            $rejected=$false;$reason=''
            try {Assert-ProbeInputs} catch {$rejected=$true;$reason=$_.Exception.Message}
            if(!$rejected -or $reason -ne $case.reason){throw "Incorrect rejection for $($case.file): $reason"}
            $results += [ordered]@{case=$case.file;rejected=$true;reason=$reason}
        } finally {[IO.File]::WriteAllBytes($full,$original)}
        Assert-ProbeInputs
    }
    [ordered]@{checked_at_utc=[DateTime]::UtcNow.ToString('o');wrapper_sha256=(Hash $wrapper);source_function='Assert-ProbeInputs extracted by PowerShell AST';scope='Tiny synthetic files only; does not launch Unity, Python, acquire slots or claim runtime world validation';results=$results} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $PSScriptRoot 'provenance-contract-results.json') -Encoding utf8
    Write-Output 'PASS matching inputs and eight stale-input rejection cases; restored valid fixture after each mutation'
} finally {Pop-Location}

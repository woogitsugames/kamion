$ErrorActionPreference='Stop'
$baseline=Get-Content artifacts/sbs-r3/baseline-completed.json -Raw | ConvertFrom-Json
$worldPath='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
$materialPath='art-source/world/materials/materials_spec.json'
if($baseline.world_exit -ne 0 -or $baseline.materials_exit -ne 0 -or $baseline.world_manifest_sha256 -ne (Get-FileHash $worldPath).Hash.ToLowerInvariant() -or $baseline.materials_spec_sha256 -ne (Get-FileHash $materialPath).Hash.ToLowerInvariant()){throw 'Need completed matching r3 baseline before import'}
$importHead=(& git rev-parse HEAD).Trim()
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh -NoProfile -File $slotScript -Acquire -Owner gpt-sbs -PollSeconds 7 -StaleHours 87600
if($LASTEXITCODE -ne 0){throw 'Unity acquisition failed'}
try {
    # Prevent import-region from silently starting build_world/build_all outside heavy.
    if(!(Test-Path Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb) -or !(Test-Path Data/Regions/bialystok-industrial-c/route_start.json)){throw 'World/route missing; regenerate through heavy before import'}
    $matRoot='art-source/world/materials'
    $spec=Get-Content "$matRoot/materials_spec.json" -Raw | ConvertFrom-Json
    $srcTime=(Get-ChildItem "$matRoot/_src" -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    $missing=0;$stale=0
    foreach($set in $spec.sets.PSObject.Properties){
        $tier=$set.Value.files.Medium
        if(!$tier){continue}
        foreach($file in $tier.files){
            $path=Join-Path $matRoot ($tier.dir+'/'+$file)
            if(!(Test-Path -LiteralPath $path)){$missing++}elseif((Get-Item -LiteralPath $path).LastWriteTimeUtc -lt $srcTime){$stale++}
        }
    }
    Write-Output "PBR preflight: $missing missing, $stale stale"
    if($missing -or $stale){throw 'PBR generation required; run through heavy, do not auto-build inside import'}
    pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c
    if($LASTEXITCODE -ne 0){throw 'Region import failed'}
    if($baseline.world_manifest_sha256 -ne (Get-FileHash $worldPath).Hash.ToLowerInvariant() -or $baseline.materials_spec_sha256 -ne (Get-FileHash $materialPath).Hash.ToLowerInvariant()){throw 'World/material changed during import'}
    [ordered]@{exit_code=0;git_sha=$importHead;completed_at_utc=[DateTime]::UtcNow.ToString('o');world_manifest_sha256=$baseline.world_manifest_sha256;materials_spec_sha256=$baseline.materials_spec_sha256} | ConvertTo-Json -Depth 4 | Set-Content artifacts/sbs-r3/import-completed.json -Encoding utf8
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    pwsh -NoProfile -File $slotScript -Release -Owner gpt-sbs
}


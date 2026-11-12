$ErrorActionPreference='Stop'
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$root='artifacts/sbs-r2/pose-diagnostic182';$file=Join-Path $root 'cameras.json';$render=Join-Path $root 'renders'
$ids=(Get-Content $file -Raw | ConvertFrom-Json).cameras.id
pwsh -NoProfile -File $slot -Acquire -Owner gpt-sbs -PollSeconds 7 -StaleHours 87600
if($LASTEXITCODE -ne 0){throw 'Unity slot acquisition failed'}
try {
    New-Item -ItemType Directory -Force $render | Out-Null
    $inputs=[ordered]@{cameras_sha256=$file;world_manifest_sha256='Data/Regions/bialystok-industrial-c/generated/world_manifest.json';materials_spec_sha256='art-source/world/materials/materials_spec.json';production_cameras_sha256='Data/Regions/bialystok-industrial-c/sbs_cameras.json'}
    $capture=[ordered]@{git_sha=(& git rev-parse HEAD).Trim();captured_at_utc=[DateTime]::UtcNow.ToString('o');tier='Low';lighting='overcast';width=1280;height=720;diagnostic_only=$true;pose_confidence='C';cameras=@($ids);status='RUNNING'}
    foreach($key in $inputs.Keys){$capture[$key]=(Get-FileHash $inputs[$key]).Hash.ToLowerInvariant()}
    $capture | ConvertTo-Json -Depth 8 | Set-Content "$root/capture.json" -Encoding utf8
    pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width 1280 -Height 720 -Gate3 $file -Cameras ($ids -join ',') -OutputDir $render
    if($LASTEXITCODE -ne 0){throw 'Diagnostic render failed'}
    foreach($key in $inputs.Keys){if($capture[$key] -ne (Get-FileHash $inputs[$key]).Hash.ToLowerInvariant()){throw "Input changed: $key"}}
    if($capture.git_sha -ne (& git rev-parse HEAD).Trim()){throw 'HEAD changed during diagnostic capture'}
    $capture.render_sha256=@{}
    foreach($id in $ids){$capture.render_sha256[$id]=(Get-FileHash (Join-Path $render ($id+'.png'))).Hash.ToLowerInvariant()}
    $capture.status='OK';$capture | ConvertTo-Json -Depth 8 | Set-Content "$root/capture.json" -Encoding utf8
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    pwsh -NoProfile -File $slot -Release -Owner gpt-sbs
}

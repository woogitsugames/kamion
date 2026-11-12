$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
# World and Materials share this branch's heavy identity. Never acquire twice.
while(-not ((Get-Content "$PSScriptRoot/baseline-wrapper.log" -Raw).Contains('released gpt-landmarks-r2'))) {Start-Sleep -Seconds 2}
& uv run --project tools/worldgen python artifacts/landmarks-r2/prepare_cache.py
if($LASTEXITCODE -ne 0){throw 'Cache inventory failed'}
$cache=Get-Content "$PSScriptRoot/material-cache.json" -Raw | ConvertFrom-Json
if($cache.missing_sets.Count) {
    & pwsh artifacts/landmarks-r2/heavy-step.ps1 -Step Materials -Only ($cache.missing_sets -join ',') -Tiers 'High,Medium,Low' -Log artifacts/landmarks-r2/baseline-materials.log
    if($LASTEXITCODE -ne 0){throw 'Missing material cache generation failed'}
}
& uv run --project tools/worldgen python artifacts/landmarks-r2/prepare_cache.py
if($LASTEXITCODE -ne 0){throw 'Cache verification failed'}
$cache=Get-Content "$PSScriptRoot/material-cache.json" -Raw | ConvertFrom-Json
if(-not $cache.all_ready){throw 'Prepared map cache still incomplete'}
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 4: brakujące nowe cache PBR po merge main przygotowano osobno pod heavy i zweryfikowano PNG. Zachowano własny fire_station. Własny marker zwalnia import; żaden generator nie startował po cichu z Unity."
& git add -f artifacts/landmarks-r2/STATUS.md artifacts/landmarks-r2/material-cache.json
& git commit -m 'wip(landmarks): przygotowanie brakujących cache po merge main'
if($LASTEXITCODE -ne 0){throw 'Cache checkpoint failed'}
Remove-Item -LiteralPath "$PSScriptRoot/DIAGNOSTICS_RUNNING"
@{complete=$true;all_ready=$true} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/cache-result.json"
exit 0

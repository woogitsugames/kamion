$ErrorActionPreference='Stop'
uv run --project tools/worldgen python artifacts/gpt-s16-r3/fingerprint_world.py after
if($LASTEXITCODE -ne 0){throw 'Raw fingerprint failed'}
$raw=Get-Content artifacts/gpt-s16-r3/raw-integrity.json -Raw | ConvertFrom-Json
if($raw.changed.Count -ne 0){throw 'Raw world changed: inspect before accepting unchanged geometry'}
@{failures=@(); raw_files=$raw.files; changed=@()} | ConvertTo-Json | Set-Content artifacts/gpt-s16-r3/world-integrity.json
git add -f artifacts/gpt-s16-r3/after-raw-sha256.json artifacts/gpt-s16-r3/raw-integrity.json artifacts/gpt-s16-r3/world-integrity.json
git commit -q -m "wip(s16): verify raw world identical after shadow flag generation"
pwsh artifacts/gpt-s16-r3/import.ps1 -Label after
if($LASTEXITCODE -ne 0){throw 'After import failed'}
pwsh artifacts/gpt-s16-r3/render.ps1 -Stage after
if($LASTEXITCODE -ne 0){throw 'After renders failed'}
pwsh artifacts/gpt-s16-r3/render-near.ps1
if($LASTEXITCODE -ne 0){throw 'Final near render failed'}
pwsh artifacts/gpt-s16-r3/test-editmode.ps1
if($LASTEXITCODE -ne 0){throw 'Full EditMode failed'}

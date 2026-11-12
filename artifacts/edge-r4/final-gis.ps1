$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r4'){throw 'Wrong round'}
& pwsh -File "$PSScriptRoot/heavy.ps1" -Task GisFinal -AtRoundEnd *> "$PSScriptRoot/gis-final.log"
$code=$LASTEXITCODE
@{owner='gpt-edge-r4';task='RoundEndGis';pool='heavy';exit_code=$code;finished=(Get-Date -Format o)}|
    ConvertTo-Json|Set-Content "$PSScriptRoot/gis-final-receipt.json"
& pwsh -File "$PSScriptRoot/post-gis.ps1" *> "$PSScriptRoot/post-gis.log"
if($LASTEXITCODE -ne 0){throw 'Post-GIS scope check failed'}
exit $code

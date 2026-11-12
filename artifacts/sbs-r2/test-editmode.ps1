$ErrorActionPreference='Stop'
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh -NoProfile -File $slotScript -Acquire -Owner gpt-sbs -PollSeconds 7 -StaleHours 87600
if($LASTEXITCODE -ne 0){throw 'Unity slot acquisition failed'}
try {
    $started=[DateTime]::UtcNow
    pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode
    if($LASTEXITCODE -ne 0){throw 'EditMode failed'}
    $result=Get-ChildItem artifacts/tests -Filter editmode-*.xml | Where-Object LastWriteTimeUtc -ge $started | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if(!$result){throw 'New EditMode XML not found'}
    Copy-Item -LiteralPath $result.FullName -Destination artifacts/sbs-r2/editmode.xml
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    pwsh -NoProfile -File $slotScript -Release -Owner gpt-sbs
}

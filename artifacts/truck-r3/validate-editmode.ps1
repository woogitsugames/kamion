param(
    [string]$Filter = '',
    [ValidatePattern('^[a-z0-9-]+$')] [string]$Label = 'final'
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
$runStart = Get-Date
$testExit = -1
try {
    $arguments = @('-Platform','EditMode')
    if ($Filter) { $arguments += @('-Filter',$Filter) }
    pwsh scripts/test.ps1 @arguments
    $testExit = $LASTEXITCODE
    $xml = Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Where-Object LastWriteTime -ge $runStart | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$xml) { throw 'Brak świeżego XML testów.' }
    Copy-Item -LiteralPath $xml.FullName -Destination "artifacts/truck-r3/$Label-editmode.xml"
    [xml]$document = Get-Content -LiteralPath $xml.FullName
    $run = $document.'test-run'
    $summary = [ordered]@{ filter=$Filter; exit=$testExit; total=[int]$run.total; passed=[int]$run.passed; failed=[int]$run.failed; skipped=[int]$run.skipped; result=[string]$run.result; source_xml=$xml.FullName }
    $summary | ConvertTo-Json | Set-Content -Encoding utf8 "artifacts/truck-r3/$Label-editmode.json"
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "EditMode $Label`: $($summary.passed)/$($summary.total), failed $($summary.failed), skipped $($summary.skipped), exit $testExit. XML i JSON w pakiecie. Następny krok: przy błędzie odczytać konkretny test; przy powodzeniu kontynuować walidację rundy."
git add -f artifacts/truck-r3/STATUS.md
git commit --only artifacts/truck-r3/STATUS.md -m "wip(truck): EditMode $Label"
if ($testExit -ne 0 -or $summary.failed -gt 0 -or $summary.total -eq 0) { throw 'Testy EditMode nie są zielone.' }

param([Parameter(Mandatory)][ValidateSet('Red','Green')][string]$Phase)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
if (-not (Test-Path "$PSScriptRoot/Before.complete")) { throw 'Complete the baseline before adding/running the regression' }
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$label = $Phase.ToLowerInvariant()
$oldResults = @(Get-ChildItem artifacts/tests -Filter '*.xml' | ForEach-Object Name)
& pwsh $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 2 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Unity slot failed' }
try {
    & pwsh scripts/test.ps1 -Platform EditMode -Filter 'Game.Tests.EditMode.WorldEdgeApronGradeTests.CornerFan_DoesNotBiasUniformPerimeterSmoothing' *> "$PSScriptRoot/corner-$label-runner.log"
    $code = $LASTEXITCODE
    $newResults = @(Get-ChildItem artifacts/tests -Filter '*.xml' | Where-Object Name -notin $oldResults)
    if ($newResults.Count -ne 1) { throw "Expected one fresh result file, got $($newResults.Count)" }
    [xml]$doc = Get-Content -LiteralPath $newResults[0].FullName -Raw
    $run = $doc.'test-run'
    if ([int]$run.total -ne 2 -or [int]$run.skipped -ne 0) { throw 'Expected exactly two executed slope cases' }
    if ($Phase -eq 'Red') {
        if ($code -eq 0 -or [int]$run.failed -ne 2) { throw 'Old production code must fail both corner regressions' }
        foreach ($test in $doc.SelectNodes('//test-case')) {
            if ($test.failure.message.InnerText -notmatch 'uniform perimeter') { throw 'Unexpected failure cause; do not classify as the intended red regression' }
        }
    } elseif ($code -ne 0 -or [int]$run.failed -ne 0 -or [int]$run.passed -ne 2) {
        throw 'Both corner regressions must pass after the fix'
    }
    New-Item -ItemType Directory -Force "$PSScriptRoot/tests" | Out-Null
    Copy-Item -LiteralPath $newResults[0].FullName -Destination "$PSScriptRoot/tests/corner-$label.xml"
    @{phase=$Phase;commit=(git rev-parse HEAD);exit_code=$code;total=[int]$run.total;
      passed=[int]$run.passed;failed=[int]$run.failed;skipped=[int]$run.skipped;
      production_sha256=(Get-FileHash game/Assets/_Project/World/Import/WorldEdgeBuilder.cs -Algorithm SHA256).Hash;
      test_sha256=(Get-FileHash game/Assets/_Project/Tests/EditMode/WorldEdgeApronGradeTests.cs -Algorithm SHA256).Hash} |
        ConvertTo-Json | Set-Content "$PSScriptRoot/corner-$label-result.json"
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Test narożnika $Phase potwierdzony: total $($run.total), passed $($run.passed), failed $($run.failed); XML i SHA w corner-$label-result.json."
git add -f artifacts/edge-r3/STATUS.md "artifacts/edge-r3/corner-$label-result.json" "artifacts/edge-r3/tests/corner-$label.xml"
git commit -m "wip(edge): record verified $label corner regression result"
if ($LASTEXITCODE -ne 0) { throw 'Checkpoint failed' }

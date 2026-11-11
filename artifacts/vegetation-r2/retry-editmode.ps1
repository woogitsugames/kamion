$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location $taskRoot
$mainRoot='C:/Users/matma/Documents/Claude/kamion'
$release=Join-Path $PSScriptRoot 'ROOT_EDITMODE_RELEASE.txt'
if(-not(Test-Path -LiteralPath $release)){throw 'ROOT must explicitly release B after phone workflow completion'}
foreach($guard in @('PHONE_RUN','GPT_UNITY_HOLD')) {
 if(Test-Path -LiteralPath (Join-Path $mainRoot "artifacts/locks/$guard")){throw "Still held: $guard"}
}
$testExit=1
try {
 pwsh scripts/test.ps1 -Platform EditMode *> artifacts/vegetation-r2/editmode-retry.log
 $testExit=$LASTEXITCODE
} finally {
 git restore --worktree -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings
 Remove-Item -LiteralPath $release -ErrorAction SilentlyContinue
}
$result=Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $result){throw 'No actual NUnit result'}
Copy-Item -LiteralPath $result.FullName -Destination artifacts/vegetation-r2/EditMode.xml
uv run --project tools/worldgen python artifacts/vegetation-r2/snapshot_canonical.py --check > artifacts/vegetation-r2/canonical-after-editmode.txt
if($LASTEXITCODE -ne 0){throw 'Canonical world changed after EditMode'}
if($testExit -ne 0){throw "EditMode retry failed: $testExit; inspect actual XML/log"}
[xml]$doc=Get-Content -LiteralPath $result.FullName
if([int]$doc.'test-run'.failed -ne 0 -or [int]$doc.'test-run'.passed -eq 0){throw 'NUnit is not a passing nonempty run'}
'B_EDITMODE_RETRY_OK'
exit 0

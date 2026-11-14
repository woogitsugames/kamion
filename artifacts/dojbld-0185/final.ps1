Set-Location $PSScriptRoot\..\..
Remove-Item artifacts/dojbld-0185/tests.status, artifacts/dojbld-0185/tests.done, artifacts/dojbld-0185/chain-r4.status -ErrorAction SilentlyContinue
pwsh -NoProfile -File artifacts/dojbld-0185/chain.ps1 -Tag r4
pwsh -NoProfile -File artifacts/dojbld-0185/tests.ps1

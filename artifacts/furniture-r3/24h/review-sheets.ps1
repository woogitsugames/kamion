param([Parameter(Mandatory=$true)][int]$PostPid)
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$post=Get-CimInstance Win32_Process -Filter "ProcessId=$PostPid"
if($post){
    if($post.CommandLine -notmatch 'furniture-r3/24h/post-candidate.ps1') {throw 'Unexpected post-candidate process'}
    Wait-Process -Id $PostPid -ErrorAction SilentlyContinue
}
$coverage=@(Get-Content "$ev/frame-coverage.json" -Raw | ConvertFrom-Json)
if($coverage.Count -ne 4 -or ($coverage | Measure-Object cameras -Sum).Sum -ne 236){throw 'Incomplete camera coverage'}
$low=@($coverage|Where-Object tier -eq 'Low')
if($low.Count -ne 2 -or @($low|Where-Object {!$_.exact_before -or !$_.exact_after}).Count){throw 'Exact Low comparison incomplete'}
$side=@(Get-ChildItem "$ev/after-side" -Recurse -Filter *.png -ErrorAction SilentlyContinue)
if($side.Count -ne 8){throw 'Second-corner capture incomplete'}
# Full image batch belongs in the heavy pool; no same-owner heavy job is started concurrently.
& pwsh "$ev/heavy-step.ps1" -Step compare -Phase after1
if($LASTEXITCODE -ne 0){throw 'Review sheet batch failed'}
$sheets=@(Get-ChildItem "$ev/compare" -Filter *.jpg)
if($sheets.Count -ne 40){throw 'Expected forty complete review sheets'}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): przygotowano 40 arkuszy przed/po dla wszystkich 236 kadrów. Pełny batch pracował w heavy, po zakończeniu liczników Low i ośmiu narożników. To nie jest deklaracja obejrzenia arkuszy. NASTĘPNY KROK: pełna recenzja wizualna, analiza budżetu i końcowe testy."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/compare" "$ev/compare-after1.log" "$ev/review-sheets.ps1"
git commit -m 'wip(furniture): preserve all 236 before-after pairs for review'

param([Parameter(Mandatory=$true)][int]$CandidatePid)
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$candidate=Get-CimInstance Win32_Process -Filter "ProcessId=$CandidatePid"
if($candidate){
    if($candidate.CommandLine -notmatch 'furniture-r3/24h/candidate3.ps1'){throw 'Unexpected candidate producer'}
    Wait-Process -Id $CandidatePid -ErrorAction SilentlyContinue
}
$coverage=@(Get-Content "$ev/iteration3/frame-coverage.json" -Raw|ConvertFrom-Json)
if($coverage.Count -ne 4 -or ($coverage|Measure-Object cameras -Sum).Sum -ne 236){throw 'Candidate3 is not complete'}
$policy=Get-Content "$ev/shelter-policy-after3.json" -Raw|ConvertFrom-Json
if(!$policy.variant_inherits_generic){throw 'No valid visibility policy'}
foreach($tier in @('Low','High')){
    & pwsh "$ev/unity-step.ps1" -Step sbs-shelter -Phase after3 -Tier $tier -Lighting overcast
    if($LASTEXITCODE -ne 0){throw "Photo hypotheses failed: $tier"}
}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): zapisano 12 dodatkowych kadrów hipotez fotograficznych (6 Low i 6 High), poza 236 kamerami budżetowymi. To nie jest potwierdzenie dopasowania zdjęcia ani oględzin. Każdy renderer pobrał i zwolnił slot Unity. NASTĘPNY KROK: obejrzeć odpowiedniki zdjęcia, wybrać lub odrzucić hipotezy z jawnym uzasadnieniem."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/photo-shelter-captures.ps1"
git commit -m 'wip(furniture): retain separate photo-pose hypothesis captures' --quiet

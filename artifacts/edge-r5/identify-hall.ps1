param([Parameter(Mandatory)][int]$WaitPid)
$ErrorActionPreference='Stop'
$env:OMP_NUM_THREADS='1';$env:OPENBLAS_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:NUMEXPR_NUM_THREADS='1'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
while(-not(Test-Path "$PSScriptRoot/Baseline.ready")){
    if(-not(Get-Process -Id $WaitPid -ErrorAction SilentlyContinue)){throw 'Baseline pipeline stopped without ready marker'}
    Start-Sleep -Seconds 5
}
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-edge-r5'){throw 'Wrong round'}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 1 -StaleHours 100000
if($LASTEXITCODE -ne 0){throw 'Inspector heavy slot failed'}
$code=1
try{
    & uv run --project tools/worldgen python "$PSScriptRoot/identify_hall.py"
    $code=$LASTEXITCODE
}finally{
    & pwsh -File $slot -Release -Pool heavy -Owner $owner -StaleHours 100000
    @{task='IdentifyHall';owner=$owner;pool='heavy';exit_code=$code;finished=(Get-Date -Format o)}|
        ConvertTo-Json|Set-Content "$PSScriptRoot/hall-identification-receipt.json"
}
if($code -ne 0){throw 'Candidate source/mesh identification failed; inspect before production changes'}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Identyfikacja C061 zakończona kodem0 pod heavy; obejrzeć hall-identified-overlay.jpg i odczytać hall-identification.json przed edycją fasady."
git add -f artifacts/edge-r5/STATUS.md artifacts/edge-r5/hall-identification.json artifacts/edge-r5/hall-identification-receipt.json
git commit -m 'WIP edge r5: match source hall geometry to frozen production meshes'
if($LASTEXITCODE -ne 0){throw 'Identification checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/Identification.ready"

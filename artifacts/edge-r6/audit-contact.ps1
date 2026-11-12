param([ValidateSet('before','after')][string]$Phase='before',[int]$WaitPid=0)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
$required=if($Phase -eq 'before'){'Baseline.ready'}else{'After.ready'}
while(-not(Test-Path "$PSScriptRoot/$required")){
    if($WaitPid -le0 -or -not(Get-Process -Id $WaitPid -ErrorAction SilentlyContinue)){throw 'Frozen phase not ready; inspect its process'}
    Start-Sleep -Seconds 5
}
$done=if($Phase -eq 'before'){'ContactBefore.ready'}else{'ContactAfter.ready'}
if(Test-Path "$PSScriptRoot/$done"){throw 'Contact phase already measured; preserve it before a deliberate new attempt'}
$env:OMP_NUM_THREADS='1';$env:OPENBLAS_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:NUMEXPR_NUM_THREADS='1'
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-edge-r6.slot'){throw 'Another own heavy lease exists; do not silently reuse it'}
& pwsh -File "$PSScriptRoot/acquire-slot.ps1" -Pool heavy -Owner gpt-edge-r6
if($LASTEXITCODE -ne0){throw 'Contact heavy acquisition failed'}
$acquired=Get-Date -Format o
$tag=Get-Date -Format 'yyyyMMdd-HHmmss'
$toolSha=(Get-FileHash "$PSScriptRoot/audit_contact.py" -Algorithm SHA256).Hash
$code=99
try{
    & uv run --project tools/worldgen python "$PSScriptRoot/audit_contact.py" $Phase *> "$PSScriptRoot/contact-$Phase-$tag.log"
    $code=$LASTEXITCODE
}finally{
    & pwsh -File $slot -Release -Pool heavy -Owner gpt-edge-r6 -StaleHours 100000
    @{phase=$Phase;owner='gpt-edge-r6';pool='heavy';acquired=$acquired;finished=(Get-Date -Format o);
      tool_sha256=$toolSha;exit_code=$code;log="contact-$Phase-$tag.log"}|
      ConvertTo-Json|Set-Content "$PSScriptRoot/contact-$Phase-$tag-receipt.json"
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Audyt rzeczywistych podstaw kurtyn $Phase zakończony pod heavy, exit=$code; log i receipt z datą zachowane. To geometria, nie potwierdzenie alfa tekstury ani widocznego szwu ze zdjęcia."
git add -f artifacts/edge-r6/STATUS.md "artifacts/edge-r6/contact-$Phase-$tag-receipt.json"
if($code -eq0){git add -f "artifacts/edge-r6/contact-$Phase.json"}
git commit -m "WIP edge r6: preserve actual imported curtain contact audit $Phase result"
if($LASTEXITCODE -ne0){throw 'Contact audit checkpoint failed'}
if($code -ne0){throw 'Contact audit failed; inspect before changing production'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/$done"

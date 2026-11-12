$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
if(Test-Path "$ev/PAUSE_UNITY"){throw 'An owned scheduling marker already exists'}
# The standard pipeline waits on this marker, even if its heavy geometry audit finishes.
# Both calls below still acquire/release the machine-wide Unity slot normally.
"Owned early shelter preview, PID $PID" | Set-Content "$ev/PAUSE_UNITY"
$ok=$false
try{
    & pwsh "$ev/unity-step.ps1" -Step import -Phase early-after1 -OwnedPauseBypass
    if($LASTEXITCODE -ne 0){throw 'Early candidate import failed'}
    & pwsh "$ev/unity-step.ps1" -Step side-render -Phase early-after1 -Tier Low -Lighting clear -CameraFile "$ev/cameras.json" -Cameras 'furniture-shelter-anders-1000-front,furniture-shelter-anders-1000-corner,furniture-shelter-factory-front,furniture-shelter-factory-corner'
    if($LASTEXITCODE -ne 0){throw 'Early shelter preview failed'}
    $ok=$true
}finally{
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): wczesny import i 4 diagnostyczne kadry wiat Low-clear; sukces=$ok. Każdy krok pobierał i zwalniał slot Unity; standardowy pipeline czekał na własny marker. Ten dodatkowy podgląd nie zastępuje 236 kadrów budżetowych ani oczekującej kontroli geometrii. NASTĘPNY KROK: obejrzeć podglądy i kontynuować pełną walidację."
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
    git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/early-shelter-preview.ps1" "$ev/unity-step.ps1" "$ev/preview_shelter_frame.py"
    git commit -m 'wip(furniture): checkpoint early candidate shelter preview'
    Remove-Item -LiteralPath "$ev/PAUSE_UNITY" -ErrorAction SilentlyContinue
}
if(!$ok){throw 'Early preview incomplete; inspect retained logs'}

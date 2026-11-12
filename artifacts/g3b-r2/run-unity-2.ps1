# Unity part of the final cycle: import (up to 3 tries: build_all.py can hit a transient MemoryError) -> SBS Low
# overcast -> SBS Low clear -> EditMode. Each step takes and releases its own Unity slot.
param([string]$Name = 'after', [string]$Tag = '2')
$d = $PSScriptRoot
foreach ($try in 1..3) {
    & pwsh -NoProfile -File "$d\run-import.ps1" -Log "import-$Tag.log" *> "$d\unity-$Tag.log"
    if (-not (Select-String -Path "$d\import-$Tag.log" -Pattern 'failed \(|Traceback' -Quiet)) { break }
    Start-Sleep 60
}
& pwsh -NoProfile -File "$d\run-sbs.ps1" -Name $Name -Lighting overcast *>> "$d\unity-$Tag.log"
& pwsh -NoProfile -File "$d\run-sbs.ps1" -Name $Name -Lighting clear *>> "$d\unity-$Tag.log"
& pwsh -NoProfile -File "$d\run-editmode.ps1" *>> "$d\unity-$Tag.log"

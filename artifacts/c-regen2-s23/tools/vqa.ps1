param([string]$Tag = 'after', [switch]$NoSlot)
# c-regen2-s23: visual-qa matrix for C + Dojlidy. One unity slot for the whole matrix (skip with -NoSlot when the caller holds it).
#   full control-camera sets : Low/High x clear/dusk (as c-regen-s22) + Low overcast (fences #109, pavements #125, Dojlidy #122)
#   C Low clear + Gate3 cams : thin shadows / bias (#110), LOD1 gantry (#124) - cameras exist in gate3_cameras.json (checked 15.11)
#   after only               : same Gate3 cameras with the pre-#110 switches (A/B of ADR 0240 on one import)
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/$Tag" 'vqa.status'
$g3 = 'Data/Regions/bialystok-industrial-c/gate3_cameras.json'
$g3cams = 'g3a_eye_s0412,g3b_eye_s1682,g3a_eye_s0212,g3b_eye_s1282,g3b_eye_s1482'
if (-not $NoSlot) { Slot-Acquire unity }
try {
    foreach ($r in $Regions) {
        foreach ($cell in @(@('Low', 'clear'), @('Low', 'dusk'), @('Low', 'overcast'), @('High', 'clear'), @('High', 'dusk'))) {
            $t, $l = $cell
            Step "vqa-$r-$t-$l" { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene $Scenes[$r] -Tier $t -Lighting $l -OutputDir "$Art/$Tag/$r/$t-$l" }
        }
    }
    Step 'vqa-C-g3-Low-clear' { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 $g3 -Cameras $g3cams -OutputDir "$Art/$Tag/bialystok-industrial-c/g3-Low-clear" }
    if ($Tag -eq 'after') {
        Step 'vqa-C-g3-Low-clear-pre0240' { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 $g3 -Cameras $g3cams -Rq 'rq_thinshadow=1,rq_shadowbias=1,rq_shadownormal=1' -OutputDir "$Art/$Tag/bialystok-industrial-c/g3-Low-clear-pre0240" }
    }
} finally { if (-not $NoSlot) { Slot-Release unity } }
Restore-UnitySideEffects
Finish 'vqa.done'

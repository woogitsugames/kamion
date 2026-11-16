param([string]$Tag = 'after', [switch]$NoSlot)
# c-regen3-s23: visual-qa matrix for C + Dojlidy, the cells the task names and that have a "before" in c-regen2-s23/after:
#   full control-camera sets : Low overcast + High clear (typology #123, vegetation #119, rondo Putry #93, fences)
#   C Low clear + Gate3 cams : the 5 cameras of c-regen2 (pair) + the Putry roundabout cameras (no pair)
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/$Tag" 'vqa.status'
$t0 = Get-Date
$g3 = 'Data/Regions/bialystok-industrial-c/gate3_cameras.json'
$g3cams = 'g3a_eye_s0412,g3b_eye_s1682,g3a_eye_s0212,g3b_eye_s1282,g3b_eye_s1482,g3b_rondo_put_above,g3b_rondo_put_approach,g3b_eye_s1632'
if (-not $NoSlot) { Slot-Acquire unity }
try {
    foreach ($r in $Regions) {
        foreach ($cell in @(@('Low', 'overcast'), @('High', 'clear'))) {
            $t, $l = $cell
            Step "vqa-$r-$t-$l" { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene $Scenes[$r] -Tier $t -Lighting $l -OutputDir "$Art/$Tag/$r/$t-$l" }
        }
    }
    Step 'vqa-C-g3-Low-clear' { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 $g3 -Cameras $g3cams -OutputDir "$Art/$Tag/bialystok-industrial-c/g3-Low-clear" }
} finally { if (-not $NoSlot) { Slot-Release unity } }
Restore-UnitySideEffects
# magenta guard: shader compile errors in the render logs (c-regen2: 28 x "undeclared identifier", EditMode did not see it)
$logs = @(Get-ChildItem "$Art/$Tag" -Filter 'vqa-*.log') + @(Get-ChildItem artifacts/logs -Filter '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $t0 })
$hits = @($logs | Select-String -Pattern 'Shader error|undeclared identifier|shader .* has errors|compile errors' )
"shader-error lines in vqa logs: $($hits.Count)" | Add-Content $St
$hits | Select-Object -First 10 | ForEach-Object { "  $($_.Filename):$($_.LineNumber): $($_.Line.Trim())" } | Add-Content $St
Finish 'vqa.done'

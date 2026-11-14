param([string]$Tag = 'before', [string[]]$Sets = @('Low:overcast', 'Low:clear', 'High:overcast'))
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\atlas-0184'
Set-Location $wt
$cams = 'r10_block_1,r10_block_2,r10_block_3,r10_block_4,r10_block_5,r10_office_2'
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner atlas-0184
try {
    foreach ($s in $Sets) {
        $t, $l = $s.Split(':')
        pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting $l -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -Cameras $cams -OutputDir "artifacts/atlas-0184/$Tag/$t-$l" *>&1 | Select-Object -Last 25
        "RENDER $Tag $t-$l exit $LASTEXITCODE"
    }
} finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner atlas-0184
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
}
"ALL DONE $Tag"

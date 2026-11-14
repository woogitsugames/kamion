param([string]$Tag = 'after', [string[]]$Sets = @('Low:overcast', 'Low:clear'))
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\atlas-0184'
Set-Location $wt
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner atlas-0184
try {
    foreach ($s in $Sets) {
        $t, $l = $s.Split(':')
        pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting $l -Gate3 artifacts/atlas-0184/lod1_cameras.json -Cameras 'a184_blk_a_p,a184_blk_a_n,a184_blk_b_p,a184_blk_b_n,a184_blk_c_p,a184_blk_c_n,a184_hi_d_p,a184_hi_d_n,a184_tower_p,a184_tower_n' -OutputDir "artifacts/atlas-0184/lod1-$Tag/$t-$l" *>&1 | Select-Object -Last 4
        "RENDER $Tag $t-$l exit $LASTEXITCODE"
    }
} finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner atlas-0184
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}

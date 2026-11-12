param([string]$Tag='probe-a')
$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
if ($Tag -notmatch '^probe-[a-z0-9-]+$') { throw 'Use a distinct safe probe tag' }
. artifacts/vegetation-r4/checkpoint.ps1
New-Item -ItemType Directory -Force "artifacts/vegetation-r4/$Tag" | Out-Null
foreach ($tier in @('Low','High')) { foreach ($lighting in @('overcast','clear')) {
    $scene=if($tier -eq 'High') {'WorldC_High'} else {'WorldC'}
    pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
    if ($LASTEXITCODE -ne 0) { throw 'Unity acquisition failed' }
    try {
        pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Width 2340 -Height 1080 -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -Cameras 'g3a-rondo-bie-approach,photo-biezenstwa-ground,r10_fence_2,fire-station-ref7197' -OutputDir "artifacts/vegetation-r4/$Tag/$tier-$lighting" *> "artifacts/vegetation-r4/$Tag/$tier-$lighting.log"
        if ($LASTEXITCODE -ne 0) { throw "Probe failed $Tag $tier $lighting" }
    } finally {
        pwsh scripts/unity-slot.ps1 -Release -Owner gpt-vegetation
        git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content artifacts/vegetation-r4/STATUS.md "Probe $Tag: $tier $lighting zapisany. Obejrzeć arkusze i koszt przed dalszą decyzją; to nie pełna macierz."
    Save-VegetationCheckpoint -Message "wip(vegetation): r4 $Tag $tier $lighting"
} }
Set-Content "artifacts/vegetation-r4/$Tag.done" 'Four probe groups completed; inspect results before acceptance.'

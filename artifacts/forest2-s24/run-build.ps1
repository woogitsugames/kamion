param([Parameter(Mandatory)][string[]]$Regions, [string]$Round = 'r1-after', [switch]$Tests, [string]$Ablation = '')
# forest2-s24: world generator of the given tiles, one after another under ONE heavy slot (the FIFO queue of the
# pool took 20-40 min per acquisition on 24.11); log + status per tile
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest2-s24'
Set-Location $wt
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner forest2-s24
try {
    if ($Ablation) {   # the same code with the class rule (KAMION_FOREST_CHM=0): clean budget baseline of one tile
        $out = Join-Path $wt "artifacts\forest2-s24\$Round\$Ablation-classrule"
        New-Item -ItemType Directory -Force $out | Out-Null
        $env:KAMION_FOREST_CHM = '0'
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $Ablation *> (Join-Path $out 'build_world.log')
        "build_world $Ablation (class rule) exit $LASTEXITCODE" >> (Join-Path $wt "artifacts\forest2-s24\build-$Round.status")
        Remove-Item Env:KAMION_FOREST_CHM
        Copy-Item "Data/Regions/$Ablation/generated/streetscape_qa.json" (Join-Path $out 'streetscape_qa.json')
        (Get-Item 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\heavy-slots\forest2-s24.slot').LastWriteTime = Get-Date
    }
    foreach ($r in ($Regions -split ",")) {
        $out = Join-Path $wt "artifacts\forest2-s24\$Round\$r"
        New-Item -ItemType Directory -Force $out | Out-Null
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r *> (Join-Path $out 'build_world.log')
        "build_world $r exit $LASTEXITCODE" >> (Join-Path $wt "artifacts\forest2-s24\build-$Round.status")
        (Get-Item 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\heavy-slots\forest2-s24.slot').LastWriteTime = Get-Date
    }
    "BUILD DONE $Round" >> (Join-Path $wt "artifacts\forest2-s24\build-$Round.status")
    if ($Tests) {   # the whole gis suite under the same slot (heavy job as well)
        uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> (Join-Path $wt "artifacts\forest2-s24\pytest-gis-$Round.log")
        "pytest gis exit $LASTEXITCODE" >> (Join-Path $wt "artifacts\forest2-s24\build-$Round.status")
    }
}
finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner forest2-s24 }

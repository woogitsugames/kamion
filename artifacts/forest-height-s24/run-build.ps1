param([Parameter(Mandatory)][string[]]$Regions, [string]$Round = 'r1-after')
# forest-height-s24: world generator of the given tiles, one after another under ONE heavy slot (the FIFO queue of the
# pool took 20-40 min per acquisition on 24.11); log + status per tile
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24'
Set-Location $wt
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner forest-height-s24
try {
    foreach ($r in ($Regions -split ",")) {
        $out = Join-Path $wt "artifacts\forest-height-s24\$Round\$r"
        New-Item -ItemType Directory -Force $out | Out-Null
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r *> (Join-Path $out 'build_world.log')
        "build_world $r exit $LASTEXITCODE" >> (Join-Path $wt "artifacts\forest-height-s24\build-$Round.status")
        (Get-Item 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\heavy-slots\forest-height-s24.slot').LastWriteTime = Get-Date
    }
}
finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner forest-height-s24 }
"BUILD DONE $Round" >> (Join-Path $wt "artifacts\forest-height-s24\build-$Round.status")

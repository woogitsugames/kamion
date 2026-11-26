param([string[]]$Tiles = @('knyszyn-w','dw671-tykocin-03'))
# road-patches-s24: rebuild tiles into the PRIVATE derived copy of this worktree (Data/raw/derived/<tile> is a copy).
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4b13d4540b9ae795'
$main = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location $wt
$st = "$wt\artifacts\road-patches-s24\rebuild.status"
foreach ($t in $Tiles) {
    if ((Get-Item "$wt\Data\raw\derived\$t").LinkType) { Add-Content $st "$t is a link - refusing"; continue }
    $log = "$wt\artifacts\road-patches-s24\logs\build-$t.log"
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner "road-patches-s24-$t" *>> $log
    $t0 = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t *>> $log; $e = $LASTEXITCODE
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner "road-patches-s24-$t" *>> $log
    Add-Content $st ("{0} build tile={1} exit={2} s={3:N0}" -f (Get-Date -Format s), $t, $e, ((Get-Date)-$t0).TotalSeconds)
}

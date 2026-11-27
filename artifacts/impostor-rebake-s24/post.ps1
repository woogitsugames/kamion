param([string[]]$Regions = @('knyszyn-w', 'dk65-07'))
# impostor-rebake-s24: put the rebaked atlases into the already imported regions (same file names = same GUIDs) and
# refit the trim polygons (ImpostorTrimBake.RunBatch). Equivalent of the texture + trim part of import-region.ps1.
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$main = 'C:\Users\matma\Documents\Claude\kamion'
$L = "$wt\artifacts\impostor-rebake-s24\logs"
Set-Location $wt
. "$wt\scripts\env.ps1"
foreach ($r in $Regions) {
    $dst = "$wt\game\Assets\_Generated\World\$r\Textures"
    Get-ChildItem "$wt\art-source\world\vegetation\impostor_tree_*.png" | ForEach-Object {
        if (Test-Path "$dst\$($_.Name)") { Copy-Item $_.FullName "$dst\$($_.Name)" -Force }
    }
}
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Acquire -Owner impostor-rebake-s24 *>> "$L\post.log"
try {
    foreach ($r in $Regions) {
        $c = Invoke-UnityBatch -LogFile "$L\trim-$r.log" -Arguments @('-executeMethod', 'Game.World.Import.ImpostorTrimBake.RunBatch', '-region', $r) -BuildTarget Win64
        Add-Content "$L\post.status" "trim $r exit=$c"
    }
} finally {
    pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Release -Owner impostor-rebake-s24 *>> "$L\post.log"
}
Add-Content "$L\post.status" "DONE"

param([string]$Rq = 'rq_card=0.2', [string]$Cameras = 'route_s0142,dk65_koscielna,b10_spawn_cab,route_s0426', [string]$Region = 'knyszyn-w')
# impostor-rebake-s24 diagnostic A/B: impostors forced close (cards end at 0.2 x the LOD1 distance), old atlases vs new,
# same code, same trim pass, same cameras. Restores the new atlases at the end.
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$main = 'C:\Users\matma\Documents\Claude\kamion'
$R = "$wt\artifacts\impostor-rebake-s24"; $L = "$R\logs"
Set-Location $wt
. "$wt\scripts\env.ps1"
$dst = "$wt\game\Assets\_Generated\World\$Region\Textures"
function Set-Atlases([string]$src) {
    Get-ChildItem "$src\impostor_tree_*.png" | ForEach-Object { if (Test-Path "$dst\$($_.Name)") { Copy-Item $_.FullName "$dst\$($_.Name)" -Force } }
}
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Acquire -Owner impostor-rebake-s24 *>> "$L\impab.log"
try {
    foreach ($v in @(@('imp-old', "$R\old-atlases"), @('imp-new', "$wt\art-source\world\vegetation"))) {
        Set-Atlases $v[1]
        $c = Invoke-UnityBatch -LogFile "$L\impab-trim-$($v[0]).log" -Arguments @('-executeMethod', 'Game.World.Import.ImpostorTrimBake.RunBatch', '-region', $Region) -BuildTarget Win64
        Add-Content "$L\impab.status" "$($v[0]) trim=$c"
        $a = @{Scene = "World_${Region}_High"; Tier = 'High'; Pc = $true; Width = 1920; Height = 1080; Lighting = 'clear'; BuildTarget = 'Win64'
               OutputDir = "$R\$($v[0])\$Region-High-clear"; Cameras = $Cameras; Gate3 = "$R\cams.json"; Rq = $Rq }
        pwsh -NoProfile -File scripts/visual-qa.ps1 @a *>> "$L\impab.log"
        Add-Content "$L\impab.status" "$($v[0]) vqa=$LASTEXITCODE"
    }
} finally {
    pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Release -Owner impostor-rebake-s24 *>> "$L\impab.log"
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
}
Add-Content "$L\impab.status" "DONE"

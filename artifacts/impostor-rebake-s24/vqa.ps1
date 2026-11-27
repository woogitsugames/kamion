param([Parameter(Mandatory)][string]$Label, [string[]]$Lightings = @('clear', 'overcast'), [string]$Rq = '', [string]$Diag = '',
      [string[]]$Scenes = @('knyszyn-w', 'dk65-07'), [switch]$Audit, [switch]$AuditReimport, [string]$Cameras = '')
# impostor-rebake-s24: High/PC control cameras of knyszyn-w (+ crown-lod cams) and dk65-07 into artifacts/impostor-rebake-s24/<Label>/
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$main = 'C:\Users\matma\Documents\Claude\kamion'
$out = "$wt\artifacts\impostor-rebake-s24\$Label"; New-Item -ItemType Directory -Force $out | Out-Null
$L = "$wt\artifacts\impostor-rebake-s24\logs"; New-Item -ItemType Directory -Force $L | Out-Null
$st = "$out\vqa.status"; $owner = 'impostor-rebake-s24'
Set-Location $wt
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
$log = "$L\vqa-$Label.log"
if ($Diag) { $env:KAMION_QA_DIAG = $Diag } else { Remove-Item Env:KAMION_QA_DIAG -ErrorAction SilentlyContinue }
pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Acquire -Owner $owner *>> $log
$e2 = @(); $t0 = Get-Date
try {
    if ($Audit) {
        . "$wt\scripts\env.ps1"
        $a = @('-executeMethod', 'Game.World.Import.ImpostorAtlasAudit.Run', '-auditOut', "$out\atlas-audit.tsv")
        if ($AuditReimport) { $a += @('-auditReimport', '1') }
        $c = Invoke-UnityBatch -LogFile "$L\audit-$Label.log" -Arguments $a -BuildTarget Win64; $e2 += "audit=$c"
    }
    foreach ($sc in $Scenes) {
        foreach ($lt in $Lightings) {
            $a = @{Scene = "World_${sc}_High"; Tier = 'High'; Pc = $true; Width = 1920; Height = 1080; Lighting = $lt; BuildTarget = 'Win64'
                   OutputDir = "$out\$sc-High-$lt" }
            if ($sc -eq 'knyszyn-w') {
                $a.Gate3 = "$wt\artifacts\impostor-rebake-s24\cams.json"
                $a.Cameras = if ($Cameras) { $Cameras } else { 'b10_spawn_cab,b10_spawn_cab_s40,route_s0142,route_s0426,route_s0710,route_s0994,tykocka_dw671_out,dk65_koscielna' }
            } elseif ($Cameras) { $a.Cameras = $Cameras }
            if ($Rq) { $a.Rq = $Rq }
            pwsh -NoProfile -File scripts/visual-qa.ps1 @a *>> $log; $e2 += "$sc-$lt=$LASTEXITCODE"
        }
    }
} finally {
    pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Release -Owner $owner *>> $log
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
}
Add-Content $st ("{0} exit={1} total_s={2:N0}" -f (Get-Date -Format s), ($e2 -join ' '), ((Get-Date) - $t0).TotalSeconds)
Add-Content $st "$(Get-Date -Format s) DONE"

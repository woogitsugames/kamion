$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
foreach($pair in @(
    @('art-source/truck/exterior/export','game/Assets/_Generated/Truck/Source/Exterior','SM_TruckExterior_LOD'),
    @('art-source/truck/trailer/export','game/Assets/_Generated/Trailer/Source','SM_Trailer_LOD')
)) {
    foreach($lod in 0..2) {
        $name="$($pair[2])$lod.fbx"
        if((Get-FileHash (Join-Path $pair[0] $name)).Hash -ne (Get-FileHash (Join-Path $pair[1] $name)).Hash){throw 'Kopia FBX nie odpowiada źródłu.'}
    }
}
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_wheel_mesh_audit_0115.py
if($LASTEXITCODE -ne 0){throw 'Nie przygotowano audytu.'}
. scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu Unity.'}
$start=Get-Date
try {
    $log="artifacts/truck-r3/mesh-audit-$(Get-Timestamp).log"
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckWheelMeshAudit0115.RunBatch','-wheelAuditOutput','artifacts/truck-r3/wheel-mesh-before.json')
    if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_WHEEL_MESH_RESULT: OK rows=6' -Quiet)){throw "Nieudany audyt siatek, exit $code."}
    $file=Get-Item artifacts/truck-r3/wheel-mesh-before.json
    if($file.LastWriteTime -lt $start){throw 'Nieświeży zrzut siatek.'}
} finally {
    pwsh $slot -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md 'Odczytano sześć siatek bazowych pod slotem Unity, bez scen i renderów. SHA sześciu źródłowych FBX zgodne z kopiami w projekcie. Następny krok: measure_wheel_mesh.py oraz świeże renderowane podglądy po przygotowaniu świata.'
git add -f artifacts/truck-r3/STATUS.md
git commit --only artifacts/truck-r3/STATUS.md -m 'wip(truck): odczyt szesciu bazowych siatek kol'

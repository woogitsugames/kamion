# ADR 0262: reimport (Low content) + start cameras of every region whose start moved. Worktree only; nothing is committed
# from _Generated. One region at a time under the unity slot. Status: renders/<id>.status, final renders.done.
param([string[]]$Regions = @('dk65-05', 'bialystok-knyszynska', 'bialystok-maczka', 'dk65-06', 'knyszyn-w', 'bialystok-kleeberga',
        'dk65-01', 'dk65-02', 'dk65-03', 'dk65-04', 'knyszyn', 'dk65-monki-01', 'dk65-07', 'dk65-08', 'dk65-09', 'dk65-10', 'dk65-11',
        'knyszyn-s', 'dw671-tykocin-01', 'bialystok-dojlidy'),
    [string]$WaitFor = '')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\spawn-fix-0262'
$d = Join-Path $wt 'artifacts\spawn-fix-0262'
$out = Join-Path $d 'renders'
New-Item -ItemType Directory -Force $out | Out-Null
Remove-Item (Join-Path $d 'renders.done') -ErrorAction SilentlyContinue
Set-Location $wt
if ($WaitFor) { while (-not (Test-Path $WaitFor)) { Start-Sleep -Seconds 15 } }
foreach ($r in $Regions) {
    $st = Join-Path $out "$r.status"
    if (-not (Test-Path (Join-Path $wt "Data/raw/derived/$r/world/chunk_0_0.glb"))) { "SKIP no generated chunks in the worktree" | Set-Content $st; continue }
    $scene = if ($r -eq 'bialystok-industrial-c') { 'WorldC' } else { "World_$r" }
    pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner spawn-fix-0262 *> (Join-Path $out "$r.slot.log")
    try {
        pwsh scripts/import-region.ps1 -Region $r -Tiers Low *> (Join-Path $out "$r.import.log")
        $ic = $LASTEXITCODE
        $qc = -1
        if ($ic -eq 0) {
            pwsh scripts/visual-qa.ps1 -Scene $scene -Tier Low -Lighting clear -Width 1280 -Height 720 -Cameras 'truck-at-gate,cab-gate' -OutputDir (Join-Path $out $r) *> (Join-Path $out "$r.qa.log")
            $qc = $LASTEXITCODE
        }
        "import=$ic qa=$qc" | Set-Content $st
    }
    finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner spawn-fix-0262 *>> (Join-Path $out "$r.slot.log") }
}
"done" | Set-Content (Join-Path $d 'renders.done')

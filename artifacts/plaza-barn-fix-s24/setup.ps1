# plaza-barn-fix-s24: worktree data layout - junctions to main, PRIVATE copy of derived/{tykocin,dk65-07,cache}, Win64 Library from a492
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Split-Path (Split-Path $PSScriptRoot)
$a492 = "$root\.claude\worktrees\agent-a492e5af856a32ed3"
foreach ($j in 'gugik', 'osm', 'refs', 'mapillary', 'fab') {
    $dst = "$wt\Data\raw\$j"
    if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; New-Item -ItemType Junction -Path $dst -Target "$root\Data\raw\$j" | Out-Null; "junction $j" }
}
function Copy-Tree($src, $dst, [string[]]$xd = @()) {
    $a = @($src, $dst, '/E', '/MT:16', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP')
    if ($xd) { $a += '/XD'; $a += $xd }
    robocopy @a | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy $src ($LASTEXITCODE)" }
    "copied $src"
}
Copy-Tree "$root\Data\raw\cc0" "$wt\Data\raw\cc0"
foreach ($d in 'tykocin', 'dk65-07', 'cache') { Copy-Tree "$root\Data\raw\derived\$d" "$wt\Data\raw\derived\$d" }
Copy-Tree "$root\art-source\world\cc0\_raw" "$wt\art-source\world\cc0\_raw"
Copy-Tree "$root\art-source\world\megascans" "$wt\art-source\world\megascans"
Copy-Tree "$root\art-source\truck\interior\export" "$wt\art-source\truck\interior\export"
Copy-Tree "$a492\game\Library" "$wt\game\Library"
Copy-Tree "$a492\game\Assets\_Generated" "$wt\game\Assets\_Generated" @("$a492\game\Assets\_Generated\World\dw671-tykocin-03", "$a492\game\Assets\_Generated\World\knyszyn-w")
Get-ChildItem "$wt\game\Assets\_Generated\World" -Filter *.meta | Where-Object { -not (Test-Path ($_.FullName -replace '\.meta$', '')) } | Remove-Item
& "$wt\scripts\repin-generated-guids.ps1" -Root $wt
"SETUP DONE"

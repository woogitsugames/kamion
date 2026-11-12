$ErrorActionPreference = 'Stop'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Split-Path (Split-Path $PSScriptRoot)
$dirs = @('Data\raw\derived','Data\raw\cc0','art-source\world\cc0\_raw','art-source\world\megascans','game\Assets\_Generated','game\Library')
foreach ($rel in $dirs) {
    $src = Join-Path $main $rel
    $dst = Join-Path $wt $rel
    if (Test-Path $src) {
        & robocopy $src $dst /E /XJ /R:1 /W:1 /NFL /NDL /NP "/LOG+:$PSScriptRoot\bootstrap-copy.log"
        if ($LASTEXITCODE -ge 8) { throw "Copy failed: $rel ($LASTEXITCODE)" }
    } else { "Absent optional/input directory: $rel" | Add-Content "$PSScriptRoot\bootstrap-copy.log" }
}
foreach ($name in @('gugik','osm','refs','mapillary','fab')) {
    $src = Join-Path $main "Data\raw\$name"
    $dst = Join-Path $wt "Data\raw\$name"
    if ((Test-Path $src) -and -not (Test-Path $dst)) {
        New-Item -ItemType Junction -Path $dst -Target $src | Out-Null
    }
}
& git -C $wt lfs checkout
if ($LASTEXITCODE -ne 0) { throw 'LFS checkout failed' }
'Bootstrap completed; raw junctions are reference-only and must never be modified.' | Add-Content "$PSScriptRoot\bootstrap-copy.log"

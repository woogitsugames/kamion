$ErrorActionPreference = 'Stop'
$src = 'C:\Users\matma\Documents\Claude\kamion'
$dst = Join-Path $src '.claude/worktrees/gpt-s16'
if ((Get-PSDrive C).Free -lt 150GB) { throw 'Insufficient disk headroom' }
foreach ($rel in @('Data/raw/derived','Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans','game/Assets/_Generated','art-source/world/materials','game/Library')) {
    if (Test-Path (Join-Path $src $rel)) {
        & robocopy (Join-Path $src $rel) (Join-Path $dst $rel) /E /XO /XJ /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
        if ($LASTEXITCODE -ge 8) { throw "Copy failed: $rel" }
    }
    if ((Get-PSDrive C).Free -lt 100GB) { throw 'Disk floor reached' }
}
foreach ($leaf in @('gugik','osm','refs','mapillary','fab')) {
    $from = Join-Path $src "Data/raw/$leaf"
    $to = Join-Path $dst "Data/raw/$leaf"
    if ((Test-Path $from) -and -not (Test-Path $to)) { New-Item -ItemType Junction -Path $to -Target $from | Out-Null }
}
git -C $dst lfs checkout
if ($LASTEXITCODE -ne 0) { throw 'LFS checkout failed' }

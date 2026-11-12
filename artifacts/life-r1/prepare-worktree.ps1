$ErrorActionPreference = 'Stop'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Join-Path $main '.claude\worktrees\gpt-life'
$copies = @('Data\raw\derived','Data\raw\cc0','art-source\world\cc0\_raw','art-source\world\megascans','game\Assets\_Generated')
foreach ($relative in $copies) {
    $source = Join-Path $main $relative
    $target = Join-Path $wt $relative
    if (!(Test-Path -LiteralPath $source)) { throw "Brak źródła: $relative" }
    & robocopy $source $target /E /XJ /R:1 /W:1 /NFL /NDL /NP /LOG+:"$wt\artifacts\life-r1\prepare-copy.log"
    if ($LASTEXITCODE -ge 8) { throw "Błąd kopii: $relative ($LASTEXITCODE)" }
}
foreach ($name in @('gugik','osm','refs','mapillary','fab')) {
    $source = Join-Path $main "Data\raw\$name"
    $target = Join-Path $wt "Data\raw\$name"
    if (!(Test-Path -LiteralPath $source)) { throw "Brak źródła junction: $name" }
    if (!(Test-Path -LiteralPath $target)) { New-Item -ItemType Junction -Path $target -Target $source | Out-Null }
}
Push-Location $wt
try { git lfs checkout; if ($LASTEXITCODE -ne 0) { throw 'git lfs checkout failed' } } finally { Pop-Location }

param([Parameter(Mandatory)][string]$Name, [switch]$Restore)
# Snapshot / restore the generator outputs the importer reads (world chunks + instances, generated/*.json, street props)
# so two world states (base, round) can be imported one after another while the generator keeps running.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
$snap = "$wt/artifacts/buildings-r15/_snap/$Name"
$pairs = @(
    @("$wt/Data/raw/derived/bialystok-industrial-c/world", "$snap/world"),
    @("$wt/Data/Regions/bialystok-industrial-c/generated", "$snap/generated"),
    @("$wt/art-source/world/props", "$snap/props"))
foreach ($p in $pairs) {
    $src, $dst = $p
    if ($Restore) { $src, $dst = $dst, $src }
    New-Item -ItemType Directory -Force $dst | Out-Null
    robocopy $src $dst /MIR /MT:16 /NFL /NDL /NJH /NJS /NP /R:1 /W:1 | Out-Null
}
"snap $Name $(if ($Restore) {'restored'} else {'saved'})"

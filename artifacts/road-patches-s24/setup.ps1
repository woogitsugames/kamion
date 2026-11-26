# road-patches-s24: junctions Data/raw/* -> main; Data/raw/derived = private dir: per-entry junctions to main,
# except the two tiles this branch rebuilds (private copies; main derived is being imported by build #10).
$ErrorActionPreference = 'Stop'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4b13d4540b9ae795'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$own = @('knyszyn-w', 'dw671-tykocin-03')
New-Item -ItemType Directory -Force "$wt\Data\raw\derived" | Out-Null
foreach ($j in 'gugik','osm','refs','mapillary','fab','cc0') {
  $src = "$main\Data\raw\$j"; $dst = "$wt\Data\raw\$j"
  if ((Test-Path $src) -and -not (Test-Path $dst)) { New-Item -ItemType Junction -Path $dst -Target $src | Out-Null; "junction $j" }
}
Get-ChildItem "$main\Data\raw\derived" | ForEach-Object {
  $dst = "$wt\Data\raw\derived\$($_.Name)"
  if (Test-Path $dst) { return }
  if ($_.PSIsContainer) {
    if ($own -contains $_.Name) { robocopy $_.FullName $dst /E /MT:16 /NFL /NDL /NJH /NJS | Out-Null; "copy $($_.Name) exit $LASTEXITCODE" }
    else { New-Item -ItemType Junction -Path $dst -Target $_.FullName | Out-Null }
  } else { Copy-Item $_.FullName $dst }
}
"done"

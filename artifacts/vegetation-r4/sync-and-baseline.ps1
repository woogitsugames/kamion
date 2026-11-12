$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r4/checkpoint.ps1
$sourceRoot = 'C:\Users\matma\Documents\Claude\kamion'
$targetRoot = (Get-Location).Path
foreach ($relative in @('Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans')) {
    $from = Join-Path $sourceRoot $relative
    $to = Join-Path $targetRoot $relative
    $tag = $relative.Replace('/','-')
    $log = "artifacts/vegetation-r4/sync-$tag.log"
    robocopy $from $to /E /XJ /R:1 /W:1 /NFL /NDL /NP "/LOG:$log"
    $copyExit = $LASTEXITCODE
    Add-Content artifacts/vegetation-r4/STATUS.md "Synchronizacja brakujących zasobów $relative, robocopy kod $copyExit (0–7 nie oznacza porażki). Nie kopiowano aktywnie generowanego świata main."
    Save-VegetationCheckpoint -Message "wip(vegetation): r4 synchronizacja $tag" -Paths @('artifacts/vegetation-r4/STATUS.md',$log)
    if ($copyExit -ge 8) { throw "Asset sync failed: $relative" }
}
pwsh artifacts/vegetation-r4/baseline.ps1 *> artifacts/vegetation-r4/baseline.log
exit $LASTEXITCODE

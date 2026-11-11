param([Parameter(Mandatory)][ValidateRange(1,10000)][int]$Round)
$ErrorActionPreference = 'Stop'
$main = 'C:/Users/matma/Documents/Claude/kamion'
$repo = [IO.Path]::GetFullPath((Resolve-Path "$PSScriptRoot/../..").Path)
Set-Location $repo
$label = "asphalt-r$Round"
$branch = (& git branch --show-current).Trim()
if ($branch -ne "gpt-$label") { throw "Wrong branch: $branch for $label" }
$source = [IO.Path]::GetFullPath((Join-Path $repo "artifacts/$label"))
$destination = [IO.Path]::GetFullPath((Join-Path $main "artifacts/$label"))
$expectedRepo = [IO.Path]::GetFullPath((Join-Path $main '.claude/worktrees/gpt-asphalt'))
if ($repo -ne $expectedRepo -or $source -eq $destination) { throw 'Unexpected worktree/copy paths' }
if (-not $destination.StartsWith([IO.Path]::GetFullPath((Join-Path $main 'artifacts')) + [IO.Path]::DirectorySeparatorChar,
    [StringComparison]::OrdinalIgnoreCase)) { throw 'Destination escaped main artifacts' }
$report = Join-Path $source 'REPORT.md'
if (-not (Test-Path $report) -or (Get-Content $report -Raw -Encoding UTF8) -match 'raport roboczy') {
    throw 'Finish the report before publication.'
}
if (-not (Test-Path (Join-Path $source 'end-round-checks.json'))) { throw 'Final checks are not recorded.' }
foreach ($pool in @('heavy','unity')) {
    $owner = if ($pool -eq 'heavy') { $branch } else { 'gpt-asphalt' }
    if (Test-Path (Join-Path $main "artifacts/locks/$pool-slots/$owner.slot")) {
        throw "Own $pool slot is active; finish that stage before copying."
    }
}
$log = Join-Path $source 'copy-to-main.log'
# Publish REPORT/STATUS last, so a leader cannot mistake a partially copied directory for a delivered round.
& robocopy $source $destination /E /XJ /MT:2 /R:2 /W:2 /NFL /NDL /NP /XF REPORT.md STATUS.md DELIVERED.json copy-to-main.log "/LOG:$log"
$copyExit = $LASTEXITCODE
if ($copyExit -ge 8) { throw "robocopy failed: $copyExit; $log" }
$excluded = @('REPORT.md','STATUS.md','DELIVERED.json','copy-to-main.log')
$files = @(Get-ChildItem -LiteralPath $source -Recurse -File | Where-Object Name -NotIn $excluded)
$missing = @()
foreach ($file in $files) {
    $relative = $file.FullName.Substring($source.Length).TrimStart('\','/')
    $target = Join-Path $destination $relative
    if (-not (Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -ne $file.Length) {
        $missing += $relative
    }
}
if ($missing.Count -gt 0) { throw "Copied file missing or wrong length: $($missing -join ', ')" }
$head = (& git rev-parse HEAD).Trim()
$delivery = [ordered]@{
    branch=$branch; head_before_delivery_commit=$head; copied_at=(Get-Date -Format o)
    source=$source; destination=$destination; robocopy_exit=$copyExit
    verified_file_count=$files.Count; verified_total_bytes=($files | Measure-Object Length -Sum).Sum
    all_source_files_present_with_matching_lengths=$true
    note='Robocopy /E without deletion; all file lengths checked. REPORT, STATUS and delivery metadata published last. No git command runs in main.'
}
$delivery | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $source 'DELIVERED.json') -Encoding UTF8
Add-Content (Join-Path $source 'STATUS.md') "$(Get-Date -Format o): Runda r$Round przekazana robocopy do main, exit=$copyExit; sprawdzono $($files.Count) plików i długości. Bez usuwania cudzych plików, bez commitu w main. Następny krok: gałąź gpt-asphalt-r$($Round+1), merge main i kolejna runda."
& git add -f -- (Join-Path $source 'STATUS.md') (Join-Path $source 'DELIVERED.json') $log
if ($LASTEXITCODE -ne 0) { throw 'Cannot stage delivery checkpoint' }
& git commit -q -m "wip(asphalt): deliver $label artifacts to main"
if ($LASTEXITCODE -ne 0) { throw 'Cannot commit delivery checkpoint' }
foreach ($name in $excluded) {
    $file = Join-Path $source $name
    if (-not (Test-Path -LiteralPath $file)) { continue }
    Copy-Item -LiteralPath $file -Destination (Join-Path $destination $name) -Force
    if ((Get-FileHash -LiteralPath $file).Hash -ne (Get-FileHash -LiteralPath (Join-Path $destination $name)).Hash) {
        throw "Published metadata hash differs: $name"
    }
}
Write-Output "Delivered $label: $($files.Count) files checked, robocopy exit $copyExit."

. "$PSScriptRoot/../common.ps1"
# import-region passes absolute paths after --project and optionally the literal python.
if ($args.Count -lt 4 -or $args[0] -ne 'run' -or $args[1] -ne '--project' -or
    [IO.Path]::GetFullPath($args[2]) -ne (Join-Path $waveRoot 'tools\worldgen')) {
    throw 'Shim obsługuje wyłącznie uv run --project <to worktree>/tools/worldgen [python] skrypt ...'
}
$start = 3
if ($args[$start] -eq 'python') { $start++ }
if ($args.Count -le $start) { throw 'Brak skryptu Python.' }
$env:PYTHONPATH = $waveRoot
$pythonArgs = $args[$start..($args.Count - 1)]
& $python @pythonArgs
exit $LASTEXITCODE

$py = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a492e5af856a32ed3\tools\worldgen\.venv\Scripts\python.exe'
$a = [System.Collections.Generic.List[string]]$args
if ($a.Count -and $a[0] -eq 'run') { $a.RemoveAt(0) } else { Write-Error "uv shim: only 'uv run' is supported: $args"; exit 97 }
while ($a.Count -and $a[0].StartsWith('--')) { if ($a[0] -eq '--project') { $a.RemoveAt(0) }; $a.RemoveAt(0) }
if ($a.Count -and $a[0] -eq 'python') { $a.RemoveAt(0) }
$env:PYTHONPATH = (Resolve-Path "$PSScriptRoot\..\..\..").Path
& $py @a
exit $LASTEXITCODE

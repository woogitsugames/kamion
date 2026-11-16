param([string]$Log, [string[]]$Steps)
# Detached step runner: each step is a command line; appends output and "exit[<n>]=<code>" to the log.
Set-Location (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$env:PYTHONIOENCODING = 'utf-8'
$i = 0
foreach ($s in $Steps) {
    $i++
    "=== step ${i}: $s  ($(Get-Date -Format s))" >> $Log
    Invoke-Expression "$s *>> `"$Log`""
    "exit[$i]=$LASTEXITCODE  ($(Get-Date -Format s))" >> $Log
}
"DONE" >> $Log

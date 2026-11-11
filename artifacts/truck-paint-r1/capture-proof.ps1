function Confirm-TruckCapture([string]$LogFile,[string]$Round,[int]$Code,[datetime]$Started) {
 $pattern='TRUCK_ROUND_RESULT: OK '+[regex]::Escape($Round)+' count=(\d+)'
 $result=Select-String -Path $LogFile -Pattern $pattern | Select-Object -Last 1
 if(-not $result){throw "No completed truck round: $Round exit=$Code"}
 $count=[int]$result.Matches[0].Groups[1].Value
 $folder=Join-Path $PSScriptRoot $Round
 $files=@(Get-ChildItem $folder -Recurse -Filter *.png | Where-Object {$_.Name -notmatch '_(envcube|mask)\.png$'})
 $fresh=@($files | Where-Object {$_.LastWriteTimeUtc -ge $Started.ToUniversalTime().AddSeconds(-1)})
 if($files.Count -ne $count -or $fresh.Count -ne $count){throw "Missing/stale truck PNG: $($fresh.Count)/$count"}
 if($Code -eq 0){Write-Output "TRUCK_CAPTURE_PROOF: OK $Round $count exit=0";return}
 $after=$result.LineNumber
 $mono=Select-String -Path $LogFile -SimpleMatch -Pattern 'Cleanup mono' | Where-Object {$_.LineNumber -gt $after} | Select-Object -First 1
 $abort=Select-String -Path $LogFile -SimpleMatch -Pattern 'abort_threads: Failed aborting' | Where-Object {$_.LineNumber -gt $after} | Select-Object -First 1
 $crash=Select-String -Path $LogFile -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
 if($mono -and $abort -and -not $crash){Write-Warning "Unity exit=$Code after all$count fresh frames, mono cleanup/abort_threads, no crashstack; accepted same ADR0083 rule as scripts/visual-qa.ps1";return}
 throw "Unaccepted truck capture failure $Round code=$Code"
}

param([ValidatePattern('^[a-z0-9-]+$')][string]$Label=(Get-Date -Format 'yyyyMMdd-HHmmss'))
$ErrorActionPreference='Stop'
$repo='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
$mainRoot='C:\Users\matma\Documents\Claude\kamion'
Set-Location $repo
$heavyRoot=Join-Path $mainRoot 'artifacts/locks/heavy-slots'
$tickets=@(Get-ChildItem (Join-Path $heavyRoot 'queue') -Filter *.wait | ForEach-Object {
    $ticketTicks=0L
    if ([long]::TryParse((Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue),[ref]$ticketTicks)) {
        [pscustomobject]@{owner=$_.BaseName; first_wait=([datetime]::new($ticketTicks)).ToString('o'); ticks=$ticketTicks; heartbeat=$_.LastWriteTime.ToString('o')}
    }
} | Sort-Object ticks)
$acquirers=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" | Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -notlike '*Get-CimInstance*' -and
    $_.CommandLine -like '*kamion*' -and $_.CommandLine -match 'unity-slot\.ps1.*-Acquire.*-Pool heavy'
} | ForEach-Object {
    [pscustomobject]@{pid=$_.ProcessId; parent_pid=$_.ParentProcessId; created=$_.CreationDate.ToString('o'); owner=([regex]::Match($_.CommandLine,'-Owner\s+"?([A-Za-z0-9._-]+)')).Groups[1].Value}
} | Sort-Object created)
$diagnostic=[ordered]@{
    observed_at=(Get-Date -Format o)
    main_policy_commit=(git log -1 --format=%H main -- scripts/unity-slot.ps1).Trim()
    main_policy_committed_at=(git log -1 --format=%cI main -- scripts/unity-slot.ps1).Trim()
    heavy_slots=@(Get-ChildItem $heavyRoot -Filter *.slot).Count
    phone_run=(Test-Path (Join-Path $mainRoot 'artifacts/locks/PHONE_RUN'))
    queue=$tickets
    heavy_acquirers=$acquirers
    d_test_log_exists=(Test-Path artifacts/vegetation-r4/pytest-green-d.log)
    d_world_log_exists=(Test-Path artifacts/vegetation-r4/world-candidate-d.log)
    note='Read-only host metadata. No foreign process, slot, ticket, PHONE_RUN, shared script or device was changed.'
}
$path="artifacts/vegetation-r4/slot-wait-$Label.json"
$diagnostic | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $path
$diagnostic | ConvertTo-Json -Depth 6

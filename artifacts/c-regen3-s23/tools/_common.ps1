# c-regen3-s23, stage 2: shared helpers. Dot-source from the step scripts. Nothing here starts Unity or a build by itself.
$ErrorActionPreference = 'Continue'
$Name = 'c-regen3-s23'
$Main = 'C:\Users\matma\Documents\Claude\kamion'
$Wt = "$Main\.claude\worktrees\$Name"
$Art = "artifacts/$Name"
$Regions = @('bialystok-industrial-c', 'bialystok-dojlidy')
$Scenes = @{ 'bialystok-industrial-c' = 'WorldC'; 'bialystok-dojlidy' = 'World_bialystok-dojlidy' }
$NoStart = -1073741502   # 0xC0000142: the process did not start (seen when a session closes); retry, do not trust .done
Set-Location $Wt

function Init-Status([string]$dir, [string]$file) {
    New-Item -ItemType Directory -Force $dir | Out-Null
    $script:O = $dir; $script:St = "$dir/$file"
    "start $(Get-Date -Format s) head=$(git rev-parse --short=9 HEAD)" | Set-Content $script:St
}

# One step = one log + one status line "name exit=<code> try=<n> <time>". Retries only the "did not start" code.
function Step([string]$name, [scriptblock]$block, [int]$Tries = 3) {
    for ($i = 1; $i -le $Tries; $i++) {
        $log = if ($i -eq 1) { "$script:O/$name.log" } else { "$script:O/$name.try$i.log" }
        $global:LASTEXITCODE = 0
        & $block *> $log
        $script:Last = $LASTEXITCODE
        "$name exit=$script:Last try=$i $(Get-Date -Format s)" | Add-Content $script:St
        # import-region.ps1 / visual-qa.ps1 exit Max(1, code) and test.ps1 exits the failure count: the "did not start"
        # code is then only in the log text
        $noStart = ($script:Last -eq $NoStart) -or (($script:Last -ne 0) -and (Select-String -Path $log -Pattern '-1073741502|C0000142' -Quiet))
        if (-not $noStart) { break }
        "$name did-not-start (0xC0000142) - retry" | Add-Content $script:St
        Start-Sleep 30
    }
}

# Every step that builds or imports must run on the integration branch (10-before.ps1 leaves it for a while).
function Assert-Branch {
    $b = (git branch --show-current | Out-String).Trim()
    if ($b -ne $Name) { "ABORT: on branch '$b' (detached = empty), expected $Name - finish / repair 10-before.ps1 first" | Add-Content $script:St; exit 3 }
}
# 0 when the status file has "<step> exit=0" as the LAST line of that step.
function Step-Ok([string]$statusFile, [string]$step) {
    $l = Select-String -Path $statusFile -Pattern "^$([regex]::Escape($step)) exit=(-?\d+)" -ErrorAction SilentlyContinue | Select-Object -Last 1
    return [bool]($l -and $l.Matches[0].Groups[1].Value -eq '0')
}
function Wait-Phone { while (Test-Path "$Main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 } }
function Slot-Acquire([string]$pool, [string]$owner = $Name) {
    if ($pool -eq 'unity') { Wait-Phone }
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool $pool -Owner $owner | Out-Null
    "slot $pool $(Get-Date -Format s)" | Add-Content $script:St
}
function Slot-Release([string]$pool, [string]$owner = $Name) {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool $pool -Owner $owner | Out-Null
}
# AGENT-RULES p. 2: Unity side effects (never committed from this worktree).
function Restore-UnitySideEffects {
    git checkout -q -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
    foreach ($p in 'game/Assets/Resources.meta') { if ((Test-Path $p) -and -not (git ls-files $p)) { Remove-Item $p -Force } }
    if ((Test-Path 'game/Assets/Resources') -and -not (Get-ChildItem 'game/Assets/Resources' -Force) -and -not (git ls-files 'game/Assets/Resources')) { Remove-Item 'game/Assets/Resources' -Force }
}
function Finish([string]$doneFile) { "DONE $(Get-Date -Format s)" | Add-Content $script:St; 'done' | Set-Content "$script:O/$doneFile" }

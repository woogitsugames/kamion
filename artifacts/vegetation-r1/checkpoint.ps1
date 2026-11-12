param([string]$Message, [string[]]$Paths = @('artifacts/vegetation-r1/STATUS.md'))

function Save-VegetationCheckpoint {
    param([string]$Message, [string[]]$Paths = @('artifacts/vegetation-r1/STATUS.md'))
    # Serialise only this session's foreground/background checkpoints. No foreign
    # locks are removed, and the shared repository configuration is unchanged.
    $checkpointMutex = [Threading.Mutex]::new($false, 'KamionGPTVegetationCheckpoint')
    $held = $false
    try {
        try { $held = $checkpointMutex.WaitOne() }
        catch [Threading.AbandonedMutexException] { $held = $true }
        $staged = $false
        for ($attempt = 0; $attempt -lt 12; $attempt++) {
            git -c core.fsmonitor=false add -f -- $Paths
            if ($LASTEXITCODE -eq 0) { $staged = $true; break }
            Start-Sleep -Seconds 5
        }
        if (-not $staged) { throw 'Checkpoint staging failed; preserve files and inspect the active git process.' }
        git -c core.fsmonitor=false diff --cached --quiet
        if ($LASTEXITCODE -eq 0) { return }
        git -c core.fsmonitor=false commit -m $Message
        if ($LASTEXITCODE -ne 0) { throw "Checkpoint commit failed: $Message" }
    } finally {
        if ($held) { $checkpointMutex.ReleaseMutex() }
        $checkpointMutex.Dispose()
    }
}

if ($Message) { Save-VegetationCheckpoint -Message $Message -Paths $Paths }

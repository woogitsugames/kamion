$ErrorActionPreference = 'Stop'
$waveDir = $PSScriptRoot
$waveRoot = (Resolve-Path "$waveDir/../..").Path
$commonGit = git -C $waveRoot rev-parse --path-format=absolute --git-common-dir
if ($LASTEXITCODE) { throw 'Nie można ustalić katalogu Git.' }
$mainRoot = Split-Path $commonGit
$waveName = 'regen-wave-14-s24'
$evidenceDir = Join-Path $mainRoot "artifacts/$waveName"
$stateDir = Join-Path $waveDir 'run'
$python = 'C:\Users\matma\Documents\Claude\kamion\scripts\cli-jobs\wgpy.cmd'  # s25: .venv python.exe zablokowany przez SAC (27.11 22:10)
$queue = @(Import-Csv "$waveDir/queue.csv")
if ($queue.Count -ne 54 -or @($queue.tile | Sort-Object -Unique).Count -ne 54) {
    throw 'Kolejka musi zawierać 54 unikalne regiony.'
}
foreach ($entry in $queue) {
    if ($entry.chain -cnotmatch '^[A-E]$' -or $entry.tile -cnotmatch '^[a-z0-9-]+$' -or
        -not (Test-Path -LiteralPath "$waveRoot/Data/Regions/$($entry.tile)/region.yaml")) {
        throw "Nieprawidłowy wpis kolejki: $entry"
    }
}
$qaTiles = @('tykocin', 'knyszyn-w', 'dk65-07', 'dw671-tykocin-03', 'bialystok-industrial-c')

function Initialize-WaveRuntime {
    if ($waveRoot -eq $mainRoot -or (git -C $waveRoot branch --show-current) -in @('', 'main')) {
        throw 'Uruchom w osobnym worktree na gałęzi fali.'
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Brak interpretera: $python" }
    $derived = Get-Item -LiteralPath "$waveRoot/Data/raw/derived"
    $expected = Join-Path $mainRoot 'Data/raw/derived'
    if ($derived.LinkType -ne 'Junction' -or
        (Resolve-Path -LiteralPath $derived.Target).Path -ne (Resolve-Path -LiteralPath $expected).Path) {
        throw "Data/raw/derived musi być junctionem do $expected."
    }
    Set-Location -LiteralPath $waveRoot
    $env:PYTHONPATH = $waveRoot
    $env:PYTHONIOENCODING = 'utf-8'
    $env:KAMION_ARTIFACTS_DIR = $evidenceDir
    New-Item -ItemType Directory -Force "$stateDir/tiles", "$evidenceDir/logs" | Out-Null
}

function Invoke-WaveStep([string]$Name, [string]$Program, [string[]]$Arguments, [string]$Log) {
    Write-Host "[$(Get-Date -Format s)] $Name ($Log)"
    Add-Content -LiteralPath $Log -Value "[$(Get-Date -Format o)] BEGIN $Name"
    $timer = [Diagnostics.Stopwatch]::StartNew()
    & $Program @Arguments *>> $Log
    $code = $LASTEXITCODE
    Add-Content -LiteralPath $Log -Value "[$(Get-Date -Format o)] END $Name exit=$code seconds=$([math]::Round($timer.Elapsed.TotalSeconds))"
    if ($code -ne 0) { throw "$Name exit=$code. Log: $Log" }
}

function Enter-WaveLock([string]$Name) {
    $path = Join-Path $stateDir "$Name.lock"
    while ($true) {
        try { return [IO.File]::Open($path, 'OpenOrCreate', 'ReadWrite', 'None') }
        catch [IO.IOException] {
            # ERROR_SHARING_VIOLATION / ERROR_LOCK_VIOLATION
            if (($_.Exception.HResult -band 0xFFFF) -notin 32, 33) { throw }
            Start-Sleep -Seconds 5
        }
    }
}

function Invoke-WithHeavySlot([string]$Owner, [string]$Log, [scriptblock]$Work) {
    $slot = 'scripts/unity-slot.ps1'
    Invoke-WaveStep 'slot heavy acquire' 'pwsh' @('-NoProfile', '-File', $slot, '-Acquire', '-Pool', 'heavy', '-Owner', $Owner) $Log
    try { & $Work }
    finally {
        Invoke-WaveStep 'slot heavy release' 'pwsh' @('-NoProfile', '-File', $slot, '-Release', '-Pool', 'heavy', '-Owner', $Owner) $Log
    }
}

function Invoke-WaveUnity([string]$Owner, [string]$Log, [scriptblock]$Work) {
    $lock = Enter-WaveLock 'unity'
    try {
        $restore = @('game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat',
            'game/ProjectSettings/QualitySettings.asset', 'game/ProjectSettings/ProjectSettings.asset')
        if (git status --porcelain -- game/ProjectSettings game/Packages ':(glob)**/*.asmdef' @restore) {
            throw 'Zabezpiecz istniejące zmiany Unity przed importem lub renderem.'
        }
        # s25: osobna nazwa — w zasięgu Invoke-WithHeavySlot `$Work` to ten blok (dynamiczny zasięg) → nieskończona rekurencja.
        $unityWork = $Work
        Invoke-WithHeavySlot $Owner $Log {
            # Slot heavy nie obsługuje blokady telefonu.
            while (Test-Path -LiteralPath "$mainRoot/artifacts/locks/PHONE_RUN") { Start-Sleep -Seconds 60 }
            try { & $unityWork }
            finally {
                foreach ($path in $restore) {
                    git diff --quiet -- $path
                    if ($LASTEXITCODE -eq 1) {
                        git restore --worktree -- $path
                        if ($LASTEXITCODE) { throw "Nie udało się przywrócić $path." }
                    }
                }
                if (git status --porcelain -- game/ProjectSettings game/Packages ':(glob)**/*.asmdef') {
                    throw 'Unity zostawiło zmianę w chronionej ścieżce. Sprawdź git status.'
                }
            }
        }
    }
    finally { $lock.Dispose() }
}

function Invoke-WaveImport([string]$Tile, [string]$Log) {
    foreach ($inputFile in @("Data/raw/derived/$Tile/world/chunk_0_0.glb", "Data/Regions/$Tile/route_start.json")) {
        if (-not (Test-Path -LiteralPath $inputFile -PathType Leaf)) {
            throw "Brak $inputFile. Import mógłby uruchomić generator; wymagany gotowy kafel i trasa."
        }
    }
    $oldPath = $env:PATH
    $env:PATH = "$waveDir/shim;$oldPath"
    try {
        Invoke-WaveStep 'import Win64 High' 'pwsh' @('-NoProfile', '-File', 'scripts/import-region.ps1',
            '-Region', $Tile, '-BuildTarget', 'Win64', '-Tiers', 'High', '-MaterialTier', 'High') $Log
    }
    finally { $env:PATH = $oldPath }
}

function Invoke-WaveTile([string]$Tile, [switch]$Redo) {
    $lock = Enter-WaveLock "tiles/$Tile"
    $worldReady = "$stateDir/tiles/$Tile.world"
    $done = "$stateDir/tiles/$Tile.done"
    $log = "$evidenceDir/logs/tile-$Tile.log"
    $owner = "$waveName-$Tile"
    try {
        if ($Redo) {
            foreach ($marker in @($done, $worldReady, "$stateDir/final.checked")) {
                if (Test-Path -LiteralPath $marker) { Remove-Item -LiteralPath $marker }
            }
        }
        if (Test-Path -LiteralPath $done) { Write-Host "$Tile gotowy"; return }
        if (-not (Test-Path -LiteralPath $worldReady)) {
            Invoke-WithHeavySlot $owner $log {
                # Bojary exceeded the default 3 h slot TTL in wave 13.
                $slotFile = "$mainRoot/artifacts/locks/heavy-slots/$owner.slot"
                $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $buildLog = "$evidenceDir/logs/build-$Tile-$stamp"
                Write-Host "[$(Get-Date -Format s)] build_world ($buildLog.out.log)"
                Add-Content -LiteralPath $log -Value "[$(Get-Date -Format o)] BEGIN build_world ($buildLog.out.log / .err.log)"
                $timer = [Diagnostics.Stopwatch]::StartNew()
                $child = Start-Process -FilePath $python -ArgumentList @('-u', 'tools/worldgen/roads/build_world.py', '--region', $Tile, '--context') `
                    -NoNewWindow -PassThru -RedirectStandardOutput "$buildLog.out.log" -RedirectStandardError "$buildLog.err.log"
                $null = $child.Handle
                try {
                    while (-not $child.WaitForExit(60000)) {
                        (Get-Item -LiteralPath $slotFile).LastWriteTime = Get-Date
                    }
                    $code = $child.ExitCode
                }
                finally {
                    # Never release the heavy slot while the generator is still running.
                    $child.WaitForExit()
                    $child.Dispose()
                }
                Add-Content -LiteralPath $log -Value "[$(Get-Date -Format o)] END build_world exit=$code seconds=$([math]::Round($timer.Elapsed.TotalSeconds))"
                if ($code -ne 0) { throw "build_world exit=$code. Log: $buildLog.err.log" }
                (Get-Item -LiteralPath $slotFile).LastWriteTime = Get-Date
                Invoke-WaveStep 'far_field' $python @('tools/worldgen/streetscape/far_field.py', '--region', $Tile) $log
                Invoke-WaveStep 'export-route' $python @('scripts/export-route.py', '--region', $Tile) $log
                Invoke-WaveStep 'fidelity' $python @('tools/worldgen/fidelity/run.py', '--region', $Tile, '--art', "$evidenceDir/fidelity/$Tile") $log
            }
            Set-Content -LiteralPath $worldReady -Value (Get-Date -Format o)
        }
        Invoke-WaveUnity $owner $log { Invoke-WaveImport $Tile $log }
        Set-Content -LiteralPath $done -Value (Get-Date -Format o)
    }
    finally { $lock.Dispose() }
}

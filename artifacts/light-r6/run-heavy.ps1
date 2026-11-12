param(
    [Parameter(Mandatory)][ValidateSet('BuildWorld','BuildAll','Fidelity','TestFile','GisFinal','Analyze')][string]$Task,
    [string]$TestFile,
    [string]$Script,
    [string[]]$ScriptArguments = @(),
    [switch]$RoundEnd
)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$owner = (& git branch --show-current).Trim()
if ($owner -notmatch '^gpt-light-r\d+$') { throw "Niewłaściwa gałąź light: $owner" }
if ($Task -eq 'GisFinal' -and -not $RoundEnd) { throw 'Pełny GIS wolno uruchomić tylko na końcu rundy: -RoundEnd' }
if ($Task -eq 'TestFile' -and ($TestFile -notmatch '^tests[/\\](gis|physics|gate3)[/\\][^/\\]+\.py$' -or -not (Test-Path -LiteralPath $TestFile -PathType Leaf))) {
    throw 'Podaj jeden istniejący plik testów przez -TestFile; pełne katalogi są zabronione w trakcie rundy'
}
if ($Task -eq 'Analyze') {
    $Script = [IO.Path]::GetFullPath($Script, $repo)
    if (-not $Script.StartsWith($PSScriptRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetExtension($Script) -ne '.py' -or -not (Test-Path -LiteralPath $Script -PathType Leaf)) {
        throw 'Analiza musi wskazywać istniejący skrypt Python w katalogu tej rundy'
    }
}
$uvArguments = @('run','--project','tools/worldgen')
switch ($Task) {
    'BuildWorld' { $uvArguments += @('tools/worldgen/roads/build_world.py','--region','bialystok-industrial-c') }
    'BuildAll' { $uvArguments += @('python','art-source/world/materials/_src/build_all.py') }
    'Fidelity' { $uvArguments += @('tools/worldgen/fidelity/run.py','--region','bialystok-industrial-c','--art',"$PSScriptRoot/fidelity") }
    'TestFile' { $uvArguments += @('python','-m','pytest',$TestFile,'-q') }
    'GisFinal' { $uvArguments += @('python','-m','pytest','tests/gis','-q') }
    'Analyze' { $uvArguments += @('python',$Script); $uvArguments += $ScriptArguments }
}
$log = Join-Path $PSScriptRoot ("heavy-{0}-{1}.log" -f $Task,(Get-Date -Format 'yyyyMMdd-HHmmss'))
$acquired = $false
for ($slotAttempt=1; $slotAttempt -le 5; $slotAttempt++) {
    $acquireLog = "$log.acquire-$slotAttempt.log"
    Write-Output "Acquire heavy attempt $slotAttempt; queue log: $acquireLog"
    & pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5 -StaleHours 87600 *> $acquireLog
    if ($LASTEXITCODE -eq 0) { $acquired=$true; Get-Content -LiteralPath $acquireLog -Tail 3; break }
    $acquireFailure=Get-Content -LiteralPath $acquireLog -Raw
    Get-Content -LiteralPath $acquireLog -Tail 12
    # The mandatory shared helper rewrites its queue heartbeat while other waiters read it. Retry only
    # that file-sharing failure, after this exact helper has exited; no Python has started yet.
    if ($acquireFailure -notmatch 'being used by another process|used by another process|używany przez inny proces') {
        throw 'Heavy acquire failed for a different reason; inspect queue log'
    }
    $ownSlot="C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"
    if (Test-Path -LiteralPath $ownSlot) { throw 'Partial own slot exists after failure; inspect before retry' }
    Start-Sleep -Seconds ([Math]::Min(10,2*$slotAttempt))
}
if (-not $acquired) { throw 'Nie uzyskano slotu heavy po błędach współdzielenia pliku kolejki' }
$code = 1
try {
    $env:PYTHONUNBUFFERED = '1'
    # Each slot is one task, not an unrestricted BLAS/OpenMP worker pool on top of the other sessions.
    $env:OMP_NUM_THREADS = '1'
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:MKL_NUM_THREADS = '1'
    $env:NUMEXPR_NUM_THREADS = '1'
    if ($Task -eq 'BuildAll') {
        & uv run --project tools/worldgen python art-source/world/materials/_src/cc0_fetch.py *> "$log.cc0-verify.log"
        $code=$LASTEXITCODE
        if($code){Get-Content "$log.cc0-verify.log" -Tail 12}
    }
    if($Task -ne 'BuildAll' -or $code -eq 0){
        & uv @uvArguments *> $log
        $code = $LASTEXITCODE
        Get-Content $log -Tail 18
    }
}
finally { & pwsh $slot -Release -Pool heavy -Owner $owner }
Add-Content (Join-Path $PSScriptRoot 'STATUS.md') "Zadanie heavy $Task zakończone kodem $code. Log: $log. Następny krok: odczytać wynik i wykonać tylko uzasadnioną następną operację."
git add -f (Join-Path $PSScriptRoot 'STATUS.md')
git commit -m "wip(light): zapisz wynik heavy $Task"
exit $code







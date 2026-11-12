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
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy' }
$code = 1
try {
    $env:PYTHONUNBUFFERED = '1'
    # Each slot is one task, not an unrestricted BLAS/OpenMP worker pool on top of the other sessions.
    $env:OMP_NUM_THREADS = '1'
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:MKL_NUM_THREADS = '1'
    $env:NUMEXPR_NUM_THREADS = '1'
    & uv @uvArguments *> $log
    $code = $LASTEXITCODE
    Get-Content $log -Tail 18
}
finally { & pwsh $slot -Release -Pool heavy -Owner $owner }
Add-Content (Join-Path $PSScriptRoot 'STATUS.md') "Zadanie heavy $Task zakończone kodem $code. Log: $log. Następny krok: odczytać wynik i wykonać tylko uzasadnioną następną operację."
git add -f (Join-Path $PSScriptRoot 'STATUS.md')
git commit -m "wip(light): zapisz wynik heavy $Task"
exit $code


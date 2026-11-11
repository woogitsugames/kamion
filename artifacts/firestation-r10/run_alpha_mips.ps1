$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$workRoot=[IO.Path]::GetFullPath((Join-Path $taskRoot '../..'))
Set-Location $workRoot
. "$workRoot/scripts/env.ps1"
function Assert-MipGate {
    if(-not(Test-Path "$taskRoot/ROOT_UNITY_RELEASE.txt")){throw 'Fresh explicit ROOT release missing'}
    foreach($guard in @('PHONE_RUN','GPT_UNITY_HOLD')) {
        if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$guard"){throw "Unity blocked by $guard"}
    }
    if(Test-UnityProjectLocked){throw 'Own Unity project already open'}
}
Assert-MipGate
$generatedRoot=[IO.Path]::GetFullPath((Join-Path $workRoot 'game/Assets/_Generated'))
$qaDir=[IO.Path]::GetFullPath((Join-Path $generatedRoot 'FireStationR7QA'))
if(-not $qaDir.StartsWith($generatedRoot+[IO.Path]::DirectorySeparatorChar)){throw 'QA path escapes own generated folder'}
if(Test-Path -LiteralPath $qaDir){throw 'QA folder already exists; inspect it before reuse'}
$log=Join-Path $taskRoot 'actual-alpha-mips.log'
try {
    New-Item -ItemType Directory -Path (Join-Path $qaDir 'Editor') -Force | Out-Null
    'E_QA_OWNED' | Set-Content -LiteralPath (Join-Path $qaDir '.e-qa-owned')
    Copy-Item -LiteralPath (Join-Path $taskRoot 'DumpAlphaMips.cs') -Destination (Join-Path $qaDir 'Editor/DumpAlphaMips.cs')
    Assert-MipGate
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','FireStationR7AlphaMips.Run')
    if($code -ne 0 -or -not(Select-String -Path $log -SimpleMatch 'E_ALPHA_MIPS_RESULT: OK' -Quiet)) {
        Show-UnityLogErrors $log
        throw "Actual mip QA failed exit $code; see $log"
    }
}
finally {
    # Exact task-created directory only; verify absolute containment/no junction before recursive removal.
    if(Test-Path -LiteralPath $qaDir) {
        $resolved=(Resolve-Path -LiteralPath $qaDir).Path
        if(-not $resolved.StartsWith($generatedRoot+[IO.Path]::DirectorySeparatorChar)){throw 'Refusing cleanup outside own generated root'}
        if((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refusing QA junction cleanup'}
        if(-not(Test-Path -LiteralPath (Join-Path $resolved '.e-qa-owned'))){throw 'QA ownership marker missing'}
        Remove-Item -LiteralPath $resolved -Recurse -Force
        if(Test-Path -LiteralPath ($qaDir+'.meta')){Remove-Item -LiteralPath ($qaDir+'.meta') -Force}
    }
}

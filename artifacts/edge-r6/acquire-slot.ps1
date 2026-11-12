param([ValidateSet('heavy','unity')][string]$Pool,[Parameter(Mandatory)][string]$Owner)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6' -or $Owner -notin @('gpt-edge','gpt-edge-r6')){throw 'Wrong owner/round'}
$central='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$mine="C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$Pool-slots/$Owner.slot"
if(Test-Path $mine){throw 'Own lease already exists; inspect active jobs rather than reuse it concurrently'}
New-Item -ItemType Directory -Force "$PSScriptRoot/slot-acquire"|Out-Null
for($attempt=1;$attempt -le5;$attempt++){
    $tag=Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $log="$PSScriptRoot/slot-acquire/$tag-$Pool-$Owner-attempt$attempt.log"
    # Retrying only a transient FIFO ticket sharing violation. All acquisition
    # rules, queue tickets, limits and PHONE_RUN handling stay in central main.
    $ErrorActionPreference='Continue'
    & pwsh -File $central -Acquire -Pool $Pool -Owner $Owner -PollSeconds 7 -StaleHours 100000 2>&1 | Tee-Object -FilePath $log
    $code=$LASTEXITCODE
    $ErrorActionPreference='Stop'
    if($code -eq0){
        if(-not(Test-Path $mine)){throw 'Central reported success without an own lease'}
        exit 0
    }
    if(Test-Path $mine){throw 'Acquisition failed with an own lease present; inspect before cleanup or restart'}
    $failure=Get-Content $log -Raw
    if($failure -notmatch 'used by another process' -or $failure -notmatch [regex]::Escape("$Owner.wait")){
        throw "Central acquisition failed for a different reason: $log"
    }
    Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Centralny Acquire nie uzyskał dzierżawy przez przejściową blokadę własnego biletu FIFO; próba $attempt i log zachowane. Ponowne wywołanie standardowego centralnego skryptu, bez zmiany limitów lub cudzych plików."
    Start-Sleep -Seconds 3
}
throw 'Repeated FIFO sharing violations; inspect saved central logs before continuing'

param([int]$ControllerId=73184)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $repo
$main='C:/Users/matma/Documents/Claude/kamion'
function Deliver {
    & robocopy $PSScriptRoot "$main/artifacts/light-r6" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if($LASTEXITCODE -ge 8){throw "Robocopy failed: $LASTEXITCODE"}
}
try{
    # Observation only: never signal, kill, release a live slot or mutate another session.
    while(Get-Process -Id $ControllerId -ErrorAction SilentlyContinue){Start-Sleep -Seconds 15}
    $branch=(git branch --show-current).Trim()
    $slot="$main/artifacts/locks/heavy-slots/gpt-light-r6.slot"
    if($branch -ne 'gpt-light-r6' -or (Test-Path -LiteralPath $slot)){
        $message="Kontroler zakończył się, ale bez automatycznej archiwizacji: branch=$branch, ownSlotExists=$(Test-Path -LiteralPath $slot). Wymagana inspekcja przed wznowieniem. Niczego nie zabito ani nie zwolniono na podstawie samego PID."
        Add-Content "$PSScriptRoot/PRZEKAZANIE.md" "`n## Aktualizacja po procesie`n`n$message"
        @{time=(Get-Date).ToString('o');status='needs-inspection';message=$message}|ConvertTo-Json|Set-Content "$PSScriptRoot/STOP-COMPLETED.json" -Encoding utf8
        Deliver
        exit 0
    }
    $snapshot=Join-Path $PSScriptRoot 'stop-generated-snapshot'
    New-Item -ItemType Directory -Force "$snapshot/files"|Out-Null
    & git diff --binary HEAD "--output=$snapshot/tracked-working-tree.patch" -- . ':!artifacts/light-r6'
    if($LASTEXITCODE){throw 'Cannot save working-tree patch'}
    $changed=(& git -c core.quotePath=false diff --name-only -z HEAD -- . ':!artifacts/light-r6') -join "`n"
    $files=@()
    foreach($relative in $changed.Split([char]0)|Where-Object {$_}){
        $source=[IO.Path]::GetFullPath((Join-Path $repo $relative))
        $destination=[IO.Path]::GetFullPath((Join-Path "$snapshot/files" $relative))
        if(-not $source.StartsWith($repo+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
            -not $destination.StartsWith($snapshot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Snapshot path outside expected workspace'}
        if(Test-Path -LiteralPath $source -PathType Leaf){
            New-Item -ItemType Directory -Force ([IO.Path]::GetDirectoryName($destination))|Out-Null
            Copy-Item -LiteralPath $source -Destination $destination
            $files+=@{path=$relative;bytes=(Get-Item -LiteralPath $source).Length;sha=(Get-FileHash -LiteralPath $source).Hash;snapshotSha=(Get-FileHash -LiteralPath $destination).Hash}
        }else{$files+=@{path=$relative;deleted=$true}}
    }
    $files|ConvertTo-Json -Depth 5|Set-Content "$snapshot/files.json" -Encoding utf8
    $ack=if(Test-Path "$PSScriptRoot/STOP-ACK.json"){Get-Content "$PSScriptRoot/STOP-ACK.json" -Raw|ConvertFrom-Json}else{$null}
    $world=Test-Path "$PSScriptRoot/world-checkpoint.json"
    $normalStop=$null -ne $ack -and $ack.task -eq 'Fidelity'
    $state=@{time=(Get-Date).ToString('o');status=if($normalStop){'stopped-before-Fidelity'}else{'controller-ended-inspect-log'};
        branch=$branch;controllerId=$ControllerId;controllerEnded=$true;heavySlotAbsent=$true;
        worldCheckpointPresent=$world;ack=$ack;snapshotFiles=$files.Count;headBeforeFinalSave=(git rev-parse HEAD).Trim()}
    $state|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/STOP-COMPLETED.json" -Encoding utf8
    $message="Proces $ControllerId zakończył się sam. Slot heavy własnej rundy jest nieobecny. World checkpoint: $world. Potwierdzone zatrzymanie przed Fidelity: $normalStop. Zarchiwizowano $($files.Count) zmienionych plików śledzonych i patch w stop-generated-snapshot. Zmiany generatora pozostawiono także w worktree; nie cofano ich i nie scalano do main. Raw derived pozostaje w tym worktree. Sprawdź STOP-COMPLETED.json i log World przed wznowieniem."
    Add-Content "$PSScriptRoot/PRZEKAZANIE.md" "`n## Aktualizacja po zakończeniu procesu ($(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))`n`n$message"
    Add-Content "$PSScriptRoot/STATUS.md" $message
    git add -f -- artifacts/light-r6
    git commit -m 'wip(light): save remaining phase and requested-stop handoff'
    if($LASTEXITCODE){throw 'Final stop save commit failed'}
    Deliver
    $sourceFiles=@(Get-ChildItem -LiteralPath $PSScriptRoot -File -Recurse)
    foreach($file in $sourceFiles){
        if($file.Name -like 'stop-closer.*.log'){continue}
        $target=Join-Path "$main/artifacts/light-r6" $file.FullName.Substring($PSScriptRoot.Length+1)
        if(-not(Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -ne $file.Length){throw "Delivery differs: $target"}
    }
    if((Get-FileHash "$PSScriptRoot/PRZEKAZANIE.md").Hash -ne (Get-FileHash "$main/artifacts/light-r6/PRZEKAZANIE.md").Hash){throw 'Handoff delivery hash mismatch'}
    Write-Output 'Requested stop saved and delivered. No process was killed. No further task is scheduled.'
}catch{
    $message="Automatyczny zapis po zatrzymaniu wymaga inspekcji: $($_.Exception.Message)"
    Add-Content "$PSScriptRoot/PRZEKAZANIE.md" "`n$message"
    Write-Error $message
}

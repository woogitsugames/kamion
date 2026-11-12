param([Parameter(Mandatory)][int]$BaselinePid)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
foreach($item in @(@{spec='Apron';name='apron'},
                  @{spec='FarField_far:far_field_buildings';name='far-opaque'},
                  @{spec='FarField_far:forest_edge_mixed';name='far-forest'})){
    & pwsh -File "$PSScriptRoot/mask-floor.ps1" -WaitPid $BaselinePid -MaskSpec $item.spec -OutputName $item.name *> "$PSScriptRoot/mask-$($item.name)-runner.log"
    if($LASTEXITCODE -ne0){throw "Ownership mask failed: $($item.name)"}
}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/OwnershipMasks.ready"
& pwsh -File "$PSScriptRoot/render-camera-height.ps1" *> "$PSScriptRoot/camera-height-runner.log"
if($LASTEXITCODE -ne0){throw 'Camera height diagnostic failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/OwnershipDiagnostics.ready"

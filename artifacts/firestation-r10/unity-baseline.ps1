param(
    [ValidateSet('Import','Vehicle','Capture')][string]$Stage,
    [ValidateSet('before','probe','core-probe','bundle-probe','round1','round2')][string]$Phase='before',
    [switch]$OnlyHero,
    [string]$CameraIds='',
    [ValidateSet('','Low','High')][string]$OnlyTier='',
    [ValidateSet('','clear','overcast')][string]$OnlyLight=''
)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$workRoot=[IO.Path]::GetFullPath((Join-Path $taskRoot '../..'))
Set-Location $workRoot
. "$workRoot/scripts/env.ps1"

function Assert-EUnityRelease {
    # ROOT must explicitly release this task; absence of transient PHONE_RUN is insufficient.
    if(-not(Test-Path "$taskRoot/ROOT_UNITY_RELEASE.txt")) {throw 'No explicit ROOT Unity release recorded for E'}
    foreach($guard in @('PHONE_RUN','GPT_UNITY_HOLD')) {
        if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$guard") {throw "Unity blocked by $guard"}
    }
    if(Test-UnityProjectLocked) {throw 'E game project is already open in Unity'}
}
function Invoke-EStage([string]$Name,[string[]]$UnityArguments,[string]$Marker) {
    $prefix=if($Phase -eq 'before') {'baseline'} else {$Phase}
    $log="$taskRoot/$prefix-$Name.log"
    Assert-EUnityRelease
    $code=Invoke-UnityBatch -LogFile $log -Arguments $UnityArguments
    if($code -ne 0 -or -not(Select-String -Path $log -SimpleMatch $Marker -Quiet)) {
        Show-UnityLogErrors $log
        throw "$Name failed, exit $code; see $log"
    }
}

if($Stage -eq 'Import') {
    if(-not(Test-Path "$taskRoot/baseline-cpu-done.txt")) {throw 'Fresh CPU products not verified'}
    Invoke-EStage 'import' @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium') 'IMPORT_RESULT: OK'
}
elseif($Stage -eq 'Vehicle') {
    Invoke-EStage 'canonical-vehicle' @('-executeMethod','Game.World.Import.WorldTruckInstaller.InstallBatch') 'TRUCK_RESULT: OK'
    @'
from pathlib import Path
import hashlib,json
r=Path.cwd();out=r/'artifacts/firestation-r10'
roots=[r/'game/Assets/_Generated/Truck',r/'game/Assets/_Generated/Trailer']
files=[p for root in roots for p in root.rglob('*') if p.is_file()]
assert files, 'Canonical vehicle fixture missing'
(out/'baseline-vehicle-sha256.json').write_text(json.dumps({p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2))
'@ | uv run --project tools/worldgen python -
    if($LASTEXITCODE -ne 0) {throw 'Vehicle snapshot failed'}
}
elseif($Stage -eq 'Capture') {
    if(-not(Test-Path "$taskRoot/baseline-vehicle-sha256.json")) {throw 'Canonical vehicle must precede matched baseline'}
    foreach($tier in @('Low','High')) {
        if($OnlyTier -and $tier -ne $OnlyTier) {continue}
        $scene=if($tier -eq 'High') {'WorldC_High'} else {'WorldC'}
        foreach($light in @('clear','overcast')) {
            if($OnlyLight -and $light -ne $OnlyLight) {continue}
            Assert-EUnityRelease
            $captureArgs=@()
            if($OnlyHero) {$captureArgs=@('-Cameras','fire-station-route,fire-station-abeam,fire-station-ref7197,fire-station-above')}
            if($CameraIds) {$captureArgs=@('-Cameras',$CameraIds)}
            $output="$taskRoot/$Phase/$tier-$light"
            if(Test-Path "$output/stats.txt") {throw "Completed evidence already exists: $output; preserve it"}
            # Standard route cameras include all four fire_station_* hero cameras.
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Width 2340 -Height 1080 -OutputDir $output @captureArgs
            if($LASTEXITCODE -ne 0) {throw "Baseline capture failed: $tier/$light"}
        }
    }
}
else {throw 'Choose -Stage Import, Vehicle or Capture'}

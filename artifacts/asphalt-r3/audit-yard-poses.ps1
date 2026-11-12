param([ValidatePattern('^[a-z0-9-]+$')][string]$Label='yard-pose-post0131',
      [ValidateSet('Low','High')][string]$Tier='Low',
      [ValidateSet('clear','overcast')][string]$Lighting='clear')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$dir="$PSScriptRoot/$Label/$Tier-$Lighting"
$probePath="$PSScriptRoot/yard-probe-baseline.json"
$probe=Get-Content $probePath -Raw|ConvertFrom-Json
$receipt=Get-Content "$PSScriptRoot/baseline-producer-progress.json" -Raw|ConvertFrom-Json
$context=Get-Content "$dir/capture-context.json" -Raw|ConvertFrom-Json
if(-not $receipt.complete -or $receipt.world_exit -ne 0 -or $probe.manifest_sha256 -ne $receipt.manifest_sha256){throw 'Baseline source probe/producer mismatch'}
if($context.schema -ne 1 -or -not $context.import.complete -or $context.ablation -ne 'none' -or $context.import.manifest_sha256 -ne $probe.manifest_sha256){throw 'Capture does not match baseline source probe'}
if($context.world_root_sha256 -ne (Get-FileHash game/Assets/_Project/World/Runtime/WorldRegionRoot.cs).Hash){throw 'Coordinate contract changed; inspect before interpreting old positions'}
if($context.fixture_sha256 -ne (Get-FileHash "$PSScriptRoot/cameras.json").Hash){throw 'Fixture changed since the pose trial; inspect a fresh trial'}
$fixture=Get-Content "$PSScriptRoot/cameras.json" -Raw|ConvertFrom-Json
$provenance=Get-Content "$PSScriptRoot/camera-provenance.json" -Raw|ConvertFrom-Json
$ids=@($provenance.new_yard_probes.ids)
if(-not $ids.Count -or @($ids|Select-Object -Unique).Count -ne $ids.Count){throw 'Invalid inspection camera plan'}
$rows=@()
foreach($id in $ids){
 $cams=@($fixture.cameras|Where-Object id -eq $id)
 if($cams.Count -ne 1 -or $cams[0].seat -ne 'road' -or $cams[0].kind -ne 'material_inspection'){throw "Unexpected inspection camera: $id"}
 $camera=$cams[0]
 $snapshot=Get-Content "$dir/runtime-cameras/QA_$id.json" -Raw|ConvertFrom-Json
 if($snapshot.schemaVersion -ne 3 -or $snapshot.camera -ne "QA_$id"){throw "Invalid runtime snapshot: $id"}
 # Actual LocalToUnity/ToGlobal contract: use recorded anchorZ and originShift, never the nominal file U.
 $e=[double]$snapshot.position.x+[double]$snapshot.originShift.x
 $n=[double]$snapshot.position.z+[double]$snapshot.originShift.z
 $u=[double]$snapshot.anchorZ+[double]$snapshot.position.y+[double]$snapshot.originShift.y
 if([Math]::Abs($e-$camera.pos[0]) -gt .002 -or [Math]::Abs($n-$camera.pos[1]) -gt .002){throw "Runtime EN differs: $id"}
 $points=@($probe.points|Where-Object {[Math]::Abs($_.en[0]-$e) -lt .002 -and [Math]::Abs($_.en[1]-$n) -lt .002})
 if($points.Count -ne 1){throw "No unique source grid point for $id"}
 $paved=@($points[0].hits|Where-Object {$_.node -eq 'paved' -and $_.material -in @('yard_asphalt','yard_behaton','yard_paving','yard_concrete','yard_concrete_worn','yard_slabs')})
 $best=$paved|Sort-Object @{Expression={[Math]::Abs($u-[double]$_.elevation_u-2.5)}}|Select-Object -First 1
 $delta=if($best){$u-[double]$best.elevation_u-2.5}else{$null}
 $accepted=$null -ne $delta -and [Math]::Abs($delta) -le .05
 $rows+=[ordered]@{id=$id;runtime_local_enu=@($e,$n,$u);source_paved_hit=$best;
     height_above_source_m=$(if($best){$u-[double]$best.elevation_u}else{$null});delta_from_2_5m=$delta;
     within_r2_scope_envelope=$points[0].within_r2_scope_envelope;accepted=$accepted;
     snapshot_sha256=(Get-FileHash "$dir/runtime-cameras/QA_$id.json").Hash;
     png_sha256=(Get-FileHash "$dir/$id.png").Hash}
}
$failed=@($rows|Where-Object {-not $_.accepted}).Count
[ordered]@{checked_at=(Get-Date -Format o);label=$Label;tier=$Tier;lighting=$Lighting;rows=$rows;failed=$failed;
    source_probe_sha256=(Get-FileHash $probePath).Hash;capture_context_sha256=(Get-FileHash "$dir/capture-context.json").Hash;
    note='Checks camera EN and actual recorded U against a source paved triangle at its footpoint, tolerance5cm. Does not identify material of every image pixel, photograph pose, ownership, visual quality or GPU timing.'
}|ConvertTo-Json -Depth 12|Set-Content "$PSScriptRoot/yard-pose-audit-$Label.json"
if($failed){throw "$failed inspection poses do not match source paved height; do not accept the full baseline"}
"Verified $($rows.Count) inspection camera footpoints; photo pose remains unverified."

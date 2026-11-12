$lifeSelection=Get-Content artifacts/life-r4/SELECTED.json -Raw|ConvertFrom-Json
if(!$lifeSelection.selected){throw 'Author selection required'}
$lifeCapture=Get-Content (Join-Path artifacts/life-r4 $lifeSelection.source_capture) -Raw|ConvertFrom-Json
function Assert-LifeSelected {
 foreach($p in $lifeCapture.source_sha.PSObject.Properties){
  if((Get-FileHash $p.Name).Hash -ne $p.Value){throw "Selected source changed: $($p.Name)"}
 }
 foreach($pair in @(@('art-source/world/props/street_props.glb',$lifeCapture.library_sha),
                    @('art-source/world/props/props_meta.json',$lifeCapture.meta_sha),
                    @('artifacts/life-r4/cameras.json',$lifeCapture.cameras_sha))){
  if((Get-FileHash $pair[0]).Hash -ne $pair[1]){throw "Selected input changed: $($pair[0])"}
 }
}
Assert-LifeSelected

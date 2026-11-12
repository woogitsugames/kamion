param([ValidatePattern('^candidate[0-9]*$')][string]$After='candidate2')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
function Read-Counters([string]$Path) {
 $rows=@{}
 foreach($line in Get-Content $Path) {
  if($line -match '^([^:]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)') {
   $rows[$Matches[1]]=[ordered]@{objects=[int]$Matches[2];draws=[int]$Matches[3];shadow_draws=[int]$Matches[4];tris_k=[int]$Matches[5]}
  } elseif($line -match '^  (.+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)') {
   $row=$rows[$Matches[1]]
   $row.instance_draws=[int]$Matches[2];$row.instances=[int]$Matches[3];$row.instance_tris_k=[int]$Matches[4];$row.cells=[int]$Matches[5];$row.forest_cells=[int]$Matches[6]
  }
 }
 return $rows
}
$plan=Get-Content artifacts/asphalt-r3/capture-plan.json -Raw | ConvertFrom-Json
$expected=@($plan.expected_ids)
if(-not $expected.Count -or @($expected | Select-Object -Unique).Count -ne $expected.Count){throw 'Invalid capture plan'}
$required=@('objects','draws','shadow_draws','tris_k','instance_draws','instances','instance_tris_k','cells','forest_cells')
$result=@()
foreach($condition in 'Low-overcast','Low-clear','High-overcast','High-clear') {
 $beforeCounters=Read-Counters "artifacts/asphalt-r3/baseline/$condition/stats.txt"
 $afterCounters=Read-Counters "artifacts/asphalt-r3/$After/$condition/stats.txt"
 if($beforeCounters.Count -ne $expected.Count -or $afterCounters.Count -ne $expected.Count){throw "Camera count mismatch: $condition"}
 foreach($id in $expected | Sort-Object) {
  if(-not $beforeCounters.ContainsKey($id) -or -not $afterCounters.ContainsKey($id)){throw "Missing camera: $id"}
  foreach($key in $required) {
   if(-not $beforeCounters[$id].Contains($key) -or -not $afterCounters[$id].Contains($key)){throw "Missing counter: $id/$key"}
   $b=$beforeCounters[$id][$key];$a=$afterCounters[$id][$key]
   $result += [pscustomobject]@{condition=$condition;camera=$id;counter=$key;before=$b;after=$a;delta=$a-$b}
  }
 }
}
$result | Export-Csv "artifacts/asphalt-r3/counter-audit-$After.csv" -NoTypeInformation
$changed=@($result | Where-Object delta -ne 0)
[ordered]@{camera_conditions=($expected.Count*4);counter_rows=$result.Count;changed_rows=$changed.Count;changes=$changed;note='CPU visibility/LOD estimates, triangles rounded in thousands; instance counters separate; not GPU timings.'} | ConvertTo-Json -Depth 5 | Set-Content "artifacts/asphalt-r3/counter-audit-$After.json"
if($changed.Count){throw 'Counter changes require review'}
Write-Output "All $($result.Count) counters unchanged across $($expected.Count*4) camera/conditions."

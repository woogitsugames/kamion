$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$base=Get-Content artifacts/life-r3/native-a-materials.json -Raw|ConvertFrom-Json
$folder='game/Assets/_Generated/World/bialystok-industrial-c/Materials'
$outside=@(foreach($entry in $base){
 if($entry.name -ne 'M_car_paint_black.mat' -and (Get-FileHash (Join-Path $folder $entry.name)).Hash -ne $entry.sha){$entry.name}
})
$before=Get-Content artifacts/life-r3/native-a-materials/M_car_paint_black.mat -Raw
$after=Get-Content (Join-Path $folder M_car_paint_black.mat) -Raw
$pattern='(?m)^(    - _CarFlake: \{r: 400, g: 1, b: )([^,}]+)(, a: 1\})\r?$'
$mb=[regex]::Match($before,$pattern);$ma=[regex]::Match($after,$pattern)
if(!$mb.Success -or !$ma.Success){throw 'Native black vector format changed'}
$oldLift=[double]::Parse($mb.Groups[2].Value,[Globalization.CultureInfo]::InvariantCulture)
$newLift=[double]::Parse($ma.Groups[2].Value,[Globalization.CultureInfo]::InvariantCulture)
$normalized=([regex]::Replace($before,$pattern,'$1LIFT$3') -ceq [regex]::Replace($after,$pattern,'$1LIFT$3'))
$result=@{stage='b';native_materials_checked=@($base).Count;changed_outside_black=$outside;
 black_lift_before=$oldLift;black_lift_after=$newLift;black_identical_outside_lift=$normalized;
 black_sha_before=(Get-FileHash artifacts/life-r3/native-a-materials/M_car_paint_black.mat).Hash;
 black_sha_after=(Get-FileHash (Join-Path $folder M_car_paint_black.mat)).Hash;
 note='Exact native material comparison preserves Tint, Pearl, roughness, texture bindings, keyword/pass state, all other paints/cabs and plate.'}
$result|ConvertTo-Json -Depth 4|Set-Content artifacts/life-r3/native-b-validation.json
if($outside.Count -or !$normalized -or [math]::Abs($oldLift-.08) -gt 1e-7 -or [math]::Abs($newLift-.025) -gt 1e-7){throw 'Native black-only ablation contract failed'}
"Native B verified: $(@($base).Count) materials; only black lift 0.08 -> 0.025"

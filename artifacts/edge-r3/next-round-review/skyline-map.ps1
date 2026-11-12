$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$cache=Get-Content Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json -Raw|ConvertFrom-Json
$proof=Get-Content artifacts/edge-r3/proof-cameras.json -Raw|ConvertFrom-Json
$camera=$proof.cameras|Where-Object id -eq 'sbs-g3-a-303305168125936'
$visibility=Get-Content "$PSScriptRoot/skyline-visibility.json" -Raw|ConvertFrom-Json
$candidate=($visibility.cameras|Where-Object camera -eq $camera.id).candidate_blocks.id
$svg=[Collections.Generic.List[string]]::new()
function N([double]$n){$n.ToString('0.###',[Globalization.CultureInfo]::InvariantCulture)}
function X([double]$e){return 350+$e*0.071}
function Y([double]$n){return 370-$n*0.071}
$svg.Add('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="720" viewBox="0 0 960 720"><rect width="960" height="720" fill="#fff"/><g font-family="Arial" fill="#222">')
$svg.Add('<text x="22" y="28" font-size="20">Bloki GIS i zasięg Low — diagnostyka planarna</text>')
$svg.Add('<text x="22" y="51" font-size="13">Źródłowe pozycje 1:1; bez okluzji, mgły i identyfikacji zdjęciowej</text>')
$cx=X $camera.pos[0];$cy=Y $camera.pos[1]
$svg.Add("<circle cx='$(N $cx)' cy='$(N $cy)' r='$(N (900*0.071))' fill='#e8f0ff' stroke='#4775c5' stroke-dasharray='5 4'/>")
$svg.Add("<rect x='$(N (X -1024))' y='$(N (Y 1024))' width='$(N (2048*0.071))' height='$(N (2048*0.071))' fill='#eff0e8' stroke='#333'/>")
# Redraw the radius on top of the region without changing the filled source extent.
$svg.Add("<circle cx='$(N $cx)' cy='$(N $cy)' r='$(N (900*0.071))' fill='none' stroke='#4775c5' stroke-dasharray='5 4'/>")
foreach($b in $cache.buildings|Where-Object {$_.typ -eq 'block' -and $_.h -ge 20}){
    $pts=($b.rect|ForEach-Object {"$(N (X $_[0])),$(N (Y $_[1]))"}) -join ' '
    $color=if($b.id -in $candidate){'#c67a21'}else{'#8f9aaa'}
    $svg.Add("<polygon points='$pts' fill='$color' stroke='$color' stroke-width='0.6'/>")
    if($b.h -ge 50){
        $e=($b.rect|ForEach-Object {$_[0]}|Measure-Object -Average).Average
        $n=($b.rect|ForEach-Object {$_[1]}|Measure-Object -Average).Average
        $svg.Add("<text x='$(N ((X $e)+4))' y='$(N ((Y $n)-3))' font-size='10'>$(N $b.h) m</text>")
    }
}
$de=$camera.look_at[0]-$camera.pos[0];$dn=$camera.look_at[1]-$camera.pos[1]
$length=[Math]::Sqrt($de*$de+$dn*$dn);$de/=$length;$dn/=$length
$svg.Add("<line x1='$(N $cx)' y1='$(N $cy)' x2='$(N (X ($camera.pos[0]+3000*$de)))' y2='$(N (Y ($camera.pos[1]+3000*$dn)))' stroke='#b02020' stroke-width='1.5'/>")
$svg.Add("<circle cx='$(N $cx)' cy='$(N $cy)' r='4' fill='#b02020'/>")
$svg.Add('<text x="670" y="100" font-size="16">Kamera 303305</text><text x="670" y="124" font-size="13">Poza B / WORKING_VALUE</text>')
$svg.Add('<text x="670" y="164" font-size="13" fill="#4775c5">Promień w skali źródła: 900 m</text><text x="670" y="186" font-size="13">Kwadrat: region 2048 × 2048 m</text>')
$svg.Add('<text x="670" y="224" font-size="13" fill="#c67a21">Pomarańczowe: środki w FOV</text><text x="670" y="244" font-size="13">po aktualnej kompresji tła</text>')
$svg.Add('<text x="670" y="264" font-size="12">Okrąg nie jest płaszczyzną far clip.</text><text x="670" y="282" font-size="13">Rysunek pokazuje pozycje GIS,</text><text x="670" y="302" font-size="13">nie skompresowane bryły renderu.</text>')
$svg.Add('<text x="670" y="342" font-size="13">Wszystkie bloki h ≥ 20 m.</text><text x="670" y="362" font-size="13">Etykiety tylko dla h ≥ 50 m.</text>')
$svg.Add('<text x="22" y="696" font-size="12">Źródła: przypięty cache BDOT10k/GUGiK LoD1/OSM; SHA w skyline-visibility.json. To nie mapa nawigacyjna.</text></g></svg>')
[IO.File]::WriteAllLines("$PSScriptRoot/skyline-map.svg",$svg,[Text.UTF8Encoding]::new($false))
& magick -limit thread 1 "$PSScriptRoot/skyline-map.svg" "$PSScriptRoot/skyline-map.png"
if($LASTEXITCODE -ne 0){throw 'Map rasterization failed'}

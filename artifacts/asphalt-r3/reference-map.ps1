$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$buildingPath='Data/Regions/bialystok-industrial-c/buildings.geojson'
$surfacePath='Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json'
$pointPath='artifacts/asphalt-r2/backlog-r3-references/pcrt-coordinate-precheck.json'
$origin=(Get-Content Data/Regions/bialystok-industrial-c/generated/world_manifest.json -Raw|ConvertFrom-Json).origin_epsg2180
$buildings=Get-Content $buildingPath -Raw|ConvertFrom-Json
$surfaces=Get-Content $surfacePath -Raw|ConvertFrom-Json
$points=@(Get-Content $pointPath -Raw|ConvertFrom-Json)
$context=Get-Content artifacts/asphalt-r3/reference/BUILDING-CONTEXT.json -Raw|ConvertFrom-Json
$ids=@($context.rows.id)
$inv=[Globalization.CultureInfo]::InvariantCulture
function N([double]$Value){$Value.ToString('0.00',$inv)}
function X([double]$E){N (50+($E-230)*2)}
function Y([double]$North){N (70+(-260-$North)*2)}
function Polygon-Path($Rings){
 $path=''
 foreach($ring in $Rings){
  $first=$true
  foreach($point in $ring){
   $command=if($first){'M'}else{'L'};$first=$false
   $path+="$command$(X ($point[0]-$origin.x)),$(Y ($point[1]-$origin.y)) "
  }
  $path+='Z '
 }
 return $path
}
$svg=[Collections.Generic.List[string]]::new()
$svg.Add('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="820" viewBox="0 0 960 820"><rect width="960" height="820" fill="#fafafa"/><defs><clipPath id="plot"><rect x="50" y="70" width="540" height="660"/></clipPath><pattern id="exclude" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M-2,2 L2,-2 M0,10 L10,0 M8,12 L12,8" stroke="#c54c53" stroke-width="1"/></pattern></defs><g font-family="DejaVu Sans,Arial,sans-serif" fill="#17212b"><text x="50" y="30" font-size="20">Kontekst źródłowy placu PCRT — bez dopasowanej pozy zdjęcia 3</text><text x="50" y="53" font-size="13">Lokalne E/N w metrach; północ u góry. Dane wejściowe, nie wynik świeżego World.</text><g clip-path="url(#plot)"><rect x="50" y="70" width="540" height="660" fill="#eef2e9"/>')
$target=@($surfaces.bdot10k.OT_PTPL_A|Where-Object id -eq '2BE4B432-6D21-1BF0-E053-CC2BA8C0D140:0')
if($target.Count -ne 1 -or $target[0].geometry.type -ne 'Polygon'){throw 'Unexpected source surface'}
$path=Polygon-Path $target[0].geometry.coordinates
$svg.Add("<path d='$path' fill='#e3c999' fill-rule='evenodd' stroke='#967239' stroke-width='2'/>")
foreach($feature in $buildings.features){
 if($feature.properties.id -notin $ids){continue}
 if($feature.geometry.type -ne 'MultiPolygon'){throw 'Unexpected building geometry'}
 $fill=if($feature.properties.id -eq 'bdot:2BE4B431-C92B-1BF0-E053-CC2BA8C0D140'){'#7e9fba'}else{'#c5cad0'}
 foreach($poly in $feature.geometry.coordinates){$path=Polygon-Path $poly;$svg.Add("<path d='$path' fill='$fill' fill-rule='evenodd' stroke='#526372' stroke-width='1'/>")}
}
$svg.Add("<rect x='$(X 400)' y='$(Y -250)' width='900' height='900' fill='url(#exclude)' opacity='.65'/>")
$svg.Add("<rect x='$(X 280)' y='$(Y -300)' width='400' height='520' fill='none' stroke='#246aa0' stroke-width='2' stroke-dasharray='7,5'/>")
for($e=250;$e -le 500;$e+=50){$svg.Add("<line x1='$(X $e)' y1='70' x2='$(X $e)' y2='730' stroke='#45545c' opacity='.15'/>")}
for($north=-550;$north -le -300;$north+=50){$svg.Add("<line x1='50' y1='$(Y $north)' x2='590' y2='$(Y $north)' stroke='#45545c' opacity='.15'/>")}
for($i=0;$i -lt $points.Count;$i++){
 if(-not $points[$i].local_en){continue}
 $p=$points[$i].local_en;$xv=X $p[0];$yv=Y $p[1];$label=$i+1
 $svg.Add("<circle cx='$xv' cy='$yv' r='9' fill='#ffffff' stroke='#0b4a73' stroke-width='2'/><text x='$xv' y='$(N ([double]$yv+4))' text-anchor='middle' font-size='12'>$label</text>")
}
$svg.Add("<text x='$(X 359)' y='$(Y -421)' font-size='14' font-weight='bold'>C92B</text></g><rect x='50' y='70' width='540' height='660' fill='none' stroke='#33434c'/>")
for($e=250;$e -le 500;$e+=50){$svg.Add("<text x='$(X $e)' y='750' text-anchor='middle' font-size='12'>$e E</text>")}
for($north=-550;$north -le -300;$north+=50){$svg.Add("<text x='43' y='$(N ([double](Y $north)+4))' text-anchor='end' font-size='11'>$north</text>")}
$legend=@('Obrysy budynków: buildings.geojson','Niebieski: BDOT C92B (kandydat)','Punkt 4 leży w jego obrysie.','','Beżowy: surowy obrys BDOT PTPL','Wejście opisane: masa bitumiczna.','To nie dowód materiału GLB.','','Przerywana linia: bbox sondy GLB','E 280–480 / N −560 do −300.','','Czerwony: bufor r2 (fragment)','E400–850 / N−700 do −250','curb_concrete / sidewalk_paving','Nie jest granicą własności terenu.','','1 / 2 / 4: przybliżone punkty','metadanych sąsiednich zdjęć.','Zdjęcie 3: brak punktu GPS.','','Nie ustalono dokładności GPS,','pozy zdjęcia placu ani jego zasięgu.','Wysokość placu: oczekuje sondy.','','Widoczny fragment kontekstu;','bez zmian geometrii lub override.','Źródła i SHA: context-map.json.')
for($i=0;$i -lt $legend.Count;$i++){$svg.Add("<text x='615' y='$(100+$i*22)' font-size='12'>$([Security.SecurityElement]::Escape($legend[$i]))</text>")}
$svg.Add('<text x="50" y="788" font-size="12">Mapa pomocnicza QA. Widoczne metadane nie są dopasowaniem fotografii ani pomiarem fizycznego materiału.</text></g></svg>')
$out='artifacts/asphalt-r3/reference/context-map.svg'
[IO.File]::WriteAllText((Join-Path (Get-Location) $out),($svg -join "`n"),[Text.UTF8Encoding]::new($false))
[ordered]@{created_at=(Get-Date -Format o);figure=$out;origin_epsg2180=$origin;bounds_local_en=@(230,-590,500,-260);sources=@($buildingPath,$surfacePath,$pointPath)|ForEach-Object {@{file=$_;sha256=(Get-FileHash $_).Hash}};surface_id=$target[0].id;surface_props=$target[0].props;note='Direct vector projection of source polygons and declared photo points. No bin geometry, camera fitting, image recoloring or Python workload.'}|ConvertTo-Json -Depth 8|Set-Content artifacts/asphalt-r3/reference/context-map.json

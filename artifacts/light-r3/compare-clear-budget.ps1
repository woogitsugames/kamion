$ErrorActionPreference='Stop'
function Read-Budget([string]$Path) {
    $items=@{}
    foreach($line in Get-Content -LiteralPath $Path){
        if($line -match '^(?<id>[^:]+): objects=(?<objects>\d+) drawsEst=(?<draws>\d+) shadowDrawsEst=(?<shadow>\d+) trisK=(?<tris>\d+)'){
            $items[$Matches.id]=@{objects=[int]$Matches.objects;draws=[int]$Matches.draws;shadow=[int]$Matches.shadow;triangles=[int]$Matches.tris*1000}
        }
        elseif($line -match '^\s+(?<id>\S+) instanced .*draws (?<draws>\d+), instances (?<instances>\d+), triangles (?<tris>\d+)k'){
            if(-not $items.ContainsKey($Matches.id)){throw 'Missing primary budget before instanced line'}
            $items[$Matches.id].instancedDraws=[int]$Matches.draws
            $items[$Matches.id].instances=[int]$Matches.instances
            $items[$Matches.id].instancedTriangles=[int]$Matches.tris*1000
        }
    }
    return $items
}
$entries=@()
foreach($tier in @('Low','High')){
    $before=Read-Budget "$PSScriptRoot/clear-budget-before/$tier/stats.txt"
    $after=Read-Budget "$PSScriptRoot/clear-final/$tier/stats.txt"
    if($before.Count -ne 61 -or $after.Count -ne 61){throw 'Expected all61 cameras'}
    foreach($id in ($after.Keys|Sort-Object)){
        if(-not $before.ContainsKey($id)){throw "Unmatched camera$id"}
        $b=$before[$id];$a=$after[$id]
        if(-not $a.ContainsKey('instancedDraws') -or -not $b.ContainsKey('instancedDraws')){throw 'Missing separate instancing'}
        $drawDelta=$a.draws+$a.shadow+$a.instancedDraws-$b.draws-$b.shadow-$b.instancedDraws
        $triDelta=100.0*($a.triangles+$a.instancedTriangles-$b.triangles-$b.instancedTriangles)/[Math]::Max(1,$b.triangles+$b.instancedTriangles)
        $entries+=@{tier=$tier;camera=$id;before=$b;after=$a;totalDrawDelta=$drawDelta;totalTriangleDeltaPercent=$triDelta}
    }
}
$bad=@($entries|Where-Object {$_.totalDrawDelta -gt 0 -or $_.totalTriangleDeltaPercent -gt 2})
@{scope='CPU estimates before SRP batching; rounded triangle counts; instancing separately included; not measured GPU or A16';entries=$entries;regressed=$bad.Count}|ConvertTo-Json -Depth 8|Set-Content "$PSScriptRoot/clear-budget-all.json" -Encoding utf8
if($entries.Count -ne 122 -or $bad.Count){throw 'Incomplete or regressed budget'}
Write-Output '122/122 camera budgets complete, draw delta0 and triangle delta0 required below.'
$entries|Group-Object totalDrawDelta,totalTriangleDeltaPercent|Select-Object Count,Name

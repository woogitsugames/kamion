param([string]$Source='art-source/world/props/street_props.glb',
      [string]$Output='artifacts/light-r6/lamp-glb-before-regeneration.json')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $repo
$stream=[IO.File]::OpenRead((Resolve-Path -LiteralPath $Source))
try{
    $reader=[IO.BinaryReader]::new($stream)
    $magic=$reader.ReadUInt32();$version=$reader.ReadUInt32();$total=$reader.ReadUInt32()
    $jsonLength=$reader.ReadUInt32();$chunkType=$reader.ReadUInt32()
    if($magic -ne 0x46546c67 -or $version -ne 2 -or $chunkType -ne 0x4e4f534a -or $total -ne $stream.Length){throw 'Unexpected GLB header'}
    if($jsonLength -gt 4MB){throw 'Refuse unexpectedly large JSON metadata in this lightweight inspection'}
    $document=[Text.Encoding]::UTF8.GetString($reader.ReadBytes($jsonLength))|ConvertFrom-Json
}finally{$stream.Dispose()}
$rows=@()
foreach($node in $document.nodes|Where-Object {$_.name -like 'lamp*' -and $_.name -notlike '*.col'}){
    if($null -eq $node.mesh){throw 'Lamp node has no mesh'}
    $slots=@();$submesh=0
    foreach($primitive in $document.meshes[$node.mesh].primitives){
        $position=$document.accessors[$primitive.attributes.POSITION]
        $indices=$document.accessors[$primitive.indices]
        $slots+=@{submesh=$submesh;materialIndex=$primitive.material;material=$document.materials[$primitive.material].name;
            vertices=$position.count;positionComponentType=$position.componentType;indices=$indices.count;
            min=$position.min;max=$position.max}
        $submesh++
    }
    $rows+=@{node=$node.name;mesh=$node.mesh;nodeTranslation=$node.translation;nodeRotation=$node.rotation;nodeScale=$node.scale;
        lensSlots=@($slots|Where-Object material -Like 'lamp_glass*');slots=$slots}
}
@{scope='GLB metadata before regeneration only. Presence and accessor bounds do not prove imported Unity binding, selected LOD, depth visibility or pixel emission.';
  source=$Source;sourceSha=(Get-FileHash -LiteralPath $Source).Hash;jsonBytes=$jsonLength;nodes=$rows
}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $Output -Encoding utf8
Write-Output "Inspected $($rows.Count) lamp mesh nodes; missing lens primitive count=$(@($rows|Where-Object {$_.lensSlots.Count -eq 0}).Count)"

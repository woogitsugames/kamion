$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$refs=(Get-Content Data/Regions/bialystok-industrial-c/sbs_references.json -Raw|ConvertFrom-Json).references
$folder="$PSScriptRoot/reference-pairs"
New-Item -ItemType Directory -Force $folder|Out-Null
$inventory=@()
foreach($id in @('sbs-g3-a-2948595898752384','sbs-g3-a-303305168125936','sbs-g3-a-cm92458760')){
    $ref=$refs|Where-Object camera -eq $id
    if($null -eq $ref){throw 'Missing reference'}
    $wet=$id -eq 'sbs-g3-a-cm92458760'
    $photo=if($wet){$ref.photo}else{$ref.comparison_photo}
    if(-not(Test-Path -LiteralPath $photo)){throw "Missing photo$photo"}
    $sourceHash=(Get-FileHash -LiteralPath $photo).Hash
    if(-not $wet -and $sourceHash -ne $ref.comparison_sha256){throw 'Rectified photo hash differs from the manifest'}
    foreach($tier in @('Low','High')){
        $render=if($wet){"$PSScriptRoot/baseline/$tier-wet1-photo/$id.png"}else{"$PSScriptRoot/clear-final/$tier/$id.png"}
        if(-not(Test-Path -LiteralPath $render)){throw 'Missing render'}
        $pair="$folder/$tier-$id.jpg"
        $warning=if($wet){'Niedopasowana poza C: tylko wyglad mokrego podloza; baseline FAIL, bez nowego presetu.'}else{'Ujecie robocze, inne warunki swiatla. Ocena horyzontu, bez fotometrii i zaliczenia bramki.'}
        $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB',
            '(',$photo,'-resize','478x269','-background','#202020','-gravity','center','-extent','478x269',
                '-gravity','south','-splice','0x24','-fill','white','-pointsize','11','-annotate','0',"Foto: $($ref.author), $($ref.license)",')',
            '(',$render,'-resize','478x269','-background','#202020','-gravity','center','-extent','478x269',
                '-gravity','south','-splice','0x24','-fill','white','-pointsize','11','-annotate','0',"Render: $tier / $id",')',
            '+append','+repage','-gravity','south','-background','#202020','-splice','0x24','-fill','white','-pointsize','12','-annotate','0',$warning,$pair)
        & magick @args
        if($LASTEXITCODE){throw 'Pair generation failed'}
        $width=& magick identify -format '%w' $pair
        if([int]$width -ne 956){throw 'Pair exceeds the review width'}
        $inventory+=@{pair=$pair;pair_sha256=(Get-FileHash -LiteralPath $pair).Hash;width=[int]$width;photo=$photo;photo_sha256=$sourceHash;
            render=$render;render_sha256=(Get-FileHash -LiteralPath $render).Hash;author=$ref.author;license=$ref.license;license_url=$ref.license_url;
            page_url=$ref.page_url;captured_at=$ref.captured_at;camera=$id;scope=$warning;photometric_use=$false}
    }
}
$inventory|ConvertTo-Json -Depth 6|Set-Content "$folder/sources.json" -Encoding utf8
@('Pary fotograficzne rundy 3, po 956 px szerokości. Zdjęcia zachowują proporcje; dopasowano je przez skalowanie i ewentualne pasy, bez kadrowania.',
'Mapillary: picturehoover i grobin, CC BY-SA 4.0. Commons: Rakoon, CC BY 3.0. Dokładne strony źródeł, licencje i hasze są w sources.json.',
'Pary Mapillary służą ocenie wyglądu nieba, bez zaliczenia pozy lub bramki. Commons pokazuje błędną pozę C: wyłącznie jakościowe odniesienie do mokrej nawierzchni. Mokry render jest odrzuconym stanem bazowym, nie nowym presetem.')|Set-Content "$folder/README.md" -Encoding utf8


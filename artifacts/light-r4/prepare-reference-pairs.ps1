$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$sources=Get-Content artifacts/light-r2/reference-pairs/sources.json -Raw|ConvertFrom-Json
$folder="$PSScriptRoot/reference-pairs";New-Item -ItemType Directory -Force $folder|Out-Null
$inventory=@();$index=0
foreach($source in $sources){
    $photo=Join-Path 'Data/raw/refs/objects/dusk-sodium/commons-search' $source.file
    if((Get-FileHash -LiteralPath $photo).Hash -ne $source.sha256){throw 'Source photo changed'}
    $id=@('route-putry-approach','r10_block_3','stretch-05-docks')[$index];$index++
    foreach($tier in @('Low','High')){
        $render="$PSScriptRoot/final-v2/$tier-night/$id.png"
        $pair="$folder/night-$index-$tier.jpg"
        $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB',
            '(',$photo,'-resize','478x269','-background','#202020','-gravity','center','-extent','478x269','-gravity','south','-splice','0x22',
                '-fill','white','-pointsize','11','-annotate','0',"Foto: Rakoon, CC0, $($source.captured_at)",')',
            '(',$render,'-resize','478x269','-background','#202020','-gravity','center','-extent','478x269','-gravity','south','-splice','0x22',
                '-fill','white','-pointsize','11','-annotate','0',"Render Night: $tier / $id",')',
            '+append','+repage','-gravity','south','-background','#202020','-splice','0x24','-fill','white','-pointsize','11','-annotate','0',
            'Inne miejsce, pora i sezon. Tylko hierarchia swiatla; bez dopasowania pozy lub fotometrii.',$pair)
        & magick @args
        if($LASTEXITCODE){throw 'Reference pair generation failed'}
        $width=& magick identify -format '%w' $pair
        if([int]$width -ne 956){throw 'Pair width mismatch'}
        $inventory+=@{pair=$pair;pair_sha256=(Get-FileHash -LiteralPath $pair).Hash;width=[int]$width;photo=$photo;photo_sha256=$source.sha256;
            render=$render;render_sha256=(Get-FileHash -LiteralPath $render).Hash;author=$source.author;license=$source.license;page_url=$source.page_url;
            captured_at=$source.captured_at;scope='Different place/time/season, winter city reference only; no pose calibration, geometry or photometry claim';photometric_use=$false}
    }
}
$inventory|ConvertTo-Json -Depth 6|Set-Content "$folder/sources.json" -Encoding utf8
@('Referencje nocnej hierarchii światła: Rakoon, CC0, lokalne pliki o haszach zgodnych z manifestem r2. Pochodzenie wcześniej sprawdzone w r2; w r4 sprawdzono lokalną integralność.',
'Każda para ma956px szerokości, zachowuje proporcje przez skalowanie i pasy, bez kadrowania. Zdjęcia przedstawiają inne miejsca, porę i sezon (zimowy Białystok), z dekoracjami i oświetlonymi witrynami.',
'To odniesienie jakościowe. Nie dowodzi zgodności pozy, fotometrii, jasności telefonów ani pełnego wyglądu nocy. Doki i okna renderu nadal wymagają pracy; poprawka r4 ogranicza jedynie nasycenie ciemnych powierzchni.')|Set-Content "$folder/README.md" -Encoding utf8

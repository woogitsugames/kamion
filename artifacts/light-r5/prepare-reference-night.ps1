$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$sources=Get-Content artifacts/light-r2/reference-pairs/sources.json -Raw|ConvertFrom-Json
$folder="$PSScriptRoot/reference-night";New-Item -ItemType Directory -Force $folder|Out-Null
$inventory=@();$index=0
foreach($source in $sources){
    $photo=Join-Path 'Data/raw/refs/objects/dusk-sodium/commons-search' $source.file
    if((Get-FileHash -LiteralPath $photo).Hash -ne $source.sha256){throw 'Source photo changed'}
    $id=@('route-putry-approach','r10_block_3','stretch-05-docks')[$index];$index++
    foreach($tier in @('Low','High')){
        $render="$PSScriptRoot/final-native-v2/$tier-night/$id.png"
        $pair="$folder/night-$index-$tier.jpg"
        $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB',
            '(',$photo,'-resize','478x269','-background','#202020','-gravity','center','-extent','478x269','-gravity','south','-splice','0x22',
                '-fill','white','-pointsize','11','-annotate','0',"Foto: Rakoon, CC0, $($source.captured_at)",')',
            '(',$render,'-resize','478x269','-background','#202020','-gravity','center','-extent','478x269','-gravity','south','-splice','0x22',
                '-fill','white','-pointsize','11','-annotate','0',"Render Night: $tier (native Low / HDR High) / $id",')',
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
@('Pary r5 po956px, Rakoon CC0; hasze i strony sources.json.','Low: jawny eksperyment native32, High: HDR intermediate reference. Inne miejsca, pora i sezon; bez fotometrii i zaliczenia pozy. Nierowny rozklad swiatla, ciemne doki/okna i halo pozostaja otwarte.')|Set-Content "$folder/README.md" -Encoding utf8

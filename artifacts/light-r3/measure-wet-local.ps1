$ErrorActionPreference = 'Stop'
$result = @()
foreach ($tier in @('Low','High')) {
    foreach ($wet in @(0,1)) {
        foreach ($id in @('light-night-driver','sbs-g3-a-2948595898752384')) {
            $args = @('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB',
                "$PSScriptRoot/wet-local/$tier-wet$wet-off/$id.png",
                "$PSScriptRoot/wet-local/$tier-wet$wet-on/$id.png",
                '-compose','difference','-composite','-format','%[fx:mean*255] %[fx:maxima*255]','info:')
            $metric = & magick @args
            if ($LASTEXITCODE) { throw 'metric failed' }
            $result += @{tier=$tier; wetness=$wet; camera=$id; mean_abs_and_max_codevalue=$metric}
        }
    }
}
$result | ConvertTo-Json -Depth 5 | Set-Content "$PSScriptRoot/wet-local-pixel-deltas.json" -Encoding utf8
$result | ConvertTo-Json -Compress

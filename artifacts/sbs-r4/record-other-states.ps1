# Bounded metadata/file-hash binding; no image decoding, metrics or rendering.
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    if((& git branch --show-current).Trim() -ne 'gpt-sbs-r4'){throw 'Expected r4'}
    $zipPath=Join-Path $PSScriptRoot 'other-states-review-evidence.zip'
    if(Test-Path -LiteralPath $zipPath){throw 'Evidence archive already exists; do not overwrite'}
    $review=Get-Content (Join-Path $PSScriptRoot 'other-states-visual-inspection.json') -Raw | ConvertFrom-Json
    $request=Get-Content (Join-Path $PSScriptRoot 'recognition-native-request.json') -Raw | ConvertFrom-Json
    $full=Get-Content (Join-Path $PSScriptRoot 'full-render-completed.json') -Raw | ConvertFrom-Json
    if($review.status -ne 'COMPLETE' -or $review.count -ne 75 -or $review.inspections.Count -ne 75 -or $review.missing_camera_ids.Count -or $review.capture_head -ne $full.git_sha -or $review.upstream_ADR0130_present -ne $false){throw 'Incomplete/stale review'}
    $sources=@{};foreach($row in $request.rows){if($sources.ContainsKey($row.camera)){throw 'Duplicate source'};$sources[$row.camera]=$row}
    if($sources.Count -ne 25){throw 'Expected 25 eligible sources'}
    $states=@('Low-clear','High-clear','High-overcast');$captured=@{}
    foreach($state in $states){
        $captured[$state]=@{}
        foreach($file in Get-ChildItem (Join-Path $PSScriptRoot ('evidence/renders/'+$state)) -Filter 'capture-*.json'){
            $capture=Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
            if($capture.git_sha -ne $full.git_sha -or $capture.status -ne 'OK' -or ($capture.tier+'-'+$capture.lighting) -ne $state){throw 'Stale capture'}
            foreach($entry in $capture.render_sha256.PSObject.Properties){if($captured[$state].ContainsKey($entry.Name)){throw 'Duplicate capture'};$captured[$state][$entry.Name]=$entry.Value}
        }
    }
    $seen=[Collections.Generic.HashSet[string]]::new();$hashes=@{}
    function File-Hash($path){if(!$hashes.ContainsKey($path)){$hashes[$path]=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()};$hashes[$path]}
    foreach($row in $review.inspections){
        $key=$row.state+'|'+$row.camera
        if($row.state -notin $states -or !$sources.ContainsKey($row.camera) -or !$seen.Add($key) -or $row.viewed -ne $true){throw 'Invalid review roster'}
        $expectedRaw=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('evidence/renders/'+$row.state+'/'+$row.camera+'.png')))
        if([IO.Path]::GetFullPath($row.raw_path) -ne $expectedRaw -or [IO.Path]::GetFullPath($row.photo_path) -ne [IO.Path]::GetFullPath($sources[$row.camera].photo_absolute)){throw 'Review path differs'}
        if((File-Hash $row.raw_path) -ne $row.render_sha256 -or $captured[$row.state][$row.camera] -ne $row.render_sha256){throw 'Raw hash differs'}
        if((File-Hash $row.photo_path) -ne $row.comparison_sha256 -or $sources[$row.camera].comparison_sha256 -ne $row.comparison_sha256){throw 'Photo hash differs'}
    }
    foreach($state in $states){foreach($camera in $sources.Keys){if(!$seen.Contains($state+'|'+$camera)){throw 'Missing pair'}}}
    [ordered]@{status='VERIFIED';recorded_at=(Get-Date -Format o);scope='Exact file hashes and capture/request roster binding of independent visual inspection; not a new D51 assessment';raw_count=75;unique_photo_count=25;unique_files_hashed=$hashes.Count;capture_head=$full.git_sha;review_json_sha256=(File-Hash (Join-Path $PSScriptRoot 'other-states-visual-inspection.json'));review_md_sha256=(File-Hash (Join-Path $PSScriptRoot 'OTHER-STATES-VISUAL-REVIEW.md'));request_sha256=(File-Hash (Join-Path $PSScriptRoot 'recognition-native-request.json'))} | ConvertTo-Json -Depth 7 | Set-Content (Join-Path $PSScriptRoot 'other-states-review-recorded.json') -Encoding utf8
    $names=@('OTHER-STATES-VISUAL-REVIEW.md','other-states-visual-inspection.json','recognition-native-request.json','other-states-review-recorded.json')
    $archive=[IO.Compression.ZipFile]::Open($zipPath,[IO.Compression.ZipArchiveMode]::Create)
    try {foreach($name in $names){[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,(Join-Path $PSScriptRoot $name),$name) | Out-Null}} finally {$archive.Dispose()}
    $entries=@();$archive=[IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        if($archive.Entries.Count -ne $names.Count){throw 'Archive roster differs'}
        foreach($name in $names){
            $entry=$archive.GetEntry($name);if(!$entry){throw 'Missing archive entry'}
            $stream=$entry.Open();try {$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream)).ToLowerInvariant()} finally {$stream.Dispose()}
            $source=Join-Path $PSScriptRoot $name
            if($entry.Length -ne (Get-Item -LiteralPath $source).Length -or $digest -ne (File-Hash $source)){throw 'Archive entry bytes differ'}
            $entries += [ordered]@{entry=$name;bytes=$entry.Length;sha256=$digest}
        }
    } finally {$archive.Dispose()}
    [ordered]@{verified_at=(Get-Date -Format o);zip_sha256=(File-Hash $zipPath);entries=$entries} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $PSScriptRoot 'other-states-review-evidence.json') -Encoding utf8
    'VERIFIED 75 raw, 25 photos, exact four-entry review archive; no image decoding.'
} finally {Pop-Location}

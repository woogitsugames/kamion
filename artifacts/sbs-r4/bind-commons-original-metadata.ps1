# Bounded I/O and SHA only: no Python, image decoding, or source/reference writes.
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$out=Join-Path $PSScriptRoot 'source-verification'
New-Item -ItemType Directory -Force $out | Out-Null
$api='https://commons.wikimedia.org/w/api.php?action=query&format=json&pageids=109685822%7C92458760&prop=imageinfo&iiprop=url%7Csha1%7Ctimestamp%7Csize%7Cmetadata&iiurlwidth=3840'
$headers=@{'User-Agent'='Kamion-SBS-reference-audit/1.0 (existing thumbnail binding)'}
$refs=(Get-Content (Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Raw | ConvertFrom-Json).references
$receipt=[ordered]@{started_at=(Get-Date -Format o);query_url=$api;status='RUNNING';scope='Existing Commons thumbnails, bounded I/O and hash only; no pose approval';rows=@()}
try {
    $before=Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 25
    $before | ConvertTo-Json -Depth 40 | Set-Content (Join-Path $out 'metadata-before.json') -Encoding utf8
    foreach($prop in $before.query.pages.PSObject.Properties){
        $page=$prop.Value;$info=@($page.imageinfo)[0];$id='cm'+$page.pageid
        $ref=@($refs | Where-Object camera -eq ('sbs-g3-a-'+$id))
        if($ref.Count -ne 1){throw 'Ambiguous local reference'}
        $uri=[uri]$info.thumburl
        if($uri.Scheme -ne 'https' -or $uri.Host -notin @('upload.wikimedia.org','thumb.wikimedia.org') -or $uri.AbsolutePath -notmatch '/thumb/.+\.jpg/'){throw 'Unexpected thumbnail source'}
        if($info.thumbwidth -ne $ref[0].width -or $info.thumbheight -ne $ref[0].height){throw 'Thumbnail size differs from comparison reference'}
        $dest=Join-Path $out ($id+'-current.jpg')
        # Existing references are 3840x2160 thumbnails, not the 1280px Unity raws.
        # Keep only in ignored artifacts, never stage images.
        Invoke-WebRequest -Uri $uri -Headers $headers -OutFile $dest -TimeoutSec 25 -MaximumRedirection 3
        if((Get-Item -LiteralPath $dest).Length -gt 8MB){throw 'Unexpected thumbnail size'}
        $local=Join-Path $root $ref[0].comparison_photo
        $localHash=(Get-FileHash -LiteralPath $local).Hash.ToLowerInvariant()
        if($localHash -ne $ref[0].comparison_sha256){throw 'Local comparison source changed'}
        $remoteHash=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant()
        $receipt.rows+=@{id=$id;page_url=('https://commons.wikimedia.org/?curid='+$page.pageid);original_sha1=$info.sha1;original_timestamp=$info.timestamp;thumbnail_url=$uri.AbsoluteUri;thumbnail_bytes=(Get-Item -LiteralPath $dest).Length;local_comparison_sha256=$localHash;download_sha256=$remoteHash;exact_thumbnail_match=($localHash -eq $remoteHash);width=$info.thumbwidth;height=$info.thumbheight}
    }
    if($receipt.rows.Count -ne 2){throw 'Incomplete source roster'}
    $after=Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 25
    $after | ConvertTo-Json -Depth 40 | Set-Content (Join-Path $out 'metadata-after.json') -Encoding utf8
    foreach($prop in $before.query.pages.PSObject.Properties){
        $old=@($prop.Value.imageinfo)[0];$new=@($after.query.pages.($prop.Name).imageinfo)[0]
        foreach($key in @('sha1','timestamp','width','height','thumburl','thumbwidth','thumbheight')){if($old.$key -ne $new.$key){throw ('Original version or thumbnail changed: '+$key)}}
        if(($old.metadata | ConvertTo-Json -Depth 30 -Compress) -ne ($new.metadata | ConvertTo-Json -Depth 30 -Compress)){throw 'EXIF changed during source verification'}
    }
    $receipt.status=if(@($receipt.rows | Where-Object {!$_.exact_thumbnail_match}).Count){'THUMBNAIL_BYTES_DIFFER'}else{'EXACT_THUMBNAILS_AND_STABLE_SOURCE_METADATA'}
    $receipt.metadata_before_sha256=(Get-FileHash (Join-Path $out 'metadata-before.json')).Hash.ToLowerInvariant()
    $receipt.metadata_after_sha256=(Get-FileHash (Join-Path $out 'metadata-after.json')).Hash.ToLowerInvariant()
} catch {
    $receipt.status='UNAVAILABLE_OR_UNBOUND'
    $receipt.error_class=$_.Exception.GetType().FullName
    $receipt.safe_reason=$_.Exception.Message
} finally {
    $receipt.completed_at=Get-Date -Format o
    $receipt | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $out 'binding.json') -Encoding utf8
}
Write-Output $receipt.status

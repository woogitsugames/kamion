$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$root='artifacts/cab-r1/cc0-prep'
New-Item -ItemType Directory -Force $root | Out-Null
$rows=@()
foreach ($asset in @('brown_leather','fabric_leather_02')) {
    $meta=Get-Content "artifacts/cab-r1/cc0-$asset-files.json" -Raw | ConvertFrom-Json
    foreach ($role in @('Diffuse','nor_gl','Rough')) {
        $kind=if ($role -eq 'nor_gl') { 'png' } else { 'jpg' }
        $file=$meta.$role.'2k'.$kind
        if (-not $file.url) { throw "Missing official file for $asset $role" }
        $path=Join-Path $root ([System.IO.Path]::GetFileName([uri]$file.url))
        if (-not (Test-Path -LiteralPath $path)) {
            & curl.exe --fail --location --silent --show-error --max-time 60 --output $path $file.url
            if ($LASTEXITCODE -ne 0) { throw "Download failed: $asset $role" }
        }
        $hash=(Get-FileHash -LiteralPath $path -Algorithm MD5).Hash.ToLowerInvariant()
        if ($hash -ne $file.md5 -or (Get-Item -LiteralPath $path).Length -ne $file.size) { throw "Checksum/size mismatch: $path" }
        $rows+= [pscustomobject]@{asset=$asset;role=$role;file=$path;bytes=$file.size;md5=$hash;url=$file.url;status='downloaded, not integrated'}
    }
}
$rows | ConvertTo-Json -Depth 5 | Set-Content "$root/downloads.json" -Encoding utf8
Write-Output 'Six official maps verified; not integrated.'

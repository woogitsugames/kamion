$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$main='C:\Users\matma\Documents\Claude\kamion'
if($root -ne (Join-Path $main '.claude/worktrees/gpt-sbs')){throw 'Unexpected worktree'}
Push-Location $root
try {
    if((& git branch --show-current).Trim() -ne 'gpt-sbs-r4'){throw 'Expected r4'}
    $rows=@()
    $logs=Join-Path $root 'artifacts/sbs-delivery-logs'
    New-Item -ItemType Directory -Force $logs | Out-Null
    foreach($relative in @('Data/raw/derived','Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans','game/Assets/_Generated')) {
        $source=Join-Path $main $relative;$target=Join-Path $root $relative
        if((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Cache destination must be private: $relative"}
        $name=$relative.Replace('/','-')
        & robocopy $source $target /E /R:1 /W:1 /NFL /NDL /NP "/LOG:$(Join-Path $logs ('r4-prepare-'+$name+'.log'))" | Out-Null
        $code=$LASTEXITCODE
        if($code -ge 8){throw "Cache copy failed $relative, exit$code"}
        $rows += [ordered]@{path=$relative;robocopy_exit_code=$code;private_destination=$true}
    }
    & git lfs checkout *> artifacts/sbs-r4/lfs-checkout.log
    if($LASTEXITCODE -ne 0){throw 'LFS checkout failed'}
    $mergeHead=(& git log -1 --merges --format=%H).Trim()
    $mergedMain=(& git rev-parse "$mergeHead^2").Trim()
    if($LASTEXITCODE -ne 0 -or $mergedMain -notmatch '^[a-f0-9]{40}$'){throw 'Cannot bind merged main'}
    [ordered]@{completed_at=(Get-Date -Format o);source_head=(& git rev-parse HEAD).Trim();merge_commit=$mergeHead;merged_main=$mergedMain;copies=$rows;lfs_checkout_exit_code=0;note='Caches refreshed read-only from main; no Library copy, no junction target writes.'} | ConvertTo-Json -Depth 6 | Set-Content artifacts/sbs-r4/preparation-completed.json -Encoding utf8
} finally {Pop-Location}

param(
    # Fresh (default): detached checkout of the main base, build_world + import + renders with MAIN code, then back to the branch.
    # Reuse: no Unity - copies artifacts/c-regen-s22/after/* (renders of the state that is in main now) as "before".
    #        Caveats: s22 has no Low overcast / Gate3 cells, and main got spawn-fix 0262 afterwards (truck start pose moved).
    [ValidateSet('Fresh', 'Reuse')] [string]$Mode = 'Fresh',
    [string]$BaseSha = ''
)
# c-regen2-s23 stage 2, step 1: "before" renders from main. Why not just render what main has on disk: main's
# Data/raw/derived/bialystok-industrial-c (glb 15.11 16:54) and _Generated scene (16:59) are OLDER than the committed
# generated/ of main (c-regen-s22 regenerated in its own worktree, 20:48-21:15); a stale "before" spoiled the attribution in s22.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/before" 'before.status'
if ($Mode -eq 'Reuse') {
    foreach ($r in $Regions) { robocopy "$Main\artifacts\c-regen-s22\after\$r" "$Art\before\$r" /E /NFL /NDL /NJH /NJS /NP | Out-Null; "reuse $r robocopy=$LASTEXITCODE" | Add-Content $St }
    'source: artifacts/c-regen-s22/after (main state before spawn-fix 0262); no Low-overcast, no Gate3 cells' | Add-Content $St
    Finish 'before.done'; return
}
$branch = (git branch --show-current).Trim()
if (-not $BaseSha) { $BaseSha = (git merge-base HEAD origin/main).Trim() }
$dirty = git status --porcelain --untracked-files=no
if ($dirty -or -not $branch) { "ABORT: tracked changes in the worktree or detached HEAD (branch='$branch')" | Add-Content $St; $dirty | Add-Content $St; exit 2 }
"branch=$branch base=$BaseSha" | Add-Content $St
# the tools are tracked on the branch only: the base checkout removes them from disk, so run the matrix from an untracked copy
$tools = "$Wt\$Art\before\_tools"; New-Item -ItemType Directory -Force $tools | Out-Null
Copy-Item "$PSScriptRoot\_common.ps1", "$PSScriptRoot\vqa.ps1" $tools -Force
Slot-Acquire heavy      # wait for the slot on the branch; leave it only when the work can start
git checkout -q --detach $BaseSha; $co = $LASTEXITCODE; "checkout-base exit=$co $(git rev-parse --short=9 HEAD)" | Add-Content $St
if ($co -ne 0) { Slot-Release heavy; exit 2 }
try {
    try { foreach ($r in $Regions) { Step "before-build_world-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r } } }
    finally { Slot-Release heavy }
    # determinism evidence: main code on main data must reproduce the committed generated/ (s22: only fidelity inputs differed)
    git status --porcelain *> "$O/before-git-status-after-build.txt"
    Slot-Acquire unity
    try {
        foreach ($r in $Regions) { Step "before-import-$r" { pwsh -NoProfile -File scripts/import-region.ps1 -Region $r } }
        & "$tools\vqa.ps1" -Tag before -NoSlot     # appends its own status file: before/vqa.status
    } finally { Slot-Release unity }
} finally {
    Set-Location $Wt
    Restore-UnitySideEffects
    git status --porcelain *> "$Art/before/before-git-status-end.txt"
    git checkout -q -- . ; git checkout -q $branch
    "checkout-branch exit=$LASTEXITCODE $(git rev-parse --short=9 HEAD) $(git branch --show-current)" | Add-Content "$Art/before/before.status"
}
"DONE $(Get-Date -Format s)" | Add-Content "$Art/before/before.status"; 'done' | Set-Content "$Art/before/before.done"

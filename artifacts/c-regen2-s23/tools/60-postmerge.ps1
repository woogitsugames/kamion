# c-regen2-s23 stage 2, step 5 (only when main moved world code since the regeneration): after `git merge origin/main`
# rebuild C + Dojlidy, refresh fidelity, selected pytest. Expected diff: only generated/fidelity_qa.json inputs_sha256.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/postmerge" 'postmerge.status'
Remove-Item "$O/postmerge.done" -ErrorAction SilentlyContinue
Assert-Branch
Slot-Acquire heavy
try {
    foreach ($r in $Regions) {
        Step "build_world-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
        Step "fidelity-$r" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r }
    }
    Step 'budget' { uv run --project tools/worldgen python "$Art/tools/30-budget.py" }
    Step 'pytest-sel' { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider -rfEs -k "0236 or 0237 or 0242 or 0219 or 0216 or far_field or budget_0221 or gate3 or g3b or dojbld or dojind or report_not_stale or streetscape or world_v31 or forest_0187 or tunnel or rail or determinism" }
} finally { Slot-Release heavy }
git status --porcelain *> "$O/git-status-after-postmerge.txt"
git diff --stat *> "$O/git-diff-stat.txt"
Finish 'postmerge.done'

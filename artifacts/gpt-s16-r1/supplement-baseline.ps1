$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$library = 'art-source/world/props/street_props.glb'
$candidate = 'artifacts/gpt-s16-r1/candidate-b-street_props.glb'
Copy-Item -LiteralPath $library -Destination $candidate
try {
    Copy-Item -LiteralPath artifacts/gpt-s16-r1/baseline-street_props.glb -Destination $library
    Add-Content artifacts/gpt-s16-r1/STATUS.md "`nTYMCZASOWA BIBLIOTEKA BASELINE dla dodatkowych kamer. NASTĘPNY KROK awaryjny: Copy-Item artifacts/gpt-s16-r1/candidate-b-street_props.glb art-source/world/props/street_props.glb; pwsh artifacts/gpt-s16-r1/import-only.ps1 -Label restore-candidate"
    git add -f artifacts/gpt-s16-r1/STATUS.md
    git commit -m 'wip(s16): mark temporary baseline import for visibility supplement'
    Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
    Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
    & pwsh artifacts/gpt-s16-r1/import-only.ps1 -Label clear-baseline
    if ($LASTEXITCODE -ne 0) { throw 'Supplement baseline import failed' }
    & pwsh artifacts/gpt-s16-r1/render-clear.ps1 -Stage before
    if ($LASTEXITCODE -ne 0) { throw 'Supplement baseline render failed' }
} finally {
    Copy-Item -LiteralPath $candidate -Destination $library
    & pwsh artifacts/gpt-s16-r1/import-only.ps1 -Label restore-candidate
    if ($LASTEXITCODE -ne 0) { throw 'Candidate recovery import failed' }
    Add-Content artifacts/gpt-s16-r1/STATUS.md "`nPrzywrócono bibliotekę i import kandydata B po dodatkowym baseline."
    git add -f artifacts/gpt-s16-r1/STATUS.md
    git commit -m 'wip(s16): restore atlas candidate after matched visibility supplement'
    Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
    Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
}

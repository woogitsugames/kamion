# Capture/review preparation only. Never writes an approval or declares visual acceptance.
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$repo='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
Set-Location $repo
$round=Join-Path $repo 'artifacts/vegetation-r4'
$approvalPath=Join-Path $round 'approved-probe.json'
if (-not (Test-Path -LiteralPath $approvalPath)) { throw 'No approved-probe.json; no full matrix or analysis launched.' }
$approval=Get-Content -LiteralPath $approvalPath -Raw | ConvertFrom-Json
if ($approval.verdict -ne 'PASS_FOR_FULL_MATRIX' -or $approval.candidate -notmatch '^candidate-[a-z][a-z0-9-]*$') {
    throw 'Probe approval missing or malformed; no capture launched.'
}
if ($approval.probe -ne ($approval.candidate -replace '^candidate-','probe-')) { throw 'Candidate/probe mismatch' }
foreach ($name in @("SELF-REVIEW-$($approval.probe).md","VISUAL-CRITIC-$($approval.probe).md")) {
    if (-not (Test-Path -LiteralPath (Join-Path $round $name))) { throw "Missing actual review: $name" }
}
if ((git branch --show-current).Trim() -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
if (@(Get-ChildItem (Join-Path $round 'after') -Recurse -Filter *.png -ErrorAction SilentlyContinue).Count) {
    throw 'After PNG already exist. Inspect live handle/results before any manual recovery; no implicit overwrite.'
}
$snapshotPath=Join-Path $round "snapshot-$($approval.candidate)/sha256.json"
$snapshot=Get-Content -LiteralPath $snapshotPath -Raw | ConvertFrom-Json
$snapshotHash=(Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($snapshotHash -ne $approval.snapshot_sha256) { throw 'Approval refers to a different snapshot' }
function Assert-CaptureInputs {
    foreach ($set in @('source_files','files')) {
        foreach ($item in $snapshot.$set.PSObject.Properties) {
            $path=Join-Path $repo $item.Name
            if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value) {
                throw "Input changed after approved probe: $($item.Name)"
            }
        }
    }
    foreach ($item in $snapshot.instance_files.PSObject.Properties) {
        $path=Join-Path $repo "Data/raw/derived/bialystok-industrial-c/world/$($item.Name)"
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value) {
            throw "Instance changed after approved probe: $($item.Name)"
        }
    }
}
Assert-CaptureInputs
. ./artifacts/vegetation-r4/checkpoint.ps1
Add-Content artifacts/vegetation-r4/STATUS.md "Mała próba $($approval.probe) dopuszczona do pełnej macierzy. Piny snapshotu zgodne; to nie końcowa akceptacja. Dalej 67 kamer kontrolnych i 25 fotograficznych w czterech warunkach."
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 zatwierdzona proba przed pelna macierza' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/approved-probe.json')
# Each wrapper acquires/releases the main Unity slot independently for every launch.
pwsh artifacts/vegetation-r4/render-matrix.ps1 -Stage after
if ($LASTEXITCODE -ne 0) { throw 'Full control matrix failed; inspect logs before recovery' }
pwsh artifacts/vegetation-r4/render-photos.ps1 -Stage after
if ($LASTEXITCODE -ne 0) { throw 'Full photographic matrix failed; inspect logs before recovery' }
Assert-CaptureInputs
$before=(Resolve-Path (Join-Path $round 'before')).Path
$after=(Resolve-Path (Join-Path $round 'after')).Path
$old=@(Get-ChildItem $before -Recurse -Filter *.png | Where-Object Name -NotLike '*_mask.png' | ForEach-Object { $_.FullName.Substring($before.Length+1) } | Sort-Object)
$new=@(Get-ChildItem $after -Recurse -Filter *.png | Where-Object Name -NotLike '*_mask.png' | ForEach-Object { $_.FullName.Substring($after.Length+1) } | Sort-Object)
if ($old.Count -ne 368 -or @(Compare-Object $old $new).Count) { throw 'Fresh frame set differs from all368 baseline frames' }
[ordered]@{candidate=$approval.candidate; probe=$approval.probe; snapshot_sha256=$snapshotHash; before_frames=$old.Count; after_frames=$new.Count; visual_accepted=$false} |
    ConvertTo-Json | Set-Content -Encoding utf8 artifacts/vegetation-r4/after-matrix-capture.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Pełna macierz ma wszystkie 368 odpowiadających baseline PNG. Piny wejść zachowane. Arkusze i koszty będą przygotowane przez heavy; nadal brak końcowej oceny wizualnej.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pelna macierz wyrenderowana' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/after-matrix-capture.json')
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$owner=(git branch --show-current).Trim()
pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 2
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition for full image analysis failed' }
try {
    $env:OPENBLAS_NUM_THREADS='1'
    $env:OMP_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    uv run --project tools/worldgen python artifacts/vegetation-r4/review_images.py *> artifacts/vegetation-r4/after-image-review.log
    if ($LASTEXITCODE -ne 0) { throw 'Full image evidence preparation failed' }
} finally { pwsh $slot -Release -Pool heavy -Owner $owner }
Add-Content artifacts/vegetation-r4/STATUS.md 'Pełne arkusze i pomiary przygotowane. Autor musi obejrzeć wszystkie 40 nowych arkuszy after i właściwe pary zdjęć; niezależny krytyk oraz sprawdzenie kosztów wszystkich kamer nadal wymagane. GIS/EditMode nie zostały tu uruchomione.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pelne dowody gotowe do obejrzenia' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/measurements.json','artifacts/vegetation-r4/stats-comparison.json','artifacts/vegetation-r4/after-image-review.log')
Set-Content -Encoding utf8 artifacts/vegetation-r4/after-approved.done 'Capture/evidence preparation only; no final visual or budget acceptance, no final GIS/EditMode yet.'

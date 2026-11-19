$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$main='C:\Users\matma\Documents\Claude\kamion'; Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seams-p3-s24'
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner seams-p3-s24-pytest *> artifacts/seams-p3-s24/logs/pytest-slot.log
uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider -n 6 *> artifacts/seams-p3-s24/logs/pytest-gis.log
$e=$LASTEXITCODE
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner seams-p3-s24-pytest *>> artifacts/seams-p3-s24/logs/pytest-slot.log
"exit=$e" | Set-Content artifacts/seams-p3-s24/pytest.status

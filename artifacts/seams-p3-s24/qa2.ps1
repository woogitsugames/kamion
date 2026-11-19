$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
Set-Location C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seams-p3-s24
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --json artifacts/seams-p3-s24/seams_pass2.json --md artifacts/seams-p3-s24/seams_pass2.md *> artifacts/seams-p3-s24/qa2.log
"exit=$LASTEXITCODE" | Set-Content artifacts/seams-p3-s24/qa2.status

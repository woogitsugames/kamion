$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
Set-Location C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24
pwsh -NoProfile -File C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Acquire -Pool heavy -Owner regen-wave-2-s24-pytest *> C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24\artifacts\regen-wave-2-s24\logs\pytest-slot.log
uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24\artifacts\regen-wave-2-s24\logs\pytest.log
$e=$LASTEXITCODE
pwsh -NoProfile -File C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Release -Pool heavy -Owner regen-wave-2-s24-pytest *>> C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24\artifacts\regen-wave-2-s24\logs\pytest-slot.log
Add-Content C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24\artifacts\regen-wave-2-s24\pytest.status "exit=$e"

param([string]$Stage = 'before')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
foreach ($tier in @('Low','High')) {
    foreach ($light in @('clear','overcast')) {
        & pwsh $slot -Acquire -Owner gpt-s16
        try {
            if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared after acquisition' }
            & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -OutputDir "artifacts/gpt-s16-r1/$Stage/$tier-$light" *> "artifacts/gpt-s16-r1/$Stage-$tier-$light.log"
            if ($LASTEXITCODE -ne 0) { throw "render failed: $Stage $tier $light" }
        } finally {
            git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
            & pwsh $slot -Release -Owner gpt-s16
        }
        @("# STATUS — gpt-s16 r1", (Get-Date -Format o), "Gałąź: $(git branch --show-current)",
          "Zapisano render $Stage/$tier-$light; liczby w stats.txt. Oględziny i recenzja pozostają otwarte.",
          'NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r1/STATUS.md', 'Gotowe do recenzji: NIE') |
            Set-Content artifacts/gpt-s16-r1/STATUS.md
        git add -f artifacts/gpt-s16-r1/STATUS.md "artifacts/gpt-s16-r1/$Stage/$tier-$light/stats.txt"
        git commit -m "wip(s16): record $Stage $tier $light camera capture"
        Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
        Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
    }
}

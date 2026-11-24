$a='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\rut-far-s24\artifacts\rut-far-s24'
$c='rg_0,rg_20,rg_40,rg_70,rg_100'
& pwsh -NoProfile -File "$a\vqa.ps1" -Label dist2-before -SkipImport -Cams $c *> "$a\run3-on.log"; "on exit=$LASTEXITCODE" | Out-File "$a\run3.status"
& pwsh -NoProfile -File "$a\vqa.ps1" -Label dist2-off -Probe off -SkipImport -Cams $c *> "$a\run3-off.log"; "off exit=$LASTEXITCODE" | Add-Content "$a\run3.status"
"DONE" | Add-Content "$a\run3.status"

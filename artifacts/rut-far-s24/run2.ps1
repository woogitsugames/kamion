$a='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\rut-far-s24\artifacts\rut-far-s24'
$c='rf_0,rf_20,rf_40,rf_70,rf_100'
& pwsh -NoProfile -File "$a\vqa.ps1" -Label dist-before -SkipImport -Cams $c *> "$a\run2-on.log"; "on exit=$LASTEXITCODE" | Out-File "$a\run2.status"
& pwsh -NoProfile -File "$a\vqa.ps1" -Label dist-off -Probe off -SkipImport -Cams $c *> "$a\run2-off.log"; "off exit=$LASTEXITCODE" | Add-Content "$a\run2.status"
"DONE" | Add-Content "$a\run2.status"

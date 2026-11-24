$a='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\rut-far-s24\artifacts\rut-far-s24'
& pwsh -NoProfile -File "$a\vqa.ps1" -Label before *> "$a\run1-before.log"; "before exit=$LASTEXITCODE" | Out-File "$a\run1.status"
& pwsh -NoProfile -File "$a\vqa.ps1" -Label before-off -Probe off -SkipImport *> "$a\run1-off.log"; "off exit=$LASTEXITCODE" | Add-Content "$a\run1.status"
"DONE" | Add-Content "$a\run1.status"

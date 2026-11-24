$a='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\rut-far-s24\artifacts\rut-far-s24'
& pwsh -NoProfile -File "$a\vqa.ps1" -Label after -SkipImport -Cams 'q_far,q_far2,rg_0,rg_20,rg_40,rg_70,rg_100' *> "$a\run4.log"; "after exit=$LASTEXITCODE" | Out-File "$a\run4.status"
"DONE" | Add-Content "$a\run4.status"

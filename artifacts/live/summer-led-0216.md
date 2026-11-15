# summer-led-0216 (ADR 0216) — live
- 15.11: worktree utworzony (gałąź summer-led-0216 z main a51ededa3). Orientacja: LP_Dusk ma już az 300°, clockHour 16:10 (listopad); k_Led globalne (1;0,93;0,82); rodziny lamp_old_* = szkło sodowe (knyszyn 216/479, knyszyn-w 72/167, bialystok-knyszynska 311/910); knyszyn-s 0 latarni; DK65 lamps:false w knyszyn/-s/-w.
- Plan: baseline render (przed build_world) -> profil regionu (lato, zegar 21:00, LED 4000 K) jako dane -> wariant LED słupa betonowego -> build_world knyszyn, knyszyn-w, bialystok-knyszynska -> import -> visual-qa.
- NASTĘPNY KROK: `pwsh scripts/visual-qa.ps1 -Scene WorldC ... ` baseline knyszyn + bialystok-knyszynska dusk/night Low/High do artifacts/summer-led-0216/before/ (sprawdź parametr regionu w scripts/visual-qa.ps1)

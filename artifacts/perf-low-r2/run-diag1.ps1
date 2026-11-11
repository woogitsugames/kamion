# ADR 0113 diag1: forest A/B (G3-B uncapped), PSO trace G3-B/G3-A + spike probe G3-A (capped 30). A16 only.
param([string]$Apk)
$d = $PSScriptRoot
$dev = 'RFGL34SJYDZ'
pwsh -NoProfile -File "$d/phone-diag.ps1" -Apk $Apk -OutTag diag1 -Segment B -Uncapped -Runs "ab_forest=rq_ab=forestfast;ab_veg=rq_ab=vegfast;ab_1pass=rq_ab=hlod1pass;ab_canopy=rq_ab=canopyfast;ab_aniso=rq_ab=veganiso"
pwsh -NoProfile -File "$d/phone-diag.ps1" -OutTag diag1 -Segment B -Runs "traceB=pso_trace=95 pso_tag=g3b"
pwsh -NoProfile -File "$d/phone-diag.ps1" -OutTag diag1 -Segment A -Runs "traceA=pso_trace=90 pso_tag=g3a;spikeA=spike_probe=1"
. (Join-Path (Split-Path (Split-Path $d)) 'scripts/env.ps1')
New-Item -ItemType Directory -Force "$d/pso" | Out-Null
& $Adb -s $dev shell ls /sdcard/Android/data/com.woogitsugames.kamion/files/ | Out-File "$d/pso/ls.txt"
foreach ($f in (Get-Content "$d/pso/ls.txt" | Where-Object { $_ -match 'graphicsstate' })) { & $Adb -s $dev pull "/sdcard/Android/data/com.woogitsugames.kamion/files/$($f.Trim())" "$d/pso/" }
"DIAG1 DONE" | Out-File "$d/diag1.done"

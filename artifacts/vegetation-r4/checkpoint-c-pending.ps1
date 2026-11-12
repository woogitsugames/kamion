$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_c_implemented_waiting_heavy'
$session.next_step='Live execution4178: focused40tests then conditional World/collision in same heavy; inspect handle/log before retry. Then candidate-c-probe.ps1 once, author eight sheets and critic. No final GIS until end of round.'
$session.state_authority='Source is B3/C; generated World and imported scene still rejected B2 until green-c-and-world.done. Source C hash in cap-study-c-cover.json; B2 snapshots/probes preserved. No acceptance of C yet.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Stan C zapisany: kod zawiera pokrywę B3, a wygenerowany i zaimportowany świat nadal przedstawia odrzucone B2. Sekwencja 4178 czeka na heavy; testy C i World jeszcze niepotwierdzone. Lekka analiza czterech rabat trwała 1,36 s i nie uruchamiała generatora świata ani testów. Najważniejsze ryzyka recenzji: szczotka pionowych kart, luki w pokrywie i wystające podstawy. To kryteria następnej próby wizualnej.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 stan kodu C i świata B2 zapisany' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-c-pending.ps1')

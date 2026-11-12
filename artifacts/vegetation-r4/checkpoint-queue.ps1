$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_a_waiting_heavy'
$session.production_changed=$true
$session.next_step='Live task 55526: focused GREEN then World and collision digest. After success snapshot candidate-a, compare_candidate.py, import-safe and probe-hedges. No parallel job with same heavy owner.'
$session.state_authority='Live task 55526 and STATUS.md; green-and-world.done only after all three successful stages.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Checkpoint kontroli pochodzenia zapisany 05283e1b. Pierwsza próba miała błędną nazwę pliku helper-syntax.json i zakończyła się bez commita; poprawiono na rzeczywisty powershell-syntax.json. Nie powtarzano testów ani generacji. Zadanie 55526 nadal żywe w kolejce heavy; pozostałe procesy i sloty pozostawiono bez zmian.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 utrwalony stan kolejki kandydata A' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-queue.ps1')

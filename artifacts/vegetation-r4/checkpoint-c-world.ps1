$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_c_world_running'
$session.next_step='Execution4178 owns heavy and runs World after40passed/11.56s, then collision digest in same slot. Inspect live handle and World log; do not restart. Only after green-c-and-world.done run candidate-c-probe.ps1 once.'
$session.state_authority='Source is B3/C. World regeneration is in progress; outputs may be mixed until terminal0 and done. Imported Unity scene remains B2. No C visual acceptance. B2 snapshots preserved.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'C uzyskało heavy około 13:48 po kolejce FIFO. Wszystkie 40 celowanych testów przeszło w 11,56 s. Sekwencja 4178 uruchomiła następnie World C i ma zdekodować kolizję w tym samym slocie, po czym go zwolnić. Nie uruchamiać importu podczas generacji; dane mogą być częściowo nadpisane. Zaimportowana scena nadal przedstawia B2. Brak jeszcze wyniku World C i oceny wyglądu C.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 czterdziesci testow C i regeneracja w toku' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-c-world.ps1')

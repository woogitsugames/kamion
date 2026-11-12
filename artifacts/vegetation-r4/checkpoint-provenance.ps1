$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
Add-Content artifacts/vegetation-r4/STATUS.md 'Przygotowano kontrolę kandydata: dokładne piny wejść, wszystkie 64 pliki instancji, dekodowana kolizja 64 chunków, niezmienny far field i liczby nasadzeń. Próba renderująca korzysta z bieżącego skryptu slotów main, więc respektuje rezerwacje priority. Składnia helperów sprawdzona; zadanie 55526 nadal oczekuje heavy, bez uruchomienia dodatkowej kopii.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 kontrola pochodzenia i rezerwacji próby' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/compare_candidate.py','artifacts/vegetation-r4/probe-hedges.ps1','artifacts/vegetation-r4/checkpoint-provenance.ps1','artifacts/vegetation-r4/powershell-syntax.json')


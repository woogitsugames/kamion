# Truck — runda 2

Start 12 listopada 2026 po przekazaniu rundy 1. Ten sam worktree, gałąź gpt-truck-r2. Merge main bez konfliktów: ca0be7c3, main 2c3939b22162659ea3ca42fb42be3d9a19cef2c2.

Krok 1: przeczytano aktualny protokół heavy, górę HANDOVER i zbiorczą recenzję s11. Nowa baza obejmuje inne materiały świata, roślinność, osobówki, tło i lusterka. Potrzebne są świeże wygenerowane wejścia i import przed baseline r2. Źródeł tych dziedzin nie zmieniamy. Skopiowano własne procedury do artifacts/truck-r2.

Zakres r2: zabrudzenia ciągnika i plandeki, progów i błotników. Najpierw kontrola _Dirt 0 / 0,5 / 1, potem wybór potwierdzonego odstępstwa od zdjęć. Bez pełnego GIS w trakcie. Następny krok: pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-r2/prepare-baseline.ps1.
Krok 2: przygotowano tymczasową kontrolę _Dirt 0 / 0,5 / 1 dla materiałów zewnętrza obu pojazdów. Adapter generuje wyłącznie ignorowany kod QA, sprawdza użyte materiały po renderze i przywraca JSON w finally. Kontrola nie jest zmianą produkcyjnego brudu; kompilacja i kadry dopiero po imporcie bazy. Następny krok: po prepare-baseline.ps1 uruchomić render-phase.ps1 -Stage before -Lighting overcast,clear, potem dirt-controls.ps1.
Krok 3: przygotowano trzy fotografie referencyjne maksymalnie 960 px z autorami, licencjami i ograniczeniami. Kontrole obejmą truck-34r, truck-side, truck-rear34 i truck-front w obu pogodach Low/High, tak aby ocenić plandekę, błotniki i dolną kabinę. Generator bazy nadal czeka na heavy; nie uruchomiono dodatkowych ciężkich zadań. Następny krok: monitorować prepare-baseline-console.log, po imporcie zapisać baseline i kontrole.

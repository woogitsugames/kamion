# STATUS — gpt-s16 r1
2026-11-12T23:00:00.1439232+01:00
Gałąź: gpt-s16-r1
Zapisano render before/High-overcast; liczby w stats.txt. Oględziny i recenzja pozostają otwarte.
NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r1/STATUS.md
Gotowe do recenzji: NIE

Bazowe 48 kamer ×4 wyrenderowane. Rozszerzam baseline o kanoniczne 30 kamer G3 oraz 36 prób blisko przełączeń wokół faktycznych instancji; stare, węższe logi zachowane jako baseline-base-*.log. NASTĘPNY KROK: pwsh artifacts/gpt-s16-r1/render.ps1 -Stage before

Wpięto konsolidację tylko LOD1/LOD2; LOD0 eksportuje te same bufory. Wspólne materials.py i WorldPbrMaterials.cs: wyłącznie nowy opt-in vehicle_lod_atlas. Importer obsługuje jawne końce LOD i alias LOD2 pojazdów placowych (ta sama geometria i jeden natywny mesh). 36/36 testów atlas/deposition/yard. Baseline rozszerzony nadal czeka na PHONE_RUN; manifest bazowy nie ma flag atlasu, więc nowy kod nie zmienia jego wyglądu.

W tle: candidate-world.ps1 (sesja 32203, pool heavy); rozszerzone before (9884) czekają na PHONE_RUN. Baseline _Generated jest zamrożony po poprawnym imporcie, generator kandydata pisze wyłącznie wejścia poza Assets; import after dopiero po wszystkich before. NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r1/after-world.log -Tail 8

Dodano EditMode: walidacja pasm i stałego cull, kontrakt UV atlasu oraz kontrola rzeczywistego importu (3 LOD, max 2 podsiatki daleko, ten sam natywny mesh/material aliasu placowych). Testy Unity jeszcze niewykonane — pełny EditMode po imporcie after.

Eksport atlasu respektuje out_dir: testowe biblioteki zapisują mapy w swoim textures, bez efektów ubocznych w globalnym art-source. W tle tylko generacja kandydata oraz kolejka before; brak importu after.

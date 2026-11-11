# ADR 0102 — strumień I
Worktree z main 9e6e9fde. Przeczytano wymagane zasady i recenzje; kopie lokalnych danych oraz junctiony referencji przygotowane. Bez telefonów/adb.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis -q

Audyt: QA bazowe 147 stopni >5 cm, max 1.087 m. Zdjęcie Mapillary p26 obejrzane (referencja lokalna). WIP: kontakt osi z widoczną siatką, fundament -1.25/+0.08 m, obejmy dopasowane do stożka; bez nowych materiałów. Wymiary WORKING_VALUE, ocena Unity nadal oczekuje PHONE_RUN.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis/test_furniture_r1.py -q

WIP r1: atlas zużycia lokalizowany wysokością (skany CC0 brushed_concrete/corrugated_iron_03), LOD starych lamp i obejmy, U-słupek tylko z tagu OSM, schodkowe przęsła z zakopanymi stopami słupków. Materiały wyłącznie addytywne furniture_*. PHONE_RUN nadal istnieje. Bazowe GIS nadal w toku (testy determinizmu).
NASTĘPNY KROK: uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c

GIS bazowe: 370 passed, 1 xfailed / 635.18 s. Regresje ADR0102: 6 passed. Korekta po audycie kodu: fundament -0.45/+0.08 m, lokalne przesunięcie lampy do 1.05 m przy ostrym uskoku zamiast głębokiego zakopania. Jawne wysokości na wiaduktach zachowane. Low starej betonowej lampy 105→91 tris, pozostałe porównane Low bez wzrostu slotów.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1

Regenerated baseline from 9e6e9fde; furniture source restored to branch HEAD.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Regeneracja bazowego kodu zakończona 297.2 s; QA odtwarza 147 / 1.087 m. W logu brak fallback=True. Dodano stałą kamerę zwykłego ogrodzenia OSM 590134608; kamery mają seat=file, tył znaku wyznaczony z yaw. Import Unity czeka na PHONE_RUN.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1

Dopracowano mapowanie atlasu: metry fizyczne (9 m atlas dla lamp, 0.9 m dla słupków) zamiast rozciągania strefy brudu z wysokością lampy. Istniejąca stopa otrzymała ten sam skan betonu przez addytywny materiał furniture_footing, bez dodatkowego slotu. Testy regresji: 6 passed.
NASTĘPNY KROK: czekać na PHONE_RUN; pipeline walidacji działa.

Przegląd współdzielonych helperów: terenowe stopy słupków ograniczone opcją ground_feet=True wyłącznie do nowego panel_fence. Bariery/ekrany korzystające z jawnego zb zachowują poprzednią geometrię; dedykowana regresja mostu 8 m przechodzi. Łącznie 7 nowych testów zielonych.
NASTĘPNY KROK: pipeline czeka na PHONE_RUN przed importem bazowym.

Produkty bazowe zachowane w ignorowanym Data/raw/derived/bialystok-industrial-c/furniture-r1-before. Build wariantu po zmianach w toku (build-after.log), bez Unity. Pipeline rozszerzony o wybieranie snapshotów, aby GIS i generację wykonać podczas blokady telefonu.
NASTĘPNY KROK: po build-after: python artifacts/furniture-r1/products.py save after; uv run --project tools/worldgen python -m pytest tests/gis -q

Build po zmianach 307.2 s, bez wzrostu błędów spójności dróg (65, identyczne kategorie jak baza). QA stopni 147→135, maksimum 1.087→0.517 m (najgorszy teraz sign_post). 100 lokalnych korekt podpór lamp; najgorsza pozostała rozbieżność w korektach 0.167 m. To relief podparcia, nie pomiar liczby wiszących obiektów. Produkty after zachowane poza gitem.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis -q

Audyt produktów: 388/388 chronionych prymitywów road_/bridge_/barrier_/marking identycznych bajtowo (POSITION/NORMAL/UV/COLOR/index), protected-geometry.json. Estymator 23 kamer: Low tris -0.3421%…-0.0047%, liczba materiałów bez zmian; to nie draws z Unity. GIS po zmianach trwa; nie uruchamiać drugiej kopii.
NASTĘPNY KROK: Get-Content artifacts/furniture-r1/pytest-after.log -Tail 10; po pytest-after.done uruchomić pwsh artifacts/furniture-r1/run-validation.ps1

Dodano do zaplanowanej walidacji istniejący Gate3Audit przed/po (Low, korytarz trasy 40 m): kontrola finalnych instancji po wszystkich filtrach usuwania/przesuwania, UV i materiałów. Nie opieramy werdyktu o kontakcie z ziemią wyłącznie na logu wstępnego osadzania.
NASTĘPNY KROK: po zakończeniu aktywnego GIS wznowić run-validation.ps1

GIS po zmianach: 377 passed, 1 xfailed / 538.42 s. Brak nowych porażek względem 370/1 bazowo. NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (import/audyt/rendery przed-po + EditMode; każdy start Unity za PHONE_RUN).

Blokada telefonu zwolniona; import bazowy w toku (przebudowa lokalnych PBR). Obejrzano blender-prototypes.png: odrębne sylwetki 12 m / betonowa 9 m / stalowa 8 m, stopy na płaszczyźnie, prawidłowy U-słupek. Blender ma jawnie przywrócone tinty z manifestu (GLB z teksturą zapisuje factor=1); to diagnostyka modeli, nie dowód Unity. Bounds zapisane w blender-prototype-bounds.json.
NASTĘPNY KROK: obserwować validation.log/import-before.log; obejrzeć before/ po pojawieniu PNG.

Rozszerzony audyt produktów obejmuje też curb_/kerb_ i collision_asphalt/curb/paving/grass: 806/806 prymitywów identycznych bajtowo. Import before nadal generuje PBR; PHONE_RUN nie istnieje. NASTĘPNY KROK: Get-Content artifacts/furniture-r1/import-before.log -Tail 8

Samokrytyka zbliżenia Blendera: usunięto pionowy profil przetłoczeń skanu metalu z atlasu. Obejrzano poprawiony blender-old-steel-foot.png i szary tył z dwiema obejmami blender-sign-back.png. Cache after odświeżony wyłącznie w 5 obrazach GLB; no-op pack identyczny bajtowo, 7252 widoki accessorów geometrii bez zmian. Nowy pełny GIS zostanie wykonany po renderach; 7 regresji nadal zielonych. Baza before nietknięta.
NASTĘPNY KROK: pipeline import/audyt/rendery, potem GIS po poprawce atlasu.

Import before przerwany: brak plików pakietów (CS0246 ColorBlock / UnlockReloadAssembliesTask). Przyczyna lokalna: zbyt szeroki filtr *lock* przy początkowej kopii Library. Uzupełniono całą PackageCache bez tego filtra; bez zmian Packages/ProjectSettings. PBR wygenerowane. NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1

Przyczyna ponownego PBR: 2 stare mapy asphalt_detail_photo; build_all pomijał ich odtworzenie, bo worktree nie miał wejściowego Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg. Skopiowano ten istniejący, ignorowany plik z main przed etapem layer bieżącego build_all; bez zmian generatorów wspólnych. NASTĘPNY KROK: sprawdzić layer asphalt_detail_photo i brak dalszych STALE/MISSING przed importem after.

Import before complete.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Ground/UV/material audit before complete.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render before Low overcast complete: artifacts/furniture-r1/before/Low-overcast
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render before Low clear complete: artifacts/furniture-r1/before/Low-clear
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render before High overcast complete: artifacts/furniture-r1/before/High-overcast
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render before High clear complete: artifacts/furniture-r1/before/High-clear
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Regenerated ADR0102 world.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Import after complete.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Ground/UV/material audit after complete.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render after Low overcast complete: artifacts/furniture-r1/after/Low-overcast
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render after Low clear complete: artifacts/furniture-r1/after/Low-clear
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render after High overcast complete: artifacts/furniture-r1/after/High-overcast
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Render after High clear complete: artifacts/furniture-r1/after/High-clear
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

R1 odrzucona po Gate3Audit: pole floating 4→27 (22 lamp12). Zdiagnozowano: probe liczy od dna bounds, więc głębokie niewidoczne końce pod pomostem powodują wybór terenu kilka metrów niżej; dodatkowo usunięty fallback kolizji zaniżył jeden sygnalizator w luce siatki. R2 przywraca wybór poziomu collision/terrain, nadal osadza na środku stopy zamiast minimum. Uproszczono niewidoczne końce modeli (cokół render −0.10/+0.08); dodano 2 regresje poziomów. 9 testów zielonych. R1 PNG/audyt zachowane w after-r1/ i audit-after-r1.json. Aktywne GIS przerwano przed regeneracją.
NASTĘPNY KROK: uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c

Korekta zapisu wyżej: pierwszy przebieg R2 miał 8 passed / 1 failed, bo test wymuszał konkretną stronę uskoku; obie płaskie strony są poprawnym podparciem. Poprawiono asercję kontaktu bez wymuszania strony. Potwierdzony wynik: 9 passed / 0.27 s (patrz wynik bieżącego pytest). Regeneracja R2 trwa.
NASTĘPNY KROK: po build-after-r2.log done zapisać snapshot after i usunąć wyłącznie markery audit/import/render-after/pytest-after.done, następnie run-validation.ps1

R2 build zakończony 307.8 s; spójność dróg 65 jak baza. Zapisano nowy snapshot after, zachowano bazę before i dowody odrzuconej R1. 9 regresji przechodzi. Markery after z R1 unieważnione; walidacja pełna ponowiona dla R2.
NASTĘPNY KROK: po load after OK uruchomić pełny GIS z pytest-after.running, równolegle do oczekiwania na PHONE_RUN.

Regenerated ADR0102 world.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Import after complete.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Ground/UV/material audit after complete.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

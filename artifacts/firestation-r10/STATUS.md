# E — JRG2 r7 (ADR0070)

Stan: bootstrap i baseline; produkcyjny model/atlas jeszcze nietknięty.
Gałąź/worktree: gpt-firestation-r7; bazowy main 901c427f2bc5cebf9571adc14df3253bbd3bd772.
Zakres: sets_fire_station.py, make_fire_station.py, art-source/world/landmarks/fire_station_jrg2; dopisek r7 do ADR0070, bez nowego ADR0090.
D48: tynk overcast110/126/145±10, zachować plaster-only x1.15. Referencja: rzeczywiste CC0 7197, nie AI Data/photos.
B pozostaje zamrożone przy9070b252; ROOT zamyka jego pozostałe EditMode/raport/kopię.
Unity przed każdym startem czeka na główny PHONE_RUN; bez adb i telefonów. Żadnych main source writes.

Krok1: przeczytano bieżące S10 E, zasady, s9§1, ADR0070 i D48. Nowy worktree z aktualnego main, git lfs checkout.
NASTĘPNA KOMENDA: `pwsh artifacts/firestation-r10/bootstrap.ps1` — prywatne kopie danych/cache, referencja i junctiony tylko do odczytu; potem świeży hero/PBR/world/canonical fixture przed baseline.

Krok2: prywatne kopie raw/cache/Fab/Generated gotowe, Library ze stabilnego C; junctiony tylko do odczytu. Kopiowano wyłącznie PNG materiałów, bez source/spec. Referencja7197 i ignorowany interiorLOD0 skopiowane. Brak dryfu śledzonych plików. NASTĘPNA KOMENDA: `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py`; CPU prep dozwolone, Unity czeka na explicit ROOT release i obie blokady.


Krok3a: plny PBR wygenerowany475s. Uzupełniono jedyne brakujące istniejące wejście pipeline: public-domain Worn_cracked_asphalt_pavement.jpg (John Harvey, LICENSES), odtworzono tylko asphalt_detail_photo. To wejście istniejącej tekstury świata, nie fizyczna referencja remizy; dla JRG2 pozostaje wyłącznie rzeczywiste7197. NASTĘPNA KOMENDA: `Get-Content artifacts/firestation-r10/baseline-world.log -Tail 8`; nadal bez Unity przed ROOT release.


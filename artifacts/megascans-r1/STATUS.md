# Megascans R1 — gpt-megascans

- Krok 1: przeczytano kontrakt i zasady; worktree z main 2df87f1. Bez zmian w main, telefonach i ustawieniach projektu.
- NASTĘPNY KROK: `robocopy C:\Users\matma\Documents\Claude\kamion\Data\raw Data\raw /E /XJ /R:1 /W:1`

- Krok 2: Data/raw skopiowane fizycznie /E /XJ; git lfs checkout zakończone. Uruchomiono 3 rozłączne zakresy: procesor Fab, rozmieszczenie, kora/liście.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (baseline przed integracją).

- Krok 3: obejrzano 7 arkuszy (80 map) i 5 szczegółów. Odrzucono round-manhole-cover (emblemat/napisy), trash-can (żółty emblemat), urban-trash (opakowania/marki), pine-bark (atlas ściółki zamiast kory pnia). Linden Branch zawiera gałąź, nie liście; liście pozostają fallback.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m fab.prepare` (po zakończeniu procesora).

- Krok 4: procesor kory/krawężnika 4/4 testy. Trzy ZIP-y różnią się od pierwotnego manifestu; potwierdzono CRC, nazwy/ID Quixel i FBX. Przypięto zaobserwowane SHA, zachowując stare wartości; przyczyna rozbieżności UNVERIFIED. Fab nadal wyłącznie lokalnie.
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/fab/prepare.py --blender C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe`.

- Krok 5: baseline build zakończony (64 chunki, 418 MiB High / 91 MiB Low); trwa import baseline z KAMION_DISABLE_FAB=1. Testy Fab 28/28. Niezależny review wykrył brak tangentów w compact mesh: normal mapy wyłączone, AO keyword naprawiony, UV0 Fab jawnie zachowane.
- NASTĘPNY KROK: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/megascans-r1/before/Low-overcast` (po imporcie).

- Krok 6: ADR 0084 a użycia/odrzucenia 19 pozycji zapisane w LICENSES. Budżet Python obejmuje zmierzone LOD Fab; UV0/alpha/AO poprawione. Baseline import regeneruje istniejące PBR (stemple świeżego worktree); nadal trwa.
- NASTĘPNY KROK: `Get-Content artifacts/megascans-r1/before-import.log -Tail 10`.

- Krok 7: 38 testów Fab PASS. Dodano denylistę samych hashy (850 członków ZIP, lokalne pochodne), kontrolę blobów indeksu i LFS oid — działa też w publicznym klonie. Stare zatwierdzenia są unieważniane przy zmianie review/SHA. Wykryto błędną skalę/osiowanie FBX małego kamienia; poprawka oparta o jego metadane 0,26×0,18×0,08 m w toku.
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/fab/audit_inventory.py` (po korekcie kamienia).

- Krok 8: baseline Unity import OK; 28 kamer Low i 28 High overcast zapisane. Low pamięć świata 112,1 MB (render76,4 + instancje19,0 + kolizja16,7), High248,8 MB (CPU/import estimates, nie telefon). Atlas3utility→1materiał gotowy; kontrola siatek odrzuciła pierwsze boxwood/elderberry zbyt przerzedzone/zepsute UV — poprawiamy przed rundą świata.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (po atlasie i poprawce roślin).

- Krok 9: EditMode188:176 PASS,0 FAIL,7 skipped,5 inconclusive (nie zatajono bramek bez danych). Obejrzano komplet56 ujęć baseline na arkuszach Low/High oraz realne referencje CC0. Samokrytyka: świat nadal zbyt równy i czysty; detal ma być lokalny, nie zasypywać utrzymanych poboczy śmieciami. Cofnięto efekty uboczne Unity w QualitySettings i Lighting.
- NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis -q` po wygenerowaniu rundy after.

- Krok 10: atlas 512/1024 ze wspólnymi UV podłączono do trzech zatwierdzonych studzienek i kratek. Krzewy z bliska otrzymują geometrię z zachowaną sylwetką; dalsze LOD mają osobny atlas billboardów. Trwa pełny GIS baseline.

- Krok 11: rozpoznano i naprawiono czerwony kanał masek Quixel. Faktyczne LOD0/1/2: boxwood7062/9/3, elderberry7139/11/3, grass3660/6/3, wildgrass3588/8/3. Atlas po zmianie map odtworzony; spoiny krawężnika zachowane. Low używa istniejącego simpleFoliage również dla Fab; fallback czyści poprzednie mapy/metalki z materiałów.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`.

- Krok 12: docelowe testy Fab52/52 PASS. Obejrzano finalny arkusz roślin (źródło/LOD0/LOD1) i7propsów; poprawiono również podwójny transform rodzica małego kamienia. Pierwszy pełny GIS:249 PASS,3 FAIL,11 ERROR;11błędów wynikało z nowej konwersji trasy ndarray→LineString (naprawione+regresja),2FAIL to znany korytarz1432–1480,1FAIL to stary raport fidelity (regenerowany).
- NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` po after-build i zakończeniu EditMode.


- Krok 13: EditMode194:182 PASS,0 FAIL,7 skipped,5 inconclusive. Odświeżenie fidelity ujawniło3odziedziczone porażki ratchet (axis0,129m,edge2,483m,6wysp); pipeline/markings/graph/overrides identyczne z main2df87f1, fidelity nie używa etapu Fab. Bez obniżania progów i bez zmian w cudzych drogach. Raport pozostaje jawnie FAIL względem pełnego DoD.
- NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` po after-build.

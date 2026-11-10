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

- Krok 14: after-build OK:64 chunki. Fab:773 podmienione wpusty,197 włazów,320propsów (161 kęp trawy,41dzikiej trawy,41bzu,5bukszpanów,54kamienie,18worków). Wszystkie miejsca WORKING_VALUE. Unity ładuje tylko rzeczywiście użyte biblioteki Fab, nie nieużywane siatki źródeł materiałowych. Trwa import i pełny GIS final.
- NASTĘPNY KROK: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/megascans-r1/after/Low-overcast` po imporcie.

- Krok 15: pierwsze56PNG after obejrzane: brak wyraźnego skoku całej sceny, a goły Lit na krawężniku usunął brud/makrowariację — FAIL i poprawka na dotychczasowy WorldPBR+fotograficzną bazę. Lowłączne estymaty +do17draw/+4ktris; znaleziono stare kratki na placach pozostawione obok nowego atlasu oraz zmianę fazy przerzedzania lasu przez nowe indeksy instancji. Oba mechanizmy poprawiane w rundzie2; nie ukrywam regresji.
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` po poprawkach atlasu/indeksów.

- Krok 16: druga runda przygotowana: wspólny atlas również dla kratek na placach, nowe włazy4,5mm nad podłożem. Odtworzono WorldPBR krawężnika z2metrowym kaflem/2spoinami. Testy powierzchni+rozmieszczenia28/28 PASS. Testy indeksowania legacy11/11 PASS w Unity (zero wpływu nowych Fab na dawną kolejność i przerzedzanie lasu). Trwa ponowny build.
- NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` po round2-build.

- Krok 17: runda2 obejrzana w56kadrach: WorldPBR usuwa rażącą jasność ściany, ale Low nadal do+19draw/+4ktris — kolejna korekta. Diagnostyka46oryginalnych wpustów: szerokość0,500m, długość0,056–1,012m, UV poprawne; materiał obejmuje je teraz bez ruszania geometrii. Wszystkie773 odtworzone zcache:V/T identyczne. Nowe Fab mają własne komórki cullingu (12/12 EditMode); billboardy skrzyżowane i osadzone naY=0 (22/22 procesora). GISr2:270PASS,5odziedziczonychFAIL,2xfail. Trwa runda3.
- NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` po round3-build.

- Krok 18: runda3 import+56PNG OK. Low szczyt956drawEst/333ktris bez wzrostu; lokalnie do+4draw/+4ktris. EditMode206:194PASS,0FAIL,7skipped,5inconclusive. GISr3:275PASS,5odziedziczonychFAIL,2xfail. Trzy dodatkowe kamery na faktycznej trasie: raycast3/3 PASS, wysokość2,300m. Zapisano1989plików stanu after w prywatnym art-source/world/megascans/_generated/qa-after-r3.zip.
- TRWA TERAZ: prawdziwy build/import fallback z KAMION_DISABLE_FAB=1 i osobne kadry before. Po nim KONIECZNIE odtworzyć after (Unity musi być zamknięte).
- NASTĘPNY KROK awaryjny: `uv run --project tools/worldgen python artifacts/megascans-r1/reversible_qa_state.py restore`; następnie wyczyścić KAMION_DISABLE_FAB i sprawdzić manifest/PNG.

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


Krok3: świeży własny PBR/alpha/layout, hero i świat z901c przed zmianami produkcyjnymi. Zapisano źródła/referencję i192rawSHA, Fab15bezfallback, hero applied. NASTĘPNA KOMENDA: po explicit ROOT release i sprawdzeniu obu blokad import-region + canonicalvehiclefixture; następnie prawdziwe baseline LowWorldC/HighWorldC_High.


Krok4: istniejący asphalt_detail_photo odtworzony bitowo identycznie z main/F/G (4 mapy); pin SHA1 pliku zgadza się z Commons, źródło PD John Harvey. Dowód asphalt-existing-input-parity.json. Przygotowano unity-baseline.ps1: oddzielne import/kanoniczny pojazd/capture, wymagany ROOT_UNITY_RELEASE.txt i brak OBU blokad przed każdym startem. Żadna Unity nie wystartowała. NASTĘPNA KOMENDA: dopiero po explicit ROOT release: pwsh artifacts/firestation-r10/unity-baseline.ps1 -Stage Import.


Krok5: wyłącznie artifact-only CPU rzuty sylwetek/layoutu i sprawdzenie kontraktu materiałów. Low używa opaque atlasu (brak alpha); High opaque core + osobna shell alpha0.5. Odrzucono cienkie/odłączone Low gałęzie i hourglass; bieżący wolumen nadal stylizowany, brak visualPASS. +4u m tylko dwóch świerków odsłania łuki; trzeci bez przesunięcia. Jitter .25: nominal2.692m, actual2.369..3.217m, max19.50%. Wszystkie192raw i4źródła/produkty bez zmian. NASTĘPNA KOMENDA: obejrzeć shape-candidates/layout.jpg; Unity nadal WYŁĄCZNIE po explicit ROOT release i sprawdzeniu obu blokad, następnie unity-baseline.ps1 -Stage Import.


Krok6: źródłowy audyt koloru (nie Unity visualmatch): coreY=.024306, farY=.064226 (2.642x), coveredShellY=.036983 (far1.737x), alpha tilecoverage87.48%. A-correct expectedGPUtint zgodny z kopiowanym cache, lecz to nieGPUreadback. Rozdzielono metrykę otworu od górnej czapy łuku: prawe archheadLow61.97→100%,High54.99→100%; lewy ~97–99% bez istotnego skoku. arch-rois.jpg pokazuje definicję masek. Bieżący CPU Low jest pełniejszy, nadal stylizowany; final visualPASS PENDING. NASTĘPNA KOMENDA: po explicit ROOT release i obu blokadach absent: pwsh artifacts/firestation-r10/unity-baseline.ps1 -Stage Import; produkcja i192raw nadal zamrożone.


Krok7: artifact-only alpha experiment z nowym CC0 fir_tree_01 (fir/conifer, niezweryfikowane Picea), sourceSHA pinned; żadnej zależności od kodu B. Rzeczywisty baselineGLB: 548+98+0 alphaUVtris bez kolizji z nową komórką po runtimeVflip. Eksportowany proxyGLB zachowuje4/2/1primitives i2Lowmaterialslots, pełne bounds identyczne; Low2828→2744tris(plants888→804). Oryginalne pixels poza cell byte-identical, gutter16px; shader/runtimebatchslot/layer/shadowpolicy zachowane w źródle. Wciąż PENDING actualUnity/stats/temporal/mip: globalalpha-coverage może zmienić stare fence/letter mips. Skorygowano rawcrop caution: źródłowe białe trójkąty mają alpha, lecz B usuwa oddzielne komponenty; B processedcard jest czysty, brak regresjiB. NASTĘPNA KOMENDA: ROOT review shape-candidates/fir-alpha-proxy-low.jpg; nadal wymagany explicit ROOT release + brak obu blokad przed unity-baseline.ps1 -Stage Import.


Krok8: source-only fir proxy pełniejszy:36nieregularnych root-attached boughcards naświerk +overlapcore/trunk. Wydano72z84Lowheadroom; plants876≤888, pełnyhero2816≤2828. Actualexportslotcount4/2/1 i boundsidentical. Newcell CPUmipcoverage~10.47%base,~10%mip4,6.35%mip5,0mip6; oldplainfilter alpha paritydo5, LANCZOS1sample6/5sample7. Importer/alpha globalsettings BEZ ZMIAN; rzeczywisteUnitymips/ASTC/shimmer/stats PENDING. Szczegóły FIR-CANDIDATE.md. NASTĘPNA KOMENDA: dopiero po explicitROOTrelease i braku obu blokad: pwsh artifacts/firestation-r10/unity-baseline.ps1 -Stage Import.


Krok9: ROOT obejrzał pełniejszy876tri CPUfirproxy: użyteczny do próby w Unity po niezmienionym baseline; koniec dalszego strojenia naślepo. Macierz akceptacji: 4herokamery (near/ref7197,route,abeam,above),LowWorldC/HighWorldC_High,clear/overcast; R1hero +R2pełna trasa. Porównać też stare napisy/płot/flagę/okrągłe okno, actualmips i znikanie nowejkomórki. Wrapper Capture rozdziela before/round1/round2 i chroni gotowe stats przed nadpisaniem. NASTĘPNA KOMENDA: po explicitROOTrelease i obu guards absent: pwsh artifacts/firestation-r10/unity-baseline.ps1 -Stage Import; potem Vehicle iCapture -Phase before. Żadnej produkcji/Unitydotąd.


Krok10: jawny ROOTrelease11:56:56; przed pierwszym Unitypotwierdzono4sourceSHA+192rawbez zmian i obie blokady absent. Baseline IMPORT_RESULT OK,64chunks,190prototypes127065instances, Low111.3MB/High239.7MB z collision+instances. KanonicznyVehicle już uruchomiony sekwencyjnie po guardcheck; brak produkcyjnych zmian. Wykryto wyłącznie serializację nowych pól LP_Clear/Dusk/LowSun iM_Sky; przywrócę tylko te własne sideeffects przed baselinecapture. Skorygowano R1cameraIDs nafire-station-*; CPUhelper zakładał horizontalFOV, a prawdziwyUnityCamera używa verticalFOV — aktualne runtimeROIs będą liczone poprawnie. NASTĘPNA KOMENDA: po końcu Vehicle restorewłasnychLightingplików; unity-baseline.ps1 -Stage Capture -Phase before.


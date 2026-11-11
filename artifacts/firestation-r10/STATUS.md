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


Krok11: kanonicznyVehicleTRUCK_RESULT OKprzedBaseline. Prawdziwe160PNG(40kamer×4cond) i4stats gotowe: LowWorldC/HighWorldC_High clear/overcast. CanonicalvehicleSHAunchanged,192rawunchanged. Własne UnitysideeffectsLighting/M_Sky/QualitySettings przywrócone doHEAD. Pierwsze960pxref potwierdzają ciemne towerwing i przesłonięty prawyłuk. CPUrzuty przeliczone/oznaczone prawidłowym verticalFOV; nieużywanejakoexactruntimeROI. NASTĘPNA KOMENDA: wąskie wdrożenie fir876tri+existingalpha+pozycje3tujaforms; potem ownbuild/import i Lowovercast ref7197/route przed pełnymR1.


Krok12: wdrożono own-repo pinnedCC0 firsprite +36Lowrootcards/54High, overlapcores,3thujahabits i±25%spacing/+4u dwóchforegrounddrzew. Dla High tylko lokalny alias fire_station_thuja_shell zastępuje dawnąshell;coreownatlas. Globalehedgebez zmian;Lowdalej2slots. Wspólnaintencjapalette zachowujepoprzedni farbase [.040,.068,.030] do actualcalibration. Testy4/4PASS; poprawionoakumulacjęmeanfloat64 do precyzyjnejkalibracjialiasu. RawFirinputsownignoredcache, metadataCC0/appliedtrue. Pierwsza kontrolaPBR12map ioldalphapoza komórką EXACTpixelparity. NASTĘPNA KOMENDA: uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c; potem guardchecked ImportPhaseprobe i2Lowovercastkameryref/route, bez nadpisania baseline.


Krok13: nowy asset zarejestrowany w docs/LICENSES.md zgodnie z CLAUDE§8. Utworzono ignorowany offlinebundle source-cache/fir_tree_01 +manifest irestore_cc0_inputs.py zpinSHA i kontrolą resolve→repo (bez junctionescape); --check-onlyPASS. Restore nie regeneruje tekstur i nie dotyka main. R1worldbuild trwa, source/api/pakiety własne zamrożone. NASTĘPNA KOMENDA: po r1-worlddone i sprawdzeniu metadata/applied15: guardchecked unity-baseline.ps1 -Stage Import -Phase probe, potem Capture -Phase probe -OnlyTier Low -OnlyLight overcast -CameraIds fire-station-ref7197,fire-station-route.


Krok14: R1world ukończony317.7s, actualGLB9296/2816/164tris, sloty3/2/1, firappliedtrue, Fab15ready/noFallback, heroFresh. RelatedGIS14/14PASS. Pierwszy postchangeUnityImport został ZABLOKOWANY przez powrót PHONE_RUN; nieuruchomionoUnity. ROOT potwierdziłrenewedHOLD, staryreleaseprzeniesiony ROOT_UNITY_RELEASE_115656_SUSPENDED.txt; żadnegoauto-resume. W CPU audytujęremainingglass/weather/tower/clinker/grilles/flag na160actualbaseline. Proponowane semanticROIs wymagają weryfikacjiwindow/clinker/foliage zanimposłużąkalibracji; świeżyfullGIS będzie po finalproducts. NASTĘPNA KOMENDA: dopiero po NOWYM explicitROOTrelease +obu guards absent: unity-baseline.ps1 -Stage Import -Phase probe; potem Capture -Phase probe -OnlyLight overcast -CameraIds fire-station-ref7197,fire-station-route (obaLow/High).


Krok15: rzeczywiste4probePNG ukończone12:50 (Low/HighOV×ref7197/route), obieUnityzakończone przed nowymhold12:50:52. Lowshutdownobsłużony istniejącąregułąADR0083(fresh2PNG+stats,monocleanup); HighexitOK.192rawR1unchanged,Fab15noFallback,vehicleSHAunchanged.2Lowviewsdraws/trisKbez wzrostu; Highinstanced−1drawkażdyview,route−1ktri. ROOT+SELF REJECTroślin: igłyczytelne/łukiotwarte,ale3firnadalanteny/szkielety; NIEvisualPASS iNIEpełnyroutebudget. NowyDIAG1HOLD,release12:46suspended, brakUnityaktywnych/autolaunch. Szkło/klinkierjeszczebez zmian—4probeizolujemorfologię/palette. CPUprzygotowano connectedcore.55/.70R, bez odłączonychdiamondów, Low36coretris×3wykorzystujeostatnie12tris(pełnyLow2828), materiały/boughs/palettebez zmian. NASTĘPNA KOMENDA: ROOT review core-fill/connected-fill-compare.jpg; potem wybranyCPUmodelbake, aUnitywyłącznie po NOWYMexplicitrelease+obu guardsabsent.


Krok16: ROOTwybrałCPU.55R, .70R odrzuconyjako zbytpełnystożek. Wprowadzono ciągły4-ringirregularcore zszersządolną1/3,36tri/coreLow(pełnyLow2828=before), radialne normalsTYLKOcore;zero-vectorswedługBlenderAPIzachowują auto innychloopów. CC0boughs/cards/palette/materiały/height/positionbez zmian. Unit4/4PASS;przedbake zapisanyprobe-sparse-hero.glb do kontroliautonormals. SourcePPglass/clinkerNIEzmienione,wciążcausalMorphonly. NASTĘPNA KOMENDA: build_world dla core-r2 podczasHOLD;potem porównaćcommonbuilding/roofnormals, metadata oraz192raw;actual4kamery dopiero poNOWYMrelease.


Krok17: connected.55Rworld ukończony300.9s, actual9344/2828/164tris, Fab15ready/noFallback, heroFresh, canonical192SHA zapisane. RelatedGIS14/14PASS. Normalparity:building/roofautoEXACT,Low/farcommonvectorsEXACT; High5innychfoliageautonormals Blenderprzekodował≤8.1e-5, leczpackedSNorm8wszystkichcommonverticesidentyczny (actualimportużywaSNorm8).3Float16fallbackfoliagekeys drobnieinne, jawnie wcore-r2-normal-parity.json. ŻadnegoPP/palette/alpha/UVoldregion/roofpaint-tuningu; rzeczywistaocenaPENDING. ArtifactsC#DumpAlphaMips.cs przygotowanypozaAssets(niezainstalowany/nieuruchomiony). NadalPHONE/ROOT_HOLD,releaseabsent. NASTĘPNA KOMENDA po freshrelease: unity-baseline.ps1 -Stage Import -Phase core-probe;Capture -Phase core-probe -OnlyLight overcast -CameraIds fire-station-ref7197,fire-station-route. Potem ROOTreview4FIRST, niepełnymatrix.


Krok18: po freshROOTrelease13:13 import i4core-probe actualPNG13:16DONE, obieUnityexitOK, brakaktywnych.192rawi canonicalvehicleSHAunchanged.2Lowviews static+instanceddraws/trisK EXACTbaseline; Highinstanced−1drawkażdyview,route−1ktri. Cztery960pxporównania/viewyobejrzane;antennaVoidwypełniony, łukiotwarte, nadalstylized/narrow—ROOTreviewPENDING, nievisualPASS. CausalPP/palette/alpha/oldfence-textpixelsbez zmian. MipQAhelper offlineC#compilePASS(337Unityrefs),nadalpozaAssets. NASTĘPNA KOMENDA:ROOTgate4framesprzedfullR1;następnieguardcheckedactualmipQA i osobnypomierzonyglass/clinker/weatherround (niezlewaćzmorfologią). GdyPHONEwróci—stop i nowyrelease, bezautoresume.


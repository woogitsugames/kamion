# S10 A — ADR0086 tint gamma

- Bootstrap: gałąź gpt-tint-gamma z main4f7da66c; przeczytano kontrakt S10, HANDOVER s9, zasady, visual-qa. Zakres: kontrakt liniowego _Tint i kalibracja importera; bez zmian geometrii/światła/roślinności.
- NASTĘPNY KROK: `git lfs checkout` oraz kopie lokalnych cache i produktów Fab; potem import/render baseline przed zmianą kodu.

- Krok2: skopiowano Data/raw/derived+cc0, CC0/_raw, megascans, Unity _Generated/Library, material PNG caches i zdjęcia; rawfab/gugik/osm/refs/mapillary = junction tylko do odczytu. Bez zmian źródeł main. NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c`; baseline wymaga świeżego importu, cache main nie jest dowodem.

- Krok3: GPU readback kopii rzeczywistego WorldPBR (zmieniony tylko zwrot fragmentu) potwierdził kontrakt Color: raw0.08 ->0.007194, raw0.5->0.214041; zapis gamma(linear) daje dokładnie0.08/0.5, takżeHDR1.5/2.5. SetColor i SetVector identycznie. Dowód tint-probe.json, UnityLinear/D3D12. NASTĘPNY KROK: po ukończeniu before-build import-region + cztery baseline Low/High clear/overcast (bez zmian importera).

- Krok4: świeży build_world zakończony329s;192/192 hashe GLB/instances zgodne z manifestem, Fab15 dostępnych/320props/954replacement bez fallback. Audyt119 definicji PBR:56 już poprawnychmodulation,33 niepoprawnychmodulation,29 ratios,1tyre. Import baseline przebudowuje cache PBR z niezmienionegoHEAD. NASTĘPNY KROK: `pwsh -ExecutionPolicy Bypass -File artifacts/tint-gamma-r1/run-round.ps1 -Round before` (wszystkie kamery, LowWorldC/HighWorldC_High × clear/overcast).

- Krok5: baseline236PNG=59kamer×4warunki, wszystkie przed zmianą importera; LowWorldC i HighWorldC_High, ten sam Gate3building JSON i MaterialTierMedium. GPUprobe+pełny baseline udokumentowane. Teraz jeden SetLinearTint dla wszystkich4 ścieżek PBR (modulation/ratio/oil-paint/tyre), bez zmian shaderów/palet/metrów/warstw. NASTĘPNY KROK: `pwsh -ExecutionPolicy Bypass -File scripts/import-region.ps1 -Region bialystok-industrial-c`; potem run-round after-contract (bez korekty palety, do pomiaru).

- Krok6: čistý kontrakt po236PNG: Highov asfalt73.7→73.6 (0.08zachováno),kostka125.9→126.7,hala93.8/97.6/96.6→135.8/139.2/138.6,ekran27.6/28.7/28.1→56.6/58.6/55.8 (foto36–40); remizaHigh105/121/137 iLow97/112/130 bez změny. Samokritika: ekran jest nadmiernie jasny, remizaLow poniżejpasma ±10. Wprowadzono eksperyment: ekranlinear.022/.024/.023 i TYLKOtynk atlasu remizy×1.15; dach/szkło/trim bez zmian. NASTĘPNY KROK: `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only fire_station` → build_world → importaktualnychcache → pełna rundaafter-calibrated.

- Krok7: eksperyment przebudowany33s(fire_station)+317s(world); import po walidacji cache zakończonyOK/SHA0. Chronione piksele dachu/trimu/szkła identyczne wHigh/Medium/Low (plaster-atlas-diff.json); 3testyGISkontraktuPASS. PierwszeEditMode223/226: wszystkie14TintGPU/CPUgreen,3starefixtureTruckDoorGlass brakMI_Ext_DoorGlassL; po finalnejparzeodświeżę canonicaltruck i powtórzętesty. NASTĘPNY KROK: `pwsh -ExecutionPolicy Bypass -File artifacts/tint-gamma-r1/run-round.ps1 -Round after-calibrated`; tabelaROI i niezależnyreviewroot.

- Krok8: GIS358pass/2xfail, canonical truck od?wie?ony po dopasowanej macierzy, EditMode226/226pass. Reviewroot wykry? plandeki dok3 rozja?nione53/55/54?110/112/109. Kalibracja wszystkich6PVC+box_white do poprzedniej efektywnej warto?ci GPU, explicit WORKING_VALUE wgADR0092/s9; roughness bez zmian. NAST?PNY KROK: build_world ? import ? after-final236PNG; rozdzieli? statystyki kanonicznego pojazdu od zmian ?wiata.

- Krok9: nowy world306.7s, importSHA0; pami??111.4MBLow/239.8MBHigh bez zmiany. Trwa after-final59?4 po canonicalfixture; wcze?niejsza dopasowana macierz kosztu nadal osobna. NAST?PNY KROK: odczytROI curtain_dock3, finalne strony960 i rootreview; finalGIS w toku.

# Megascans R1 — raport końcowy, 2026-11-11
Gałąź `gpt-megascans`, zwalidowany stan implementacji `71d502d`; bez push/merge. Wynik: **pełny DoD NIEZALICZONY**; implementacja i cztery rundy QA zakończone.
Źródła: 19 ocenionych, 15 użytych, 4 odrzucone (znaki/nieodpowiednia zawartość); 3 zmienione piny ZIP potwierdzono CRC/tożsamością Quixel, historia zmiany UNVERIFIED.
Wpięto krawężniki, korę brzozy/lipy, atlas odwodnienia, roślinność, worki i kamienie; istniejące liście i kora sosny pozostały — dostarczone skany nie zawierają odpowiedniego materiału.
Świat: 64 chunki; 773 wpusty +190 kratek placów ze wspólnym atlasem, 197 nowych włazów, 320 propsów; pozycje i skale WORKING_VALUE.
Własne LOD0/1/2, billboardy, limity tris, albedo/alpha/PBR; fotobaza trawy bez nowej geometrii. Low/Medium material512, High material1024 dostępny osobnym importem; oba profile QA używały512.
Licencja: wyłącznie kod/metadane w git; hash guard 850 członków ZIP +650 lokalnych produktów, także siatki Unity; indeks sprawdzony, 3/3 PASS.
Testy GIS: 282 PASS, 5 odziedziczonych FAIL, 2 xfail; 3 ratchety fidelity i 2 znane błędy s1432–1480. Nowe testy trawy dodano po kolekcji; cały zestaw Fab osobno76/76 PASS.
EditMode: 209 przypadków, 197 PASS, 0 FAIL, 7 ignored, 5 inconclusive; nativeUnity2/wrapper1 jak baseline, nie deklarujemy zielonego kodu procesu.
Prawdziwy fallback bez Fab: build exit0, import obu tierów i6PNG before OK; EditMode0FAIL. Końcowe192/192 hashe świata i3/3 raycasty kamer PASS (oko2,300m nad jezdnią).
Low szczyt956drawEst/333ktris bez wzrostu, lecz lokalnie do+4draw/+4ktris — ścisły budżet każdego kadru NIEZALICZONY. High lokalnie do+8draw/+20ktris; to estymatyCPU, nie GPU/telefon.
Pamięć importu: Low112,1→113,0MiB, High248,8→249,7MiB. Fab tekstury512: konserwatywnie8,689MiB ASTC+mipy; legacy31,1MiB ich nie obejmuje (razem najwyżej39,79MiB zasobów, nie pomiar rezydencji).
PNG przed: `before/{Low,High}-overcast/` (56); po: `round4/{Low,High}-overcast/` (56); dodatkowe prawdziwe pary: `detail-before/` i `detail-after/` (po6).
Porównania: `round4/*-before-after.jpg`, `detail-*-before-after.jpg`, `detail-*-crops.jpg`; dane: `round4-comparison.csv`, `round4/import-report.json`, `round4/fab-textures-budget.json`.
Ocena niezależna: `round4/CRITIC.md` — lokalna poprawa PASS, duży skok realizmu całej sceny FAIL; Low właz ma mały kontrast, pozostają uproszczone korony i proceduralne duże powierzchnie.
Otwarte: pełna bramka wizualna, ścisły koszt Low, odziedziczony GIS; High1024 i SamsungA16 runtime UNVERIFIED. Telefonów/adb nie używano; normal maps Fab wyłączone do sprawdzenia tangentów.
Dokumentacja: `docs/adr/0084-megascans-import.md`, `docs/LICENSES.md`, `docs/WORLD_GENERATION.md`; przebieg i komendy w `STATUS.md`.
Przewidywane konflikty: `materials.py`, `plantings.py`, `life_props.py`, `build_world.py`, etap streetscape i import instancji/materiałów. Lider powinien sprawdzić bramki przed integracją; po scaleniu wygenerować prywatne produkty lokalnie.

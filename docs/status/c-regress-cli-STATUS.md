# c-regress-cli

2026-11-21: baza 83345868e (origin/main, wyłącznie dokumentacja ponad e16a5e240).
Log wejściowy: 28 failed, 2779 passed, 4 skipped, 2 xfailed (3398 s).
Wejścia raw przez dowiązania; derived C to prywatna kopia, bez zapisów do wyników main. Bez Unity.
Krok 1: rozdzielono licznik starych instancji ogrodowych od koron ADR0308;
fixture world jawnie buduje D94; bridge_clearance weryfikuje aktualną jezdnię zamiast pozornej rekonstrukcji starej kolizji.
NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_bridge_clearance.py -q` (slot heavy).
Test bridge_clearance: 23 passed (27 s). Świadkowie kolizji zamrożeni z historii git, bo bieżące QA po regeneracji słusznie nie zawiera bridge_kerb. Hero width sprawdza kapę względem aktualnych lg/rg i bufora zamiast starego stałego 10,6 m.
Krok 2: bariera mostowa trwa do kapy 0,30 m (zgodnie z meshing); authored rails dopasowane do finalnej jezdni przed clippingiem, z zachowaniem 0,25 m + obwiedni hardware. Testy celowane: 19 passed. Brama dobiera przekrój do stałego zasięgu szlabanu po D94. NASTĘPNY KROK: przebudowa C po poprawkach meshing/markings/far_field.
Krok 3: link dk65-01-s8-corner używa head_from Jeroniki; regeneracja tylko metadanych linków, błąd 0,375 m -> 0,0 m. NASTĘPNY KROK: pełny pytest po przebudowie C.
Krok 4: Low tła: uproszczenie pylonów 204->32 tris, reguła małych dalekich kopert, zachowane zamknięte dachy; ADR0318. Testy pylonów19 passed, dopisane testy farfield6 passed. Typology: dowód wyłączenia roof_variant przywraca dokładnie stare hashe12 domów Dojlidy/16 C; jawna zgoda tylko roof_karp_red, budżety tris/kamer bez zmian;4 passed. NASTĘPNY KROK: build_world C po finale verge/markings.
Krok 5: PatchHeight ma ciągły zanik wpływu jezdni do IDW; nowy test wartości i pochodnej. Bridge/patch testy8 passed. NASTĘPNY KROK: pełna przebudowa i GIS.

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
Krok 6: po buforze kapy pinned końce separatora DK8 zostały1,23/1,07m od końców deck. Nowe dopasowanie wyłącznie authored->deck, sprawdza tangent/poziom i nadal przechodzi finalną kontrolę nawierzchni; nie łączy przeciwległych authored rails.16 passed. NASTĘPNY KROK: build C po finalnych poprawkach verge/paint.
Krok 7: zebry P10/P11 przycinają wyłącznie zewnętrzne kolizyjne paski; wewnętrzna przeszkoda nadal blokuje, oba rzędy P11 wspólne. Oba węzły False->True; targeted7 passed. Pasy zieleni mają płynne ograniczenie promienia: replay1666 emisji270->32 steep, bez wycinania geometrii. NASTĘPNY KROK: build C po korekcie klasyfikacji powierzchni.
Krok 8: QA filarów używa tego samego przekroju octagon co rzeczywisty collider underdeck, zamiast prostokąta; stacje i pozycje bez zmian,2.4947->2.6433m, pełne testy filarów + regresje16 passed. Pylony Low pozostają widoczne ze wszystkich rogów właściciela:32 passed, PNG w artifacts. NASTĘPNY KROK: build_world C w tle przez heavy.
Krok 9: SurfaceIndex.classify porównuje rzeczywiste wysokości płaszczyzn trójkątów, a niższa trawa nie przesłania jezdni; zachowano okno poziomów DZ_M i wszystkie ratchety.6 unit passed; C983.06/-934.05 -> carriageway. NASTĘPNY KROK: Get-Content artifacts/c-regress-cli/build-c.log -Tail 20 (build C w tle).

# Zlecenie dla sesji Claude Code w CHMURZE „C” (do 5 agentów Opus/Fable), s20, 15.11 po południu

Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1). Jesteś w chmurze: NIE masz Unity, telefonów ani Data/raw. Masz do 5 agentów; każdy robi jedno zadanie na swojej gałęzi. Subagenci nie tworzą subagentów. Lider (sesja lokalna) jest jedynym integratorem main: zbuduje świat, wyrenderuje, zmierzy i scali. Ty NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/05 (mapa i dane), HANDOVER.md (blok „SESJA 20”, najnowsze wpisy na dole), docs/11_DECYZJE_WLASCICIELA.md (D63–D65), research/dk65-knyszyn-refs/README.md (K1: liczby DK65 i Knyszyna) oraz ADR 0205, 0207, 0212, 0215 (jak budowane są kafle DK65).

Uruchamiasz tylko czysty Python: `uv run --project tools/worldgen python -m pytest tests/gis -k <wybrane>`. Testy wymagające Data/raw pomiń i wypisz w raporcie. Dane regionów (Data/Regions/<id>/*.geojson, overrides.yaml, generated/*.json) są w gicie. Wszystko, co wymaga build_world, Unity albo renderu, wpisz do raportu jako DOKŁADNĄ komendę dla lidera.

NIE dotykaj: kafli dk65-06…11 i ich wpisów w regions.py (lokalny agent 0214), regionów knyszyn*, bialystok-knyszynska ani presetów nieba i latarni (lokalny agent 0216, ADR 0216), tunelu ronda Szymańskiego (0211) ani wody (0213, ADR 0210/0213). Nowe ADR numeruj od 0217 wzwyż: C1=0217, C2=0218, C3=0219, C4=0220.

C1 torowisko i przejazdy kolejowe (gałąź rail-0217). Generator świata nie ma dziś torów: 0212 zgłosił brak przejazdu kolejowego na DW671, a D65 i K1 mówią o torowisku wzdłuż DK65. Dodaj do tools/worldgen:
  - geometrię torowiska z OSM `railway=rail` (podsypka, podkłady, szyny jako prosta siatka LoD dla mobile, skrajnia);
  - przejazd kolejowy w poziomie jezdni (płyty, krzyże św. Andrzeja G-3/G-4, rogatki/półrogatki według OSM `railway=level_crossing` i `crossing:barrier`);
  - opt-in per region (`Region.rail` jak `Region.water` w ADR 0210).
  Testy jednostkowe na syntetycznych danych. Budżet trójkątów oszacuj i wpisz do ADR.
C2 rondo DK65×DW671 dla ciężarówki (gałąź roundabout-0218). Według K1: średnica osi ok. 17,6 m, 4 wloty jednopasowe; średnica zewnętrzna i wyspa UNVERIFIED. Sprawdź, czy generator rond (tools/worldgen/roads) obsługuje przejezdny pierścień wewnętrzny (opaska z kostki dla naczep) i czy ciągnik z naczepą 16,5 m przejedzie. Policz to geometrycznie (promienie skrętu z docs/04 i tools/physics-runner) i zapisz w ADR. Dodaj obsługę opaski jako dane (override) z testem. Nie zmieniaj regionu knyszyn: przygotuj override i komendę dla lidera.
C3 narzędzia QA dla wszystkich regionów (gałąź qa-tools-0219):
  (a) tools/worldgen/fidelity/run.py pada dla bialystok-dojlidy w `metrics.node_arm_check`: `int(str(n).lstrip("n"))` nie parsuje id węzłów typu 'Bw443103344:...'. Napraw tak, żeby fidelity działało dla każdego regionu (C się nie zmienia, test regresji);
  (b) 0208 zgłosił, że drugi powiat jest pomijany w far_field, lod2_extract i water (regiony na granicy powiatów). Znajdź przyczynę i napraw z testem.
C4 elementy przekroju DK65 z K1 (gałąź dk65-k1-0220), tylko kafle dk65-01…05:
  - zatoki autobusowe, przerywane odcinki linii krawędziowych i bariery z tabeli K1 (km → współrzędne przez geometrię drogi w danych regionu);
  - rozstaw linii krawędziowych 6,0–6,4 m (mediana 6,2) kontra obecny generator (0212: 7,1 m linia–linia, ortofoto 6,8 m). Zaproponuj poprawkę wspólnej stałej albo override per kafel z uzasadnieniem.
  Ul. Ełcka: K1 daje ok. 6,5–6,6 m, właściciel w D65 6,9 m. NIE zmieniaj, opisz rozbieżność w raporcie.
C5 (jeśli PR #89 M67 nadal ma status FIX i nikt go nie poprawia): poprawki według docs/reports/REVIEW-2026-11-15-s20-cloudB-rooftop-gsm.md na tej samej gałęzi research/rooftop-gsm-s21.

ZASADY: commit i push po każdym kroku; nie zmyślaj liczb (źródło, ESTIMATED albo WORKING_VALUE); bez ProjectSettings/, Packages/, asmdef i wspólnych scen; bez Google Maps, Street View, Earth i 3D Tiles; nagłówki HTTP bez nazwy projektu; stopka commitów zgodna z modelem. Na koniec każdego zadania PR (nie draft) z raportem do 20 linii po polsku:
- co zmienione;
- testy uruchomione i ich wynik;
- testy NIEuruchomione;
- DOKŁADNE komendy dla lidera;
- co otwarte;
- „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”.
NIE scalaj. Na końcu podsumowanie z numerami PR.
```

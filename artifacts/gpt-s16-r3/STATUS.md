# STATUS — gpt-s16 r3 / ADR 0155
2026-11-13 02:31 CET. Baza r2 1f81e87ee + origin/main e638abf31; konflikty tylko wygenerowane, ours + zaplanowana regeneracja.
R1 i R2 wypchnięte, bez merge/push main. R2 pełny GIS 986 passed / 4 xfailed, EditMode 484/484, critic PASS zakresu, D51 PARTIAL.
R3: diagnoza plam pod Putrą. Kod produkcyjny jeszcze bez zmian; przedmiotem kontroli są shadow caster, bias/kaskady i wypiekane far shadows.
Przygotowano te same kontrolne/G3 kamery, wszystkie SBS i dwa zbliżenia wyspy; wartości poz klasy B / WORKING_VALUE, bez udawanej kalibracji.
NASTĘPNY KROK: pwsh artifacts/gpt-s16-r3/baseline-world.ps1 -Stage baseline
Sprzątanie: kopie całego świata zastępują hashe; dowody tylko zwarte, pełne PNG lokalne. Usuwanie r1 clear-rejected zablokowane przez automatyczny przegląd — bez obchodzenia.

Dodano diagnostykę Editor-only natywnych casterów/bias/kaskad oraz odwracalną ablacją TwoSided (bez produkcyjnego ustawienia). NASTĘPNY KROK po generatorze: import.ps1 -Label baseline, probe.ps1 -Mode report.

2026-11-13T02:33:42.8504662+01:00 — Zweryfikowano SHA obu lokalnych zdjęć richlv i obejrzano arkusz: zdjęcia mają bezchmurne niebo i szeroki cień pod pomostem. Kierunku/czasu światła nie kalibrowano. Przekazanie lidera uaktualnione, R1/R2 wypchnięte.

Korekta zakresu wstępnego ray testu: mały nos gravel E534–540/N−700…−690, nie główna wyspa E558/N−734; test nie obejmuje hero instancji. Nie dowodzi przyczyny plam na głównej wyspie. Detale kamer poprawiono przed baseline, probe rozszerzono o hero LOD/maski/material flags. NASTĘPNY KROK: końcowy generator baseline, import i natywne obrazy.

Świat baseline wygenerowany: 546.121204 s, bez fallback=True. NASTĘPNY KROK: import i kamery baseline.

Po preflight usunięto niewykorzystaną zmianę/restore natywnych casterów z probe: narzędzie jest teraz wyłącznie read-only. Ablacje użyją istniejących rq i zapiszą efektywny URP. Cel nie oznacza zaciemnienia całego żwiru — zdjęcia mają także jasny żwir na pierwszym planie. NASTĘPNY KROK: import i bazowe obrazy po generatorze.

Generator bazowy zakończony bez fallback; zapisano SHA surowego świata bez dodatkowej kopii. NASTĘPNY KROK: import.ps1 -Label baseline, probe report, render before.

Import baseline zakończony.

Zapisano before/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Natywny probe: chunk bridge On w Low i High, hero LOD0/1 On, LOD2 Off; profil Low35m/1024/1 i High100m/2048/3. To dane assetu, efektywny URP będzie z VQA. Osobny niezmienny zestaw diagnostyczny dodał kamerę bliżej głównej wyspy (wewnątrz35m), bez zmiany zestawu pełnego baseline w toku. NASTĘPNY KROK: ablate.ps1 po pełnych renderach before.

Zapisano before/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano ablacją Low/baseline (). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją Low/zero-bias (rq_shadowbias=0,rq_shadownormal=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją Low/baked-only (rq_shadow=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją Low/no-baked (rq_worldsun=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją Low/no-shadows (rq_shadow=0,rq_worldsun=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/baseline (). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/zero-bias (rq_shadowbias=0,rq_shadownormal=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/baked-only (rq_shadow=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/no-baked (rq_worldsun=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/no-shadows (rq_shadow=0,rq_worldsun=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją Low/zero-normal (rq_shadownormal=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/zero-normal (rq_shadownormal=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją Low/zero-depth (rq_shadowbias=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Zapisano ablacją High/zero-depth (rq_shadowbias=0). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą.

Ablacje Low/High: zero-normal usuwa rząd plam, zero-depth go pozostawia; no-baked też pozostawia. Autor i critic potwierdzają kierunek, crop nie certyfikuje self-shadow konstrukcji. Kandydat: jawne shadow_normal_bias_scale=0 tylko viaduct_concrete, keyword wyłącznie istniejącego ShadowCaster PBR, zachowany depth bias. Legacy ma dokładnie dawną ścieżkę kompilacji; zero nowych materiałów/geometrii/przebiegów. Dodano 7 testów kontraktu materiału i natywnego zakresu. NASTĘPNY KROK: baseline-world.ps1 -Stage after, import, docelowe after i pełne testy.

Świat after wygenerowany: 513.270614 s, bez fallback=True. NASTĘPNY KROK: import i kamery after.

Materiałowy backup prywatny obejmuje458zweryfikowanychplików, w tym podkatalogProto; pierwszy zapis przerwał brak podkatalogu docelowego, poprawiono tworzenie rodziców i audyt rekurencyjny. Każdy SHA kopii zgodny z baząr2. NASTĘPNY KROK: verify-after.ps1 po zakończonym generatorze.

Import after zakończony.

Zapisano after/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

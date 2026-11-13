# STATUS KOŃCOWY — gpt-s16 r3 / ADR 0155
2026-11-13T04:09:44.420239+01:00
Gałąź gpt-s16-r3; zweryfikowany i wypchnięty commit 4ff1774f0f. Gotowe do recenzji: TAK (statyczny edytor).
R1 wypchnięta: eb718b7f8; R2: 1f81e87ee; R3: regionalna polityka 3 materiałów i pełna końcowa QA.
EditMode 493/493, 0 failed/skipped; GIS 986 passed, 4 xfailed, 945,46 s; fidelity exit 0; critic PASS.
122 kamery × 4 warunki: delta scene/instance/shadow draws i dokładnych tris = 0; globalny URP bez zmian.
193 surowe pliki identyczne SHA; 455/458 materiałów identycznych, 3 właściwe flagi tylko keyword/scale=0, zero nowych.
Autor obejrzał 488 par, 26 zbliżeń i 8 foto; critic PASS zakresu. Telefon, GPU, ASTC, ruch i pełne D51/Gate3 pozostają u lidera.
Sprzątnięto 2 duplikaty arkuszy, cofnięto 138 szumów cache i wcześniejsze eksperymenty; zero testowych plików policy w game/Temp.
Dowody są kompaktowe, bez prywatnych materiałów i pełnych PNG w Git.
DECYZJA: własne r1 clear-rejected (0,412 GB) pozostało po automatycznym odrzuceniu usuwania („blocked by policy”); nie obchodzono blokady.
NASTĘPNY KROK: końcowe przekazanie i kopia dowodów; lider recenzuje i integruje r1 → r2 → r3 oraz mierzy telefony.

---
Historia WIP (wcześniejsze hipotezy i odrzuconeA nie są stanem końcowym):
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

Zapisano after/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Fidelity odświeżone dla końcowego generatora r2; pełny GIS może sprawdzić świeży raport.

EditMode zakończony: exit 0; szczegóły EDITMODE-STATUS.md i final-editmode.xml.

FAIL kandydata A: wyłącznie M_viaduct_concrete nie usuwa plam w produkcyjnym Low-clear. Autor i critic potwierdzili obraz inspection/candidate/sbs2818-Low-clear.jpg. Nie zgłaszać PASS. Przygotowano izolowane natywne próby M_bridge_concrete i M_road_asphalt; po wyborze konieczne ponowne źródło/generator/import/QA/testy. NASTĘPNY KROK po zakończeniu EditMode A: pwsh artifacts/gpt-s16-r3/material-ablate.ps1

Natywna izolacja materiału M_bridge_concrete zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster.

Natywna izolacja materiału M_road_asphalt zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster.

Izolacje: bridge_concrete=0 dodaje drugi szereg plam, road_asphalt=0 zmniejsza/zmienia wzór, lecz go nie usuwa. Następna rozstrzygająca próba: obie sąsiednie powierzchnie pomostu razem=0 (bez hero). NASTĘPNY KROK: material-ablate.ps1 -Materials deck-pair

Natywna izolacja materiału deck-pair zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster.

Deck-pair nadal nie odtwarza globalnego normal=0. Próba all-pbr sprawdzi równoważność lokalnej ścieżki shaderowej wobec globalnego biasu; dopiero wynik uzasadni dalszy dobór materiałów lub poprawkę implementacji. NASTĘPNY KROK: material-ablate.ps1 -Materials all-pbr

Natywna izolacja materiału all-pbr zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster.

All-PBR0 odtwarza globalne normal0 w obrazie wyspy — lokalna ścieżka shaderowa działa. Diagnostykę poprawiono tak, by każda kolejna próba resetowała WSZYSTKIE wspierane PBR do1, unikając skażenia po szerokiej ablacji. Testujemy bridge_kerb osobno i deck-triple. NASTĘPNY KROK: material-ablate.ps1 -Materials M_bridge_kerb,deck-triple

Natywna izolacja materiału M_bridge_kerb zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster.

Natywna izolacja materiału deck-triple zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster.

Deck-triple usuwa wzór we wszystkich5diag kadrach Low, critic potwierdza bez oczywistego nowego acne. B: jawny shadow_caster_bias.json regionu dla bridge_concrete/bridge_kerb/road_asphalt, hero flaga usunięta. Polityka odczytywana po centralnym CreateMaterialCore, obsługuje także niestandardowe fabryki PBR, reset po usunięciu pliku/wpisu.9testów łącznie, w tym policy reset/schema i natywne3materiały. NASTĘPNY KROK: odtworzyć cache eksperymentów, generator B i pełny import/QA/testy.

Guard cache wykrył dodatkowe nieaktywne _RECEIVESHADOWS_ON/_ZWRITE_ON dodane do m_InvalidKeywords przez import shadera. Po obejrzeniu diff dopuszczono usunięcie wyłącznie tych dwóch wpisów; reszta nadal wymaga pełnej zgodności tekstu i SHA. Eksperymenty cofnięte, 458 bazowych SHA przywrócone.

Świat after wygenerowany: 543.6574765 s, bez fallback=True. NASTĘPNY KROK: import i kamery after.

Import after zakończony.

Zapisano after/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Docelowy import B: bliska kamera wyspy Low clear zapisana, bez globalnych rq override. NASTĘPNY KROK: final_details.py i pełny EditMode.

Docelowy import B: bliska kamera wyspy High clear zapisana, bez globalnych rq override. NASTĘPNY KROK: final_details.py i pełny EditMode.

EditMode zakończony: exit 0; szczegóły EDITMODE-STATUS.md i final-editmode.xml.

Docelowy B: pełny EditMode493/493,0failed/skipped. Wszystkie122kamery×4 mają delta scene/instance/shadow draws0 i dokładne tris0; globalny URP identyczny tekstowo. Po ścisłym cleanup455/458matów identycznych SHA, tylko3polityki różnią się wyłącznie keyword/scale0, zero nowych. Cofnięto138szumów cache, zachowując właściwą korektę. NASTĘPNY KROK: oględziny kompletów obrazów i końcowycritic; fidelity/GIS czekają na slotheavy.

Fidelity odświeżone dla końcowego generatora r3 B; pełny GIS może sprawdzić świeży raport.

Autor obejrzał wszystkie24author-overviews(488par),26crops i8foto. Critic końcowy PASS zakresu statycznego B; brak nowej konkretnej regresji do poprawy. FIDexit0, pełnyGIS już działa w slocieheavy. Usunięto2zastąpione duplikaty arkuszy materiałowych; dowody diagnostyczne i końcowe pozostają. NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r3/final-gis.log -Tail 5

Pełny GIS zakończony: exit 0; szczegóły GIS-STATUS.md oraz final-gis.log.

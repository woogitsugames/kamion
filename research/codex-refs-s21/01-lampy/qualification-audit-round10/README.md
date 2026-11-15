# Audyt kwalifikacji M59 — runda10

**Nowy audyt obrazu:10/45=22,22%, opisy zgodne10, sprzeczne0. M59 pozostajeNIESPEŁNIONE.** Główny manifest początkowo miał41wierszy, lecz w trakcie dodano opublikowany Proplast: końcowy snapshot45 (8lokalnych/37link-only),SHA256 `6582c9632f3828a4285f245b101e6c046681d83757595d1911460341cdb24282`. Próg≥20% to9. Nie doliczono peerProplast drugiego agenta do osobistych10.

Metoda: celowo dobrano tylne optyki, noc i lampkętablicy. Nowy jawny seed2026111510 służy wyłącznie powtarzalnemu porządkowaniu10wybranych ID przezSHA256(seed:id); **nie udajemy losowego doboru po fakcie ani statystycznej oceny pozostałych35**. Obraz każdego ID obejrzano osobno:3lokalneID (005/006/RN3-04; dla005/006 osobno całość i istniejący detal) oraz7publicznych link-only. Browserowe obrazy otwarto dokładnie pod zapisanym adresem. 0pobrań,0zapisanych screenshotów i0nowych fotografii. Szczegółowe własne obserwacje oraz porównanie z manife­stem w `audited10.csv` i`visual-audit.json`; dokumentacyjna klasyfikacja reszty w `inventory45.csv` wyraźnieNOT_REVIEWED_W_TEJ_RUNDZIE.

## Kryteria, bez podnoszenia i obniżania progu

Źródło: `docs/owner/MISTRAL-FIXES-12.md` M59-FIXpkt2/4 i`docs/reports/REVIEW-2026-11-15-s20-mistral-m59-fix.md` pkt1/FIX4. ≥15zbliżeń tylnych lamp zespolonychECE ciągników/naczep; lampa≥10% szerokości kadru **albo** ≥300px szerokości na wycinku z oryginału. W tej grupie≥4włączone i≥3zmierzch/noc; osobno≥5lampek tablicy ciężarówek/naczep. Pełny numerE+funkcje raportujemy osobno — nie dopisujemy wymogu pełnego numeru jako nowego literalnego progu15. Widoczne marki służą wyłącznie referencji kształtu. Samo10R lubMD nie jest pełnym dowodem fotometrii.

## Co rzeczywiście potwierdzono w próbce

SOURCED [nowe indywidualne oględziny, audited10.csv]: **8kadrów dużej tylnej optyki** spełnia geometryczny wariant≥10% z dużym marginesem. Nie wykonano dokładnego pomiaru każdej szerokości; opartoPASS na widoczności większości kadru/około1/3, nie na przypadkach granicznych. Szerokość odnosi się do pola obrazu bez czarnych marginesów przeglądarki. Lokalne detale005/006 są istniejącymi pochodnymi; nie nowymi fotografiami.

- **4potwierdzone źródłowo jako właściwy typ i geometrycznie**:01-005 naczepa,01-006 ciągnik,01-EUP-001 naczepa,01-EUP3-002 detal lampy naczepy. To4odrębne zdjęcia; nie4zweryfikowane certyfikaty. 005/006bez czytelnegoE, EUP3z przyciętymE9; EUP-001maE9/5497 i funkcje. Formalny statusECE/certyfikat i brakujące przyporządkowania funkcji są jawnie wCSV.
- **4dalsze fizyczne tylne lampy ciężarowe z geometriąPASS**:MAN-001,UP3-01,UP3-04,UP4-03. Zastosowanie do europejskich modeli jest w zapisanych źródłach; konfiguracja **ciągnik** zamiast innego wariantu ciężarowego nie została tu potwierdzona. Zostają cenną referencją, lecz stricttypUNVERIFIED. DAFma tylkoE2; MANpowiązana etykietaMD/EMC nie domyka fotometrii.
- **RN3-04**: rzeczywista czerwona emisja za ciągnikiem i czerwone odbicia na mokrym podłożu, nocPASS. Pojedyncza grupa lamp jest na800px miniaturze wyraźnie węższa niż80px; wariantu300px na oryginalnym wycinku nie badano. To **1kontekst emisji,0potwierdzonych włączonych/nocnych zbliżeń**. Nie zamieniamy dwóch lamp w dwie fotografie.
- **HP7-04**:1fizyczne okno optyczneSIM; zastosowanie tablicoweKrone/Schmitz z oferty, nie z domysłu po kształcie. E/L/numer i emisjaUNVERIFIED. To1część, choć jej opublikowana galeria ma4kadry. Proplastjest drugą rodziną ze źródłową funkcją, lecz nie był nowo oglądany przeze mnie wtym audycie i nie dodaje się do10z peer drugiego agenta.

Pozostałe35nie są nowymiPASS. `inventory45.csv` wskazuje13potencjalnych kadrów tylnej optyki według dotychczasowej dokumentacji — nie13zweryfikowanych dziś kwalifikacji. PrzódFH4/Renault/Commons, strażacki innego typu, katalogi o niepewnej technice, MD/EMC, etykiety, złącza i logo pozostają odrębne. DetalEUP3zL nie jest samym w sobie fotografią tablicowego okna. GeneryczneLNKnie mają potwierdzonego ciężkiego zastosowania; dolne okienkoUP3-07ma funkcjęUNVERIFIED.

## Egzemplarze i brakująca praca

EUP-001/EUP-002 to1część; EUP3-001/002/003 to1część; MAN001/002 to1; UP3-04…07 to1; UP4-03/04 to1; HP7-01…04 to1rodzina/część. Przeciwne konfiguracjeUP3-01/02 iUP4-01/02 nie są automatycznie jednym egzemplarzem. ProplastMenge2 nie dowodzi dwóch osobno sfotografowanych egzemplarzy. Globalna liczba fizycznych lamp45kadrówUNVERIFIED; nie sumujemy obrazów etykiet jako nowych lamp.

Z samej potwierdzonej próbki brakuje co najmniej11do15właściwych typem/geometrią kadrów; to **nie twierdzenie, że nieoglądane35są bezwartościowe**. Wymagają osobnego sprawdzenia zamiast automatycznegozaliczenia. Cała podgrupa4włączonych/3nocnychzbliżeń pozostaje otwarta. Dwie znane fizyczne rodziny tablicowe nie zamykają5urządzeń/referencji; powtórne fotografie tej samej części nie mogą udawać5niezależnych lampek. Brak2,5cd/m² w kadrze nie jest błędem fotografii — zdjęcie nie jest pomiarem laboratoryjnym.

Nie zmieniono parentmanifestów/opisów, nie kopiowano firmowych zdjęć, nie wykonywano git. Raport nie deklaruje domknięcia15/4/3/5 ani pełnej recenzji wszystkich45.

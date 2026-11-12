# Stan furniture r3

Runda2 zamknięta5d7ff5c9, artifacts skopiowane do main:1908 plików,4,249GB,
robocopy exit1. Ta sama lokalizacja worktree, gałąźgpt-furniture-r3 z r2.
Scalono main889201d5 do tej gałęzi, bez merge do main/push.
Konfliktujące generatedJSON/GLB orazprops_meta przyjęto z main do regeneracji.
materials.py iLICENSES zachowują oba addytywne dopiski; fabrykaPBR połączyła się
bez konfliktu. Kod r2 nie wymaga ponownych zmian do rozpoczęcia baseline.

Zakresr3:przystanki,wiaty,kosze,słupki według Mapillary, bez barier drogowych.
Referencje przygotowane w artifacts/furniture-r2/24h/bus-reference-preview,
shortlista zawiera autorów/licencje/hashe. Czerwona wiata przy5802408812
potwierdzona zdjęciami2018 i2024; druga przyFabryceDywanów widoczna w2019.
Brak tagu shelter/bin nie dowodzi braku obiektu; brak widoczności zdjęcia również.

NASTĘPNY KROK:przygotować baseline po merge (cachePBR jeżeli nieaktualny,
build_world w heavyOwner gpt-furniture-r3, import/rendery w UnityOwnergpt-furniture),
potem poprawić największe udokumentowane odstępstwo wiaty. WIP po każdym kroku.

2026-11-12T11:01:04.0365756+01:00: przygotowano helpery r3 z identyfikatorem artefaktówr3 i właścicielemheavy bieżącej gałęzi. Przed baseline sprawdzeniecachePBR:nieaktualnychplikówMedium=0. Baseline kolejnoPBR,world,snapshot,import,220 kadrówclear/overcast. Brak nowych zmian geometrii przed baseline.

2026-11-12T11:02:26.9638208+01:00: korekta pipeline:cachePBRMedium aktualny(0stale), więc wycofano wyłącznie własny oczekujący etapPBR przed rozpoczęciem (PID68624/72788/49776, brak dzieci pracyPython). Nie przebudowywać bez potrzeby. Baseline wznowiony odworld; żaden generator nie był przerwany. Sloty cudzych właścicieli nietknięte.

2026-11-12T11:03:05.7729976+01:00: oprava usunięcia etapuPBR:poprzednia zamiana tekstowa nie pasowała do końców linii. Ponownie zatrzymano tylko własne procesy oczekujące, bez pracyPython, usunięto obie linie etapupbr i jawnie sprawdzono ich brak. Właściwe wznowienie odworld następuje teraz.

2026-11-12T11:04:47.8512498+01:00: przygotowano mały helper kamer wiat z wygenerowanych instancji, uruchamiany po zakończeniu world przed importem baseline. Cztery kadry(front/corner dla dwóch potwierdzonych referencjami przystanków) są WORKING_VALUE, nie dopasowaniem zdjęcia. Zachowuje55 dotychczasowych kamer; docelowo59×4=236 baseline. Nie uruchamiano helpera na starych instancjach przed przebudową świata.

2026-11-12T11:06:14.7676534+01:00: obejrzano crop450px referencji2024:potwierdzony czerwony szkielet,szkło i profil dachu; zapisano OBSERVATIONS z ograniczeniami metrycznymi i zakazem globalnego kolorowania wszystkichwiat. Prototyp produkcyjny nadal niezmieniony; czekamy baseline po merge.

2026-11-12T11:09:20.2467484+01:00: dodatkowa referencjaWodociągi983799980108126 obejrzana≤960, odrzucona jako dowód rodziny wiaty z powodu niewystarczającej widoczności. Bez rozszerzania zmian na wszystkie przystanki. Baselineworld nadal oczekuje w heavy; proces65664 potwierdzony.

2026-11-12T11:19:06.9450335+01:00: heavy world before; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T11:20:39.6922644+01:00: world baseline zakończony510,1s,64GLB,479MiBHigh/150MiBLow, brakfallback=True. Geometrysnapshot czeka naheavy. Mały helperJSON przygotował59 kamer, w tym4zbliżenia wiat; pochodzenie/hash instancji zapisano. Pozycje i powiązanie najbliższego źródła nadalWORKING_VALUE do obejrzenia renderów.

2026-11-12T11:20:55.9543893+01:00: doprecyzowanie liczbykamer:plik zawiera11 własnych wpisów(7z r2+4wiaty); oczekiwane59 obejmuje również kamery sceny, musi zostać potwierdzone logiem renderera. Źródła przystanków mają odległość1,06m i1,59m od wybranych instancji. Nie traktować11 wpisów jako pełnej liczby kadrów ani59 jako już wyrenderowanych.

2026-11-12T11:22:46.0832558+01:00: heavy geometry before; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T11:24:14.6230225+01:00: Unity import before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:24:48.1357883+01:00: Unity render before Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:25:15.0764235+01:00: Unity render before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:25:59.7451223+01:00: Unity render before High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:26:17.3199219+01:00: import baselineOK,6833payloady przed zmianą zapisane. Low-clear iLow-overcast po59PNG. Obejrzano4zbliżeniaLow-clear(front/corner obu wiat):potwierdzony płaski dach, ciemne nieprzezroczyste panele i osadzenie na trawie obok chodnika. Zlecono niezależną ocenę tych4widoków i referencji450px; nie zmieniać cudzej nawierzchni/budynków. Highbaseline trwa. Modelr3 nadal niezmieniony.

2026-11-12T11:26:32.5077208+01:00: Unity render before High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

# 0098 — światło i post-process r12
Data: 2026-11-11. Status: wdrożone w `gpt-light-r12`, niezależny przegląd PASS; bez merge na main.
Problem: High wzmacniał szum nieba i prześwietlał jasne ściany; cienie hali tworzyły pasy i trójkątne plamy.
Decyzja: wyłączyć dithering nieba przed LUT na profilach post; zachować końcowy dithering URP chroniący przed pasami.
High zachowuje FSR/EASU, przy jawnym `fsrSharpness=0`; zainstalowany URP pomija wtedy keyword RCAS.
Clear używa `lookWhiteClip=1.2` jako WORKING_VALUE; ekspozycja i kotwice asfaltu/szarości pozostają stałe, overcast bez zmiany.
Medium/High: bias głębokości/normalnych 0.4/0.3; High rozdziela kaskady 0.20/0.55, przy tych samych 2048 px i 3 kaskadach.
Jawna semantyka `_ArchitecturalGlass` obejmuje wyłącznie `kp_glass_block`; odbiornik cienia Medium/High przesunięty o maks. 8 cm wzdłuż normalnej.
8 cm to najmniejsza zaakceptowana badana wartość WORKING_VALUE; geometria i ShadowCaster pozostają bez zmian, Low/Ultra mają domyślnie 0.
Przyczynę przeszkleń izoluje osobne wyłączenie realtime/baked sun; pozostaje rzeczywisty cień ram 6.59 poziomu, kontakt naczepy MAX różnicy 0.
Profil revision98 i generowanie URP zapisują politykę w assetach; `rq_*` służy odtwarzalnym ablacjom, finalne obrazy używają pustego Rq.
High clear: RMS nieba 3 px 1.827→0.555; szczyt domu 254.671/243.840/212.340→240.836/229.444/195.223, czerwony p95=241.
Koszt jakości: przy proxy skali 70% krawędź farby 2.218→2.551 px, kontrast cyfry kabiny 128→126; czytelność zachowana, dodatkowa miękkość jawna.
Low: identyczne statystyki CPU obu warunków i niezmieniona polityka; wynik nie jest pomiarem GPU telefonu.
Weryfikacja: świeży build/import, 192 SHA, 236 PNG przed i po + wybrane lowsun/Medium; GIS 355 PASS/2 xfail, EditMode 221/221.
Dowody: `artifacts/light-r12/{REPORT,REVIEW,SELF-CRITICISM}.md`, `final-metrics.json`, `floor/edge-metrics.json`, `shadow/glass-acceptance-metrics.json`.
Ograniczenia: GPU/termika i rzeczywisty device EASU UNVERIFIED; kalibracja KP/noise-wall należy do ADR0101, materiały/roślinność do innych strumieni.

## Uzupełnienie po niezależnej recenzji s10 (2026-11-11)
Scalenie ocenione warunkowo PASS, jakość całego celu0098 — FAIL.
Recenzja: docs/reports/visual/REVIEW-2026-11-11-s10-0088-0098.md na main.
P0: RCAS=0 rozmywa asfalt przed kabiną; wcześniejsza akceptacja tego kompromisu
jest wycofana. Zysk nieba pochodzi głównie z wyłączenia ditheru przed LUT.
Pozostały pieprz ścian, falisty brzeg cienia przy lowsun; mgiełka i AO były
udokumentowanym stanem istniejącym, nie nową realizacją tych celów.
Testy355 passed/2xfailed i EditMode221/221 oraz identyczne stats pozostają
potwierdzeniem poprzedniego kodu, nie akceptacją jakości ani wydajności GPU.
Lider przydzielił0108 / gpt-light-r13 w GPT-FEEDBACK-S10.md: po bieżących
F/G/E/D, przed roślinnością0109. Ten zapis nie zmienia kodu i nie scala main.
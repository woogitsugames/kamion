# S10 — raport końcowy pakietu A–G

Pakiet GPT-TASK-02-S10 został zamknięty technicznie: osobne gałęzie/worktree, commity WIP i STATUS po krokach, raporty oraz kopie artefaktów. **Nie jest to zbiorczy PASS wyglądu.** Część celów wizualnych nie została osiągnięta i jest jawnie przekazana do kolejnych rund. Ta sesja nie scalała ani nie pushowała main; wcześniejsze A/B/C/F/E integrował lider Claude. D/G pozostają do jego integracji.

Wyniki poniżej odnoszą się do przypiętych wersji poszczególnych gałęzi, nie do jednego wspólnego testu aktualnego main.

| Strumień i gałąź | Źródła / walidacja | Ograniczenia i dalszy właściciel |
|---|---|---|
| A /0086, gpt-tint-gamma | 1317afba; GIS359+2xfail, EditMode226. Lider poprawił kalibrację hali/ekranów w0101; późniejszy test main245/245. | Proceduralny wygląd hali pozostaje poza poprawką kontraktu tintu. |
| B /0088, gpt-vegetation-r2 | Kod4db366ad, raport63fa644f; GIS364+2xfail, EditMode218. | Jakość FAIL: korony Putry, sosny, żywopłoty i trawa. Kolejna dziedzina vegetation /0109. |
| C /0098, gpt-light-r12 | Kod5db77e9d, raport77b718c4; GIS355+2xfail, EditMode221. | Wycofano akceptację rozmycia High. C13/0108: RCAS, niebo, cienie, ekspozycja i mgła. |
| F /0087, gpt-truck-paint | Źródła2086e780, późniejsze dowody8ecfca00; GIS370+1xfail, EditMode238,102 pary. | Wygląd PARTIAL/FAIL: kredowy lakier, jasny dach, szkło i clipping DRL. Kolejna dziedzina truck /0115, także FragFast. |
| E /remiza r7, gpt-firestation-r7 | Runtime63c7a76f; GIS375+1xfail, EditMode227,160 par i16 kontroli ścieżek Low/High. | PARTIAL: szkło clear za jasne, odwrócony gradient, wąskie/blade korony i subtelne zacieki. Historyczne pary pojazdów mają lukę kadrowania. Kolejna dziedzina landmarks /0116. |
| D /0099, gpt-surface-wear | Zwalidowany kod0d51805c, zamknięciee78d919a; późniejsze audytyc7306100. GIS388+1xfail, EditMode240,372 pary. | Techniczny nonregression PASS; cel asfaltu FAIL według recenzji lidera. Sterylność Low, brak szerokich łat/kolein/spękań pozostają. Przekazanie asphalt /0118 z tej gałęzi po merge main. |
| G R4 /0089, gpt-car-paint | Zwalidowane źródłabf83923a; końcowe przekazanie4dd22764, czysta gałąź. GIS526+1xfail638.73s i EditMode274/274, oba exit0.368 par; liczniki bez zmian. | Naprawa plam i tablice PASS w sprawdzonym zakresie; fotograficzny realizm kurzu PARTIAL. Dalsza dziedzina life zachowuje te ograniczenia. |

## Końcowe dowody G

ROOT obejrzał184 pary Low, E niezależnie184 High, z dodatkowymi kontrolami natywnymi. ROOT samodzielnie porównał368 par pozy/liczników i736 pakietów live: wszystkie wybrane pola pozy zgodne, dziewięć liczników bez zmian, właściwy shader tablic i MotionVectors wyłączony. Oddzielny odczyt GPU260 potwierdza numeryczny wybór komórek; jego ograniczenia są w recenzjach.

Pełny generator PBR odtworzył443 PNG/spec identycznie; ROOT niezależnie zahashował bieżące443 pliki. Po GIS ROOT sprawdził192 raw,90 elementów pojazdów i40 źródeł: zero rozbieżności. Fab15 bez fallbacku. Niezależnie potwierdzono kopię736 obrazów QA i12 metadanych do głównego artifacts; prywatne native/preplate/cache/raw snapshoty wykluczono.

Koszt G jest jawny: estymacja payload UV1 +584576B, P2 tablic zero dodatkowego stride i tekstur. D niezależnie sprawdził +170368B projekcji mipów ASTC i +1813016B estymaty desktop Profiler. Porównanie tekstur to zależności sceny względem kontrfaktycznej podmiany bindingów R3, nie zmierzona historyczna rezydencja GPU. A16, czas GPU, termika i rzeczywisty pipeline upscale pozostają UNVERIFIED; telefonu/ADB nie używano.

## Przekazanie

Raporty strumieni: artifacts/{tint-gamma-r1,vegetation-r2,light-r12,truck-paint-r1,firestation-r10,surface-wear-r1,car-paint-r1}/REPORT.md. Recenzje koordynatora i niezależne JSON są w artifacts/s10. Integracja wymaga unii wspólnych bloków shader/material/importer i kanonicznej regeneracji; same zielone testy nie stanowią akceptacji fotograficznej.

Aktualny main65f8829b wprowadził osobny pakiet GPT-TASK-05-24H i sesje dziedzinowe, które przejmują dalsze rundy. C13 preflight jest gotowy w C13-DISPATCH.md, ale **C13 nie uruchomiono**; przydział tej dalszej pracy został zgłoszony użytkownikowi do wyjaśnienia. Nie rozszerzano samodzielnie tego przebiegu do wszystkich10 sesji ani24h backlogu. Następne uruchomienia Unity wymagają nowego release, scripts/unity-slot.ps1 oraz bezpośredniej kontroli PHONE/HOLD. Token G zakończono, własny monitor86680 zamknięto jego flagą stop.

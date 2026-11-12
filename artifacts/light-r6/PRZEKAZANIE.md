# Przekazanie sesji light — 12 listopada 2026

Pracę wstrzymano na polecenie właściciela z powodu zbliżającego się limitu tygodniowego. Cel 24-godzinny nie został oznaczony jako wykonany. Nie uruchamiać kolejnych rund bez nowego polecenia właściciela.

## Najważniejsze teraz

Istniejący kontroler przygotowania rundy 6 nie został przerwany. W chwili przekazania `BuildWorld` czekał w kolejce heavy. Po uzyskaniu slotu może jeszcze wygenerować świat i sam zwolnić slot. Nowa faza Fidelity zostanie zatrzymana przed Acquire i przed uruchomieniem Pythona przez marker `STOP-REQUESTED.txt`. Import, Unity i baza obrazów nie zostaną uruchomione przez ten kontroler.

Kontroler: PID **73184**, początek 14:06:09; uchwyt narzędzia **15781**. Repo: `C:\Users\matma\Documents\Claude\kamion`. Worktree: `.claude/worktrees/gpt-light`. Gałąź: **gpt-light-r6**. Nie przełączać gałęzi ani nie usuwać worktree, dopóki kontroler i zapis końcowy nie zakończą pracy.

Plik **STOP-COMPLETED.json** i końcowa sekcja tego dokumentu zostaną dopisane przez lekki skrypt `finish-requested-stop.ps1` po samoczynnym zakończeniu kontrolera. Nie uruchamia on pracy produkcyjnej ani testów: czeka, zapisuje pozostały stan, wykonuje WIP i robocopy własnych artifacts do main. Nie zabija procesów i nie usuwa slotów. Jeśli slot pozostanie lub zmieni się gałąź, zapisze potrzebę inspekcji.

Kod 130 przed Fidelity i późniejszy komunikat kontrolera o tej fazie oznaczają żądane zatrzymanie, a nie nieudany test. Jeśli World zakończy się błędem wcześniej, końcowy zapis zachowa log i oznaczy konieczność inspekcji.

## Co jest ukończone

Rundy **1–5** mają REPORT, ADR 0108, commity oraz artifacts skopiowane i zweryfikowane w głównym repo. Bez pushowania i bez scalania do main przez tę sesję. Ostatnia zamknięta runda 5: końcowa dostawa `00e03bb1`, raport `7b550c1b`; EditMode **341/341**, GIS **690 passed, 1 xfailed**, 865,12 s.

Najważniejsze rezultaty: RCAS High 0,75 z poprawnym jawnym zerem; fotograficzne chmury CC0 i korekta granicy dolnej półkuli; korekta białego klipu; preset Night i prezentacja ciemnych kolorów. Eksperymenty headlamp, lokalnych mokrych odbić i natywnej LUT nie są zatwierdzonymi rozwiązaniami produkcyjnymi. Natywna LUT pozostaje domyślnie wyłączonym eksperymentem Editor. Nie ma nowego pomiaru GPU lub telefonu.

Runda 5 wyjaśniła, że standardowy VisualQaRunner używa ARGB32 także dla High. Osobny LightHdrQaReference ma faktyczny dowód R16Half przed postprocessingiem. Czysty native lab v6 ma 65 obrazów dla pięciu presetów; final-native-v2 ma 654 obrazy, 109 kamer, wszystkie obejrzane przez rodzica/krytyka. Poprawa koloru nie oznacza zgodności całej klatki: regresje Overcast w kabinie, szkło, geometria i koszty GPU pozostają otwarte.

## Runda 6 — rzeczywisty stan

R6 zaczęto od main `3cdd6da465b82d9687f27ad95ec5fce692e1898b` (merge `1549384c`). Odświeżono wymagane raw, Generated i LFS; junctiony pozostają tylko do odczytu. Bazowy SHA przed przygotowaniem zatrzymania: `9d77e9ccf7b907512386a5307577bfdb616f8052`.

**Materiały ukończone:** BuildAll kod 0, 588 s; CC0 verify 13 assets / 65 files / 0 problems. `materials-checkpoint.json` ma 151 plików Medium; wszystkie hasze sprawdzono ponownie. Logi i checkpoint są w WIP (`1e244eef`); punkt kontynuacji `d63ac005`.

**World:** w chwili przygotowania przekazania nadal w kolejce. Log kolejki: `heavy-BuildWorld-20261112-153549.log.acquire-1.log`; rzeczywisty log powstanie jako `heavy-BuildWorld-20261112-153549.log`. Nie powtarzać Materials. Aktualny wynik World, obecność `world-checkpoint.json` i faktyczne zwolnienie slotu trzeba odczytać w końcowej aktualizacji / STOP-COMPLETED.

**Jeszcze niewykonane w R6:** Fidelity, import, świeża baza 1090 obrazów, nowe obrazy po zmianie, testy końcowe, REPORT kończący rundę. Brak nowego visual PASS i brak zatwierdzonej poprawki P1 horyzontu. Kod gry w Assets nie został w R6 zmieniony; prototypy są wyłącznie w artifacts.

## Przygotowane materiały do dalszej pracy

- `baseline.json`: 109 kamer × Clear/Overcast/LowSun/Dusk/Night × Low/High HDR, razem 1090 obrazów. Jawny plik 61 dodatkowych kamer, 48 bazowych; twarde expected 109. `make-contacts.ps1` pomija kostki/maski i zapisuje hasze źródeł.
- `horizon-triage.json`: 90 obrazów dla trzech kamer, pięciu presetów, obu tierów: samo niebo, samo niebo bez obu rodzajów chmur, świat bez warstwy mgły przy ziemi. `rq_haze=0` pozostawia jednorodną mgłę. Plan i niezależna recenzja są w HORIZON-TRIAGE-PLAN oraz review/HORIZON-METHOD-REVIEW.
- `horizon-prototype/`: pięć **niekompilowanych** kopii źródeł i testy LightCloudHorizonTests. Opcjonalny yaw-only domyślnie OFF, QA zmiany elewacji, sonda rzeczywistych shader globals. Manifest source/candidate SHA. Nie kopiować w ciemno: najpierw świeża baza i oględziny. Yaw-only nie dopasowuje wysokości światła chmur i zmieni też capture; nie jest wybranym rozwiązaniem.
- `verify-horizon-state.ps1`: wymaga nowych pól sondy. Sprawdza rzeczywiste wyłączenia chmur/mgły, globalne exposure i lamp activation, elewację oraz aktywną rotację. Nie uruchomiono go na R6, bo nie ma jeszcze takich renderów.
- `night-pool-ablation.json`: 10 przyszłych obrazów office1/2, Low 0/4 i High 0/4/8 pul, istniejący rq_lamppools. Nie podnosi Low ponad produkcyjne 4. Dopiero po bazie; P1 horyzont ma pierwszeństwo.

## Ważne ustalenia, których nie należy upraszczać

Szeroki szaro-beżowy pas przy horyzoncie pozostaje P1. Nie jest automatycznie dawnym ostrym wycięciem źródła chmur. SkyModel dostarcza niezależny kolor horyzontu do sky/fog/reflection; samo wyrównanie obrotu fotograficznej mapy może nie pomóc. Sprawdzić inne wysokości słońca: 9/25/42/60 stopni. Bez wyników nie podnosić EV ani nie dobierać koloru mgły ze zdjęcia o innym świetle i filtrze szyby.

Historyczne Night R5: wszystkie 109 kamer mają dodatnie wybrane pule, ale w 15 żadna sonda środka pod lampą nie leży w kadrze. Nie dowodzi to braku oświetlenia. Office2 ma jasne plamy i ciemną głowicę. Cztery obejrzane tory (Low produkcyjne, Low native, High legacy, High HDR) pokazują ciemną głowicę, a oba High biały trzon. Actual probe: Low 4 pule / 0 point, High 8 / 4 przy tej samej ekspozycji. To nie dowód przyczyny lub actual shadera trzonu.

Surowy GLB przed regeneracją zawiera soczewkę we wszystkich 16 renderowanych węzłach lamp, także LOD1. Bounds lamp_10m pokazują około 1 mm odstępu pod obudową; pozycje Unity są Float32, Forward respektuje Cull. Zarejestrowane materiały z emisją nie dowodzą przypisania do konkretnej soczewki w draw. WorldInstances zeruje m_BatchCount po Flush; resztki macierzy po endCameraRendering nie są actual draw proof. Nie poprawiać tego przez bloom, zwiększoną emisję lub cudzą geometrię bez dowodu.

Nominalne 200000 cd/m² × historyczne modelExposure daje przed dalszym tone około 14146 dla Dusk i 35418 dla Night, poniżej 65504. To nie ogólny audyt operacji half ani pomiar actual global/material. Szczegóły: NIGHT-POOL-NOTES, NIGHT-LENS-FOLLOWUP, historical-emission-range i night-lens-history/states.json.

## Zasady wznowienia

1. Najpierw przeczytać docs/owner/GPT-TASK-05-24H.md, bieżące HANDOVER/feedback i ten dokument. Oryginalny termin 24 h wynosił 12.11 21:30:47 Warszawa; dalszy czas ustala właściciel po tej pauzie.
2. Sprawdzić STOP-COMPLETED, STOP-ACK, logi, PID i slot. Nie zakładać zakończenia z samego pliku blokady. Nie uruchamiać drugiego heavy z tym samym ownerem.
3. Skrypt końcowego zapisu zachowa zmienione pliki śledzone oraz patch w stop-generated-snapshot, a także pozostawi wynik generatora w worktree. Nie usuwać raw/derived lub worktree. WIP dotyczy własnych artifacts; nie włączać wygenerowanych zmian innych dziedzin do produktu bez normalnego zamknięcia rundy.
4. Dopiero po wyraźnym wznowieniu przez właściciela zarchiwizować marker STOP-REQUESTED pod inną nazwą. Jeśli World checkpoint i jego źródła/hasze są zgodne, wznowić `pwsh -NoProfile -File artifacts/light-r6/regenerate-baseline.ps1 -StartAt Fidelity`. Jeśli World nie ukończony, najpierw zdiagnozować log i wybrać właściwą fazę. Nie restartować wszystkiego od Materials.
5. Po bazie obejrzeć wszystkie kadry, niezależny krytyk High, potem triage P1. Pełny GIS wyłącznie na końcu rundy. Brak REPORT R6 oznacza brak zamkniętej rundy.

Ciężki Python: centralny `scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-light-r6`, Release po każdej fazie. Unity: owner **gpt-light**, osobny Acquire/Release; heavy zwolniony podczas oczekiwania/renderowania. Bez Priority i bez usuwania cudzych slotów/PHONE_RUN. Używany helper jest z main, PollSeconds 5, StaleHours 87600. Limity NumPy/BLAS/OpenMP ustawione na 1. Bez telefonów/adb, push i merge do main. Root STATUS należy HUD.

## Gdzie są pliki

Worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-light\artifacts\light-r6`.
Kopia dla właściciela: `C:\Users\matma\Documents\Claude\kamion\artifacts\light-r6`.
Własny bieżący STATUS, szczegóły wznowienia CONTINUE i ADR `docs/adr/0108-light-sky-exposure-post.md` są zapisane. Ta kopia jest przekazaniem przerwanej rundy, nie REPORT końcowym ani zgodą na integrację.

# Przekazanie sesji asphalt — wstrzymanie na prośbę właściciela

Praca została wstrzymana 12 listopada 2026 r. z powodu kończącego się limitu tygodniowego. Nie ubito procesów. Dalsza pętla i ponowienie kamer wymagają nowego polecenia właściciela. **Runda 3 jest WIP, niegotowa do scalenia.**

## Miejsce pracy

- Repo główne: `C:\Users\matma\Documents\Claude\kamion`.
- Jedyny worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-asphalt`.
- Gałąź: `gpt-asphalt-r3`. Baza: merge `e5eb5902`, zawierający main `11db0552` i poprawkę lidera ADR 0131.
- Szczegóły zapisano w `artifacts/asphalt-r3/STATUS.md`, `SESSION-STATE.json` i `docs/adr/0118-asphalt-material.md`.
- Nie wykonano push ani scalenia do main. Kopia artefaktów w main jest wyłącznie migawką plików.

## Co jest ukończone

Rundy 1 i 2 dostarczono wcześniej na gałęziach `gpt-asphalt-r1` i `gpt-asphalt-r2`. Ich raporty są w `artifacts/asphalt-r1/REPORT.md` oraz `artifacts/asphalt-r2/REPORT.md`. R2: 328 par i wszystkie 2952 liczniki bez delty; EditMode 312/312, GIS 604 passed i 1 oczekiwany xfailed. Physics/gate3: 47 passed i 1 historyczna porażka odtwarzalności. Lider ocenił przyrost materiału jako PARTIAL / scalenie warunkowe, bez zatwierdzenia pełnego realizmu lub Gate3.

Historyczne wskaźniki kontrastu śladów kół R1 0,970/0,972 zostały wycofane: błędnie odtworzono wysokość kamery. Nie używać ich ani starych masek jako dowodu. Sprostowania są zapisane i przekazane. Main później naprawił test fizyki w `b1c83d58`; wynik R3 wymaga nowego sprawdzenia.

## Aktualna runda 3

Zakres: materiały placów przemysłowych poza Kwadratem. **Nie wybrano ani nie wdrożono zmiany produktu R3.** Nie zastępować tego zadania samą drobną korektą publicznej kostki.

1. Przygotowanie worktree i surowców wykonano. Wcześniejszy build materiałów: exit 0, 515 s, pod heavy. Po synchronizacji ADR 0131 źródła `_src` nie zmieniły się, a cache przeszedł kontrolę świeżości, więc go wykorzystano ponownie.
2. Nowy kanoniczny World: **exit 0, 624,7 s**, zakończony 15:47:52. Manifest SHA256: `BF4A2C8F5DD033E22868E642BAFF744EACF5DDF5AD0A25236786B71DAD777B1B`. Potwierdzono **196 odwołań/SHA bez rozbieżności**. Megascans: 15 dostępnych zestawów, 320 propsów, brak literalnego `fallback=True` w logu. QA nie ma jawnego pola fallback. Dowody: `baseline-producer-progress.json`, `baseline-world-check.json`.
3. **Świeży import zakończony exit 0 o 16:19:10.** `current-import-state.json` ma complete=true i powyższy SHA manifestu. Wyniki: `baseline-import.json`, `baseline-import-progress.json`, `baseline-import.log`. Ustawienia Unity przywrócono w finally. Nie zaliczać starego importu pre0131 do tej bazy.
4. Przygotowano 39 kamer pomocniczych, w tym cztery inspekcje PCRT. `material_inspection` z `seat=road` oznacza kolizję +2,5 m; początkowe U=150 jest tylko roboczym początkiem raycastu. Nie jest zmierzoną wysokością ani dopasowaną pozą fotografii.
5. Pierwsza próba kamer zakończyła się **exit 1 przed uruchomieniem Unity**, przez błąd składni warunku wrappera. Poprawiono go w `eb9c5fc4`; parser przechodzi. Po poleceniu zatrzymania nie ponawiano próby. Brak zaakceptowanych nowych PNG i pełnego baseline.

## Pozostawiony proces — bez ubijania

W chwili przygotowania przekazania **PID 13412**, `post-world-baseline.ps1`, sesja narzędzia **15215**, był aktywnym oczekującym procesem heavy. Należy sprawdzić stan ponownie, bo może się zmienić po zapisaniu pliku.

To wcześniej zakolejkowany, skończony łańcuch: YardProbe → GeometryAudit → opcjonalny mały wycinek ortofotomapy. Sam zwolni slot i zapisze WIP/STATUS oraz `baseline-analysis-progress.json`. Nie uruchamia po sobie Unity ani zmiany produktu. Może dopisać commit po commicie przekazania. **Nie uruchamiać drugiej kopii, dopóki istnieje.**

Pozostałe zadania są terminalne: World 87456/exit 0; import 13823/exit 0; próba kamer 82908/exit 1. Dawne PID 43640 i 17940 zakończyły się. Nie restartować gotowego World lub importu.

Źródłem prawdy pozostaje worktree. Kopia artefaktów w main jest migawką zatrzymania. Późniejsze wyniki pozostawionego procesu mogą być tylko w worktree do następnego kopiowania.

## Dowody i narzędzia do wykorzystania

- `DIAGNOSTICS.md` i wcześniejsze PNG są **pre0131**. Wskazały CRACKS jako źródło białych pętli oraz osobno grime na yard_paving/yard_behaton i road_paving. Nie stanowią aktualnego baseline.
- Biały połysk zalewki naprawił lider w ADR 0131 (`smooth +0,06`), nie R3. Pętle/kropki maski i czytelność ciemnej zalewki z kabiny pozostają P2.
- Referencja PCRT: Rakoon, lipiec 2020, CC BY 3.0, zazębiająca się kostka. Brak GPS i kierunku potwierdzono w oryginalnym EXIF. Nie ma dopasowanej pozy lub kalibracji albedo. Pełny oryginał pozostaje lokalnie poza Git.
- `reference/context-map-960.png` i sidecary pokazują kontekst źródłowy. Sąsiedni punkt zdjęcia wnętrza leży w obrysie BDOT C92B; nie ustala to pozy zdjęcia placu. Mapa przeszła własną i niezależną kontrolę czytelności, bez PASS produktu.
- Sonda odczytowa obejmuje E280–480/N−560…−300, 130 punktów z definicji. `within_r2_scope_envelope` oznacza położenie względem zakresu r2, nie aktywne wyłączenie każdego materiału. Ochrona produktu Kwadrat pozostała bez zmian.
- `run-unity-stage.ps1` zawiera slot, restore, kontrolę świeżego importu i `capture-context.json` z SHA źródeł. Snapshoty QA mają schemaVersion=3 i dziewięć rekordów materiałów.
- `audit-yard-poses.ps1` porówna rzeczywiste U (`anchorZ + position.y + originShift.y`) z paved GLB: wysokość 2,5 m ±5 cm. Nie dowodzi materiału każdego piksela lub pozy zdjęcia.
- Opcjonalne `behaton_preview` używa tymczasowych MaterialPropertyBlock i istniejącego materiału. Nie uruchomiono go. Najnowszy kod C# wymaga sprawdzenia kompilacji przy kolejnym Unity. Jego liczników nie używać do budżetu.
- Opcjonalna ortofotomapa powstanie w istniejącym heavy SourceAudit. `reference/ortho-context.json` poda available/unavailable; exit 0 geomaudytu nie oznacza powodzenia opcjonalnego obrazu.

## Wznowienie po nowym poleceniu właściciela

Najpierw sprawdzić `SESSION-STATE.json`, `STATUS.md`, pozostawiony proces i jego wynik. Nie zaczynać od ponownej generacji lub zmiany bazy. Brak starego PID wymaga odczytania wyniku, a nie automatycznego restartu.

Po sprawdzeniu istniejących wyników można ponowić wyłącznie próbę kamer, o ile nie powstała już taka próba:

```powershell
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-asphalt'
pwsh artifacts/asphalt-r3/run-unity-stage.ps1 -Stage Probe -Label yard-pose-post0131 -ProbeTier Low -ProbeLighting clear -Cameras 'asphalt_pcrt_front_context,asphalt_pcrt_long_context,asphalt_pcrt_surface_west,asphalt_pcrt_surface_east'
```

Wrapper sam bierze i zwalnia slot. Obejrzeć cztery PNG i po zgodnej sondzie wykonać `pwsh artifacts/asphalt-r3/audit-yard-poses.ps1 -Label yard-pose-post0131`. Odrzucone pozycje poprawić i sprawdzić nową próbą z unikalną etykietą. Następnie wyprowadzić `capture-plan.json` z rzeczywistego `camera-inventory.json`, zebrać pełny baseline Low/High × clear/overcast i dopiero wybrać zmianę produktu.

R3 nie ma kandydata, pełnego porównania, końcowych testów ani REPORT. Po zmianie nadal wymagane są generator, import, cztery serie, wszystkie kamery i dziewięć liczników każdej (instancje osobno), audyt geometrii, inspekcja arkuszy i niezależny krytyk. Pełny GIS dopiero na końcu rundy; ponadto EditMode, physics/gate3 i fidelity. **Końcowych testów R3 jeszcze nie wykonano.** GPU A16 pozostaje niezweryfikowane przez tę sesję.

Nie pushować, nie scalać do main, nie używać telefonów/adb, nie ruszać cudzych źródeł ani Claude. Nie usuwać cudzych slotów lub PHONE_RUN. Skrypt slotów zawsze z main, bez Priority: Unity Owner `gpt-asphalt`, heavy Owner bieżącej gałęzi; jedno własne ciężkie zadanie naraz. Zachować `_Tile`, liniowy `_Tint`, weather/runoff, draws trasy +0 / tris ≤+2% i ochronę Kwadratu.

Przyszły temat: zgłoszona w handover uwaga właściciela o szarej prostokątnej łacie na łuku. Nie oglądano tu filmu i nie ustalono, czy to decal_patch. Sterylność placu startowego dotyczy Kwadratu, poza tą sesją.

# Bramka 3 — Próbka jakości 300–500 m (szablon raportu dla właściciela)

Data: ____ · Commit / APK: `____` (SHA256 `____`) · Unity 6000.3.28f1
Telefony: Samsung Galaxy A16 (SM-A165F, RFGL34SJYDZ) · Samsung Galaxy S24+ (SM-S926B, RZCX60VE8ZY)
Plan i kryteria: `docs/plan/STAGE-3.md`. Odcinki: `Data/Regions/bialystok-industrial-c/gate3_segment.json`.

## Werdykt: ____ (SZKIC / ZALICZONA / NIEZALICZONA)
Jedno–dwa zdania: co działa, co nie, czy odcinek wygląda jak prawdziwe miejsce, a nie jak typowa gra mobilna. **Bramka jest zaliczona tylko z liczbami z telefonu i Twoją akceptacją kierunku artystycznego.** Render z edytora ani z Blendera tego nie zastępuje.

## Odcinek
- **G3-A** (domyślny): plac i rampy Kwadrat Park → brama → Rondo Bieżeństwa → początek łącznicy; s = 12–450 m, długość **436,7 m**.
- **G3-B:** gen. Andersa → Rondo Putry; s = 1232–1718 m, długość **485,9 m**. (Brama → Putry w jednym kawałku to 1468 m, za dużo na tę próbkę.)
- Co było mierzone: ____ (A / B / oba)

## Liczby z telefonu (z `artifacts/gate3/<ts>/<serial>/gate3-result.json`)
Pomiar na odblokowanym telefonie, zestaw 40 t na autopilocie. Odrzucone pomiary przy blokadzie nie są tu wpisywane.

| Telefon / profil | FPS cel | p50 [ms] | p95 [ms] | p99 [ms] | max [ms] | klatki >50 ms | PSS [MB] | temp. start→koniec [°C] | termika | Limit (p95 / p99 / PSS) | Wynik |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A16 Low | 30 | | | | | | | | | 34,0 / 40 / 1000 | |
| A16 Medium | 30 | | | | | | | | | 34,0 / 40 / 1200 | |
| S24+ High | 60 | | | | | | | | | 17,0 / 20 / 2000 | |

Limity to WORKING_VALUE z `docs/PERFORMANCE_BUDGETS.md`. GPU/CPU p50/p95: ____. Hitching (skoki >2× mediany) przy ____: ____.

| Rozmiar | Wartość | Limit |
|---|---|---|
| APK razem | Low 159,7 MB (`c59209e`, SHA256 `9e39e370...f5880a2f`) · High `-WorldHigh` 302,2 MB (`fefd804`, SHA256 `fae53320...e8657d`) (Stage 2: 48,5 MB) | brak twardego limitu — raportuję |
| Świat Low w APK | 140,0 MB (`world_bytes` z `*.content.json`, w tym siatki 97,4 MB; **ponad limit**, szacunek build report, nie z telefonu) | ≤ 110 MB (WORKING_VALUE, decyzja D24 z 2026-11-10; wcześniej 60 MB) |
| Draw calls / trójkąty w kadrze (z edytora, szacunek) | Low ___ / ___ · Medium ___ / ___ · High ___ / ___ | 250/350 k · 350/550 k · 800/1,5 M |

## Kamery kontrolne i porównanie ze zdjęciami (docs/06 §5)
Każdy wiersz: render z edytora **i** zrzut z telefonu, podpisane źródłem. Referencje: tylko CC0 w raporcie; zdjęcia właściciela z `Data/photos/` to obrazy z generatora (**„AI reference, not photo”**).

| Kamera | Render edytor | Zrzut telefon | Referencja | Werdykt (zgodne / niepewne / odstępstwo + powód) | visual-critic |
|---|---|---|---|---|---|
| `photo_biezenstwa_ground` | | | CC0 `20201102_152339` | | |
| `g3b_rondo_putry_approach` | | | CC0 `7204_May_2021` | | |
| Andersa, pobocze + straż pożarna | | | CC0 `7197_May_2021`, `20240626_103137` | | |
| brama / plac / rampy | | | brak prawdziwego zdjęcia — niepewne do sesji zdjęciowej | | |
| oko kierowcy co ~50 m (A: 9, B: 10) | | | — | | |
| kabina + lusterka w odcinku | | | — | | |

Stan kamer z `gate3-result.json`: CAPTURED ___ / MISSING_IN_SCENE ___ / SKIPPED ___ / REJECTED_LOCKED ___.

**Checklista anty-slop `docs/06` §5 (PASS/FAIL, FAIL blokuje):**
- [ ] 1. Zestaw kamer kontrolnych (stałe pozycje, FOV, pora dnia): ____
- [ ] 2. Render z edytora i zrzut z telefonu w raporcie: ____
- [ ] 3. Side-by-side z referencją w tym samym kadrze: ____
- [ ] 4. Przegląd `visual-critic` (inny agent niż autor): ____
- [ ] 5. Kontrole automatyczne (histogram albedo, texel density, tekstury w budżecie, normalne/UV, obiekty pod/nad terenem): ____
- [ ] 6. Wynik końcowy: ____

## Co zrobić na telefonie
1. **Odblokuj telefon**, wyłącz usypianie ekranu, zostaw podłączony kablem (tylko jeden proces Unity naraz).
2. A16: `pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30`, potem `-Tier Medium -SkipBuild`.
3. S24+: `pwsh scripts/gate3-run.ps1 -Serial RZCX60VE8ZY -Tier High -Fps 60 -WorldHigh`.
4. Wyniki: `artifacts/gate3/<ts>/<serial>/`.

## Test „feelingu” właściciela
Przejedź odcinek ręcznie (nie autopilotem), A16 Low i S24+ High. Do każdego punktu: tak / nie / uwaga.
- [ ] **Pierwsze wrażenie:** to wygląda jak prawdziwa ulica Białegostoku, a nie jak „typowa gra mobilna”?
- [ ] **Asfalt i oznakowanie:** wyświetla się jak polski asfalt (łaty, rysy, wytarte linie), nie jak plastik?
- [ ] **Kierunek światła i nieba:** pochmurno i słonecznie — czy kolory i cienie są wiarygodne?
- [ ] **Budynki:** hala Kwadrat Park / straż pożarna / wiadukt — czy rozpoznajesz miejsce? Co zdradza „sztuczność”?
- [ ] **Roślinność i pobocza:** drzewa, trawa, krawężniki, latarnie — czy gęstość i zniszczenie są właściwe?
- [ ] **Skala i prędkość:** czy 2,5 m oczu kierowcy, szerokość pasa i prędkość wyglądają realnie?
- [ ] **Kabina i lusterka:** czy widać, co trzeba, czy nic nie zasłania? Czy lusterka nie dławią klatek?
- [ ] **Płynność:** ruch płynny, bez szarpnięć przy rondach, wiadukcie i zmianie LOD?
- [ ] **Telefon:** nagrzewanie po ~2 minutach, czas ładowania sceny, brak zabicia procesu?
- [ ] **Decyzja:** akceptuję kierunek artystyczny i skalujemy mapę — tak / nie / tak, z poprawkami: ____

## Znane braki i ryzyka
(Wypełnij po pomiarze. Znane z przygotowania: brak prawdziwych zdjęć właściciela z tego miejsca; gra nie czyta jeszcze `route_s`, `route_end` i `qacam_set`, więc G3-B i kadry ¾ wymagają zmian w kodzie; pas łącznic i `maxspeed` mają niską pewność; Rondo Putry w szacunku Medium jest ponad budżetem trójkątów.)

## Decyzje dla Ciebie
- Jedna próbka (G3-A) czy dwie (A + B)?
- Czy robimy sesję zdjęciową (brama, plac, hale, przekrój Andersa) przed oceną wizualną?
- ____

## Pomiary z telefonu: dopisek wykonawcy (build-qa, 2026-11-10)
- Źródła: `artifacts/gate3/20261110-085644/RFGL34SJYDZ` (A16 G3-A), `.../20261110-091317/RFGL34SJYDZ` (A16 G3-B), `.../20261110-075407/RZCX60VE8ZY` (S24+ G3-A), `.../20261110-082229/RZCX60VE8ZY` (S24+ G3-B). Wszystkie `valid=true`, klucz ekranu sprawdzony przed każdym krokiem.
- **Różne buildy:** A16 z `c59209e` (po merge main: koła LOD, szyby, cień kontaktowy, regeneracja świata); S24+ z wcześniejszego `fefd804`. Wyniki High nie obejmują poprawek z `c59209e`.
- Kamery: A16 21/21 (G3-A) i 23/23 (G3-B). S24+ G3-A 17/21 (2x MISSING_IN_SCENE: `g3a_eye_s0012`, `g3a_eye_s0362`; 2x NO_SCREENSHOT: `s0262`, `s0312`), G3-B 23/23. Zrzuty: `artifacts/gate3/final/{s24_high_,a16_low_}*.png`, kopie ≤1024 px w `final/small/`.
- S24+ High: p50 16,7 ms, ale p95/p99 ≈ 50 ms (skok do ok. 20 FPS), GPU p95 19,3 ms (G3-A) / 18,5 ms (G3-B), CPU main p95 20,7 / 19,0 ms. Przyczyny nie rozdzielono (UNVERIFIED): GPU p95 jest bliski budżetowi klatki 16,7 ms, a temperatura rosła do 38,5 °C (thermal 2).
- DK8 (nagrania 10 s, S24+ High, kamera statyczna `dk8-dk19-exit`, nie jazda): `final/dk8/s24_high_dk8_msaa_default.mp4` i `..._msaa_2.mp4`. Obie wersje dają ok. 39 FPS średnio, p50 16,7 / p95 50,0 ms, PSS 1,3 GB, GPU p95 26,4 ms (domyślne MSAA) / 27,0 ms (MSAA 2x). **Różnicy MSAA 2x vs domyślne w FPS nie widać; ocena wizualna: UNVERIFIED (nikt nie obejrzał klipów).** Pomiar przy 36 °C, jeden przebieg każdy.
- E5: A16 temperatura start → koniec 27,7 → 27,6 °C (G3-A), 28,0 → 28,1 °C (G3-B), thermal 0. Test 30 min poza zakresem bramki.
- Draw calls i trójkąty (E7) i test feelingu: nie mierzone.
- Bateria S24+ na koniec: 54 % (po ostatnim przebiegu), gra zamknięta (`am force-stop`).

## Dopisek: A16 Low 30 FPS, build `ecfd03b058` (build-qa, 2026-11-10 po poprawkach W-N10)
- **Build:** `ecfd03b058` (main `f0a1884` + poprawka kamery `g3a_eye_s0012`, kontrola kadrów, kamery kabiny w gate3-run). APK `artifacts/apk/kamion-0.1.0-ecfd03b058.apk`, 161,1 MB, SHA256 `be7f9a3eada90bfe04eaa22512912cf94d6d9fc89e00ee54aea9f05f38d91ced` (zapisany też w `gate3-result.json` jako `apk.sha256` i `gitSha`). Świat w edytorze (źródło glTF): 728 MB.
- **A16 `RFGL34SJYDZ`, Low, 30 FPS, autopilot 30 km/h** (`valid=true`, keyguard sprawdzany przed/po każdym kroku, bateria 29,4 °C, thermal 0):
  - G3-A (`artifacts/gate3/20261110-120931/RFGL34SJYDZ`): p50 33,33 / p95 33,50 / p99 33,67 ms (mean 29,95 FPS, 342 klatek > 33 ms, 4 > 50 ms), GPU p95 25,5 ms, CPU main p50 21,0 / p95 26,5 / p99 44,8 ms, PSS 700,7 MB.
  - G3-B (`.../20261110-123803/RFGL34SJYDZ`): p50 33,33 / p95 33,48 / p99 33,66 ms (mean 29,98 FPS, 321 klatek > 33 ms, 2 > 50 ms), GPU p95 25,9 ms, CPU main p50 20,7 / p95 26,1 / p99 42,5 ms, PSS 674,9 MB. Temperatura 29,4 -> 29,5 °C.
  - Budżet WORKING_VALUE Low (p95 <= 34, p99 <= 40, PSS <= 1000): p95, p99 i PSS w normie. Uwaga: p50 = p95 = 33,3 ms to cap 30 FPS, więc te liczby nie pokazują zapasu. Ogon CPU main p99 42-45 ms przekracza 40 ms (to czas CPU wątku głównego, nie klatki; przyczyna UNVERIFIED).
- **Kamery z telefonu:** G3-B 23/23 CAPTURED. G3-A 16/27 w pierwszym przebiegu (21 kamer gate3/kontrolnych + 6 nowych `truck-34` i `cab-dash` x overcast/lowsun/dusk: wszystkie 6 CAPTURED); 7x NO_SCREENSHOT, 4x MISSING_IN_SCENE i 1 PNG ucięty (`g3a_ext34_s0338`, nie wliczony do 16). Przyczyna (hipoteza, UNVERIFIED): w trakcie przebiegu demon adb był restartowany (dwie wersje adb: adb ze scrcpy w PATH vs adb z Unity SDK używany przez skrypty, uruchamiane równolegle przez innych agentów), a potem A16 przeszedł w stan `offline` i nie wrócił bez fizycznego wpięcia. Powtórka brakujących 12 kamer G3-A: NIE wykonana, `g3a_eye_s0012` jest CAPTURED i czytelny.
- **W-N10:** kamera `g3a_eye_s0012` przesunięta o 18 m przed punkt startu ciężarówki (s=30 m zamiast 12 m), id bez zmian. Kadr z telefonu pokazuje drogę, halę i naczepy na dokach (nie czarne pudło). Nowa kontrola `frame_exposure` w `gate3_evidence.py` (p50 <= 15 % lub > 20 % pikseli < 3 % luminancji = FAIL; kadry `cab-*` tylko limit 8 % z L1-r5). Wynik: 222/222 renderów edytora (37 kamer x Low/Medium/High x overcast/lowsun) i 29/29 czytelnych kadrów świata z telefonu PASS (najniższe p50 renderów edytora 21,9 %). **FAIL: 3 kadry `cab-dash` z A16 (overcast, lowsun, dusk): piksele < 3 % luminancji 30,4 / 35,9 / 47,2 % przy limicie 8 %**, kabina nadal prawie czarna na Low.
- **Kontrole docs/06 §5 (edytor, `artifacts/gate3/20261110-a16-low-ecfd03b/evidence/gate3-evidence.md`):** albedo FAIL (16 materiałów z 187, m.in. szkło `M_glass`/`M_car_glass`, guma, `M_signal_backplate`; część to czerń z założenia, do oceny), texel density FAIL (7 z 149, ogrodzenia 42-82 texel/m), tekstury w budżecie PASS (31,9 MB korytarza vs 64 MB Low), siatki normalne/UV PASS, obiekty vs teren FAIL (64 z 252 instancji unosi się, 29 zagłębionych; głównie `lamp_12m` i `sign_post`), renderów kompletnych PASS (222/222), `frame_exposure` FAIL (3x `cab-dash`).
- Wizualnie (kadry <= 1024 px w `.../small/`): droga i hala w `s0012` OK; `truck-34` overcast: front TRAKT, koła na ziemi, druty WN jako cienkie przerywane łuki; `cab-dash`: ciemna kabina, wskazania czytelne, obręcz czarna; linie i strzałki nadal białe (W-H6 otwarte); na drogach nie widać aut osobowych (tylko ciągniki z naczepami na dokach, jeden niebieski).
- Dowody: `C:\Users\matma\Documents\Claude\kamion\artifacts\gate3\20261110-a16-low-ecfd03b\phone\` (kopie kadrów A16), `...\evidence\`. Gra na A16 NIE została zamknięta `am force-stop` (telefon offline w adb po przebiegu; do wykonania po powrocie urządzenia). S24+ nie dotknięty.

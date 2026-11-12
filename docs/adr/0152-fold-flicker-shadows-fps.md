# ADR 0152: Fold — „przeskakujący” obraz, migające cienie, niski FPS

Status: propozycja (rendering-perf, gałąź `fold-flicker`, z main `41e6fd89f`), 2026-11-12.
Powiązane: ADR 0046/0062 (adaptacyjna skala, fallbacki High), 0056 (przechwyt odbić), 0135/0147 (Fold), 0136 (A16 Low).

## Zgłoszenie
Właściciel, Galaxy Fold (ekran wewnętrzny), nagranie `artifacts/owner-feedback/2026-11-12-fold-video2/…212807…mp4` (155 s):
„od ok. 1:40 cienie itp. renderują się za późno; ekran migał na czarno i mało FPS było; nie widać na nagraniu czarnych klatek”.
Drugie nagranie (`…-fold-video3/…213650…mp4`, 14,6 s, ciężarówka stoi): „patrz jak napierdziela obraz, to samo na A16 z botem”.

## Fakty (zmierzone)
**Urządzenie** (logi lidera `fold-logs/`, tylko odczyt): SM-F976B, platforma `canoe`, `ro.hardware.vulkan=adreno`, ekran wewnętrzny
2256×2504 (5,65 Mpx), 120 Hz. `[DIAG]` tej sesji: **tier=Ultra target=60**, p50 66,7–83,3 ms, p95 133–183 ms, thermal=2 (SKIN ≥ 40 °C),
PSS 1719–1725 MB, `scale=1.00`, `mir=6.00/f`. Reguły auto-tieru dają Adreno 8xx → High; Ultra/60 pochodzi z zapisanego wyboru
(PlayerPrefs, menu startowe / przycisk tieru). Ultra: renderScale 1,0, MSAA 4×, cienie 4096/4 kaskady/150 m, SSAO, przechwyt odbić
256 px co 2 klatki — **bez** adaptacyjnej skali, bez fallbacku termicznego i pacingu. Ultra nigdy nie był strojony na flagowcu.

**Nagranie 2 (znaczniki klatek nagrywarki, `artifacts/fold-flicker/video/frames.csv`)**: 1817 klatek / 155 s. Nowe klatki/s:
0–60 s 13,5–18,3; 60–130 s 8,7–11,6 (mediana odstępu 99–117 ms); brak przerw > 200 ms. Spadek ~60 s = termika (thermal=2 w logu).
Jedna przyciemniona klatka 124,90 s: niebo 102→61, jezdnia 52→27 (×0,55), lusterka i UI bez zmian → ciemniejszy był sam render
kamery głównej, nie kompozycja. Nagrywarka Samsunga rejestruje ~co drugą klatkę gry (A16: 297 klatek screenrecord / 60 s przy
~10 FPS gry) — naprzemienność klatka-do-klatki jest na nagraniu niewidoczna (aliasing), stąd „nie widać na nagraniu”.

## Przyczyny
1. **Sprężyna głowy kierowcy (`CameraRig.UpdateCab`) niestabilna poniżej ~11 FPS.** Jeden krok półniejawnego Eulera na klatkę,
   ω = 2π·1,8 Hz, ζ = 0,7: wartość własna macierzy kroku < −1 dla dt > ~0,09 s (dt 0,10 → ρ = 1,31; 0,12 → 2,16; 0,15 → 3,63).
   Offset głowy zmienia znak co klatkę i siedzi na klamrze ±6 cm (`headMaxOffset·1,5`) — także na postoju (wystarczy szum
   przyspieszenia). To jest „przeskakujący obraz” z nagrania 3 i „cienie przeskakujące” z nagrania 2 (cały kadr bliży przesuwa się
   co klatkę; cienie na jezdni z nim). Przy 30–60 FPS (dt ≤ 0,033) stabilna, dlatego niewidoczna na A16 Low i S24+.
2. **Za ciężki tier na ekranie 5,65 Mpx**: Ultra/60 na Foldzie = 66–183 ms/klatkę → dt > 0,09 s → (1).
3. **Adaptacyjna skala nie działa poniżej 15 FPS**: okno 2 s wymagało 30 próbek GPU; przy 10 FPS ~20 → okno odrzucane, skala
   zostaje 1,00 (A16 High: GPU p50 91 ms, `scale=1.00` cały przebieg). Dotyczy High (Ultra adaptacji nie ma).
4. **Przechwyt odbić na Ultra pada na każdej ścianie** (Fold, Adreno 840, Vulkan): `VehicleReflectionCapture.RenderFace` →
   „RenderPass: Fake or uninitialized surface is not supported for attachment 0/1”, „EndRenderPass: Not inside a Renderpass” —
   4575 / 4398 linii w 120 s, od pierwszej klatki (nie tylko po wznowieniu); High na tym samym Foldzie: 0. Ultra ma jedyny
   renderer z SSAO (`Mobile_Renderer_SSAO`, ADR 0080); render request przechwytu przez niego się nie składa. Cube odbić = śmieci,
   a zepsuty render pass co 2. klatkę zbiega się z pojedynczymi **przyciemnionymi klatkami** widoku 3D (Fold Ultra przed:
   klatka 970 jezdnia 86→51, niebo 186→178, lusterka/UI bez zmian — ta sama sygnatura co 124,90 s u właściciela).

## Decyzja (najmniejsze zmiany)
- `CameraRig.StepHeadSpring`: pod-kroki ≤ 1/60 s (maks. 12; dt i tak ≤ 0,1 s przez `Time.maximumDeltaTime`). Ta sama odpowiedź
  co przy 60 FPS, stabilna przy każdym dt. Diagnostyka: `cam_legacy=1` (stary krok, tylko A/B), `camlog=1` (CSV pozy kamery na
  klatkę `diag/campose.csv`, poza pętlą jazdy domyślnie wyłączone).
- `AdaptiveRenderScaleController`: okno rośnie do 30 próbek (maks. 6 s), decyzja od 8 próbek.
- `VehicleReflectionCapture`: renderer bez SSAO dla przechwytu, gdy aktywny asset tieru ma go pod indeksem 1 (Ultra:
  `URP_Ultra.m_RendererDataList[1] = Mobile_Renderer`, także w `SsaoRendererSetup.Ensure`); zwolnione cele po wznowieniu
  (IsCreated == false) → odtworzenie + pełny cube. Lusterka bez zmian (nie sypią błędów; koszt SSAO w 6 renderach lusterek/klatkę
  na Ultra — osobny temat).
- Ultra dostaje siatkę bezpieczeństwa High: adaptacyjna skala 0,70–1,00, fallback termiczny 30 FPS, pacing 30 FPS
  (`QualityProfile.asset` + `Defaults()`; test `UltraHasTheHighSafetyNet_Adr0152`). Zapisany wybór gracza (Ultra/60) nie jest
  nadpisywany; reguły auto-tieru bez zmian (Adreno 8xx → High, domyślnie 30 FPS).

## Wyniki (telefony, `artifacts/fold-flicker/`)
**Sprężyna głowy, A16 SM-A165F, High/30, `rq_scale=1` (skala stała, ~10 FPS), trasa route_s=12, 60 km/h, 150 s, `campose.py`:**

| przebieg | dt p50 | head_z: krok p95 | head_z: |x| p95 | klatki naprzemienne head_z / head_x |
|---|---|---|---|---|
| przed (`cam_legacy=1`) | 100 ms | 48,96 mm | 26,1 mm | 15,6 % / 10,6 % (okna 10 s do 85–100 %, ±53–60 mm) |
| po | 100 ms | 1,51 mm | 9,3 mm | 0,0 % / 0,0 % |

Wykres: `a16_head_offset_before_after.png`. Pochylenie/odchylenie kamery względem ciężarówki bez zmian (krok p95 0,3° / 0,01°).
Fold (chłodny, Ultra/60, ~25 FPS, dt 33 ms): naprzemienności 0 % w obu wariantach — błąd pojawia się dopiero < ~11 FPS
(u właściciela po nagrzaniu, thermal=2).

**Adaptacyjna skala, A16 High/30, 150 s:** przed: skala 1,00 cały czas, 10,2 FPS, GPU p50 91,0 ms; po: 0,70 od pierwszego
okna (1744/1777 klatek), **13,4 FPS**, klatka p50 66,8 / p95 116,6 ms, GPU p50 68,6 / p95 95,7 ms. (A16 = Low wg D49; to tylko
dowód działania mechanizmu).

**Fold SM-F976B (Adreno 840, 2256×2504), trasa jak wyżej, 120 s, start < 30 °C:**

| przebieg | FPS | klatka p50/p95/p99 | GPU p50/p95 | PSS | błędy capture | ciemne klatki (screenrecord 60 s) |
|---|---|---|---|---|---|---|
| Ultra/60 przed | 25,2–25,6 | 33,3 / 66,7 / 66,7 | 29,1–29,4 / 37,1 | 1837–1872 MB | 4398–4575 | 1 / 1595 |
| Ultra/60 po (capture) | 25,6 | 33,3 / 66,7 / 66,7 | 29,8 / 41,9 | 1845 MB | **0** | 0 / 1590 |
| High/30 | 29,98 | 33,3 / 33,3 / 33,3 | 23,8 / 27,8 | 1471 MB | 0 | — |

**Fold High/30, 300 s (APK `550a353f48`)**: 29,97 FPS, klatka p50/p95/p99 33,3/33,3/33,3 ms, GPU p50/p95 24,7/28,8 ms,
PSS 1460 MB, thermal 0, bateria 27,0 °C po biegu; FPS/min: 29,5 / 29,9 / 30,0 / 30,0 / 27,8 (ostatnia minuta niepełna — zbieranie
metryk). Ultra/60 300 s z nową siatką bezpieczeństwa — NIE zmierzone (przerwane na polecenie lidera, limit sesji).
**A16 Low/30, regresja (ten sam skrypt `fold-run.ps1`, trasa route_s=12, 60 km/h, 200 s, start 28–29 °C; statystyki po 25 s
rozgrzewki, `ft.py`)**:

| APK | FPS | klatka p50/p95/p99 | GPU p50/p95 | skala | PSS | hitch > 100 ms | thermal |
|---|---|---|---|---|---|---|---|
| main `e364975f12` (`r1/low`) | 29,28 | 33,3 / 33,6 / 50,1 | 32,3 / 39,0 | 0,75 | 972 MB | 0 | 0 |
| gałąź `550a353f48` (`a16low2/low_new`) | 29,28 | 33,3 / 33,6 / 50,1 | 32,3 / 38,9 | 0,75 | 945 MB | 0 | 0 |

Brak regresji (różnice w szumie). Logcat bez błędów gry (65 dopasowań = szum systemowy Samsunga).

Ciemne klatki: 1 vs 0 zdarzeń — zgodne z hipotezą, za mało zdarzeń na dowód (UNVERIFIED).

## Tier domyślny Folda (z liczb powyżej)
- Ekran wewnętrzny 2256×2504 = 5,65 Mpx (S24+ 1080×2340 = 2,53 Mpx, ×2,2). Przy renderScale 1,0 Ultra (MSAA 4×, SSAO, cienie
  4096/4 kaskady) to GPU p50/p95 29,8/41,9 ms → **60 FPS nieosiągalne** (budżet 16,7 ms; nawet p50 ×1,8 ponad), 30 FPS też nie
  (p95 > 33,3 ms) bez adaptacji skali. High/30: GPU p50/p95 24,7/28,8 ms, 5 min bez spadków, thermal 0 → **zapas ~13 % do 33,3 ms**.
- Decyzja: **domyślnie High/30 bez zmian** (reguła `Adreno (TM) 8` → High, już była; notatka reguły zamiast `UNMEASURED` podaje
  pomiar Folda). Nie dodajemy reguły po rozdzielczości: jedyny pomiar to ten Fold, a High/30 trzyma 30 FPS przy skali 1,0.
- Ultra zostaje do wyboru, ale z siatką bezpieczeństwa (adaptacja 0,70, fallback 30). High/60 na Foldzie niezmierzone; GPU p50
  24,7 ms wskazuje, że 60 FPS wymagałoby skali ~0,7 (szacunek z liniowej proporcji pikseli — `UNVERIFIED`).

## Otwarte
- **Fold Ultra/60 300 s z nową siatką bezpieczeństwa — NIE zmierzone** (Fold odłączony przez właściciela 22:30). Komenda:
  `pwsh artifacts/fold-flicker/fold-run.ps1 -Serial RFGL80RXBPZ -MinBattery 40 -CoolBelowC 36 -Duration 300 -Apk <apk> -OutTag foldultra -Runs "ultra60=Ultra;fps60;camlog=1"`.
- Fold High/30 30 min (termika długoterminowa) — niezmierzone.
- Menu: czy oferować 60 FPS z Ultra na ekranach > 4 Mpx — do decyzji (gameplay-ui), dane wyżej.
- Czarne mignięcia przy prezentacji — UNVERIFIED do przebiegu na Foldzie z logcat na żywo.

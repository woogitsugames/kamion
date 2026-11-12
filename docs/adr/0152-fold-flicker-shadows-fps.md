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
4. **Przechwyt odbić po powrocie z tła**: `VehicleReflectionCapture.RenderFace` → „RenderPass: Fake or uninitialized surface…”,
   „EndRenderPass: Not inside a Renderpass” — 108+108 linii błędów w 2 min po wznowieniu (Fold 21:36:33–21:37:20).

## Decyzja (najmniejsze zmiany)
- `CameraRig.StepHeadSpring`: pod-kroki ≤ 1/60 s (maks. 12; dt i tak ≤ 0,1 s przez `Time.maximumDeltaTime`). Ta sama odpowiedź
  co przy 60 FPS, stabilna przy każdym dt. Diagnostyka: `cam_legacy=1` (stary krok, tylko A/B), `camlog=1` (CSV pozy kamery na
  klatkę `diag/campose.csv`, poza pętlą jazdy domyślnie wyłączone).
- `AdaptiveRenderScaleController`: okno rośnie do 30 próbek (maks. 6 s), decyzja od 8 próbek.
- `VehicleReflectionCapture`: zwolnione cele (IsCreated == false) → odtworzenie + pełny cube.

## Wyniki
(uzupełniane — patrz niżej)

## Otwarte
- Tier Folda (Ultra/60 zapisany przez gracza) — patrz Wyniki/Fold.
- Czarne mignięcia przy prezentacji — UNVERIFIED do przebiegu na Foldzie z logcat na żywo.

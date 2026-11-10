# ADR 0052: kamera kabiny na punkcie oczu kierowcy (H-point + 0,635 m), ruch głowy w granicach szyi

Status: przyjęty (2026-11-10). Źródło zadania: HANDOVER "Następne kroki" pkt 7.

## Kontekst
Kamera kabiny (`Game.Cameras.CameraRig`, tryb Cab) jest dzieckiem `DriverEyePoint` na pivocie zawieszenia kabiny
(`VehicleVisuals.cabPivot`), więc już podąża za resorowaną kabiną, nie za ramą. Brakowało: jawnych danych H-point,
testu zależności oko–H-point, granic ruchu głowy opartych na szyi (stare: yaw ±130°, pitch −35/+25°) oraz obrotu
wokół osi szyi zamiast wokół oka.

## Decyzja
- **Dane** (`art-source/truck/dims.json`, lustro w `TractorDimensions`, sprawdzane przez `ReadAndCheckDims` + test):
  `driver_h_point_m` = (−0,55; 0,45; 1,865) WORKING_VALUE (wysokość R-point), `driver_eye_above_h_point_m` = 0,635 m
  SOURCED (UNECE R46: punkty okularowe kierowcy 635 mm pionowo nad R-point). Manifest wnętrza (`H_POINT`, `EYE_POINT`)
  zgadza się co do 2 mm (test). Oko = H + (0; 0,635; 0) w ramie kabiny, nie zmieniono geometrii wnętrza ani sightline.
- Porównanie z SAE J1100/J941 (elipsa oczu, 50./95. percentyl): wartości tabelaryczne nie były otwierane, zgodność
  rzędu wielkości (środek elipsy w ~0,1 m od punktu R46) jest **UNVERIFIED**. Półosie elipsy dają górną granicę dla
  ruchu głowy: `headMaxOffset` 0,04 m (×1,5 twardy limit) mieści się w nich z zapasem.
- `Game.Cameras.DriverHead` (czysta matematyka): yaw ±90°, pitch w dół 50° / w górę 55° względem spojrzenia
  spoczynkowego 6° w dół (= kamera kontrolna `cab-driver`), oś szyi 0,11 m pod i 0,09 m za okiem — wszystko
  WORKING_VALUE (typowe zakresy ruchu szyi: rotacja ~70–90°, zgięcie 45–60°, wyprost 50–70°; nie mierzone).
  W pozie spoczynkowej kamera leży dokładnie w `DriverEyePoint`; przy rozglądaniu oko przesuwa się o paralaksę szyi.
- Prefab: marker `DriverHPoint` pod `cabPivot` (z `H_POINT` manifestu wnętrza), do testów.
- Testy: `DriverSeatCameraTests` (EditMode: wymiary, manifest, poza spoczynkowa, kabina przechylona, limity szyi,
  powrót), `TraktTruckRigTests` (PlayMode: eye − H = 0,635 m na prefabie).

## Konsekwencje / otwarte
- Spoczynkowy pitch zmieniony 7° → 6° (jedna stała dla gry i kamer kontrolnych).
- Eyellipse SAE do potwierdzenia ze źródła; gyro-look nie istnieje (żyroskop steruje kierownicą) — bez zmian.
- Kadr gry używa FOV 55° (ustawienie gracza), kamery kontrolne 62°.

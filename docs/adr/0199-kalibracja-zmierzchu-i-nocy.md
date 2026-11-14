# 0199 — Kalibracja zmierzchu i nocy: tabela E(h), pastelowa łuna, włączanie latarni, okna, podłoga nocna

Status: kandydat (gałąź `dusk-cal-0199`), nie scalone. Data: 2026-11-14 (s20). Dotyczy: ADR 0062 (zmierzch), 0182 (dusk), 0191/0192
(pule, okna, magenta). Źródła: `research/cloud/p17-dusk-lighting/` (README + errata), `docs/reports/REVIEW-2026-11-14-s20-cloud-m60-compare.md`
(§4, §6), `REVIEW-2026-11-14-s20-mistral-m60.md`, `REVIEW-2026-11-14-s20-cloud2-r7.md` (§3).

## Kontekst
1. `TwilightFactorAt` był log-liniowy od modelu przy 0,5° (2248 lx samo niebo) do 3,4 lx przy −6°: wg tabeli Schlytera gra była
   za jasna ×1,8 przy 0° i ×1,24 przy −1°, za ciemna o 12–16 % przy −3…−5°, za jasna ×1,32 przy −8°.
2. Koralowy pas nad horyzontem w `LP_Dusk` w stronę słońca (ADR 0192 P2-1). Probe (`TwilightSkyProbe`, `probe-before.tsv`):
   LUT kopuły 2–6° nad horyzontem, γ 0–10°: liniowo R 2,0–2,3, G 0,66, B 0,44–0,8 (nasycenie na ekranie 0,40–0,53) — to obszar
   `glow` w `ApplyTwilightChroma`, który zostawiał paletę zachodu liczoną dla słońca +0,5°. Hipoteza R7 potwierdzona w Unity;
   `HorizonColorExposed` (kolor mgły) nie bierze udziału (pas kierunkowy).
3. Latarnie włączały się przy +3°…+1° (przed zachodem); zdjęcia: świecą przy −3,1°, −3,7°, jedna arteria jeszcze nie przy −3,3°.
4. Okna mieszkań 0,40→0,50 (literaturowe maksimum, nie typ), 15 cd/m² (zmierzone 6), biura wg słońca zamiast zegara.
5. Podłoga nocna 1 lx do 45 m od oprawy, dalej 0 (zdjęcia: nigdy czarno).

## Decyzja
1. **Tabela E(h)** `SkyModel.TwilightTableLux` co 1° od +1° do −8°: 1270 / 759 / 405 / 189 / 79,1 / 29,9 / 10,4 / **3,4** / 1,09 / 0,348 lx
   (Schlyter radfaq, SOURCED_SECONDARY; węzły +1/−1/−2° odczytane z tej samej tabeli 2026-11-14; −6° = `CivilTwilightEndLux` 3,4 lx,
   komentarz → SOURCED: 3,41 Schlyter / 3,5 Spitschan miasto / 4,3 Muneer). Interpolacja log-liniowa między węzłami. Skalowanie do
   modelu: współczynnik = 1 przy 0,5° (model 2248 lx), log-liniowo do tabeli przy 0° (760 lx), od 0° w dół tabela w luksach absolutnie.
   Bez skoku przy 0,5°. Wynik (probe): 0° 760, −0,5° 554 (tabela 562), −1° 405, −2° 189, −4° 29,9, −6° 3,40, −8° 0,348 lx.
2. **Łuna**: w obszarze `glow` (γ < 15–75°, v < 0,15–0,6) kolor LUT zachodu zastąpiony pastelowym gradientem
   `TwilightGlowColour(v)`: przy horyzoncie żółtawo-brzoskwiniowy (1,38 / 1 / 0,62 liniowo), od 2,5° do 5° przejście w słaby róż
   (1,65 / 0,88 / 0,97), wyżej dotychczasowy błękit zmierzchu; siła = rampa t (0 przy 0,5°, 1 przy −3,5°), pełna w rdzeniu łuny.
   `SuppressTwilightMagenta`: tolerancja `TwilightPinkAllowance` 0,03 (min(R,B) − G), żeby pastelowy róż nie został zamieniony w szarość;
   test ADR 0192 (nadmiar > 0,06 = magenta) bez zmian. Kolejność jak na zdjęciach (C60-064 „żółtawo-brzoskwiniowy → lawenda →
   niebieski”, −5,4°; R7 c32/c16). WORKING_VALUE (barwy wg opisu kadrów; zdjęcie właściciela rozstrzyga).
3. **Latarnie**: `StreetLamps.SwitchOn` = liniowo od −2° (0) do −3,5° (1). Dusk −6° bez zmian (1). WORKING_VALUE.
4. **Okna**: mieszkania 0,25 (−6°) → 0,28 (−16°) (ESTIMATED: zliczenia 6–28 %, wieczór 22–27 %); `MeanLuminance` 15 → 8 cd/m²
   (6 zmierzone Novak 2025 + zapas na mały ekran, WV); biura `OfficeShareAtHour(h)`: 0,4 do 17:00, → 0,1 o 19:00, 0,05 po 19:30 i przed
   7:00, 0,4 od 8:00 (WV). Nowe pole `LightingPreset.clockHour` (domyślnie 12): `LP_Dusk` 16:10 (koniec zm. cyw. 15 XI, `sun.py`),
   `LP_Night` 22:00. Rampa włączania okien 4°→−2°, klatki 0,35, hale — bez zmian (poza zakresem).
5. **Podłoga daleka**: poza 45 m podłoga nie spada do 0, tylko do 0,03 lx (bezchmurnie) / 0,2 lx (pochmurnie), lerp po `overcast`
   presetu (`StreetLamps.FarFloorLux`, ESTIMATED rząd wielkości). Przekazywana w wolnym kanale `_KamionLampColor.w` (udział podłogi
   bliskiej), w HLSL `lerp(_KamionLampColor.w, 1, fade²)`. Nadal wyłączana flagą `lampFloorOff`, tylko gdy latarnie świecą.
6. Narzędzie `Game.Rendering.Editor.TwilightSkyProbe.Dump` (batch, `-probeOut`): barwa i luminancja kopuły dusk/night w siatce wysokość ×
   azymut oraz E(h).

## Budżet (A/B, WorldC, `stats.txt`, 5 kamer × Low/High × dusk/night)
- drawsEst / shadowDrawsEst / tris: **identyczne** before vs final (np. High-night chase 631 / 477 / 827 900).
- Warianty shaderów: 0 nowych słów kluczowych. ALU: podłoga +1 lerp (~2 ALU/px, tylko przy zapalonych latarniach); łuna = LUT na CPU
  przy `Apply` (0 GPU); latarnie/okna/zegar = uniformy. Pamięć: 0. **GPU ms na A16/S24+: niezmierzone** (zakaz adb w zadaniu).

## Walidacja
- Rendery: `artifacts/dusk-cal-0199/{before,final}/{Low,High}-{dusk,night}/` (chase, route_putry_approach, driver_andersa_to_putry,
  kwadrat_park_gate, trailer-34), arkusze `sheet-*.jpg`, `lum.tsv`; zbliżenia nieba `cmp-*-High-dusk-r3.jpg`; probe `probe-before.tsv` /
  `probe-r6.tsv`.
- Zmierzch: luma kadru bez zmian (p50 ±0,1 pp, pas jezdni ±0,2 pp) — oczekiwane, −6° i EV stałe. Niebo route_putry x 1000:
  before y 450–480 (186,129,128)…(232,130,113), nasycenie 0,31–0,51 → final (144–153, 140, 141–146), 0,04–0,10; driver_andersa
  x 1060: dół (134,119,104) brzoskwinia, wyżej (161,141,140) róż, (146,142,145) lawenda → błękit.
- Noc: tabela przy −8° 0,46 → 0,348 lx; auto-ekspozycja Night podąża (−0,40 EV100) → latarnie, pule, okna +32 % na ekranie względem
  tła: pas jezdni p50 Low chase 25,6 → 29,3, High gate 44,3 → 49,4 (szczegóły `final/lum.tsv`). Okna nocą rzadsze (biura 0,15 → 0,05
  o 22:00, mieszkania 0,50 → 0,28) i ciemniejsze (8 cd/m²).
- EditMode: nowe `DuskCalibrationTests` (6): tabela w 9 węzłach ±2 % i zgodność z `SkyModel`, brak skoku przy 0,5°, monotoniczność,
  zachód nie za jasny (0° < 800 lx, −1° < 430 lx, −4° > 28 lx); łuna bez koralu (R/max(G,B) < 1,7, nasycenie < 0,4, magenta ≤ 0,06),
  żółtawo nisko / róż wyżej / zenit niebieski; latarnie 0 przy −2°, 0,5 przy −2,75°, 1 przy −3,5°; okna 0,25/0,28, 8 cd/m², biura wg
  zegara i niezależne od słońca, zegar presetów; podłoga daleka 0,03/0,2 lx + HLSL. Zmieniony `NightWindowTests.Shares_*` (nowa
  sygnatura, zakres 0,2–0,3). Pełny EditMode: wynik w `final.status` (2 porażki `CarPaintMaterialTests.DepositionChannel_*` — czysta logika
  `WorldPbrMaterials.Channels` (World.Import), plik i test identyczne z main a08f9935d, diff 0199 ich nie dotyka; w ADR 0191 te same
  2 porażki w bazie).

## Otwarte
- Model dzienny przy +0,5° daje 2248 lx (tabela 994 lx całk.) — wzór kopuły powyżej 0,5° poza `TwilightFactorAt`, nadal ×2,3 przy
  samym zachodzie (≈ 3–5 min gry). Do poprawy w modelu dziennym (niska elewacja) osobno.
- Noc +0,4 EV na latarniach względem przeglądu Night (ADR 0108): jeśli właściciel woli dawny wygląd → `LP_Night.exposureCompensation`
  −3 → −3,4 (tło wtedy o 0,4 EV ciemniejsze niż dziś). Decyzja przy przeglądzie.
- Sezon presetu: `LP_Dusk` azymut 300° (lato, ~20:30) vs zegar 16:10 (listopad) — do decyzji właściciela (R7: zima 238–245°).
- Porównanie obok siebie z kadrem C60-064 (CC0, Wikimedia) — nie pobrany (bez zgody na pobieranie w tym zadaniu); ocena wg opisu kadru.
- Rampa okien +1° → −5°, klatki 0,6, rozrzut CCT mieszkań (tabela §6 przeglądu M60) — poza zakresem.
- Pomiar GPU na A16/S24+ i ocena łuny/okien na telefonie.

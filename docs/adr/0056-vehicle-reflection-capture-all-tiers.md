# ADR 0056: odbicie otoczenia ciężarówki działa naprawdę i na każdym tierze (r7, D30/D31)

Status: przyjęty (rendering-perf), 2026-11-10. Źródło: `docs/11` D30, D31; `docs/reports/visual/REVIEW-2026-11-10-r7.md`
§2, §5. Uzupełnia ADR 0021 (capture), 0038 (lakier), 0048 (szyba). Dowody: `artifacts/truck-fixes/paint-glass-r7/`.

## Co było zepsute (zmierzone w edytorze, WorldC `truck-34`)
1. **Capture nie miał świata.** Każda ściana szła przez `SingleCameraRequest` prosto do cube RT. URP robi wtedy własny
   tymczasowy 2D RT z domyślnego deskryptora, bez bufora głębi (`UniversalRenderPipeline.ProcessRenderRequests`). Render
   graph ostrzegał „the output Render Texture must have a depth buffer” (12×/run) i opaque nie rysował się. W cube było
   tylko niebo (zrzut `dumpH_cube.png`). Jawny format głębi w samym cube RT nie pomaga (`v1`: ostrzeżenie zostaje).
2. **Probe nie docierał do ciężarówki.** Custom `ReflectionProbe` z tym cube: renderery zgłaszają go z wagą 1,00
   (`GetClosestReflectionProbes`), ale shader brał domyślny sky cube. Cube wyczyszczony na czerwono zmienił 0 px kadru
   (`renders/red`). Zawartość cube'a (niebo → hale) zmieniła 0,01 % pikseli. Przyczyna leży po stronie engine/URP (probe
   atlas + blending na Low/High). Nie badałem jej dalej, bo obejście jest prostsze i tańsze.

Od ADR 0021 „capture High” był więc analitycznym niebem, a pomiar A8 (+0,5 ms CPU na S24+) mierzył samo niebo.

## Decyzja
- `VehicleReflectionCapture`: ściana renderuje się do własnego 2D RT z D24S8 i jest kopiowana `CopyTexture` do cube'a
  (orientacja potwierdzona testem pół-biały/pół-czarny, `renders/half`). Nie ma już ReflectionProbe. Cube jest globalną
  teksturą `_KamionVehicleEnvCube`, a `KamionVehicleEnv.hlsl` próbkuje go bezpośrednio (mip = mapowanie URP, 6 kroków).
  Dowód: czerwony cube barwi lakier i szyby (`renders/red2`).
- **Low/Medium dostają capture:** 64 px, jedna ściana co 10 klatek (Medium co 6), far 150 m. **Gdy ciężarówka stoi**
  (przesunięcie < 2 m i cube młodszy niż 20 s), nie renderuje się żadna ściana. High: 128 px co 3 klatki (było 2),
  Ultra: 256 px co 2. Próg 0,5 m i 10 s, bo capture renderuje teraz prawdziwą geometrię.
  Pola `envCaptureMinMove` i `envCaptureMaxAge` są w `QualityProfile`. `rq_envcap=0` wraca do ścieżki analitycznej
  (ziemia ADR 0038 r6).
- Bez box projection: odbijana treść jest w większości daleka, a pudło wokół jadącej ciężarówki nie odpowiada żadnej
  ścianie otoczenia. Wariant jest też wycięty (`m_PrefilterReflectionProbeBoxProjection: 0`).
- Lakier bez zmian: coat F0 0,04, roughness 0,08 (w zakresie 0,05–0,15 lakieru bezbarwnego). Siatka: przy 3× zoomie
  narożnika brak facetowania (`corner_zoom.png`), więc normale nie są przyczyną.

## Zmierzone (edytor, metoda r7: luma Rec.709 %, 1024 px; przed = HEAD 799b3af, po = ta zmiana)
| tier/światło | szyba p50 | szyba σ | narożnik p99−p50 | dach p99−p50 | drzwi (profil) |
|---|---|---|---|---|---|
| High overcast | 38,8 → **31,1** | 4,53 → 4,20 | 6,5 → 6,1 | 24,0 → 24,0 | 1,1 → 1,2 |
| Low overcast | 36,3 → **29,7** | 4,20 → 4,02 | 2,1 → 2,4 | 19,2 → 19,2 | 2,0 → 1,0 |
| High lowsun | 21,3 → 18,5 | 7,59 → 7,38 | 34,0 → 32,6 | 62,6 | 7,5 → 6,1 |
| Low lowsun | 19,4 → 16,9 | 7,23 → 7,02 | 27,5 → 27,4 | 45,9 | 4,8 → 3,4 |
| High clear | 31,0 → 25,3 | 5,01 → 6,09 | 28,0 → 28,4 | 3,1 | 2,7 → 3,1 |
| Low clear | 28,6 → 25,0 | 4,70 → 5,71 | 18,1 → 18,1 | 12,3 | 3,1 → 3,3 |

Obszary w 1024 px: szyba 380–460 × 160–200, narożnik 478–495 × 215–255, dach 440–520 × 120–134, drzwi 514–533 × 218–252
(max−min średnich wierszy). Metodą r7 odtwarzam 38,8 / 4,53 / 6,7 (tu 6,5) / 2,1. Wartość drzwi z r7 (6,7) ma
nieopisany obszar i jej nie odtworzyłem.

## Wnioski fizyczne (do decyzji właściciela, bez kręcenia shaderem)
- **D31 p50.** W szybie odbija się teraz ciemna hala za kamerą zamiast samego nieba, dlatego p50 spada do 30–31 %
  (pochmurno), 25 % (słońce). Volvo na zdjęciu ma 23 %. Pasmo 33–45 % zakładało odbicie samego nieba (ADR 0048 r6),
  więc teraz to FAIL progu, ale bliżej zdjęcia.
- **D31 σ ≥ 8: FAIL (4,0–4,2 pochmurno, 5,7–6,1 słońce).** Hala daje strukturę, ale słabą przy F ≈ 0,1. σ 17 w Volvo
  pochodzi głównie z wnętrza widocznego przez szybę (kierowca, kamizelka, fotel) i z odbić drzew. U nas wnętrze to jasny
  prostokąt N-8, a drzewa, latarnie i auta są instancjonowane: `WorldInstances` pomija kamerę Reflection. Dźwignie:
  (a) world-builder: tania ścieżka „reflection” w `WorldInstances` (HLOD lasu + impostory, ≤ 120 m), bo pełne instancje
  na ścianę kosztowały +4 ms CPU na S24+ (A8); (b) wnętrze: zagłówek/kierowca/zasłona zamiast N-8.
- **D30 krzywizna: narożnik FAIL (6,1 High / 2,4 Low), deflektor dachu PASS (24 / 19).** Narożnik w obszarze r7 jest
  pionowym walcem poniżej kamery (2,1 m). Odbija lekko w dół, czyli ziemię i podstawy hal, a nie niebo. Przy F 0,04–0,06
  na białym lakierze daje to fizycznie 2–6 pkt. Wyższa liczba wymagałaby niefizycznego F0. Proponuję mierzyć D30 na
  deflektorze/czapie dachu albo przy lowsun/clear (narożnik 27–34 / 18–28).

## Koszt (szacunek, telefon NIE mierzony)
Jedna ściana (log `[ENVCAP]`, górna granica: wszystkie aktywne MeshRenderery w frustum, wszystkie poziomy LOD):
średnio 148 draws i 179k trójkątów na Low (far 150 m), 155 draws i 180k na High.
A16 Low: widok truck-34 to GPU p50 15,9 ms przy ~1,4 M trójkątów. Przy założeniu w pełni vertex-bound
(pesymistycznie) ściana kosztuje ≤ 2 ms, czyli ≤ 0,2 ms/klatkę przy 1 ścianie na 10 klatek podczas jazdy, a 0 ms na
postoju. Fill 64² to 0,3 % pikseli widoku, mipy cube'a 64 px są pomijalne. Shader na Low robi teraz 1 próbkę cube
zamiast 2 i nie liczy ~15 ALU analitycznej ziemi, więc piksel jest tańszy. Szacunek: **≤ +0,2 ms GPU średnio (budżet
0,3)**. Szczyt ~1–2 ms GPU i ~1–2 ms CPU w klatce ze ścianą (148 draws). High: realny koszt capture jest wyższy niż
w A8, bo dopiero teraz rysuje geometrię. Interwał 2 → 3 i postój bez odświeżania kompensują to. Do pomiaru:
`device-metrics.ps1` z i bez `rq_envcap=0`, w jeździe i na postoju (A16 Low, S24+ High 60 FPS, ADR 0046).

## Konsekwencje
- Globalny cube widzi każdy materiał Truck Exterior/Glass, także naczepa (dobrze) i ewentualne inne pojazdy z tym
  shaderem (odbicie otoczenia gracza, akceptowalne). Wcześniej ograniczało to pudło probe.
- Narzędzie QA: `visual-qa.ps1 -EnvDump` zapisuje `<id>_envcube.png`. Na PNG ściany są w orientacji cube (do podglądu
  trzeba je odwrócić w pionie).
- Test `VehicleReflectionCaptureTierTests` (EditMode).

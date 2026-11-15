# ADR 0239 — Płot panelowy: pokrycie siatki z dystansem zamiast wyboru „mora albo zanik” (B-082)

Status: Proposed (agent rendering-perf, s21 chmura D runda 2, gałąź `fences-0239`), 2026-11-15. Do scalenia przez lidera.
**Kod C#/shader NIEskompilowany w chmurze, nic nie wyrenderowano ani nie zmierzono na telefonie.**
Poprzednicy: ADR 0120 (płot panelowy), ADR 0185 (wyłączenie `mipMapsPreserveCoverage` dla `fence_*`, cofnięte przez lidera
s20), recenzje `docs/reports/REVIEW-2026-11-14-s20-0185.md` (werdykt, P1-3) i 0179 (P11-094). Backlog: B-082.

## Kontekst
Siatka zgrzewana to tekstura `fence_mesh.png` (512 px = 1 m, UV w metrach; drut 3 px = 5,9 mm co 50 mm, poziomy 4 px co
200 mm; średnia alfa 0,152 — policzone z generatora `streetscape.export.fence_mesh_png`). Materiały `fence_*_mesh`
rysował URP Lit z odcięciem 0,5. Na Low (810 px wysokości przy 1080p × 0,75; 60° → 1,4 mrad/px, ESTIMATED z ustawień
tieru) drut jest węższy niż piksel od ok. 4 m. Stałe odcięcie ma wtedy tylko dwa złe wyniki:
- mipy z zachowaniem pokrycia: ~15 % tekseli zostaje nad progiem na każdym poziomie → plamy bijące z siatką pikseli,
  biała mora na 40 m (0179, P11-094);
- zwykłe mipy box: średnia alfa 0,15 < 0,5 → siatka znika, zostają słupki. Rachunek: przy 10 m piksel = 14 mm płotu,
  czyli mip ~2,9, gdzie szczyt alfy drutu spada poniżej 0,5 — zgadza się z obserwacją „od ok. 10 m” (0185 P1-3, lider s20).
Aparat widzi tam coś trzeciego: druty uśredniają się w zasłonę kryjącą ~15 % piksela.
Wszystkie tiery mają MSAA (Low/Medium/High 2×, Ultra 4× — `QualityProfile.Defaults`), więc alpha-to-coverage jest
dostępne wszędzie; przy 2× daje jednak tylko 3 poziomy, a kamery bez MSAA (np. cele pomocnicze) też muszą działać.

## Decyzja
1. **Shader `Kamion/World FenceMesh`** (`game/Assets/_Project/Rendering/Shaders/WorldFenceMesh.shader`,
   `FenceMeshForward.hlsl`, `FenceMeshCoverage.hlsl`): oświetlenie i bufor materiału to nadal URP Lit (wzór:
   `Kamion/Furniture Sign`), podmieniona jest tylko alfa:
   - blisko (piksel < 3,3 mm płotu): ostre odcięcie jak dotąd (krawędź 1 px, A2C wygładza);
   - daleko (piksel > 9,3 mm): alfa = pokrycie. Rozdawane stałym szumem ekranowym (interleaved gradient noise) tak, by
     średnia po sąsiednich pikselach równała się alfie: bez MSAA całe piksele, z A2C w krokach pół piksela — shader
     wypisuje wyłącznie 0 / 0,5 / 1, czyli wartości, które każda implementacja A2C mapuje tak samo przy 2× i 4×;
   - pomiędzy: płynne przejście. Szum bez składnika czasu (brak TAA na wszystkich tierach → migotałby).
   Progi 3,3 / 9,3 mm to WORKING_VALUE wyprowadzone z szerokości drutu w teksturze (1,8 px i 0,6 px drutu), do oceny
   na renderach i telefonie. Odpowiada to ok. 2,3–6,5 m na Low i 3,1–8,7 m na High (płot prostopadle do osi kamery).
2. **Mipy**: `fence_mesh.png` dostaje zwykłe mipy box (`mipMapsPreserveCoverage = false`, filtr Box) — średnia alfa
   teksela mipy jest wtedy udziałem drutu, który shader wydaje jako pokrycie. Dotyczy **tylko tego pliku** (nie całego
   `fence_*`) i tylko gdy shader istnieje; bez shadera (błąd kompilacji) zostaje stan s20 (mora, ale siatka widoczna).
   Własne generowanie mip w Pythonie nie jest potrzebne — generator i glb bez zmian, **zero zmiany trójkątów**
   (kamery C, w tym stretch_04 = 2 022 535, bez zmian; wystarczy reimport).
3. **Importer**: `RegionImporter` po `LitMaterial` woła `FenceMeshCoverage.Apply` dla materiałów z teksturą
   `fence_mesh` (`fence_green/anthracite/galv_mesh`, także w prototypach bram i placu budowy — ten sam asset).
4. **Cień siatki wyłączony** (`FenceMeshCoverage.CastsShadow = false`, przejście `ShadowCaster` wyłączone na
   materiale): drut 5 mm jest węższy niż teksel mapy cieni na każdym tierze (Low: 35 m / 1024 px ≈ 68 mm przy jednej
   kaskadzie, ESTIMATED), więc caster rysował paski aliasingu albo nic (por. B-088). Słupki i podmurówka rzucają cień
   jak dotąd. Jedna stała przywraca caster URP Lit.
5. Odrzucone: (a) samo A2C z nieostrzoną alfą — 15 % przy 2× MSAA zaokrągla się do zera albo zależy od sterownika;
   (b) przezroczysta „mgiełka” w kolejce Transparent — blending i sortowanie z szybami/wodą, drugi materiał i LOD;
   (c) jawne `SV_Coverage` — wymaga GLES 3.1 / liczby próbek, której URP nie udostępnia shaderowi.

## Koszt (ESTIMATED, nie zmierzone)
| pozycja | zmiana |
|---|---|
| fragment forward | +~20 ALU netto (4 pochodne UV, `fwidth`, szum, kwantyzacja; minus `AlphaClip` URP), 0 dodatkowych próbek tekstur; reszta = URP Lit jak dotąd |
| overdraw forward | bez zmian względem main: geometria siatki jest podwójna (dwa nawinięcia) i `Cull Off` → 2 warstwy; daleko przeżywa ~15 % pikseli (tyle co z mipami „coverage”) |
| przejście cieni | **mniej**: siatka (15,7 km płotu panelowego w C wg `streetscape_qa.json` → `furniture.fences.panel_m`) nie jest rysowana do mapy cieni |
| tekstury / trójkąty / draw calle forward | bez zmian |
| warianty shadera | +1 shader, zestaw wariantów jak `Kamion/Furniture Sign` bez cech materiału |

## Testy
- EditMode `FenceMeshCoverageTests` (NIEuruchomione — brak Unity): polityka importu mip, zgodność stałych HLSL ↔ C#,
  kompilacja shadera i kontrakt właściwości Lit, podmiana materiału (kolor/tekstura/kolejka/instancing/cień), przejście
  blisko→daleko dla Low i High, średnie pokrycie = alfa z MSAA i bez (siatka 128×128 px), MSAA ≥ 2 na każdym tierze.
- pytest `tests/gis/test_dojbld_0185.py` 7/7 (zdjęty `xfail` płotu; sprawdza linie importera i średnią alfę 0,152 tekstury).
  Lustro matematyki przeliczone w Pythonie: średnie 0,050 / 0,152 / 0,350 / 0,800 ± 0,001 w obu trybach.

## Weryfikacja u lidera (kolejność)
```
pwsh scripts/test.ps1 -Platform EditMode
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -SkipCopy
pwsh scripts/import-region.ps1 -Region bialystok-dojlidy -SkipCopy
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low  -Lighting overcast -Width 1920 -Height 1080 -Cameras 'kwadrat-park-gate,truck-at-gate,r10_fence_1,r10_fence_2,r10_fence_3,furniture-fence' -OutputDir artifacts/fences-0239/C-Low-overcast
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear    -Width 1920 -Height 1080 -Cameras 'kwadrat-park-gate,truck-at-gate,r10_fence_1,r10_fence_2,r10_fence_3,furniture-fence' -OutputDir artifacts/fences-0239/C-High-clear
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low  -Lighting overcast -Width 1920 -Height 1080 -Cameras 'photo_P11-001,photo_P11-094,photo_P11-129c' -OutputDir artifacts/fences-0239/D-Low-overcast
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier High -Lighting overcast -Width 1920 -Height 1080 -Cameras 'photo_P11-001,photo_P11-094,photo_P11-129c' -OutputDir artifacts/fences-0239/D-High-overcast
pwsh scripts/build-android.ps1 -Install -Run -Serial RFGL34SJYDZ -Tier Low -LogcatSeconds 60
pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Serial RFGL34SJYDZ
```
Kryteria: P11-001 — siatka czytelna jako wypełnienie na 10–100 m (nie same słupki); P11-094 — brak białej kraty/mory na
~45 m; kwadrat-park-gate Low — siatka jest; z bliska druty ostre jak dotąd; w ruchu na A16 brak „pełzania” ziarna
(tego kadry statyczne nie pokażą). p95 klatki na trasie C Low nie gorszy niż w ostatnim pomiarze main.

## Otwarte
- O-1: wygląd ziarna w ruchu i przy skali 0,75 (UNVERIFIED). Gdy razi: podnieść `FENCE_MESH_FADE_FAR_M` (dłużej ostre),
  albo zamienić szum ekranowy na zakotwiczony w UV (hashed alpha, Wyman 2017) — to samo miejsce w `FenceMeshCoverage.hlsl`.
- O-2: gęstość zasłony 15 % na jasnym tle dla `fence_galv_mesh` (albedo 0,40) może znów czytać się jako jasna mgła na
  P11-094 — regulacja `FENCE_MESH_FAR_GAIN` (WORKING_VALUE 1,0 = udział fizyczny).
- O-3: mapowanie A2C 0,5 → 1 z 2 próbek na Mali (A16) i Adreno — UNVERIFIED; gdyby sterownik nie stosował maski,
  zasłona będzie ok. 2× gęstsza (nie zniknie).
- O-4 (poza zakresem, generator): siatka ma podwójną geometrię + `Cull Off` = 2 warstwy fragmentów. Jedno nawinięcie +
  odwrócenie normalnej na tylnej ścianie w tym shaderze dałoby −50 % fragmentów i mniej trójkątów w C; wymaga
  regeneracji regionów, więc nie w tym PR.
- O-5: brak przejścia DepthNormals — na Ultra SSAO nie widzi siatki (jak `World PlotKit` i roślinność).

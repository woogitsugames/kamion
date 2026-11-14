# 0192 — Okna zapalone o zmierzchu/nocą, magenta horyzontu, glare opraw

Status: kandydat (gałąź `nightwin-0192`), nie scalone. Data: 2026-11-13 (s20). Dotyczy: ADR 0182 (zmierzch), 0081 (atlas fasad), 0062 (pule latarni), 0015/0141 (dalekie fasady).
Źródło: `docs/reports/REVIEW-2026-11-13-s19-0182.md` P2-6 (okna), P2-7 (magenta), P2-8 (rozbłysk/glare).

## Kontekst
1. **Okna:** o końcu zmierzchu cywilnego 0 zapalonych okien — „martwy świat z gry”.
2. **Magenta:** sprawdzono render-y after5 (24 klatki, High/Low × clear/overcast/dusk) pod kątem koloru błędu shadera (R,B > 150, G < 0,45·min) — **brak** brakującego shadera/tekstury/wariantu. Magenta = poświata horyzontu: after5 route (143,119,137) sRGB, B > G mimo r5 (B −15 %).
   Przyczyna: `SkyModel.ApplyTwilightChroma` miesza liniowo ciepły kolor LUT (R wysokie) z głębokim błękitem (B wysokie) — ścieżka przez magentę.
   W trakcie tej pracy pojawiła się prawdziwa magenta błędu (after1–6, dalekie fasady `_FAR_FACADE` w World Surface): D3D11 X8000
   „Incompatible min precision … expected int or uint”. 7 bisectów (int→float, hash bez int, bez macierzy, target 3.5, bez branch,
   bez kotwicy) nie usunęło błędu → **World Surface przywrócony do main**; okna na dalekim pierścieniu skyline = otwarte. after7: 0 px magenty błędu.
3. **Rozbłysk:** oprawy = białe punkty z twardą krawędzią. Przyczyna: Bloom wyłączony z założenia (docs/06 §2, `LookDevAssets`), a Low renderuje bez HDR — próg > 1 nie odróżni soczewki 2·10⁵ cd/m² od białej ściany.

## Decyzja
1. **Okna** (`KamionNightWindows.hlsl`, World PBR `_NIGHTWIN` na `facade_atlas` (LOD0) i `*__far_*` (LOD1, 22 materiały WorldC)):
   - dane nocne atlasów generowane z TYCH SAMYCH wywołań, które malują albedo (`art-source/world/materials/_src/night_facade.py` → `Rendering/Resources/Night/`): transmisja szyby (rama/skrzydło 0, czysta szyba 0,55–1,0 wg wysokości w pokoju, firana 0,72, roleta 0,25, zasłony 0,08 z kolorem tkaniny) + id (środek komórki, klasa: mieszkanie / klatka / biuro / hala);
   - przynależność piksela do okna: kotwica = środek komórki w UV przeniesiony na fasadę pochodnymi ekranowymi (afiniczne UV→pozycja w trójkącie, pozycja względna kamery dla precyzji), w przestrzeni obiektu → hash na siatce 1 m: decyzja stała per okno, bez migotania i bez danych w siatce (bez regeneracji świata);
   - rozkład: okna jednego mieszkania (6 m × kondygnacja) razem (P 0,75 | mieszkanie zapalone, 0,06 pojedyncze), biura piętrami, hale 30 m, klatki osobno; udziały z wysokości słońca (`NightWindows.cs`): mieszkania 0,40→0,50, biura 0,65→0,15, hale 0,45→0,30, klatki 0,35; włączanie stopniowe 4°→−2° (stały hash < udział × on); CCT 2700/3200/4000/4500 K wg klasy, jasność ×0,55–1,45 per okno; luminancja średnia 15 cd/m² × ekspozycja. **WORKING_VALUE** (brak zdjęć właściciela nocą).
   - przełącznik profilu: `nightWindowsOff` (odwrócony — stare profile mają włączone).
2. **Magenta:** `SkyModel.SuppressTwilightMagenta` w ostatnim przebiegu LUT (PO adaptacji balansu bieli, która przywracała róż) — gdzie
   min(R,B) > G podnosi G do min(R,B) (blady przejściowy pas łuku zmierzchowego), w niskim pasie w stronę słońca do B/0,85 (B < G).
   Obniżanie R/B zostawiało twarde pomarańczowe komórki obok niebieskich, które bilinearne próbkowanie LUT mieszało z powrotem w róż.
   Horyzont route_putry (1170,420): (143,119,137) → (132,124,126) High; LUT: 0/133 próbek dolnej kopuły z nadmiarem magenty > 0,06.
3. **Glare:** `Kamion/Lamp Glare` + `LampGlare.cs` — jeden ukryty mesh (4 wierzchołki/głowę, 1 draw), billboard o stałym rozmiarze kątowym (3°), L = K·E/φ² (Stiles–Holladay, K = 0,4 dla obiektywu telefonu zamiast 10 dla oka — WORKING_VALUE), E z profilu oprawy pul (full cut-off, 4 % poza 75°). Bez bloomu, działa na Low bez HDR. Przełącznik `lampGlareOff`.

## Budżet (A/B)
- Draws: +1 (glare, tylko gdy latarnie włączone). Trójkąty: +2/głowę (698 głów WorldC = 1396 tris, billboardy poza ekranem odcina clip).
- Dzień: fasady — jeden uniform branch; noc: piksele okien +1 LOAD + 1 sample + ~40 ALU; `posOS`+`posRel` +2 varyingi tylko w wariancie `_NIGHTWIN`.
- Pamięć: Id 512² + 256×512 RGBA32 bez mip (1,5 MB), T 1024² + 512×1024 z mip, ASTC (~0,7 MB). **Telefon: nie zmierzono** (do następnego APK).

## Walidacja
- Rendery WorldC (`artifacts/nightwin-0192/`): before = `artifacts/dusk-0182/after5`; after7 = wersja końcowa High/Low × dusk/overcast
  (`after7/lum.tsv`, `sheet-*.jpg` = before High / after High / before Low / after Low). p50 zmierzch +0,1…+0,9 pp (okna), overcast
  ≤ 0,9 pp (trailer-34: różnica w bazie main po 0182, nie okna — on = 0 w dzień). Okna: blok/dom przy route, biurowiec-wieżowiec piętrami
  w chase, Low = High (te same okna). Glare: subtelne halo widoczne przy oprawie w chase (crop `nw-lampcrop.png`, after1).
- EditMode 23/23 (`NightWindowTests` 7 + `SkyModelTests` + `DuskStreetLampTests`): `NightWindowTests` (udziały, włączanie, tekstury id bez filtrowania/kompresji, flagi materiałów, brak magenty w dolnej kopule zmierzchu, B < G na horyzoncie w stronę słońca, mesh glare) + `SkyModelTests`, `DuskStreetLampTests`.

## Otwarte
- Głowy latarń (`WorldInstances.SendLampHeads`) = środek bounds LOD0, nie soczewka — dla opraw na wysięgniku halo i pule siedzą w połowie ramienia. Do lamppool-0191 / world (nie ruszane tu).
- Okna na dalekim pierścieniu skyline (World Surface `_FAR_FACADE`): X8000 w edytorze D3D11; do zbadania na kodzie skompilowanym
  (Frame Debugger / „Show compiled code”), ewentualnie osobny wariant shadera.
- Kotwica okna: ryzyko ~1e-4 na okno trafienia w krawędź siatki hasha (pojedyncze okno może się dzielić). Docelowo: seed okna w uv1 quada atlasu z generatora (przy regeneracji).
- Pomiar A16/S24+ (frame time nocą), ocena właściciela gęstości okien i siły glare; zdjęcia Białegostoku nocą jako referencja.

## Integracja s20 (night-int-0191-0192, z ADR 0191; recenzja `docs/reports/REVIEW-2026-11-14-s20-0191-0192.md`)
- **Pozycje halo:** `LampGlare.Sync(heads, axes, …)` dostaje oprawy z ADR 0191 (środek szkła na końcu ramienia, 2 na latarnię
  podwójną) — „Otwarte: głowy = środek bbox” zamknięte (crop `final/High-*/chase.png`: halo na końcu wysięgnika).
- **P1-5/P1-6 barwa:** kolor halo per oprawa w kolorze wierzchołka (`axes.z` = sód → `StreetLamps.SodiumLightColor`, LED biel-ciepła);
  `_KamionLampGlareColor` = 1. Oprawy świecą (halo + soczewka), także na Low.
- **P1-7 duchy na drzwiach naczepy:** przyczyna = **okna nocne w kostce odbić pojazdu** (`VehicleReflectionCapture`, 64–128 px; okno
  20–40 m = kilka tekseli, mipy szorstkości filtrowane pudełkowo → kwadratowa miękka plama; `trailer-34_envcube.png` w `r1/`). Poprawka:
  na czas renderu kostki `_KamionWindowsLum` = 0, a `Kamion/Lamp Glare` zwija quad przy `_KamionSkyCapOff` (glare to efekt obiektywu,
  nie radiancja sceny). r1 (z oknami w kostce): plamy na drzwiach High/Low; r2/final: brak (`final/*/trailer-34.png`).
- **P1-8:** klatki nocne w dowodzie (`final/{Low,High}-night`).
- **P2-1 niebo:** próba w `SuppressTwilightMagenta` (minimalny odcień 15° po ciepłej stronie, −B w szarym przejściu) — **0 zmian** w
  pomiarze (route_putry High-dusk kolumna x 1000–1080: y450 (179,127,127) → to samo) → cofnięta. Koralowy pas y 450–480 nie pochodzi z LUT
  kopuły; kandydat: kolor mgły horyzontu (`SkyModel.HorizonColorExposed` / far-field) — **Otwarte**.
- **Budżet A/B** (`final` vs `final-off` = `rq_glare=0,rq_nightwin=0,rq_lampfloor=0` i vs main `artifacts/lamppool-0191/before`, ten sam świat):
  drawsEst / shadow / tris **identyczne** na 5 kamerach × Low/High noc (np. Low chase 416 / 89 / 308 005, High trailer-34 950 / 483 / 1 305 712).
  Poza `SceneStats`: glare +1 draw, +2 tris/oprawę (719 opraw WorldC = 1438 tris). Nowe warianty: tylko `_NIGHTWIN` (shader_feature_local,
  WorldPBR, z 0192) + `Kamion/Lamp Glare` (1 wariant); integracja s20 nie dodaje słów kluczowych (gałęzie uniform). ALU: podłoga ~4/px,
  ogon pul ~4/pulę. **GPU ms na A16/S24+: niezmierzone** (zakaz adb w zadaniu).
- **Luma (`final/lum.tsv`, pas 55–95 %, p10):** noc Low chase 2,0 (0191 after1) → 10,1, route 5,4 → 12,1, gate 5,1 → 11,4, trailer-34 1,6 → 2,4
  (cień pod naczepą); High chase 4,0 → 11,0. Udział podłogi (on vs off): Low chase p10 6,3 → 10,1, route 6,7 → 12,1. Zmierzch p50 trailer-34
  12,5 (0191) → 16,8 Low / 20,3 High (latarnia nad pasem). Overcast p50 = after7 0192 (±0,1 pp: w dzień nic się nie zmienia).
- **Testy:** EditMode pełny 581: 580 OK, 0 porażek, 1 pominięty (`artifacts/tests/editmode-20261114-042553.xml`); nowe `NightIntegrationTests` (6).
- **Otwarte (s20):** koralowy pas horyzontu (P2-1); wieżowiec piętrami jednolity (P2-2, bez zmian); słup latarni łukowej na High nocą
  świeci pomarańczowo na całej wysokości (we stożku spotu, fizycznie możliwe — do oceny na zdjęciach); tuje przy driver_andersa jasne;
  pojazdy na Low bez światła latarń (pule tylko na świecie); pomiar GPU A16/S24+; zdjęcia nocne Białegostoku od właściciela.

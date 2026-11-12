# Recenzja niezależna — pakiet B rund GPT (life r2, cab r2, sbs r2, vegetation r3) — s12

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review. Tylko odczyt (jedyny zapisany plik: ten).
Pytanie: czy każdą gałąź można **scalić do main** (`67f6702c`, po pakiecie A). Kryteria jak w `REVIEW-2026-11-12-s12-gpt-batch-a.md`: (a) brak regresji rozpoznawalności trasy wg D51 i obrazu w kadrach trasy/kabiny, (b) Low draws nie rośnie, tris ≤ +2 %, (c) docs/06 — poprawa albo brak pogorszenia, (d) licencje/marki. PARTIAL dopuszczalny bez regresji.
Wszystko to render edytora. Żadna runda nie była na telefonie — koszt GPU A16: **UNVERIFIED** dla wszystkich czterech.

Metoda własna: `git merge-tree --write-tree main <gałąź>` (bez refów) i `git diff main <drzewo>` = **rzeczywista zmiana netto wobec main** (stat `main...gałąź` jest mylący: wiele baz scalenia, pokazuje pliki sbs r1 / watchdog / unity-slot, które są już na main); obejrzane pary ≤960 px; własne pary przed|po i wycinki obszaru zmiany (life: `before-exact` vs `after-c-exact`, średnie |Δ| luminancji w 1/4 rozdzielczości na 114 kamerach Low-clear); przegląd diffów kodu (WorldPBR, WorldPbrMaterials, life_cars, materials.py, sbs_gate3.py, sbs-gate3.ps1); rozmiar artefaktów wnoszonych do gita.

## Podsumowanie

| Runda | Werdykt | Jakość | (a) trasa D51 | (b) Low draws / tris | (c) anti-slop | (d) licencje |
|---|---|---|---|---|---|---|
| life r2 (osie/koła LOD1, brud kabin placowych) | **SCAL** (generaty --ours + regeneracja) | PARTIAL | bez regresji; 76/114 kadrów Δ<0,01, max 1,37 (zbliżenie `yard_trailer_curtain_0_side8`) | 0 / max +1,76 % trasa (+2,24 % jedno zbliżenie spoza trasy) | mała poprawa (koniec „klocka opon” w LOD1); pojazdy placowe nadal low-poly (P1) | OK (Commons CC BY-SA / CC0 tylko jako referencja, bez logo w grze) |
| cab r2 (skóra CC0 Poly Haven, ziarno tworzywa) | **SCAL warunkowo** (wpis w `docs/LICENSES.md`) | PARTIAL, wizualnie ~0 poza makro | bez zmian (`cab-driver`, `cab-dash` nierozróżnialne) | 0 / 0 (78 kamer) | ziarno: mała poprawa na High; „plastik” = tłoczenie skóry (P1) | **brak wpisu Brown Leather w LICENSES.md** (P0 dla DoD) |
| sbs r2 (metryki v2, raport HTML, fotometria) | **SCAL** | narzędzie PASS, świat bez zmian | n/d — pozy produkcyjne nietknięte (`sbs_cameras.json` poza diffem netto) | 0 / 0 (168) | n/d | OK (atrybucja w każdym arkuszu, raport offline) |
| vegetation r3 (B8 — wszystkie próby odrzucone) | **SCAL warunkowo** (tylko docs + lekkie dowody; bez `snapshot-*`) | brak zmiany produkcji; uczciwy NO-OP | B8 nadal FAIL (stan main) | 0 / 0 (kod = main) | odrzucenie wariantów słuszne | OK |

### Konflikty `git merge-tree --write-tree main <gałąź>`
- **life r2**: 1 konflikt — `Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json` (generated → `--ours` + regeneracja). Auto-merge: `generated/world_manifest.json`, `art-source/world/props/props_meta.json` (pochodne → regeneracja), `WorldPBR.shader`, `WorldPbrMaterials.cs`, `tools/worldgen/streetscape/materials.py`. Kod łączy się automatycznie i poprawnie: materials.py zmienia tylko wiersze `trailer_curtain_*` i `tractor_paint_*` w środku słownika `M`; blok asfaltu r1 (ADR 0118) i pigment filarów (0119) z main zostają — po scaleniu potwierdzić `grep -n "_underdeck_pier_paint\|road_asphalt" materials.py`. `street_props.glb` (LFS) przyjdzie z gałęzi, ale i tak zostanie wygenerowany na nowo.
- **cab r2**: czysto. `TruckAssetBuilder.cs` +31 (addytywnie, `CabLeatherMapping`).
- **sbs r2**: czysto. Dotyka tylko `tools/refs/sbs_*.py`, `scripts/sbs-gate3.ps1`, ADR 0111, nowe `sbs_photometry.json`, `sbs_recognition.json`.
- **vegetation r3**: czysto. Netto: `docs/adr/0109-vegetation-24h.md` (+34), `docs/reports/visual/2026-11-12-vegetation-0109-r3.md` i 805 plików `artifacts/vegetation-r3/` (≈53 MB, z czego ≈46 MB to JSON w `snapshot-baseline/` i `snapshot-candidate-a/` — wymuszone dodanie mimo `.gitignore:31 artifacts/`).
- Między gałęziami: brak wspólnych plików w zmianie netto (life: świat/shader; cab: kabina; sbs: tools/refs; vegetation: ADR 0109). Kolejność nie generuje nowych konfliktów.
- **Kod wymagający ręcznej unii: żaden w tym pakiecie.** Do `--ours` + regeneracji: `generated/fidelity_qa.json` (konflikt), a po scaleniu life — `generated/world_manifest.json`, `generated/streetscape_qa.json`, `props_meta.json`, `street_props.glb`.

Sugerowana kolejność: **sbs r2 → cab r2 (+ wpis LICENSES.md) → vegetation r3 (bez `snapshot-baseline/`, `snapshot-candidate-a/`) → life r2 (`--ours` fidelity_qa.json)** → jedna regeneracja świata + import + `WorldTruckInstaller.InstallBatch` → kamery kontrolne Low/High × clear/overcast; obejrzeć `yard_*` i `stretch-05-docks` (lakier kabin placowych na stanie z asfaltem r1) oraz zaległy warunek pakietu A (klin far-field g3-a 2948 / 303305 clear).

---

## 1. life r2 — SCAL · PARTIAL

1. **Zmiana jest tam, gdzie raport mówi, i tylko tam.** Własna Δ na 114 kamerach Low-clear: 76 kadrów <0,01 LSB; największe w kadrach placowych (`yard_trailer_curtain_0_side8` 1,37, `yard_tractor_white_front34` 0,79, `yard_trailer_curtain_0_front34` 0,55); z trasy najwięcej `stretch-05-docks` 0,15 (przed|po nierozróżnialne w 960 px). Wycinek obszaru zmian `yard_trailer_curtain_3_side35` (High-clear, x 1570–2257): przed — jeden ciemny „klocek” opon pod naczepą, po — trzy oddzielne koła z prześwitami. Realna poprawa sylwetki LOD1 na średnim dystansie, zgodna z referencją Krone/Wielton (trzy osie, szczeliny). Kabiny `lod22`: różnica niedostrzegalna w 960 px.
2. **Lakier kabin placowych (`yard_paint`, `_CarFlake.w=2`) nie rusza osobówek.** W `WorldPBR.shader` gałąź `w<1.5` zawiera dokładnie poprzedni kod (keepUpper/legacyMultiplier przeniesione do środka bez zmiany wartości); `WorldPbrMaterials.YardPaint()` wymaga jawnej flagi + `car_grime_clean` + `paint[4]`. 59/76 PNG osobówek identyczne — spójne z tym odczytem. Brud na kabinach (`compare-b-c-blue.jpg`): ledwie widoczne przyciemnienie przy progu; uczciwie opisane jako „subtelny”.
3. **Budżet OK:** draws świata +0, draws instancji +0; tris trasy Low max +1,76 % (≤2 %), High +0,34 %. LOD1 plandeki 220→316 tris. Limit testu LOD1 podniesiono z 260 na 320 „do wyniku” — dopuszczalne, bo limit trasy 2 % został, a porażka jest zachowana, ale to luzowanie testu pod implementację (P2: limit uzasadnić budżetem, nie maksimum).
4. **Zdjęcie | render (`refs/sbs-yard-rear34-c.jpg`, `sbs-yard-side-c.jpg`) — co odróżnia render od zdjęcia:**
   - P1 · koła: w renderze płaskie szare dyski na całą średnicę, bez felgi, rantu, nakrętek i ciemnego wnętrza; na zdjęciu stalowe felgi z otworami i czarny bok opony. Na zbliżeniu: „gra mobilna z 2012”. Poprawka: w LOD0 osobne pierścienie felgi/opony (ta sama grupa materiałów, rozróżnienie vertex color), ciemne wnętrze felgi.
   - P1 · brak osprzętu podwozia naczepy: barierki boczne przeciwnajazdowe, skrzynka, chlapacze, tylny zderzak z lampami i tablicą (bez znaków). Na zdjęciu Wieltona dominują tył i barierki; w renderze tył to goła rama — zestaw czyta się jak pudło na kółkach.
   - P1 · plandeka: jednolite pionowe fałdy o stałym rytmie na całej długości (powtarzalność); na zdjęciu plandeka napięta, fałdy tylko przy górnej listwie i klamrach, pasy napinające gęsto. `set_tile` poprawił skalę, nie rytm.
   - P2 · kabiny placowe (`yard_tractor_*`): pudło z czarnym prostokątem okna, bez lusterek, osłony przeciwsłonecznej, kratki, stopni. Z odległości trasy akceptowalne (D51), z kadrów placowych nie.
5. Licencje: referencje Commons tylko do analizy; logo Wieltona/Krone nie trafia do gry (materiały bez tekstur z napisami). ADR 0122 ma nieaktualny status „końcowy GIS w toku” (P2 — poprawić przy scaleniu).

Oceny (1–10): skala/proporcje 6 · światło 5 · materiały 4 · zużycie/osadzenie 4 · powtarzalność 4 · polskie realia n/d · czytelność 6 · artefakty 7.

## 2. cab r2 — SCAL warunkowo · PARTIAL

**Warunek:** wpis `brown_leather` (Rob Tuytel, Poly Haven, CC0 1.0, URL, data pobrania, hash z `art-source/truck/interior/cab_material_scans.json`) w `docs/LICENSES.md`. Gałąź go nie dodaje (LICENSES.md poza diffem), a CLAUDE.md §8 wymaga „każdy zasób w LICENSES.md”. Bez tego nie scalać.

1. **Wizualnie ~0 w kadrach gry.** `baseline-High-clear-960.jpg` vs `scan2-High-clear-960.jpg`: 7 kamer nierozróżnialnych w 960 px; `scan2-cab-dash-Low-overcast-before-after-960.jpg` — to samo. Zmiana żyje tylko w makro (`cab-grain`, siedzisko).
2. **Ziarno tworzywa** (`plastic-grain-High-clear-before-after-960.jpg`): przed — gładka, gumowa deska bez mikrodetalu (czerwona flaga docs/06: plastik CG); po — nieregularne ziarno i rozbity połysk. Poprawa, ale to tłoczenie skóry przeskalowane do kafla 10 cm, więc górna deska wygląda jak **pomięty skaj**, nie tłoczone TPO/PP (na referencjach z `cab-r1` ziarno deski jest drobniejsze, regularne, matowe, bez makrofal). Normal 0,6 w niskich częstotliwościach za mocny — P1: high-pass tłoczenia przed normal albo osobny CC0 skan tworzywa.
3. **Skóra** (`leather-seat-High-clear-before-after-960.jpg`): ziarno na obręczy kierownicy (korekta UV 5→12 cm trafna) i na brzegu siedziska. Brak wytarcia w miejscach kontaktu (boczek wejściowy siedzenia, góra obręczy) — P1, autor to przyznaje (K6).
4. **AO (K4):** pasmo AO na High clear nadal widoczne; wariant bez mipów nic nie zmienił. P1 do r3.
5. Koszt 0/0/0/0 na 78 kamerach. EditMode 279/279. GIS 521 pass / 2 fail / 1 xfail — porażki `test_report_not_stale` i `test_export_is_deterministic` (chunk 0_0) zgłoszone jako bazowe z r1. **Lider musi potwierdzić `test_export_is_deterministic` na czystym main** (life r2: 585 pass, sbs r2: 561 pass, vegetation r3: tylko `not_stale` — żadna nie ma porażki determinizmu; jeśli na main jest zielona, to regres cab, nie baza).
6. Na piaście kierownicy widoczny napis (stan main, nie ta runda) — potwierdzić, że to fikcyjny znak projektu, nie marka.

Oceny: skala 7 · światło 5 · materiały 5 (z 4) · zużycie 3 · powtarzalność 6 · czytelność 7 · artefakty 6 (pasmo AO).

## 3. sbs r2 — SCAL · narzędzie PASS, świat bez zmian

1. **Nie psuje main.** Zmiana netto nie dotyka `sbs_cameras.json`, `sbs_references.json`, świata, shaderów ani runtime. `measurements()` przeniesione do `sbs_photometry.image_measurements` (refaktor); `compose()` dokłada pola do `metrics.json` (`schema kamion/sbs-metrics/2`) — addytywnie. Zależności tylko stdlib/numpy/PIL (już w `tools/refs`); raport HTML bez zasobów sieciowych (linki źródeł http/https z `noreferrer`). GIS 561 / 1 xfail, kod 0; report 25/25, photometry 13/13. Zrzut UI `report-ui/sbs-desktop.png`: czerwona belka „Ostatnia recenzja D51: FAIL 12/11/2” na górze — raport nie maskuje stanu bramki.
2. **Zmiana zachowania `sbs-gate3.ps1`, którą lider musi znać (P1):** (a) `-ComposeOnly` bierze teraz **slot heavy na cały batch** — nie wołać z procesu, który już trzyma heavy (oczekiwanie do StaleHours=87600); (b) każdy przebieg bez `-RenderOnly` kończy `Save-EvidenceInputs`, który **rzuca wyjątek**, gdy SHA `world_manifest.json` / `materials_spec.json` / `sbs_cameras.json` / `sbs_references.json` w drzewie różni się od SHA w capture. Na main z brudnymi `generated/*.json` (typowe po cudzej regeneracji) compose się wysypie. Ścisłość słuszna, ale render i compose muszą iść na tym samym, czystym stanie świata.
3. **Pozy G3-B (na main, niezmienione — poprawnie):**
   - **275528** (grobin 2019, B; arkusz r2 obejrzany, świat sprzed ADR 0125): bramownica na horyzoncie, a na zdjęciu wyraźnie bliżej, z dwiema zielonymi tablicami i parą żółtych trójkątów ostrzegawczych po bokach, których render nie ma. Po ADR 0125 (`PRE-R3-VISUAL.md`) portal jest za blisko i ucięty, więc kamera i portal nie zgadzają się w żadnym ze stanów. Plan r3 (cofnięcie wzdłuż kierunku 0/12/16/20 m) rozsądny, ale **kotwice muszą być dwie i niezależne** (portal + nos wyspy/krawędź jezdni), inaczej poza zostanie dopasowana do błędu świata.
   - **837235** (grobin, B): portal w oddali, szewron i nos wyspy niezgodne — rozdzielić błąd pozy od geometrii nosa.
   - **3281350 / 297817** (zsolt, ta sama sekwencja Mapillary, Δt 2,7 s): kolejność i współrzędne spójne; 297817 ma portal daleko w tle. 297817 to też kadr B8 vegetation — **jego poza blokuje vegetation** (§4). Zastrzeżenie D51 dla 3281350 (jezdnia) nadal otwarte.
   - **1801374** (gpsmapper, B): ekran i włączenie łącznicy w innym miejscu względem kamery — przesunięcie wzdłuż drogi, nie zmiana FOV.
   - **494288** (szurek 2017, B; arkusz r2 obejrzany): horyzont zgodny, ale oś obrazu skręca w lewo, na zdjęciu jezdnia prosto/lekko w prawo; ekran po lewej w renderze r2 na zdjęciu nie istnieje (main po ADR 0125 go usunął). Korekta kursu względem osi pomostu.
   - Wszystkie zostają B/WORKING_VALUE; żadnej nie awansować, dopóki r3 nie pokaże dwóch kotwic na aktualnym main.
4. Fotometria: 3 próbki Low-clear, wszystkie Δ=0 (te same piksele co r1) — narzędzie zweryfikowane, wartość diagnostyczna na razie zerowa. Nie cytować tych liczb jako zgodności ekspozycji.

Oceny (narzędzie): poprawność 8 · uczciwość raportu 9 · wpływ na obraz n/d.

## 4. vegetation r3 — SCAL warunkowo · NO-OP produkcji (sprawdzone)

1. **Raport mówi prawdę: produkcja = main.** Zmiana netto nie zawiera żadnego pliku kodu, danych wejściowych ani generatów — tylko `docs/adr/0109` (+34 linie dziennika r3), `docs/reports/visual/2026-11-12-vegetation-0109-r3.md` i artefakty. `vegetation.py` i testy bajtowo jak na main. Probe B/120 Low-overcast bajtowo równy baseline (SHA `958eb031…`).
2. **Odrzucenie prób słuszne** (`rejected-comparison.jpg`): na zdjęciu zsolt dwa duże, gęste liściaste po lewej i kilka niższych w tle; w renderze baseline po lewej tylko niskie tuje i jedno drzewo-bonsai. Wariant `maple_height_only` to **lizak: kilka oderwanych kęp liści na gołym pniu** — czerwona flaga docs/06 (drzewo z asset store/generatora), gorsza niż brak drzewa. B1 nie zmienił piksela w obszarze koron. Słusznie nic nie wdrożono.
3. **Ważniejsze niż drzewa: poza 297817 jest niezgodna.** Na zdjęciu kamera jedzie drogą z zieleńcem po lewej, bez widocznej drugiej jezdni; w renderze po lewej leży pełna druga jezdnia z pasem zieleni. Dopóki SBS r3 tego nie skoryguje, brak dużych koron może być w dużej części błędem pozy. Kolejność: **SBS r3 poprawia 297817, dopiero potem vegetation przypisuje korony** (autor doszedł do tego samego).
4. Polskie realia w kadrze: na zdjęciu biało-czerwone kominy EC i niebieska tablica po prawej — w renderze mgła je zjada (stan main; P2 dla landmarks/far-field).
5. **Warunek scalenia:** nie wnosić ≈46 MB JSON (`snapshot-baseline/instances`, `snapshot-candidate-a/instances`) — to kopie generatów; dowodem są `sha256.json` i `world-proof.json`. Zostawić md/jpg/csv/json raportowe (≈7 MB). Kopia `viaduct_putry_underdeck.spec.json` w `generator-side-effects/` zostaje w artefaktach — nie kopiować do `Data/`.
6. Następna runda (berberys jak bordowe bale) — zgoda, cel niezależny od pozy. Uwaga: propozycja 18 402 tris na cztery obrysy to dużo jak na krzewy przy drodze — policzyć wobec 2 % na trasie przed renderem.

Oceny (stan main w kadrze 297817): skala 5 · światło 4 · materiały 4 · powtarzalność 5 · polskie realia 5 · czytelność 5.

---

## Uwagi do następnych rund GPT

- **life r3:** felgi/opony LOD0 (ciemny bok, rant, piasta), osprzęt podwozia naczepy (barierki boczne, zderzak + lampy + tablica bez znaków), napięta plandeka z pasami zamiast regularnych fałd; limit testu LOD z budżetu, nie z maksimum; status ADR 0122.
- **cab r3:** osobny CC0 skan tworzywa albo high-pass tłoczenia; wytarcie kontaktowe (boczek siedzenia, obręcz); pasmo AO; `test_export_is_deterministic` na czystym main; wpis LICENSES.md od razu przy pobraniu zasobu.
- **sbs r3:** pozy z dwiema niezależnymi kotwicami na aktualnym main (z ADR 0125); priorytet 297817/3281350 (odblokowuje vegetation B8), potem 275528/837235, 1801374, 494288; compose zawsze na czystym stanie świata (nowy guard SHA).
- **vegetation r4:** nie dotykać B8 przed korektą pozy 297817; berberys z pomiarem kosztu; nie commitować kopii generatów do artefaktów.
- Wszystkie: GPU A16 nadal UNVERIFIED — lider po integracji pakietów A+B: APK + `device-metrics.ps1` na A16 (telefon odblokowany).

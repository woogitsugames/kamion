# ADR 0216 — lato jako domyślna pora roku i białe latarnie LED w regionach DK65 / Knyszyn
Status: Proposed (agent rendering-perf, s20, gałąź `summer-led-0216`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D65 p.7–8 (`docs/11`), ADR 0182/0199 (LP_Dusk, zegar), 0191/0192 (pule i glare latarni), 0204/0208/0209
(regiony), research K1 (`research/dk65-knyszyn-refs`), K69/M69 (`research/night-lamps-s21`).

## Kontekst
- D65 p.7: domyślna pora roku/światło na trasie DK65/Knyszyn = lato (zmierzch ~21:00, azymut ~300°). D65 p.8: latarnie białe LED.
- Stan przed: `LP_Dusk` ma słońce −6° / azymut 300° (już letni wieczór), ale `clockHour` 16:10 (listopad, ADR 0199 —
  „do decyzji właściciela o porze roku”). Zegar steruje tylko udziałem świecących okien biurowych. Liście i trawa
  generatora są letnie (`leaf_textures.py`, `hedge_textures.py`: „summer, muted”) — potwierdzone na renderach dziennych.
- Latarnie: barwa LED jest globalną stałą `StreetLamps.k_Led` (1; 0,93; 0,82). Rodzina „starych” słupów ulic bocznych
  (`lamp_old_concrete_9m`, `lamp_old_steel_8m`) ma głowicę sodową (`lamp_glass_sodium`, pomarańczowa pula i halo):
  `knyszyn` 216 z 479 latarni, `knyszyn-w` 72 z 167, `bialystok-knyszynska` 311 z 907 (audyt `lamp_audit.py`), `knyszyn-s` 0.
- K1: na DK65 poza zabudową latarni brak (ortofoto, OSM 0 węzłów `street_lamp`). W `knyszyn` reguła stawiała 15 słupów
  na DK65 (Obozowa, way 286990127) na południe od miasta — w ADR 0204 zostawione jako „niezweryfikowane”.

## Decyzja
1. **Profil oświetlenia regionu jako dane**: `Data/Regions/lighting_profiles.json` → `RegionLightingProfiles`
   (Rendering/Runtime) → import (`WorldSceneBuilder`) zapisuje pola w `EnvironmentLighting` sceny regionu:
   `season`, `duskClockHour`, `ledColour`. Region spoza listy zachowuje dotychczasowe zachowanie (kafel C, Dojlidy,
   Maczka, Kleeberga — bez zmian; test EditMode i pytest to sprawdzają).
2. **Lato** (`summer-dk65-knyszyn`): `bialystok-knyszynska`, `dk65-01…11`, `knyszyn-s`, `knyszyn`, `knyszyn-w`,
   `dk65-monki-01`, `dw671-tykocin-01`. `LP_Dusk` zachowuje słońce (−6°, az. 300° = wartość właściciela) i ekspozycję;
   zegar zmierzchu 21:00 zamiast 16:10 (udział świecących okien biurowych 0,40 → 0,05, `OfficeShareAtHour`). `LP_Clear`,
   `LP_LowSun`, `LP_Night` bez zmian (noc 22:00 jest zgodna z lipcem: Słońce ok. −8°). Sceny dostają profil przy
   następnym imporcie; w tej gałęzi zaimportowane są cztery regiony z p. 3 (kafli `dk65-*` nie dotykano).
   Astronomia (`artifacts/summer-led-0216/sun_summer.json`, Białystok 53,13° N): koniec zmierzchu cywilnego (−6°)
   1 VII 21:48 / az. 323°, 15 VII 21:34 / 319°, 31 VII 21:07 / 311°, 15 VIII 20:34 / 303°; zachód 31 VII 20:24 / 303°.
   Para „21:00 i 300°” nie występuje jednocześnie przy −6°: najbliżej jest koniec lipca (21:07, 311°). Zostawiono
   azymut właściciela (300°); zegar kabiny liczony ze słońca (`SolarClock`) pokazuje przy zmierzchu 20:20. Otwarte p. 1.
3. **Białe LED** (`led-white-4000k` + override `kind: lamp_policy, family: led`): `knyszyn`, `knyszyn-s`, `knyszyn-w`,
   `bialystok-knyszynska`.
   - Generator: `furniture.lamps()` z polityką `led` stawia te same słupy w tych samych miejscach, ale z prototypem
     `lamp_old_concrete_led_9m` / `lamp_old_steel_led_8m` (`props.lamp_old(led=True)`: płaska głowica LED, materiały
     `luminaire_housing` + `lamp_glass`, liczba trójkątów i slotów materiałów bez zmian). Bez polityki wynik jest
     identyczny jak dotąd.
   - Barwa: nominalnie 4000 K (przetargi ZDM 2023–2024, K69 §4 — SOURCED dla ulic Białegostoku; Knyszyn UNVERIFIED,
     deklaracja właściciela „białe”). `ledColour` = (1; 0,96; 0,90) liniowo Rec.709 — WORKING_VALUE dobrana na kamerach
     zmierzchu tak, by soczewka i pula czytały się jako białe. Konwencja: gra ma stały balans bieli światła dziennego;
     kolorymetryczne 4000 K względem D65 to (1; 0,68; 0,36), czyli wyraźnie żółte — nie tak wygląda biała latarnia na
     zdjęciu z telefonu (częściowa adaptacja). Dotychczasowe `k_Led` w konwencji tabeli okien (`KamionNightWindows`:
     4000 K = 1,12; 0,99; 0,85) odpowiada ok. 4300 K, a mimo to na tle nieba zmierzchu czyta się ciepło.
   - `StreetLamps.SetLedColour` (wywoływane z `EnvironmentLighting.Apply`) przebarwia soczewki, światła, pule, podłogę
     nocną i halo. Głowice sodowe zachowują chromatyczność (test); ich poziom idzie za luminancją LED (+2,9 %).
4. **DK65 poza zabudową bez latarni**: `knyszyn` — nowy override `dk65-obozowa-south-unlit-0216`
   (`set: {lamps: false}`, way 286990127; dwa wycinki ortofoto 0,1 m z 2025-05-27 bez słupów i cieni). `knyszyn-s`
   i `knyszyn-w` miały to już (ADR 0204/0209). `bialystok-knyszynska`: Szosa Knyszyńska/Ełcka leży w granicach miasta,
   na ortofoto widać słupy po stronie N — zostawione regule (UNVERIFIED, otwarte p. 3).

## Budżet (przed → po, edytor, kamery o tych samych id)
`scripts/visual-qa.ps1`, kamery świata wspólne dla obu przebiegów (bez kabiny/pojazdu), `stats.txt` (szacunek edytora
przed SRP batching), narzędzie `artifacts/summer-led-0216/tools/budget.py`. Wartości identyczne dla clear/dusk/night.

| region / tier | kamer | draws suma | draws instancji suma | tris suma | maks. draws na kamerę | maks. tris na kamerę |
|---|---|---|---|---|---|---|
| knyszyn Low | 26 | 4517 → 4516 | 1276 → 1279 | 4 380 430 → 4 378 600 | 498 → **499** | 388 839 → 388 805 |
| knyszyn High | 26 | 6542 → 6541 | 2230 → 2210 | 9 821 658 → 9 819 996 | 843 → 843 | 1 008 653 → 1 008 637 |
| bialystok-knyszynska Low | 17 | 2975 → 2924 | 970 → 997 | 2 732 055 → 2 708 931 | 498 → 498 | 296 646 → 296 658 |
| bialystok-knyszynska High | 17 | 6005 → 5951 | 1593 → 1618 | 6 331 951 → 6 092 373 | 1246 → 1246 | 868 712 → 868 816 |

- Latarnie: `knyszyn` 479 → 464 (−15 na DK65 płd.), głowice sodowe 216 → 0; `knyszyn-w` 167 → 167, sód 72 → 0;
  `bialystok-knyszynska` 907 → 907, sód 311 → 0; `knyszyn-s` 0 → 0.
- Jedyne pogorszenie: `knyszyn` Low, najgorsza kamera +1 draw instancji (498 → 499; prototypy LED starej rodziny są
  osobnymi prototypami obok zwykłych LED). W `bialystok-knyszynska` suma draws instancji +27 na 17 kamer przy −51 draws
  zwykłych i −240 tys. tris na High — w całości z jednej kamery `seam-e-into-tile`, która po regeneracji stoi w innym
  miejscu (`control_cameras.json`, ADR 0208), więc nie jest to porównanie tego samego kadru. Bez czterech kamer `seam-*`
  (13 kamer): Low draws 2283 → 2283, draws instancji 753 → 753, tris 2 091 272 → 2 091 513; High draws 4296 → 4297,
  draws instancji 1217 → 1217, tris 4 537 263 → 4 538 010; maks. na kamerę Low 498 → 498, High 1171 → 1171.
  Pozostałe kamery: +2…+159 tris na kamerę w siatkach statycznych (źródło nierozdzielone — regeneracja świata, nie
  instancje latarni: tris instancji bez zmian).
- Odniesienie do `docs/PERFORMANCE_BUDGETS.md` (draw calls przed SRP batching: Low 250, High 800): najgorsze kamery były
  ponad budżetem już przed zmianą (knyszyn Low 498, High 843; bialystok-knyszynska Low 498, High 1246) — to szacunek
  edytora dla kamer przeglądowych, stan zastany; ta zmiana dokłada +1 (knyszyn Low).
- Dane: `Data/raw/derived/<id>/world` knyszyn 793 → 794 MB, bialystok-knyszynska 979 → 979 MB; `_Generated/World`
  knyszyn 758 → 759 MB, bialystok-knyszynska 887 → 888 MB. Biblioteka `street_props.glb`: +2 prototypy (2 × 174/91 tris).
- Shadery, tekstury, liczba świateł i pul: bez zmian (zmienia się kolor globalny, nie liczba próbek).
- Telefon: nie mierzono (lider).

## Walidacja
- **Rendery (edytor, `scripts/visual-qa.ps1 -Scene WorldC`, Low i High × clear/dusk/night, przed i po):**
  `artifacts/summer-led-0216/{before,after}/{knyszyn,bialystok-knyszynska}/{Low,High}-{clear,dusk,night}/*.png`
  (24 przebiegi, wszystkie exit 0); zestawienia przed (góra) / po (dół): `artifacts/summer-led-0216/view/ab_*.jpg`.
  Obejrzane: `knyszyn` dusk/night `rynek-grodzienska-north`, `goniadzka-jagiellonska`, `dk65-inlet-south`;
  `bialystok-knyszynska` dusk/night `route-s0925`, `route-s1665`, `route-s2404`.
  - Pomarańczowa (sodowa) pula i halo przy Rynku w Knyszynie zniknęły; soczewki, pule na jezdni i poboczu czytają się
    jako neutralnie białe na tle nieba zmierzchu, bez przepalenia i bez bloomu większego niż przed zmianą.
  - `dk65-inlet-south` (DK65 na południe od Knyszyna): przed — rząd słupów i pula na jezdni; po — brak słupów,
    droga ciemna (kamera kontrolna bez reflektorów pojazdu), w tle widać dopiero latarnie miasta.
  - Low (tier telefonu minimum) obejrzany osobno: `after/knyszyn/Low-dusk/rynek-fountain`, `Low-night/dk65-poludniowa`,
    `after/bialystok-knyszynska/Low-night/route-s0925`, `Low-dusk/route-s2404` — ta sama biel, bez sodu.
    W `bialystok-knyszynska` zamianę głowic na ulicach bocznych potwierdza tylko audyt (kamery ich nie pokazują).
  - Zmierzch: okna biurowe wg zegara 21:00 (pojedyncze zamiast rzędów), mieszkalne bez zmian. Dzień bez zmian.
  - `bialystok-knyszynska`: na kamerach trasy stoją słupy LED głównej ulicy — różnica to nieco chłodniejsza biel
    soczewek i pul; głowice sodowe były na ulicach bocznych (311 → 0, audyt niżej).
- **Audyt latarni** (`artifacts/summer-led-0216/tools/lamp_audit.py`, wyniki `after/data/<id>/lamp_audit.json`):
  głowice sodowe 0 we wszystkich czterech regionach. DK65: `knyszyn-s` 0 latarni na całej długości; `knyszyn`
  way 286990127 (528 m, 2,7 bud./100 m) 15 → 0; `knyszyn-w` way 232511647 (pola, 0 bud./100 m) 1 słup przypisany
  przez audyt do najbliższej krawędzi (położenie UNVERIFIED, way ma `lamps: false`), odcinek przez miasto (way 232511646, 6,9 bud./100 m) 31 słupów — oświetlony wg ortofoto (ADR 0209).
- **Testy:** po scaleniu `origin/main` (bez konfliktów; main nie zmieniał danych czterech regionów).
  - `uv run --project tools/worldgen python -m pytest tests/gis -q`: 1373 passed, 5 failed, 6 skipped, 5 xfailed
    (`artifacts/summer-led-0216/postmerge/pytest-postmerge.log`). `test_lamp_led_0216` 9/9 (w tym 4 po regeneracji),
    `test_knyszynska_0208` zielony po poprawce (override `lamp_policy` jest regionowy, nie ma `target`).
    Pięć porażek nie dotyczy tej zmiany: dwie znane z main (HANDOVER: `test_hero_bridge::test_asset_lods_and_budget`
    2 022 535 > 2 000 000 tris, `test_world_v31::test_frame_budget_with_forest_hlod`); trzy dotyczą kafla C
    (`test_far_field::test_generated_far_field_qa_and_manifests`, `test_world_v31::test_forest_trees_reference_their_cell`,
    `test_road_fidelity::test_report_not_stale` — `fidelity_qa.json` z main odwołuje się do
    `tools/worldgen/roads/tunnels.py`, którego nie ma w repozytorium: plik jest nieśledzony w katalogu main). Przed
    scaleniem main ten sam zestaw dawał 1319 passed / 1 failed (ten z 0208), więc trzy porażki kafla C przyszły z main
    (wniosek z porównania przebiegów; nie sprawdzano ich na czystym checkoucie main).
  - EditMode (`pwsh scripts/test.ps1 -Platform EditMode`): 606 testów, 605 passed, 0 failed, 1 skipped (Ignored) — po
    obu scaleniach main (`artifacts/tests/editmode-20261115-182356.xml`), w tym `RegionLightingProfileTests`.
  - `CarPaintMaterialTests.DepositionChannel_*` (2 porażki w pierwszym przebiegu worktree): na main 6/6 Passed
    (`artifacts/tests/editmode-20261115-165944.xml`), w worktree od drugiego przebiegu też — efekt świeżego worktree.
- **Telefon:** nie mierzono — brak p50/p95/p99, PSS i temperatury dla tej zmiany (lider, po scaleniu; zakaz procesów
  Unity podczas przebiegów na telefonie). Oczekiwanie (nie pomiar): bez zmiany kosztu klatki — te same siatki, materiały,
  liczba świateł i pul; zmienia się stała koloru i wybór prototypu.

## Otwarte
1. Właściciel: zmierzch „21:00 / 300°” — czy przestawić słońce `LP_Dusk` w regionach letnich na az. ~311° (31 VII,
   wtedy zegar kabiny pokaże ok. 21:05), czy zostawić 300°. Dane mają na to pole do dodania (`duskSunAzimuthDeg`).
2. Kafel C i Dojlidy kwalifikują się na lato tak samo (D65 p.7 mówi o trasie DK65/Knyszyn; ADR 0199 czekał na decyzję o
   porze roku) — wystarczy dopisać id do profilu i zaimportować. K69 podaje też 4000 K dla Andersa/Maczka/Tysiąclecia:
   globalne `k_Led` do decyzji lidera/właściciela po zdjęciach nocnych.
3. Knyszyn: typ słupa (K1: betonowe z wysięgnikiem po jednej stronie, zdjęcia 2009–2012), wysokość i rozstaw —
   WORKING_VALUE generatora (`standards.LAMP`); główne ulice (DW671) mają słupy stalowe ocynkowane z reguły. Potrzebne
   zdjęcie nocne od właściciela. Latarnie stylizowane przy kościele (P14/P15) — nie zrobione.
4. Przejścia dla pieszych 5700 K (K69) i redukcja 70 % po 22:00 — poza zakresem.
5. Telefon: nie mierzono (lider). Zmiana nie dodaje draw calli ani tekstur; koszt shaderów bez zmian.

## Rozszerzenie 0216b — lato i LED w kaflu C i na Dojlidach (D68), 2026-11-15
Status: Proposed (agent rendering-perf G5, chmura, gałąź `summer-cd-0216b`; bez Unity, bez Data/raw — świat NIE
przebudowany). Owner D68: (1) azymut zmierzchu 300° zostaje, (2) lato także w C i na Dojlidach, (3) LED 4000 K zostaje.

**Dane** (`Data/Regions/lighting_profiles.json`, dwa nowe profile; profile Knyszyna bez zmian):
- `summer-bialystok-cd` → `bialystok-industrial-c`, `bialystok-dojlidy`: `season: summer`, `duskClockHour: 21.0`.
  `LP_Dusk` bez zmian (−6°, az. 300°). Zegar 21:00 = wartość właściciela (D65 p.7), WORKING_VALUE.
- `led-white-4000k-bialystok` → te same dwa regiony: `ledCctK: 4000`, `ledColour` (1; 0,96; 0,90) = wartość Knyszyna
  (WORKING_VALUE z kamer zmierzchu 0216). 4000 K SOURCED dla ulic z przetargów miasta: C — Andersa, al. 1000-lecia,
  Maczka (ZDM-VII.7021.1.14.2023, e-zamówienia 93688, TED 658997-2023; K69 §4); Dojlidy — Kuronia, Dywizjonu 303,
  Mickiewicza i 7 innych (ZDM-VII.7021.1.7.2024 / 122716, TED 769998-2024). Stan montażu 2026 UNVERIFIED.

**Astronomia** (`tools/worldgen/qa/sun_noaa.py`: równania kalkulatora słonecznego NOAA GML / Meeus, Białystok
53,13° N 23,16° E, rok 2026, CEST; środek tarczy −6° bez refrakcji; zachód = −0,833°). Odtwarza tabelę 0216 z
dokładnością ≤ 1 min / ≤ 0,5° (test):

| data | zachód / az. | koniec zmierzchu cywilnego (−6°) / az. |
|---|---|---|
| 21 VI | 20:57 / 313,0° | 21:49 / 323,8° |
| 15 VII | 20:46 / 308,9° | 21:34 / 318,8° |
| 31 VII | 20:23 / 302,5° | 21:06 / 311,4° |
| 3 VIII | — | 21:00 / 309,8° |
| 15 VIII | 19:54 / 294,8° | 20:34 / 302,8° |
| 20 VIII | 19:44 / 291,9° | 20:22 / 299,7° |

Para „21:00 i 300°” nie występuje jednocześnie: 21:00 przy −6° to 3 VIII (309,8°), 300° przy −6° to 19–20 VIII
(20:22–20:25). Zostaje decyzja właściciela (D68 p.1: 300°) i zegar 21:00 — WORKING_VALUE, rozjazd ≤ 38 min / ≤ 10°.
Zegar kabiny (`SolarClock`, bez równania czasu) dla −6°/300° pokazuje 20:20 (port w teście; zgodny z NOAA ≤ 18 min).

**Latarnie — źródło dla każdej głowicy LED** (`research/led-tenders-0216b/`: wyciąg 19 ogłoszeń TED Miasta Białystok
o „dostawie i montażu energooszczędnych opraw ledowych” 2024–2026, API TED v3, bez nazw wykonawców i produktów).
- OSM nie daje sygnału: w C 11 węzłów `street_lamp` (6 × `lamp_type=electric`, bez `light:method`), na Dojlidach 0
  (`research/night-lamps-s21/osm-street-lamps.json`, 15.11.2026; tagi `lamp_type=sodium`/`light:method=led` są tylko
  poza tymi kaflami).
- Reguła generatora (`tools/worldgen/qa/lamp_family_audit.py`, liczona na danych w repo — szacunek, nie pomiar)
  stawia starą rodzinę słupów z głowicą sodową w C na ok. 205 pozycjach (QA z main: 199), na Dojlidach ok. 187 (QA: 179).
- **Dojlidy** — nowy override `lamp-policy-led-tender-0216b` (`kind: lamp_policy, family: led, target: {osm_way}`):
  głowica LED tylko na 10 ulicach z ogłoszenia o udzieleniu zamówienia TED 769998-2024 (17.12.2024, cz. II; poz. 14
  Myśliwska, 15 Sępia, 16 Kormoranów, 18 Mickiewicza, 19 Karpińskiego, 22 Kuronia, 23 Dywizjonu 303,
  24 Spadochroniarzy, 25 Hake, 28 Ciołkowskiego) — 64 way grafu o tych nazwach (test: dokładnie ten zbiór). Szacunek
  audytu: 56 z 187 starych głowic → LED (Mickiewicza 29, Kormoranów 6, Myśliwska 6, Karpińskiego 6,
  Spadochroniarzy 6, Sępia 3). Bez źródła (głowica sodowa zostaje, UNVERIFIED): Borsucza, Grabowa, Jaskółcza, Krecia,
  Królicza, Praw Kobiet, Szpacza, Wiewiórcza, Zajęcza, Żurawia i ulice bez nazwy (ok. 131).
- **Kafel C** — override `lamp-policy-unverified-0216b` (`family: unchanged`, tylko zapis): żadna z ulic ze starymi
  słupami (Motoszko, Skidelska, Buska, Sokólska, Łańcucka, Olsztyńska, Świsłocka, Bełzy, Białostoczek, Grodzieńska,
  Kombatantów, bez nazwy) nie występuje w ogłoszeniach LED miasta → sód zostaje, UNVERIFIED. Andersa/Maczka/1000-lecia
  mają słupy LED reguły (zmienia się tylko barwa z profilu).
- Ogłoszenie podaje ulicę, nie odcinek ani datę montażu: Mickiewicza jest też w cz. III (TED 32657-2025) — który
  odcinek dotyczy Dojlid, UNVERIFIED.
- Generator (`streetscape/furniture.py`): reguła wyboru prototypu wydzielona do `chain_lamp_proto` (wspólna z audytem),
  `lamp_led_scope`; polityka z `target` zamienia głowicę tylko na łańcuchach, których środkowy odcinek leży na
  wskazanym way; raport `lamps.policy = led-target`, `led_target_ways`, `led_target_stale`. Bez `target` — jak w 0216;
  bez polityki — wynik identyczny.

**Budżet (oczekiwanie, NIE pomiar):** C — bez zmian geometrii i prototypów; Dojlidy — te same słupy w tych samych
miejscach, ale w scenie oba warianty starej rodziny (sód + LED, prototypy z biblioteki 0216) → do +2 draws instancji
na kamerę, gdzie widać oba (w `knyszyn` 0216: +1). Barwa i zegar: 0 draw calli, 0 tekstur. Telefon: nie mierzono.
Uwaga dla bramki 3 (C): zmierzch C dostaje zegar 21:00 → udział świecących okien biurowych 0,40 → 0,05 (jak 0216);
kadry zmierzchu C sprzed zmiany (0182) przestają być odniesieniem 1:1.

**Walidacja w tej gałęzi:** `uv run --project tools/worldgen python -m pytest tests/gis/test_summer_cd_0216b.py
tests/gis/test_lamp_led_0216.py -q` — 19 passed (schemat i zakresy profili, ApplyTo-bliźniak w Pythonie, NOAA vs
tabela 0216, zegar kabiny, każda ulica LED w ogłoszeniu o udzieleniu zamówienia i w grafie, wyciąg TED bez nazw firm,
reguła: LED tylko na ulicach z przetargu, te same słupy). EditMode `RegionLightingProfileTests` zaktualizowany
(nowy test C/Dojlidy; Maczka/Kleeberga bez profilu) — NIE uruchomiony (chmura bez Unity).

**Walidacja po regeneracji (c-regen-s22, 2026-11-15; raport `docs/reports/INTEGRATION-2026-11-15-c-regen-s22.md`):**
build_world C i Dojlid exit 0. Dojlidy `streetscape_qa.json`: `lamps.policy = led-target`, `led_target_ways = 64`,
`led_target_stale = []`, `lamp_old_concrete_led_9m` 21 + `lamp_old_steel_led_8m` 35 (sód: 50 + 73); C `by_family` bez
`*_led_*`. Import obu regionów loguje `lighting profiles … summer-bialystok-cd,led-white-4000k-bialystok`.
Budżet (`frame_estimate`): C 23 kamery bez zmian (max High 1 986 314); Dojlidy max High 1 768 028, Low −0,8…−4,8 %
(skutek 0221 w `roads`, nie tej zmiany). EditMode 629 = 626 pass / 2 fail (CarPaint DepositionChannel, niezwiązane) /
1 skip — `RegionLightingProfileTests` zielone. Rendery Low/High × clear/dusk before/after
(`artifacts/c-regen-s22/view/ab_*.jpg`): o zmierzchu mniej świecących okien biur (zegar 21:00), dzień bez zmian,
brak regresji. Głowice LED starych słupów Dojlid nie są widoczne w żadnej kamerze kontrolnej (potwierdzone tylko
liczbami); telefon niemierzony.

**Komendy dla lidera (po scaleniu budget-fix 0221; jedna regeneracja C+D):**
```
uv run --project tools/worldgen python -m pytest tests/gis/test_summer_cd_0216b.py tests/gis/test_lamp_led_0216.py -q
uv run tools/worldgen/build_region.py --region bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
uv run tools/worldgen/build_region.py --region bialystok-dojlidy
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy
uv run --project tools/worldgen python tools/worldgen/qa/lamp_family_audit.py --region bialystok-dojlidy   # porównać z generated/streetscape_qa.json
pwsh scripts/import-region.ps1 -Region bialystok-dojlidy
foreach ($t in 'Low','High') { foreach ($l in 'clear','dusk','night') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting $l -OutputDir artifacts/summer-cd-0216b/after/bialystok-dojlidy/$t-$l } }
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
foreach ($t in 'Low','High') { foreach ($l in 'clear','dusk','night') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting $l -OutputDir artifacts/summer-cd-0216b/after/bialystok-industrial-c/$t-$l } }
uv run --project tools/worldgen python -m pytest tests/gis -q
pwsh scripts/test.ps1 -Platform EditMode
pwsh scripts/build-android.ps1 -Install -Run -Tier Low -Fps 30 -LogcatSeconds 60
pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90
```
Oczekiwane w `generated/streetscape_qa.json` Dojlid: `lamps.policy = led-target`, `led_target_ways = 64`,
`led_target_stale = []`, `lamp_old_*_led_*` > 0 i `lamp_old_concrete_9m` + `lamp_old_steel_8m` > 0; w C `by_family`
bez `*_led_*`. Import loguje `[IMPORT] lighting profiles for <id>: summer-bialystok-cd,led-white-4000k-bialystok`.

**Ryzyko konfliktów:** `bialystok-dojlidy/overrides.yaml` — `dojlidy-0242` (F9) zmienia linie ≤ 700, ten blok jest na
końcu pliku: `git merge-tree` czysty. `budget-fix-s21` (0221) i `fences-0239` — bez wspólnych plików (konflikt tylko w
`STATUS.md`). Region `knyszyn` (Codex 0227) i generator dróg C nietknięte.

**Otwarte (0216b):**
1. Montaż w terenie (2025–2026) i odcinek Mickiewicza — nocne zdjęcie właściciela: Mickiewicza/Kormoranów oraz jedna
   ulica spoza przetargu (Żurawia, Krecia); w C Sokólska lub Kombatantów.
2. D68 „lato wszędzie”: `bialystok-maczka` i `bialystok-kleeberga` nie są w profilu (zadanie obejmowało C i Dojlidy) —
   dopisać id, gdy lider zechce (te same dane).
3. Przejścia dla pieszych 5700 K i redukcja 70 % po 22:00 (ZDM) — nadal poza zakresem (0216 p. 4).

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
  `knyszyn` 216 z 479 latarni, `knyszyn-w` 72 z 167, `bialystok-knyszynska` 311 z 910, `knyszyn-s` 0.
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

## Budżet (przed → po, edytor, te same kamery)
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
  zwykłych (kamery szwów przesunęły się po odświeżeniu `control_cameras.json`, ADR 0208) — maksimum bez zmian.
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
  - Zmierzch: okna biurowe wg zegara 21:00 (pojedyncze zamiast rzędów), mieszkalne bez zmian. Dzień bez zmian.
  - `bialystok-knyszynska`: na kamerach trasy stoją słupy LED głównej ulicy — różnica to nieco chłodniejsza biel
    soczewek i pul; głowice sodowe były na ulicach bocznych (311 → 0, audyt niżej).
- **Audyt latarni** (`artifacts/summer-led-0216/tools/lamp_audit.py`, wyniki `after/data/<id>/lamp_audit.json`):
  głowice sodowe 0 we wszystkich czterech regionach. DK65: `knyszyn-s` 0 latarni na całej długości; `knyszyn`
  way 286990127 (528 m, 2,7 bud./100 m) 15 → 0; `knyszyn-w` way 232511647 (pola, 0 bud./100 m) 1 słup przy rozwidleniu
  Goniądzkiej, odcinek przez miasto (way 232511646, 6,9 bud./100 m) 31 słupów — oświetlony wg ortofoto (ADR 0209).
- **Testy:** __TESTS__
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

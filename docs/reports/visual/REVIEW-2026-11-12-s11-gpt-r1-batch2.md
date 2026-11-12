# Recenzja niezależna — pakiet 2 rund GPT r1 (asphalt, landmarks, light, truck) — s11

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review.
Pytanie: czy każdą gałąź można **scalić do main** (`3e7b6bd5`, zawiera już life/vegetation/cab/edge r1). Kryteria jak w `REVIEW-2026-11-12-s11-gpt-r1-batch.md`: (a) brak regresji rozpoznawalności trasy wg D51 i obrazu w kadrach trasy/kabiny, (b) Low draws nie rośnie, tris ≤ +2 %, (c) docs/06 — poprawa albo brak pogorszenia. PARTIAL dopuszczalny bez regresji.
Wszystko to render edytora. Żadna runda nie była na telefonie — koszt GPU A16: **UNVERIFIED** dla wszystkich czterech.

Metoda własna: obejrzane pary przed/po i zdjęcie|render ≤960 px; różnica luminancji (1/4 rozdzielczości, średnie |Δ| w LSB) na pełnych zestawach PNG; zbliżenia natywne wycinków; `git merge-tree --write-tree main <gałąź>` (tylko odczyt); przegląd diffów shaderów.

## Podsumowanie

| Runda | Werdykt | Jakość | (a) trasa D51 | (b) Low draws / tris | (c) anti-slop |
|---|---|---|---|---|---|
| asphalt r1 (+ wciągnięte 0099 surface-wear) | **SCAL** | PARTIAL | bez regresji układu; ślady kół widoczne na trasie (max śr. Δ 1,1 LSB w kadrach trasy, 2,3 w kontrolnych) | 0 / 0 (312 wierszy) | ślady: poprawa; łaty jako „naklejki” bardziej widoczne (P1) |
| landmarks r1 (remiza) | **SCAL** | PARTIAL | bez regresji; zmienia się tylko 5 kamer remizy (max 0,47) | 0 / 0,0 % (192 wiersze) | neutralnie / lekka poprawa świerków |
| light r1 | **SCAL warunkowo** | PARTIAL, największa zmiana obrazu pakietu | Low-overcast bez zmian (40/40 identycznych); Low-clear: niebo zmienione całkowicie; **odsłonięty szary klin far-field** nad horyzontem w pozach g3-a | 0 / 0 % (160 wierszy); +1 tekstura nieba (~5 MB ASTC 6x6, szacunek) i 1 fetch w Sky na Low | duża poprawa nieba; nowy widoczny artefakt (P1) |
| truck r1 | **SCAL** | PARTIAL, wizualnie ~0 | bez zmian (cab-driver Δ ≤ 0,02) | 0 / 0 (96 wierszy) | neutralnie (DRL bez przepału) |

### Konflikty `git merge-tree --write-tree main <gałąź>`
- **asphalt**: 3 konflikty treści — `Data/Regions/bialystok-industrial-c/generated/{fidelity_qa,streetscape_qa,world_manifest}.json` (pliki generowane → wziąć main i zregenerować). `WorldPBR.shader`, `RegionImporter.cs`, `WorldPbrMaterials.cs`, `materials.py` scalają się automatycznie; w scalonym `WorldPBR.shader` brak zduplikowanych deklaracji, ale gałąź zmienia bramki `_KAMION_WORLD_DETAIL` (Low dostaje próbki spękań i foto-detalu) obok zmian life/vegetation z main → obowiązkowa kompilacja wariantów GLES3/Vulkan Low/Medium i kamery kontrolne na wspólnym stanie.
- **landmarks**: 1 konflikt — `generated/streetscape_qa.json` (main + regeneracja). `materials_spec.json`, `world_manifest.json` auto.
- **light**: czysto (0 konfliktów; `QualityProfileApplier.cs` auto).
- **truck**: czysto (0 konfliktów; `TruckGlass.shader` auto mimo cab r1 w main).
- Między gałęziami: jedyne wspólne pliki to asphalt × landmarks w `generated/` (`roads_qa`, `streetscape_qa`, `world_manifest`) — rozwiązać regeneracją. Sugerowana kolejność: truck → light → landmarks → asphalt → jedna regeneracja świata + import + kamery.
- Gałęzie są ~310 commitów za main (bazy `5f2aa277`, light `4c9905b1`).

---

## 1. asphalt r1 — SCAL · PARTIAL

Uwaga procesowa: gałąź **zawiera `gpt-surface-wear` (ADR 0099)**, dotąd nie scaloną (cel FAIL w `REVIEW-2026-11-11-s10-gpt-0099.md`, scalenie techniczne PASS warunkowy). Baseline rundy już ją zawiera, więc pary przed/po pokazują tylko deltę r1; delta 0099 wobec main była zmierzona jako ~0 % pikseli. Scalenie asphalt = scalenie 0099 + r1. Zaszyty mnożnik `wheel_wear × 0,5` z 0099 jest tu usunięty — dobrze.

1. **Ślady kół: realna, widoczna poprawa.** `review-candidate2-960/Low-d_wear_lane_old.jpg` oraz kadr trasy `g3b_eye_s1382` (Low-overcast): przed — pas równo szary, po — dwa ciemniejsze, miękkie pasy w osi kół. Natywne zbliżenie `d_wear_mark_signal` (Low-overcast, High-clear): ziarno kruszywa zachowane, bez nowego moiré. Odwrócono błąd „ślady jaśniejsze niż środek” (1,045 → 0,970), ale do zdjęcia (~0,67) daleko — ślady za słabe, zbyt równoległe i jednakowe na każdym typie nawierzchni.
2. **Łaty: bardziej widoczne, ale jako naklejka (P1, docs/06 §2).** `High-asphalt_patch_aged_fill_close.jpg` i `g3b_eye_s1382` (prawy pas, trasa G3-B): stara łata to idealny jaśniejszy prostokąt z ciemnym obrysem, płaska faktura, zero spękań przy krawędzi, zero zalewki bitumicznej. W baseline też prostokąt, ciemniejszy i mniej kontrastowy. Geometria bez zmian, czytelność „naklejki” większa — na granicy regresji; akceptuję, bo łaty były już na trasie.
3. **Nowa droga — zebra (P1).** `Low|High-d_wear_newroad_negative.jpg`: przed — rozmazane ciemne plamy na pasach; po — trzeci pas ma ostre pionowe ciemne „przecięcie” przez całą długość, piąty pas ucięty. Inny błąd, nie mniejszy. Kadr kontrolny, nie trasa.
4. **Falisty wzór przy krawężniku** — przyczyna nieustalona, wyraźny przy sile 0,80 (`isolation-comparison-960.jpg`), słaby przy wybranym 0,45. P2 do diagnozy (podejrzenie: nakładanie podmateriałów jezdni).
5. **Budżet (b):** draws/shadow/tris/instancje Δ 0 w 312 wierszach; bajty geometrii i tekstur importera identyczne. **Ale Low dostaje dodatkowe próbki istniejących tekstur (spękania, foto-albedo) w shaderze dominującej powierzchni kadru** — potencjalnie najdroższa zmiana pakietu dla A16 Low. Warunek po scaleniu: pomiar A16 Low na trasie; jeśli p95 rośnie > 1 ms — wyłączyć parametrem (`_AsphaltWear.zw = 0`) na Low.
6. Kadry trasy: max śr. Δ 1,1 LSB (`g3b_eye_s1382`), z kabiny 0,21 — kierowca zobaczy ślady na dalszym planie, nie zmianę charakteru drogi. Asfalt nadal czyta się jako czysta tekstura gry.

Następna runda (asphalt r2, przed krawężnikami):
- Łaty: nieregularny obrys, zalewka bitumiczna (ciemny szew 2–4 cm z połyskiem), spękania odbite od krawędzi, ton zależny od wieku skalibrowany na zdjęciu.
- Ślady kół: zmienność wzdłuż, inna siła na wiadukcie i na ulicy; cel kontrastu ~0,8 dla starej nawierzchni (zdjęcie 0,67).
- Zebra nowej drogi: usunąć ostre przecięcie pasa 3 i ubytek pasa 5.
- Pomiar A16 kosztu Low-detail.

## 2. landmarks r1 (remiza JRG2) — SCAL · PARTIAL

1. **Zmiana wąska i bezpieczna.** Różnica Low-overcast: `fire-station-ref7197` 0,47, `abeam` 0,09, `route` 0,08, `driver-andersa-to-putry` 0,04, `above` 0,03; pozostałe 0. Trasa nietknięta. Tynk D48 zachowany (natywne wycięcie szczytu hali: identyczny pigment, napis, okno okrągłe).
2. **Świerki przy prawej elewacji** (`fire-station-ref7197`, wycięcie dolnej elewacji, Low-overcast i High-clear): przed — smukłe „płomienie”, po — szersze, ciemniejsze stożki piętrowe. Masą bliżej zdjęcia Commons 7197 (szerokie ciemne świerki przy hali), ale w High-clear czytają się jako fasetowane origami — piramidy z płaskimi płatami. Lekka poprawa, nadal proceduralne.
3. **Tuje (26 szt., wygładzone normalne):** z 960 px niemal bez zmian — identyczne wrzeciona w równym rzędzie co ~2 m, jak z katalogu. Na zdjęciu nierówne, różnej wysokości, z przerwami. P1 powtarzalności.
4. **Ciemniejszy dół szkła hali:** widoczny tylko w High-clear (dolne łuki okien). Dobry kierunek, efekt mały.
5. Różnice wobec zdjęcia (nie tej rundy): przed „998” brak symbolu z napisu na zdjęciu; na zdjęciu jedna flaga na wysokim maszcie przy lewym rogu, w renderze krótki maszt przy łączniku; napis renderu idealnie czysty. Zacieki r1 niewidoczne z drogi.
6. Budżet: 192 wiersze, draws +0, instancje +0, tris +0,0 % (zaokr.); model LOD0 9344 → 9584, Low 2828 → 2818. Pełny GIS nie był powtórzony po redukcji rdzeni (tylko 7/7 i 10/10 testów remizy) — po scaleniu pełny GIS lidera.

Następna runda (landmarks r2): tuje — zmienność wysokości/szerokości, przerwy, skos; świerki — rozbić fasetowanie (karty igliwia na obrysie); symbol przy „998” i maszt flagi wg zdjęcia; zacieki czytelne z 30 m.

## 3. light r1 — SCAL warunkowo · PARTIAL (największa poprawa obrazu w pakiecie)

1. **Niebo clear: z martwego szaroniebieskiego klosza na fotograficzne cumulusy.** `sbs/before|after/pairs/Low-clear-sbs-g3-b-494288258686575.jpg`: przed — jednolite szare niebo, które samo krzyczało „render”; po — chmury Poly Haven CC0 z poprawną skalą i perspektywą, bliżej czerwcowych zdjęć Mapillary. Dotyczy **Low** (bramka A16). Na montażu 40 kadrów Low-clear: brak szwu na zawinięciu długości, brak schodków przy horyzoncie.
2. **Nowy widoczny artefakt w kadrach trasy (P1): szary klin far-field.** Low-clear i High-clear, pozy `sbs-g3-a-2948595898752384` i `sbs-g3-a-303305168125936` (wiadukt, prawa połowa kadru): nad halami płaska szara płaszczyzna z ostrą ukośną górną krawędzią. W main niewidoczna, bo miała kolor nieba; teraz odcina się od bieli chmur. To odsłonięcie istniejącej geometrii, nie nowa geometria, ale w obrazie trasy to nowy sygnał „koniec świata”. **Warunek scalenia:** lider po integracji renderuje obie pozy na main (z edge r1); jeśli klin widoczny — w tym samym cyklu korekta koloru/wysokości far-field do koloru mgły horyzontu (edge r2 / light r2). Bez tego nie używać zrzutów clear jako dowodu bramki 3.
3. **Ekspozycja Low: bez regresji w overcast, lekko jaśniej w clear.** Low-overcast: 40/40 kadrów identycznych (Δ ≤ 0,01). Low-clear: dolna połowa kadru +1,6 LSB średnio (max +4,4), górna +7,2 (chmury). High-clear dół +2,2. Render clear już był jaśniejszy od zdjęć (asfalt 99,5 vs 77,8), więc to mały krok w złą stronę (< 1 %) — tolerowany, nie regresja.
4. **whiteClip 1,2 → 1,8:** przepał białego lakieru furgonetki znika (≥250: ~74 % → 0 %), ale detalu nie odzyskano — jednolite 245 zamiast 250. Kosmetyka.
5. **RCAS 0,75 i brak dithera tylko High:** natywne wycięcie `g3-a-303305` High-clear — barierki i krawędzie nieco ostrzejsze, bez halo. Pasma 8-bit w gradiencie nieba na telefonie UNVERIFIED. Filtr cieni High/LowSun: próg ≤1 px/10 m niespełniony (1,44 px vs 1,55 przed).
6. **Chmury — ryzyko powtarzalności i „pocztówki” (P2):** jedna mapa na całe niebo — w tym samym kierunku z każdego miejsca trasy te same chmury; nasycony błękit (chroma 2) i idealne cumulusy, zawsze pogodnie. Wnętrza dużych chmur płaskie (autor przyznaje).
7. Budżet: 160 wierszy draws +0, tris +0 %. Koszt poza draws: +1 tekstura 4096x2048 (Android ASTC 6x6, ~5 MB z mipami — szacunek z meta) i `SAMPLE_TEXTURE2D_GRAD` + `atan2/asin` na piksel nieba na wszystkich tierach, także Low. Do pomiaru A16.

Następna runda (light r2): klin far-field (z edge); 2–3 warianty mapy chmur lub obrót sesyjny; ciemniejsze podstawy chmur; kalibracja jasności terenu clear w dół do zdjęć (ROI asfalt/trawa); pomiar A16 Low i High (pasma bez dithera).

## 4. truck r1 (szyba FragFast, DRL) — SCAL · PARTIAL, wizualnie ~0

1. **DRL bez przepału.** `final-candidate/High-overcast/review-lamp-left.jpg`: przed — światłowód przepalony (1214 px ≥254), po — nadal czytany jako świecący. Gradient minimalny; światłowód wygląda bardziej jak biała farba niż kanał z rozproszeniem.
2. **Szyba FragFast (Low):** `Low-clear/review-cab-driver.jpg`, `review-truck-front.jpg` — nierozróżnialne (śr. Δ cab-driver 0,016, max 2,6 LSB). Poprawka matematyczna bez skutków ubocznych.
3. **Reszta bez zmian i nadal FAIL wyglądu:** `photo-render-working-tractor-High-overcast.jpg` — kredowy płaski biały lakier bez odbić (D44 0,49/0,53 przy celu ≥0,7), mleczno-szara szyba, jednolicie biały dach, zero brudu na progach i błotnikach. Obok zdjęcia wygląda jak model z gry mobilnej z 2016 — to stan main, nie regresja rundy.
4. Budżet: 96 wierszy identyczne, siatki i prefaby bez zmian (566 plików), build Android OK. Koszt: kilka ALU w FragFast (UNVERIFIED A16).
5. Low-dusk: moduły reflektorów to płaskie białe pola bez wnętrza — bez bazy, P1 na r2.

Następna runda (truck r2): lakier (F0/clearcoat, odbicie nieba, wypukłość drzwi w normalnej), brud progów/błotników/plandeki, wnętrze reflektorów (soczewki, odbłyśniki), szyba z odbiciem nieba zamiast mlecznej szarości.

---

## Oceny 1–10 (stan po rundzie; w nawiasie zmiana vs main)

| Kategoria | asphalt | landmarks | light | truck |
|---|---|---|---|---|
| Skala i proporcje | 5 (0) | 6 (0) | 6 (0) | 6 (0) |
| Światło i ekspozycja | 5 (0) | 6 (0) | 6 (+2, niebo clear) | 5 (0) |
| Materiały | 5 (+1, ślady) | 5 (0) | 5 (0) | 4 (0) |
| Zużycie i osadzenie | 4 (+1) | 4 (0) | — | 3 (0) |
| Powtarzalność | 4 (0, łaty-prostokąty) | 4 (0, tuje) | 4 (nowe ryzyko: jedna mapa chmur) | — |
| Realia PL | 5 (0) | 6 (0) | 6 (+1) | 5 (0) |
| Czytelność | 6 (0) | 6 (0) | 6 (+1) | 6 (0) |
| Artefakty | 5 (0, zebra/łaty) | 6 (0) | 5 (−1, klin far-field) | 7 (+1, DRL) |
| Budżet Low | 7 (próbki na Low, UNVERIFIED) | 9 | 7 (fetch nieba, UNVERIFIED) | 9 |

Wniosek: wszystkie cztery do scalenia; light z warunkiem sprawdzenia klina far-field po integracji. Po scaleniu: jedna regeneracja świata + import, kompilacja wariantów Low/Medium `WorldPBR`, kamery kontrolne Low/High × clear/overcast na wspólnym stanie, pełny GIS i **pomiar A16 Low** (asphalt Low-detail i niebo light to dwa nowe koszty fragmentu na Low bez zmiany draws). Jedyna runda, która realnie zmienia to, co właściciel zobaczy na telefonie, to light (niebo); asphalt zmienia drogę subtelnie; landmarks i truck są praktycznie niewidoczne z kabiny.

Obrazy pomocnicze recenzenta (≤960 px, katalog tymczasowy sesji, poza repo): stos przed/po `light_lowclear_g3-a-2948595898752384.jpg`, wycinek klina `light_2948_horizon.jpg`, `asph_g3b_eye_s1382.jpg`, `lm_low_High-clear.jpg`.

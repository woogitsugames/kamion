# Visual QA — kafel `bialystok-industrial-c`, v2: otoczenie (2026-11-09)

Rendery kontrolne z Blendera 4.2.9 (EEVEE, 1600×900, 64 próbki, AgX Base Contrast, bez bloomu, winiety i aberracji). Każda kamera ma dwa oświetlenia: **pochmurno** (`__overcast`) i **nisko słońce** (`__lowsun`, 8° nad horyzontem, WSW). Źródło: chunki GLB z pipeline'u (`docs/WORLD_GENERATION.md`), instancje wyposażenia i drzew, materiały proceduralne z masek, które dostanie shader gry. **To render offline, a nie URP na telefonie.** Wersja URP i zrzut z Samsunga A16 są nadal do zrobienia (docs/06 §5, punkt 2: FAIL). Zdjęć właściciela jeszcze nie ma, więc porównuję z ortofoto GUGiK 2024-05-27 i z wiedzą o polskich strefach przemysłowych. Poprzednia wersja (v1) jest w plikach `before_v1_*`, a ocena krytyka v1 w `docs/reports/visual/REVIEW-2026-11-09.md` (na `main`).

## Odcinek referencyjny (Etap 3): brama Kwadrat Parku → Rondo Bieżeństwa, ok. 420 m

Kamery na wysokości oczu kierowcy (2,5 m), kolejno wzdłuż trasy:

| Kamera | Pochmurno | Nisko słońce | Co widać |
|---|---|---|---|
| `stretch_01` — plac Kwadrat Parku, s = 30 m | [overcast](stretch_01__overcast.jpg) | [lowsun](stretch_01__lowsun.jpg) | droga placowa bez krawężnika od strony placu z kostki (BDOT `OT_PTPL_A`), hala z płyty warstwowej po lewej, rampy Kwadrat Parku w głębi po prawej, latarnie 8 m |
| `stretch_02` — droga między halami, s = 150 m | [overcast](stretch_02__overcast.jpg) | [lowsun](stretch_02__lowsun.jpg) | B-33 „30” (OSM `maxspeed`), biurowiec z oknami we wnękach, kostka placu, trawa koszona/niekoszona |
| `stretch_03` — brama, s = 255 m | [overcast](stretch_03__overcast.jpg) | [lowsun](stretch_03__lowsun.jpg) | rozjazd wjazd/wyjazd z wysepką, przejścia P-10 z D-6 po obu stronach, wiata (OSM `building=roof`), słup 110 kV z przewodami |
| `stretch_04` — dojazd do Ronda Bieżeństwa, s = 360 m | [overcast](stretch_04__overcast.jpg) | [lowsun](stretch_04__lowsun.jpg) | wiadukt Andersa z barierą i balustradą, ścieżka z kostki odsunięta od jezdni (BDOT `OT_SKRP_L`), ogrodzenie panelowe zakładu, wiata przystanku |
| `stretch_05_docks` — rampy Kwadrat Parku | [overcast](stretch_05_docks__overcast.jpg) | [lowsun](stretch_05_docks__lowsun.jpg) | 11 ramp numerowanych od 1: bramy segmentowe 3×3 m na wys. 1,20 m, uszczelnienia z żółtymi pasami, odboje, pomosty z pasami ostrzegawczymi, sygnalizatory, prowadnice kół, daszek, betonowy fartuch z nacięciami i plamami |

## Kamery kontrolne v1 (to samo ujęcie co wcześniej)

| Kamera | Pochmurno | Nisko słońce | Przed (v1) |
|---|---|---|---|
| Kierowca Andersa → Rondo Putry | [overcast](driver_andersa_to_putry__overcast.jpg) | [lowsun](driver_andersa_to_putry__lowsun.jpg) | [v1](before_v1_driver_andersa_to_putry.jpg) |
| Rondo Putry z ~40 m | [overcast](putry_above__overcast.jpg) | [lowsun](putry_above__lowsun.jpg) | [v1](before_v1_putry_above.jpg) |
| Brama Kwadrat Parku (z drogi publicznej) | [overcast](kwadrat_park_gate__overcast.jpg) | [lowsun](kwadrat_park_gate__lowsun.jpg) | [v1](before_v1_kwadrat_park_gate.jpg) |
| Wylot DK8/DK19 | [overcast](dk8_dk19_exit__overcast.jpg) | [lowsun](dk8_dk19_exit__lowsun.jpg) | [v1](before_v1_dk8_dk19_exit.jpg) |
| Rondo Bieżeństwa z góry | [overcast](biezenstwa_above__overcast.jpg) | [lowsun](biezenstwa_above__lowsun.jpg) | [v1](before_v1_biezenstwa_above.jpg) |
| Ortofoto + nakładka (place: turkus/fiolet/zieleń, ścieżki czerwone) | [overlay](ortho_putry_overlay.jpg) | | [v1](before_v1_ortho_putry_overlay.jpg) |

## Co się zmieniło względem v1 (odpowiedź na REVIEW-2026-11-09, punkty 1–3 i 7–9)

| Uwaga krytyka | Stan v2 |
|---|---|
| P0 #1: drzewa jak „lizaki” | Własny generator drzew (`make_trees.py`): sosna (szary dół i rdzawa góra pnia, płaska korona z okółków), brzoza (biała kora, zwisające gałązki), olsza, klon, lipa i krzewy. Korony z kart liści, pnie zwężające się, 3 warianty, losowa skala, pochylenie i obrót, krzewy na skraju lasu. LOD0 do 80 m, LOD1 do 250 m, dalej impostor (wypalony render). Rozmieszczenie: gatunki wg kategorii lasu BDOT10k, drzewa pojedyncze i szpalery z BDOT/OSM, samosiew na nieużytkach. |
| P0 #2: wszędzie trawnik | Place, parkingi, fartuchy ramp i ścieżki z BDOT10k i OSM (ok. 230 tys. m²): kostka szara, beton z nacięciami, płyty drogowe, asfalt, kruszywo, czerwone drogi rowerowe. Ogrodzenia panelowe 3D na cokole (15,9 km) i z płyt betonowych (2,2 km), 23 szlabany i 36 bram z OSM. Budynki mają fasady wg typologii (hala, biurowiec, blok, dom, budynek gospodarczy). |
| P0 #3: krawężniki niezależnie od klasy | Przekrój zamiejski: strony jezdni GP/G przy ≥ 70 km/h bez chodnika lub ścieżki w odległości 7 m mają pobocze utwardzone i nieutwardzone, rów i brak krawężnika. Pas dzielący przy DK8 (90 km/h) ma opaskę, trawę i barierę stalową. Na mostach jest bariera na kapie i szara balustrada (już nie biała). Krawężniki są szare (albedo 0,26), w segmentach 1 m ze stykami i brudem. Drogi placowe nie mają krawężników. |
| P1 #7: asfalt i linie | Asfalt: łaty (prostokątne komórki), rysy z zalewaniem bitumem, polerowane ślady kół i lekkie koleiny (z `TEXCOORD_1` = współrzędna pasa), plamy oleju w osi pasa, brud przy krawężniku, szew między pasami. Linie są wytarte i zabrudzone. |
| P1 #8: teren | Pasy dzielące i wyspy mają powierzchnię rozpiętą między krawędziami dróg (koniec z garbami). Skarpa 1,5–12 m od drogi jest wygładzona (bez faset). Maski podłoża: trawa koszona i niekoszona, ściółka, goła ziemia, pas piachu przy krawędzi. Kępy trawy i chwastów przy krawężnikach. |
| P1 #9: przejścia w trawę, ekrany, wiadukty | Ścieżki odsunięte od jezdni domykają część przejść. Ekrany akustyczne z BDOT10k `OT_OIKM_L` (1,7 km, m.in. Andersa). Na mostach bariera + balustrada. Cień pod wiaduktem widać w `lowsun`. |
| Wyposażenie (zakres Etapu 3) | 705 latarni, A-7 + C-12 na wlotach rond, A-7/D-1, 64 × B-33 (powtarzane za skrzyżowaniem), 81 × D-6, D-15 + wiaty na 23 przystankach, 9 schematycznych E-2 z OSM `destination`, S-1 na 33 wlotach z sygnalizacją, linie 15 kV/110 kV ze słupami. |

## Pętla poprawek (moje uwagi z renderów i co zrobiłem)

1. **r1** ([before_r1_stretch_01_washed_kerbs.jpg](before_r1_stretch_01_washed_kerbs.jpg)):
   - prześwietlony obraz, ciemny pas „ziemi” Nishity za kaflem → mgiełka horyzontu, daleka płaszczyzna terenu, ekspozycja −0,45;
   - rysy jak czarne patyki → cieńsze i rzadsze;
   - wysoki krawężnik między drogą placową a placem → drogi serwisowe biegnące przez plac BDOT/OSM są bez krawężnika, a obrzeże placu nie powstaje tam, gdzie plac styka się z jezdnią;
   - UV v przesunięte o 1 m w imporcie → poprawiony zapis `TEXCOORD` w GLB.
2. **r2** ([before_r2_dk8_orange_branches_flat_grass.jpg](before_r2_dk8_orange_branches_flat_grass.jpg)):
   - pomarańczowe gałęzie sosen i białe gałęzie brzóz → osobna kora gałązek, mniej nasycona kora sosny;
   - goła brązowa ściółka → zieleńsza z mchem;
   - płaska zielona „wykładzina” → kępy trawy (w r2 nie działały: zła przestrzeń współrzędnych w Geometry Nodes);
   - białe bariery → ciemniejsza stal ocynkowana;
   - zbyt jasne, błyszczące ślady kół → większa szorstkość.
3. **r3** ([before_r3_andersa_grass_through_asphalt.jpg](before_r3_andersa_grass_through_asphalt.jpg), [before_r3_stretch_03_moss_blotches.jpg](before_r3_stretch_03_moss_blotches.jpg)):
   - trawa przebijająca asfalt przy wyspach → maska R = 0 dokładnie pod drogą/placem i próg 0,7 m;
   - plamy mchu na całych wyspach → mech tylko w fugach (odwrócony współczynnik cegły) do 0,6 m od krawędzi;
   - kępy w trawie koszonej za wysokie → skala zależna od maski koszenia.
4. **r4/final**:
   - za czerwona kostka przejazdowa rond → szaro-czerwona;
   - jaśniejsze kępy trawy;
   - z tyłu tablicy prześwitywało lustrzane „30” → tył tablicy zasłania lico (backface culling).

## Wyniki liczbowe (z `Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json`)

| | Wartość |
|---|---|
| Budynki | 79 hal, 109 biurowców/usług, 51 bloków, 270 domów (dach dwuspadowy), 120 budynków gospodarczych, 14 wiat; 207 ramp (11 na Kwadrat Parku: elewacja od placu) |
| Place [m²] | BDOT `PTPL` 174 680, ścieżki `SKRP` 24 181, fartuchy ramp 14 467, BDOT `KUKO` 8 975, OSM 10 173 |
| Drzewa | sosna 36 515, brzoza 25 570, olsza 14 260, klon 11 138, lipa 8 296, krzewy 13 695 |
| Rozmiar GLB | High ~390 MB (217 MB to teren 1 m), Low/Medium `.low.glb` ~85 MB (normalne int8, kolory 8-bit) |
| Klatka (klin 120°, bez occlusion cullingu) | Low 0,24–0,81 mln trójkątów; High 1,0–3,1 mln, w lesie przy DK8 8,1 mln |

## Nadal do zrobienia (ocena: wyraźny postęp, ale **jeszcze nie PASS** jako próbka referencyjna Etapu 3)

- **Uskok krawężnika na bramie** (rozdzielenie jezdni dwukierunkowej na wjazd i wyjazd z wysepką) nadal jest widoczny na `kwadrat_park_gate`. Zwężenie skosem 1:10 działa tylko dla tej samej drogi zmieniającej szerokość (75 miejsc w kaflu).
- **Bariery na nasypach:** reguła „nasyp > 2 m” nie znalazła żadnego odcinka. Trzeba sprawdzić próg i spadki na wylocie DK8.
- Szlaban na bramie stoi wg węzła OSM. Pozycja i portiernia wymagają zdjęć.
- Budynki to bryły LoD1 z otworami. Brak attyk z obróbką w kolorze, reklam, rynien, klimatyzatorów. Kolory hal nie są zweryfikowane (zdjęcia).
- Kępy trawy są tylko w renderze. W grze potrzebny jest system detail grass w URP.
- Budżet: High w lesie przekracza cel (8 mln) → gęstsze impostory/HLOD lasu i occlusion culling. Low przy Andersa 0,81 mln → ścisłe LOD terenu.
- Rozmiar: kompresja `EXT_meshopt_compression` przy buildzie (glTFast) oraz teren 1 m tylko w pasie drogi.
- Tekstury CC0 ze skanów (Poly Haven / ambientCG, zgoda lidera z 2026-11-09) nie są jeszcze użyte. Asfalt, beton i kostka są w pełni proceduralne. Następny krok to porównanie ze skanem.
- Ocena `visual-critic` dla v2 i porównanie ze zdjęciami właściciela (sesja z `docs/map-decisions.md`).

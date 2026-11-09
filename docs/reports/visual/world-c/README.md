# Visual QA — drogi i teren, kafel `bialystok-industrial-c` (2026-11-09)

Rendery kontrolne z Blendera 4.2.9 (EEVEE, 1600×900, 64 próbki), wygenerowane z chunków GLB pipeline'u (`docs/WORLD_GENERATION.md`). Materiały to proste proceduralne PBR, a budynki (bryły LoD1) i drzewa (rozrzut w lasach z BDOT10k) są tylko kontekstem. **To nie jest finalna grafika.** Zdjęć właściciela z tego miejsca jeszcze nie ma, więc porównuję z ortofotomapą GUGiK 2024-05-27 (tylko referencja) i z wiedzą o polskich drogach. Krytyk `visual-critic` nie oceniał (subagenci nie tworzą subagentów), więc ocena wymaga drugiej pary oczu.

| Kamera | Plik | Co widać | Ocena |
|---|---|---|---|
| Kierowca 2,5 m, Andersa → Rondo Putry | [driver_andersa_to_putry.jpg](driver_andersa_to_putry.jpg) | dwie jezdnie z pasem dzielącym, P-1b, P-7b, zjazd w prawo z łukiem krawężnika, las z BDOT | proporcje i szerokości wiarygodne; brak latarni, znaków i ekranów (poza zakresem) |
| Rondo Putry z ~40 m | [putry_above.jpg](putry_above.jpg) | pierścień pod wiaduktem Andersa, przejazdowa kostka wyspy, P-14 i strzałki na wlotach, balustrady wiaduktu | układ zgodny z ortofoto; teren poza drogą to wszędzie trawa |
| Brama Kwadrat Parku | [kwadrat_park_gate.jpg](kwadrat_park_gate.jpg) | droga dojazdowa 7 m (override), rozwidlenie | **odstępstwo**: w rzeczywistości utwardzony plac, a nie trawa (place nie są modelowane); uskok krawężnika na rozwidleniu |
| Wylot DK8/DK19 (Al. Tysiąclecia) | [dk8_dk19_exit.jpg](dk8_dk19_exit.jpg) | dwie jezdnie w lesie sosnowym, most nad doliną (balustrady), P-7b | wiarygodne; drzewa low-poly jako kontekst |
| Rondo Bieżeństwa z góry | [biezenstwa_above.jpg](biezenstwa_above.jpg) | wiadukt Andersa nad rondem, wyspa z pasem kostki, P-10 | zgodne z ortofoto |
| Ortofoto + nakładka | [ortho_putry_overlay.jpg](ortho_putry_overlay.jpg) | po lewej ortofoto, po prawej wygenerowane drogi (asfalt ciemny, krawężniki białe, chodniki pomarańczowe, oznakowanie żółte, mosty niebieskie) | jezdnie Andersa, Maczka i Al. Tysiąclecia leżą na swoich jezdniach z ortofoto; odchyłki są w granicach opisanych w `docs/DATA_QA.md` §5 (oś OSM Andersa 1,5–2 m od środka jezdni) |

## Co znalazłem na renderach i poprawiłem

1. **Rozsypane trójkąty mostów i krawężników** ([before_r1_putry_above_scrambled_bridge.jpg](before_r1_putry_above_scrambled_bridge.jpg)): przez wiadukt szły długie, cienkie trójkąty, a przy przyczółkach były dziury. Przyczyna: maska „na moście” liczona per wierzchołek zamiast per trójkąt (`T // n` zamiast `T.min(1) // n`), więc indeksy mieszały się przy podziale na część naziemną i mostową. Naprawione w `build_ribbon` i `_emit_strip`.
2. **Wyspa ronda przebijająca wiadukt** ([before_r2_biezenstwa_deck_in_nmt.jpg](before_r2_biezenstwa_deck_in_nmt.jpg)): NMT 2025 pod wiaduktem nad Rondem Bieżeństwa ma „grunt” na wysokości pomostu (profil: spadek 6,5 m tylko na 15 m, reszta pod pomostem płaska na 140–141 m). Generator ma teraz dwa przebiegi: wykrywa komórki NMT w grubości pomostu i zastępuje je interpolacją harmoniczną (12 545 węzłów), a teren trzyma ≥ 0,3 m pod spodem pomostu. Pierścień ronda jest teraz pod wiaduktem.
3. **Niweleta oderwana od NMT o 1,5 m** na Andersa (wykres profilu: minimalny promień pionowy 1500 m wymuszał „wyprostowanie” garbu przy moście). Promienie zmniejszone (GP 800 m, WORKING_VALUE). Mediana RMS względem NMT 0,01 m.
4. **Krawężniki w poprzek jezdni i olbrzymie trójkąty łat** przy Rondzie Putry (klaster 8 ramion o średnicy 45 m). Limit klastra zmniejszony do 30 m. Na łatach naprawianych przez `make_valid` krawężnik powstaje tylko na zewnętrznym obrysie. Długie ukośne połączenia prostych narożników zastąpione zejściem po krawędzi jezdni.
5. **Nosy pasa dzielącego wchodzące na jezdnię poprzeczną** (dwa półokręgi nachodzące na siebie przy przejeździe przez pas dzielący): przycięcie ramion wydłużane o promień nosa.
6. **Rozwidlenia łącznic** (dwie jezdnie od jednego węzła pod małym kątem): nos ustawiany tam, gdzie krawędzie się rozchodzą (szukanie do 160 m), a nie w węźle.
7. **Uskok krawężnika „Z” na bramie bazy** ([before_r5_gate_kerb_notch.jpg](before_r5_gate_kerb_notch.jpg)): zastąpiony zwężeniem po krawędzi dłuższego ramienia. Uskok jest mniejszy, ale jeszcze nie znikł (patrz braki).
8. **Białe pełne ściany na mostach** ([before_r2_dk8_no_vegetation_solid_parapet.jpg](before_r2_dk8_no_vegetation_solid_parapet.jpg)): balustrada była pełnym metalowym blokiem, a przyczółek wystawał 0,5 m poza pomost. Teraz jest ażurowa balustrada (poręcz, pochwyt, słupki co 2 m), przyczółek ma szerokość pomostu, a beton jest ciemniejszy.
9. **Pusty, płaski krajobraz („zabawka”)**: dodany kontekst lasów z BDOT10k (las sosnowy przy DK8 jest zgodny z ortofoto), stonowane albedo brył budynków, AO, kontrast AgX.

## Nadal do zrobienia (FAIL dla jakości Etapu 3, OK jako pipeline Etapu 4)

- Brak placów, parkingów i chodników oddalonych od krawężnika. Teren poza drogą to wszędzie trawa.
- Brak wyposażenia (latarnie, znaki pionowe, sygnalizatory, bariery na pasie dzielącym, ekrany akustyczne).
- Asfalt bez kolein, spękań i łat z maskami (jest tylko szum).
- Uskok krawężnika na rozwidleniach o różnej szerokości.
- Porównanie ze zdjęciami właściciela (sesja z `docs/map-decisions.md`) i ocena `visual-critic`.

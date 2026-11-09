# Unity look (WorldC) — pierwsze kadry z silnika, 2026-11-09

Źródło: **edytor Unity 6.3, URP, batchmode** (`pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier … -Lighting …`), rozdzielczość
telefonu 2340×1080 z MSAA i skalą renderu danego profilu (emulacja), zmniejszone do 1600 px JPG. **To nie są zrzuty z
telefonu** — Galaxy A16 był zablokowany PIN-em cały dzień. Decyzje i liczby: ADR 0010 (wygląd), ADR 0011 (import świata).

## Podsumowanie dla właściciela (PL)
- **Świat C jest w Unity i da się nim jechać.** 64 kafle z generatora (glTFast), materiały z manifestu, kolizja z osobnych
  siatek z typem nawierzchni. Ciągnik solo i zestaw 40 t przejechały automatycznie całą trasę 2,4 km (brama Kwadrat Parku →
  Rondo Bieżeństwa → Andersa → Rondo Putry → DK8/DK19) bez przelecenia przez podłoże (test `WorldCRouteTests`).
- **Niebo i światło są teraz policzone, a nie „na oko”:** model nieba Preetham (pogodnie) i CIE (pochmurno), natężenie
  słońca i nieba z danych dla światła dziennego, ekspozycja jak ze światłomierza (EV 14,5 w słońcu, 12,3 w pochmurny dzień).
  Z tego jednego modelu idą słońce, niebo, światło otoczenia, odbicia i mgła — dlatego horyzont nie ma już szwu.
- **Tonemapping: Neutral, nie ACES.** Porównanie jest niżej: ACES robi ciemne, nasycone „HDR-owe” zdjęcie (czarna burta
  naczepy, jaskrawozielona trawa). Neutral wygląda jak zwykłe zdjęcie z telefonu.
- **Linie na jezdni nie migoczą w oddali** (przesunięcie głębi + filtrowanie z odległością), **trawa nie ma widocznego
  kafelkowania** (druga skala tekstury + szum makro).
- **Low i Medium wyglądają prawie tak samo** (Low bez post-processingu, w mniejszej rozdzielczości) — to dobra wiadomość
  dla A16. Wydajność: **niezmierzona**, wszystkie budżety oznaczone UNMEASURED (`docs/PERFORMANCE_BUDGETS.md`).
- **Czego te kadry NIE naprawiają** (to zadania world-buildera z przeglądu z 9.11): drzewa, place i parkingi zamiast trawy,
  bariery na DK, budynki. Świat to dalej „drogi na trawniku” — tylko teraz poprawnie oświetlone.
- **Twoja opinia potrzebna:** niebo w pogodny dzień wydaje mi się trochę zbyt szare/łupkowe względem zdjęcia. Zanim je
  podkręcę, chcę porównać z Twoimi zdjęciami z Białegostoku (pogodny dzień, ok. południa, widok wzdłuż drogi).

## Kadry
| Plik | Co pokazuje | Co widzę |
|---|---|---|
| `driver-andersa-to-putry_Low-clear.jpg`, `_Medium-clear.jpg`, `_High-clear.jpg` | oczy kierowcy 2,5 m, prawy pas Andersa w stronę Ronda Putry, 3 profile | asfalt ciemnoszary (albedo 0,075), linie ostre blisko i spokojne w oddali; Low lekko miększy (skala 0,75), bez różnic w ekspozycji; brak migotania przerywanych linii; niebo bez bandingu |
| `driver-andersa-to-putry_Medium-overcast.jpg`, `_Low-overcast.jpg` | to samo, pochmurno | płaskie, szare niebo CIE, brak cieni, kontrast niski jak w pochmurny dzień; trawa nie przesycona |
| `putry-above_Medium-clear.jpg`, `_Medium-overcast.jpg`, `_High-clear.jpg` | węzeł Putry z ~40 m | brak kafelkowania trawy na dużych połaciach; dalekie linie przefiltrowane (wcześniej iskrzyły); horyzont kafla = koniec danych (płaska krawędź) |
| `kwadrat-park-gate_Medium-clear.jpg`, `_Medium-overcast.jpg` | brama bazy, droga dojazdowa | uskok krawężnika na rozwidleniu (znany brak generatora); teren poszarpany przy krawędzi drogi (przegląd #8) |
| `dk8-dk19-exit_Medium-clear.jpg`, `_Low-overcast.jpg` | wylot DK8/DK19 | droga krajowa bez barier i pobocza (przegląd #3, world-builder) |
| `truck-at-gate_Medium-clear.jpg`, `_Low-clear.jpg` | zestaw na spawnie przy bramie | koła na kolizji, cień zestawu na asfalcie bez trądziku cieni (bias 1,0), strona naczepy w cieniu czytelna, nie czarna |
| `truck-at-gate_Medium-clear-ACES.jpg`, `driver-andersa-to-putry_Medium-clear-ACES.jpg` | **A/B tonemappingu** — ACES | ciemniej, burta naczepy prawie czarna, trawa jaskrawa, niebo granatowe → odrzucone |
| `cab-gate_Medium-clear.jpg` | widok z kabiny (graybox) na spawnie | lusterko pokazuje naczepę; widoczność drogi dojazdowej |

## Poprawki pipeline’u zrobione w pętli wizualnej
1. Iteracja 1: niebo z różowym pasem nad horyzontem (artefakt chromatyczności Preethama) → chromatyczność liczona nie niżej
   niż 6° nad horyzontem; turbidity 3 → 2,5.
2. Iteracja 1: dalekie linie iskrzą (pod-pikselowa geometria) → filtr pokrycia w shaderze.
3. Test SH: światło otoczenia było **1,9× za jasne** (normalizacja `AddDirectionalLight` w Unity) → kalibracja, test w EditMode.
4. Iteracja 3: na Low trawa i asfalt miały „chmurkowy” szum (jedna próbka tekstury) → mniej niskich częstotliwości w
   teksturach, słabsza wariacja makro na asfalcie.
5. Iteracja 4: trójkąty w widoku ponad budżet Medium → LOD bias Low 0,5 / Medium 0,8.

## Następne kroki
- Pomiar na A16 (FPS, PSS, temperatura) dla Low/Medium: `pwsh scripts/device-metrics.ps1 -Launch -Scene WorldC -Autopilot route -Speed 50`.
- Zrzuty z telefonu z tych samych kamer i porównanie side-by-side (docs/06 §5 pkt 2).
- Przegląd `visual-critic` tych kadrów.
- Tekstury: zgoda na pobranie skanów CC0 (Poly Haven / ambientCG) dla asfaltu, trawy, kostki.

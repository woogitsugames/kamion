# ADR 0102 — Meble uliczne r1

Status: WIP, dowody Unity i budżet w toku. Data: 2026-11-11. Gałąź: `gpt-furniture-r1`, baza `9e6e9fde`.

## Problem i źródła

QA bazowe `generated/streetscape_qa.json`: `pole_footing_steps` 147 / maks. 1,087 m.
To miara reliefu pod stopą, a nie licznik udowodnionych wiszących słupów. Dotychczas osadzenie wybierało
minimum pięciu próbek oraz obniżało widoczny słup do rzadszej siatki kolizji, przez co zakopywało jego oś
w górnej stronie skarpy. ADR 0069 i lokalne referencje Mapillary p12/p15/p20/p26/p30 pokazują rodziny
wyposażenia; zdjęcia pozostają wyłącznie referencjami. Przypisania rodzin do poszczególnych bocznych ulic
pozostają heurystyką WORKING_VALUE, nie pomiarem inwentaryzacyjnym.

## Decyzje

- Oś słupa stoi na widocznej powierzchni w swoim położeniu; kolizja nie obniża geometrii renderowanej.
  Latarnie przy ostrym uskoku mają deterministyczne szukanie stabilnego podłoża w promieniu do 1,05 m
  (próg reliefu/rozbieżności kolizji 0,15 m, oba WORKING_VALUE). Nadal obowiązują istniejące usuwanie
  kolizji z jezdnią i wiaduktem. Jawne wysokości lamp na pomostach nie są przesuwane.
- Fundament latarni stalowej: dół −0,45 m, góra +0,08 m; żerdź betonowa: osadzenie −0,30 m.
  Są to WORKING_VALUE konstrukcji, a nie wymiary z dokumentacji producenta. Nie zakopujemy ponad metra
  modelu: audyt bramki 3 interpretuje dolny punkt bounds jako kontakt z podłożem.
- Stare rodziny zachowują sylwetki `lamp_old_concrete_9m` / `lamp_old_steel_8m`; obejmy żerdzi dopasowane
  do promienia na wysokości montażu, stalowy słup ma drzwiczki rewizyjne. Betonowa rodzina Low redukuje
  liczbę segmentów wysięgnika. Nie dodajemy slotów materiałowych do istniejących prototypów.
- Atlas UV lamp/słupków: wysokość fizyczna słupa, bez powtarzania rdzy co metr. Mikrostruktura z istniejących
  CC0 `brushed_concrete` i `corrugated_iron_03` (bez szerokich przetłoczeń); lokalna warstwa brudu przy gruncie,
  drobnej korozji stalowych malowanych części i resztek papieru bez treści/marek. Brak skanu = jawne ostrzeżenie
  oraz płaska baza. Dodatkowe klucze `furniture_*` w `materials.py`, bez zmian pigmentów współdzielonych.
- Znaki zachowują istniejący szary tył, zagięty rant oraz dwie obejmy; test pilnuje prześwitu dolnej krawędzi
  po zmianie osadzenia. Słupek U tylko dla oznaczonych punktów OSM; wymiary modelu WORKING_VALUE.
- Spawane panele ogrodzenia mają poziome przęsła schodkujące na skarpie, słupki na granicach przęseł
  i w załamaniach linii, podmurówkę pod każdym przęsłem. Lekki zwis 4,5 cm (WORKING_VALUE) jedynie przy
  `fence_type=chain_link|wire`. Bez zmian barier energochłonnych, krawężników i danych ADR 0100.

## Weryfikacja i ograniczenia

Bazowe GIS: 370 passed, 1 xfailed / 635,18 s. GIS po zmianach: 377 passed, 1 xfailed / 538,42 s. Nowe regresje: 7 passed. Budżet prototypów w
`artifacts/furniture-r1/prototype-budget.json`: Low betonowej latarni 105→91 tris; stalowej 53→53;
nowoczesnej 53→53; łukowej 88→88; zwykłego słupka 50→50. To nie są statystyki kadru ani pomiar GPU.

Kamery `furniture_cameras.json` mają stałe pozy wyprowadzone z bazowych instancji. Pipeline odtwarza świat
z bazowych modułów przed porównaniem, zamiast porównywać nową generację ze starą, odziedziczoną sceną.
`run-validation.ps1` czeka na brak globalnego `PHONE_RUN` przed każdym startem Unity; bez adb/telefonów.
Rendery, wyniki EditMode, zmierzone budżety kadrów oraz samokrytyka będą w `artifacts/furniture-r1/REPORT.md`.
Niezależna recenzja i pomiary na telefonie należą do lidera; nie stanowią dowodu tej sesji.

Przewidywane konflikty: addytywne klucze w `materials.py`; `export.py`; wygenerowane GLB/metadata i QA.
Po scaleniu z innymi strumieniami regeneracja zamiast wybierania obcych produktów binarnych.

### Wyniki generacji r1

- Stopnie podparcia: 147 → 135, maksimum 1,087 → 0,517 m. Najgorszy pozostały wpis dotyczy `sign_post`.
- Korekty podpór lamp: 100, najgorsza pozostała wartość kryterium w tych korektach 0,167 m.
- Finalny filtr usuwa 3 zamiast 2 słupów spod pomostu; po odsunięciach nadal 0 pozostawionych na jezdni.
- Estymator generatora (23 kamery): Low tris −0,3421%…−0,0047%, liczba materiałów bez zmian.
  Nie zastępuje to SceneStats ani pomiaru GPU.
- 806 chronionych prymitywów dróg, mostów, barier, oznakowania, krawężników i kolizji drogowej porównano w obu wariantach:
  POSITION/NORMAL/UV/COLOR/index identyczne bajtowo (`protected-geometry.json`).
- Zużycie atlasu dotyczy koloru. Roughness/metallic pozostają stałe per materiał; osobna mapa korozji
  zmieniająca metaliczność nie jest częścią r1. Nie ma fotogrametrycznej inwentaryzacji każdej bocznej ulicy.
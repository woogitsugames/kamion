# ADR 0102 — Meble uliczne r1, wynik rundy 2

Status: gotowe do recenzji i integracji przez lidera. Data: 2026-11-11.
Gałąź `gpt-furniture-r1`, baza `9e6e9fde`. Zakres: strumień I pakietu S10-B.

## Problem i źródła

Bazowe QA wykazywało 147 różnic wysokości pod stopami słupów, do 1,087 m. To relief podparcia,
a nie licznik udowodnionych wiszących obiektów. Dotychczasowy wybór minimum z pięciu próbek obniżał
całą latarnię na górnej stronie skarpy. ADR 0069 oraz Mapillary p12/p15/p20/p26/p30 są referencjami
wyposażenia, bez pikseli Mapillary w buildzie. Rodziny na bocznych ulicach pozostają istniejącą heurystyką
WORKING_VALUE; nie wykonano inwentaryzacji każdej latarni ani pomiaru katalogowego.

## Decyzje

- Podparcie wyznacza środek stopy. Zachowano wybór poziomu z kolizji/terenu z ADR 0076, niezbędny przy
  nakładających się drogach i małych lukach siatki. Nie przenosimy podpór między poziomami wiaduktu.
- Dla lamp bez jawnej wysokości: deterministyczne szukanie stabilnego punktu do 1,05 m od źródła,
  próg reliefu/rozbieżności 0,15 m (WORKING_VALUE). Nadal działają filtry jezdni i pomostów.
- Renderowana siatka stalowego cokołu: −0,10…+0,08 m; rzeczywistej głębokości fundamentu pod ziemią nie
  modelujemy. Długi niewidoczny koniec poniżej pomostu sprawiał, że istniejący audyt od bounds.min wybierał
  niższy teren jako podporę. Analogicznie skrócono ukryte końce znaków i sygnalizatorów, bez zmiany wysokości lica.
- Starsze rodziny `lamp_old_concrete_9m` i `lamp_old_steel_8m`: obejmy dopasowane do stożka żerdzi,
  drzwiczki rewizyjne stalowej lampy, uproszczony wysięgnik betonowej w LOD1. Brak nowych slotów w istniejących modelach.
- Zużycie ma metryczne UV: mikrostruktura CC0 `brushed_concrete` i `corrugated_iron_03`, brud przy ziemi,
  drobna korozja i resztki papieru bez marek. Usunięto profil pionowych przetłoczeń skanu blachy po przeglądzie zbliżenia.
  Brak skanu powoduje jawne ostrzeżenie i płaską bazę. Roughness/metallic pozostają stałe per materiał.
- Addytywne materiały `furniture_*` kopiują pigmenty istniejących materiałów. Kontrakt liniowego koloru,
  reguły `_Tile` oraz `weather`/`runoff` nie zostały zmienione.
- Tył znaków zachowuje szary metal, rant i dwie obejmy. Regresja kontroluje prześwit po osadzeniu na krawężniku.
  Prototyp U używany wyłącznie z odpowiedniego tagu OSM; w regionie brak takich instancji, pokazany w diagnostyce modeli.
- Panele ogrodzenia mają poziome przęsła, stopniowanie, podmurówkę oraz słupki na granicach przęseł i w narożnikach.
  Zwis 4,5 cm (WORKING_VALUE) dotyczy tylko `fence_type=chain_link|wire`. Helper słupków zachowuje dotychczasowe
  zachowanie barier i ekranów; terenowe stopy włącza wyłącznie nowe ogrodzenie.

## Zmierzone wyniki

- GIS R2: 379 passed, 1 xfailed / 649,86 s; 9 nowych regresji. EditMode: 226/226, 0 failed, 0 skipped.
- QA reliefu: 147 → 107, maksimum 1,087 → 0,411 m; 20 lokalnych korekt lamp.
- Gate3Audit, korytarz 40 m: 223 podpory, floating 4 → 0, sunk 0 → 0. Sygnalizator przy
  E −597,535 / N 20,717 zachowuje poziom: 141,384 → 141,386 m, nie spada do dolnej jezdni.
- 806 prymitywów dróg, mostów, barier, oznakowania, krawężników i kolizji: identyczne payloady
  POSITION/NORMAL/UV/COLOR/index w obu wariantach (`protected-geometry.json`).
- SceneStats Low, 4 kamery trasy × 2 oświetlenia: max draws delta 0; konserwatywna górna granica
  zmiany tris +1,183%, uwzględniająca zaokrąglenie obu liczników do tysięcy. CPU estimate, nie licznik GPU.
- Pamięć siatek świata z importera Low: 111,3 → 112,3 MB, High 239,7 → 240,7 MB.
- Low starej betonowej lampy 105 → 91 tris, stalowej 53 → 53; nowoczesnej 53 → 53, łukowej 88 → 88.
  Sloty istniejących prototypów bez wzrostu (`prototype-budget.json`).

## Dowody, odtwarzanie i otwarte

`artifacts/furniture-r1/`: before/ i after/ (po 36 PNG, R2 = final after), compare/ (8 obejrzanych arkuszy),
audit-before/after.json, frame-budget*.json, logi i REPORT.md. `after-r1/` jest odrzuconą rundą, nie dowodem końcowym.
Kamery `furniture_cameras.json` mają stałe pozy i `seat=file`; tył znaku jest wyznaczony z yaw słupka.
Blender-prototypes/sign-back/old-steel-foot to osobna diagnostyka modeli, nie render Unity ani pomiar telefonu.

Pipeline zapisuje produkty A/B poza gitem w Data/raw/derived, czeka na PHONE_RUN przed Unity i cofa jego efekty uboczne.
Przy kopiowaniu Library wykluczać konkretne pliki blokad, nie `*lock*` (pomija też ColorBlock.cs).
Pełne odtworzenie PBR wymaga istniejącego Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg; brak powodował pomijanie
warstwy i powtórne przebudowy. Plik skopiowano do worktree, poza gitem. Brak `fallback=True` w logach generacji.

Samokrytyka: docs/reports/visual/REVIEW-2026-11-11-s10-0102-self.md. Niezależna recenzja i telefon pozostają dla lidera.
Otwarty detal: większa różnorodność zużycia i mapa korozji sterująca metalicznością; ciężka podmurówka na części skarp
wymaga lepszej referencji wysokości. Nie jest to zamknięcie bramki 3 całego świata.
Przewidywane konflikty: addytywne materials.py, export.py, biblioteka props/metadata, generated QA/manifest i LICENSES.md.
Po integracji innych strumieni regenerować produkty zamiast wybierać obce binaria.

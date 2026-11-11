# D Low wear packing — jedna ograniczona opcja, tylko plan źródłowy

Odczyt D: `5cbbd928` po cofnięciu odrzuconych trzech bloków BROAD. Nie zmieniono źródeł/tekstur, nie pobrano plików, nie wykonano Unity ani testów. Dane wejściowe to aktualny shader/factory, `native-gate-r2.json`, `wear-source-field-metrics.json`, bieżący materiał oraz PNG i importer `.meta`. Osobny `D-low-wear-map-inventory.json` zapisuje konkretne kanały, rozmiary, SHA i rachunek ASTC. Nie dotykano produktów G, geometrii dróg ani hero E.

**Wniosek:** wykonalny jest wspólny packed MaskMap tylko dla `road_asphalt`, z zachowaniem High i czterech bazowych próbek Low. R z 16m maski open-crack, G/B/A z istniejącej4m maski powtórzone4×4. Wymaga osobnej skali Mask UV=.25 i efektywnego2048² zamiast512². Nowa unikalna mapa daje **+1,398,144B ≈1.33337MiB** payload ASTC z mipami, nie zerowy koszt. Bez zgody na ten przyrost nie widzę wariantu spełniającego równocześnie16m wzór, niezmienioną gęstość G/A i brak nowej próbki. Nie proponuję drugiego eksperymentu ani wielu amplitud.

## Fakty o rzeczywiście używanych danych

`M_road_asphalt.mat` i native binding mają `Kamion/World PBR`, `_CRACKS,_PHOTO_DETAIL,_ROADWEAR`, `_Tile=(4,4,16,1)` oraz `_MetallicScale=0`. Base/Normal/Mask używają dziś tej samej 4 m współrzędnej. Obie sceny/tiery współdzielą materiał i mapy **Medium**, więc etykieta jakości Low nie oznacza automatycznie tekstur Low. Spec skanu podaje 4.04 m, ale factory celowo zachowuje recenzowane 4 m poza `set_tile`/element scan/atlas (`WorldPbrMaterials.cs:160–173`). Tego kontraktu skali nie należy zmieniać przy okazji.

| Mapa worn w aktualnym cache | Faktyczne kanały/znaczenie | Android według importera; pełny payload |
|---|---|---|
| BaseColor | PNG RGB1024²; importer `alphaUsage=0`/AlphaSource.None. Nie ma istniejącej użytecznej alpha. | ASTC6×6,1024²,11mipów:626,288B. |
| Normal | PNG RGB1024², import NormalMap. Kanałów nie wolno traktować jak dowolnego RGB/A po platformowym UnpackNormal. | ASTC6×6,1024²,11mipów:626,288B. |
| MaskMap | PNG RGBA1024². R=0; G AO111–255; B=255 (detail gate); A smoothness0–66. **Wolne jest R tylko w tym nie-metalicznym zastosowaniu, nie A.** | Source1024² → Android512², linear, ASTC8×8, alphaUsage1, Box mip filter, mipy włączone:87,424B/10mipów. |
| Var | PNG RGBA1024²: height/id/joint/convexity. Plain old-road Low nie pobiera tej mapy w swojej bazowej ścieżce. Wolny lub stały kanał Var nie jest darmową próbką. | Android512² ASTC8×8, Point, **bez mipów**:65,536B. |

Low pobiera Base, Normal, Mask i Macro. `_CRACKS && _KAMION_WORLD_DETAIL` dodaje zewnętrzne CrackMap i CrackNormal dopiero Medium/High; `_PHOTO_DETAIL` dodaje albedo/normal detalu z tym samym globalnym gate. Samo usunięcie gate dla Low dodaje próbki i nie spełnia zadania. Macro RGBA ma już cztery role przy 64 m, nie wolną alpha na16m pęknięcia.

### Wszystkie odczyty R i kanałów — sprawdzone źródło

W `Environment/Shaders/WorldPBR.shader:251–256` jedyny odczyt **`mask.r`** to `metal=mask.r*_MetallicScale`. Inne użycia mask to A smoothness (`:254`), G AO (`:255`), B foto-detail (`:395`) i A wet-clean (`:640`). Dodatkowy `sm` w gałęzi decal czyta tylko A (`:465–468`), a road_asphalt nie ma tych decal keywordów. Nie znaleziono innego odczytu R dla High. Factory ustawia MetallicScale0 (`WorldPbrMaterials.cs:206`), potwierdza to bieżący `.mat`. Zmienny R nie robi więc drogi metalicznej przy zachowaniu tego warunku. **B pozostaje255**, bez propozycji seal w B kosztem High detail.

## Jedyna proponowana próba: wspólny packed MaskMap dla starej drogi

1. **Offline map:** nowy, osobno nazwany packed mask tylko dla `M_road_asphalt`. R bierze obecny open-crack z aktualnie przypiętej 16 m `asphalt_cracks_layer/Medium/..._Mask.png` (1024²); nie zmienia wzoru, szerokości ani seeda. G/B/A są powtórzone4×4 z obecnej4m maski worn. Przy źródłowym1024² daje to4096² PNG RGBA, Android override2048². R można przeskalować do tej siatki, ale to nie tworzy nowych szczegółów ponad źródłowe15.625mm/texel. Większa mapa jest potrzebna do zachowania G/A, nie do udawania nowej rozdzielczości źródła pęknięć.
2. **Binding/factory:** `WorldPbrMaterials.cs` podpina packed map w tym samym `_MaskMap` slot tylko starego `road_asphalt`, dla wspólnego materiału Low+High. Oddzielne Mask UV=.25 względem dotychczasowego `uvb`; Base/Normal/Var i `_Tile.xy=4` zostają niezmienione. Jawny material-scoped znacznik packingu, domyślnie wyłączony, zapobiega interpretowaniu R innych materiałów. Nie jest potrzebny runtime manager materiałów Low ani klonowanie na zmianę jakości. Import musi mieć per-map rozmiar4096/source i2048/Android — bieżące `Layer` bierze cap z `info.res`, więc samo zapisanie większego PNG bez aktualnego metadanych zostawiłoby zły cap512.
3. **Low shader:** ta sama pojedyncza próbka MaskMap, przy zmienionym UV, daje open-crack R. Tylko `!_KAMION_WORLD_DETAIL` i aktywny znacznik starej drogi używają go do istniejącej odpowiedzi open-crack albedo oraz istniejącego `_CrackStrength`/macro amount. Bez nowych odczytów, noise, shaderowych rys, geometrii i bez nowego polish. To uproszczone **otwarte pęknięcia**: bez osobnego seal/halo/normal z pełnej warstwy. Nie rozszerzać tego na fresh road, farbę, yard lub hero w tej jednej próbie.
4. **High:** packed R jest ignorowane przez nową odpowiedź Low, a metal pozostaje0. Dotychczasowy zewnętrzny16m `_CRACKS` i `_PHOTO_DETAIL` pozostają aktywne bez zmian — **nie podwajać pęknięć** w RGB ani w shaderze. G/B/A z mapy tiled4× mają tę samą4m skalę i fazę co przed zmianą. B=255 zachowuje detail, A zachowuje smoothness/wet-clean. High ma nadal jedną próbkę MaskMap, ale większy footprint pamięci.

## Dokładny koszt i mip/LOD

Rachunek to suma16B na każdy blok ASTC na każdym poziomie: `Σ ceil(w/8)*ceil(h/8)*16`, aż do1×1, z zaokrągleniem do minimum jednego bloku. Nie przybliżenie4/3 i nie fizyczny pomiar PSS.

- Obecny Mask512²:87,424B,10mipów; przy 4 m7.8125mm/texel.
- Packed2048²:1,398,144B,12mipów; przy 16 m **7.8125mm/texel dla G/A**, tak samo jak dotychczas. UV/4 i rozmiar×4 zachowują gęstość oraz wybór fizycznego LOD; nie dodawać kompensacyjnego mip bias±2. Dodatkowe dolne poziomy mają zachowywać średnią, bez progowego maskowania alpha.
- Gdyby zastąpić i całkowicie usunąć stary mask z wszystkich konsumentów: delta1,310,720B=1.25MiB. **Nie jest to domyślny bilans tej próby:** yard/paint/inne materiały mogą nadal potrzebować starej mapy. Osobny unikalny packed asset dodaje pełne1,398,144B≈1.33337MiB do zależności; nie zakładać automatycznego unload starego maska na Low.
- Źródłowy4096² RGBA to64MiB surowych pikseli podczas obróbki/importu (nie rozmiar PNG i nie docelowa pamięć ASTC). Bazy/normalne pozostają1024² oraz na4m; ich ziarno nie jest rozciągane. Pozostałe mapy i liczba próbek pozostają. Realny peak GPU/PSS i cache/bandwidth są **UNVERIFIED**; brak nowej próbki nie oznacza braku kosztu. Budżet64MiB Low jest założeniem profilu, nie dowodem dostępnego zapasu.

**Istotne ograniczenie kompresji:** metadata obecnego maska potwierdza ASTC8×8/linear/alpha/mipy, ale nie istnieje native readback nowego packa. Dodanie zmiennego R do bloku może zmienić błąd ASTC G/A mimo identycznych źródłowych wartości. Dlatego nie obiecuję pixel-exact High; po ewentualnym wdrożeniu trzeba odczytać rzeczywiste mipy/format i sprawdzić G/A/High neutralne powierzchnie. PBR writer (`pbrkit.py:215–273`) filtruje Toksvig per tier; powielać gotowe kanały tego samego tieru i zachować kolejność downsample/import, zamiast przeliczyć je z innego tieru.

## Dlaczego nie ma darmowego skrótu

Ten sam512² mask przy 16 m miałby31.25mm/texel i zmniejszyłby szczegół G/A czterokrotnie w osi — odrzucone, nie „bez zmian”. Całe16m cracklayer w4m tile zmniejszyłoby fizyczne szerokości/odstępy4×; crop4m zachowuje szerokości, ale ma rozpoznawalną repetycję4m i nie jest tą16m próbą. BaseMap RGB nie ma alpha danych, importer ją odrzuca; RGBA wymagałoby zmiany kontraktu i nadal nie rozwiązuje dwóch skal w jednym odczycie. Przy stałym ASTC bitrate alpha nie musi zwiększyć bloków Android, lecz zmienia kodowanie/błędy i może zmienić automatyczny format innych platform. Nie nazywać tego uniwersalnie darmowym kanałem.

## Źródła pęknięć i zdjęcia — bez nowych licencji/domysłów

Worn baza jest obecnie z przypiętego CC0 `asphalt_04` (lokalny `cc0_manifest.json`, `sets_scan.py`, source w spec); nie jest wyłącznie proceduralnym fallbackiem `sets_asphalt.worn`. Natomiast16m `sets_asphalt.py::cracks_layer` jest **już istniejącą offline autorską maską**, z R open1–5mm, G seal25–40mm, B alligator zone i A halo; nie udajemy, że to fotograficzny skan spękania. W tej próbie chodzi o realne dane tekstury już używanej na High, nie nowy runtime noise.

Istniejące zdjęcie Johna Harveya `Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg` jest lokalnie dostępne, SHA256 `e26237d85c097af9560537c60e6ed6f67ed0090e284398a5d7a7a2bf41889135`; lokalne LICENSES/spec opisują domenę publiczną. `sets_other.py:465–480` bierze **crop bez spękań** `(1830,0,2726,896)`, high-pass i normalizuje go do 1 m detalu. Gotowy DetailAlbedo to L512² i DetailNormal RGB512² w aktualnym Medium cache. Samo włączenie PHOTO_DETAIL na Low nie dostarczy dużych pęknięć, a doda próbki. Nie pobierano nowych zdjęć i nie proponuje się nowej ekstrakcji fotospękań bez skali/proweniencji.

## Decyzja do lidera

Jedna próba jest źródłowo wykonalna z powyższym budżetem, bez nowego runtime managera i bez zmiany próbek. Jeżeli dodatkowe≈1.333MiB jest niedopuszczalne, należy ją odrzucić lub jawnie poluzować warunek — nie deklarować, że ta sama jakość/16m/G/A mieści się bezkosztowo w512². Po osobnej zgodzie: wąski guard fresh-road, unknown glyph/UV, stare kerb scuffs, High bez double cracks i zgodność G/A/mipów; te same Low/High clear/overcast kamery i runtime poses. To **plan, nie wykonana implementacja, native compression test ani visual PASS**. Nie otwiera 0108/B3 i nie dotyka prac G.

ROOT wybra? t? jedn? opcj? wy??cznie do CPU prototypu w artifacts D: source4096 / Android2048, G/B/A tiled4?4, R open-only. To nie jest zgoda na binding/shader lub render przed kontrol? CPU. Bie??cy koszt dotyczy rzeczywi?cie wsp??dzielonego material tier Medium; nie przenosi? go automatycznie na inny rozmiar material tier High. ?r?d?owa zgodno?? G/B/A i rachunek ASTC nie zast?puj? native compression parity.

# Kabina: pionowy słup mgły — s24 #11 (P2)

Gałąź: `cab-haze-cli`. Zakres: shader przedniej szyby; bez Unity, buildów i pushowania.

## Przyczyna i dowód

Źródło wskazane przez analizę kodu i obrazu: **proceduralny film drogowy poza polami wycieraczek**,
nie cząsteczki wydechu. `game/Assets/_Project/Editor/Setup/TruckAssetBuilder.cs:409` ustawia `_Wiper = 0.35`;
linie 410–413 definiują dwa pola wycieraczek. `game/Assets/_Project/Rendering/Shaders/TruckGlass.shader:242`
tworzy maskę niewytartego obszaru, linia 246 dodaje ją do brudu. Film zmniejsza transmisję oraz dodaje
światło nieba/słońca (linie 281, 305–306). To geometria maski na szybie, bez ruchu powietrza.
Odpowiednik w ścieżce Low: linie 166–175, 194, 198–199.

Obejrzano wszystkie cztery PNG z `win-build/artifacts/win/runs/20261119-140004/`:

- `shot_t0050.png`: jasna, miękka pionowa smuga po prawej od środka szyby, przed wiaduktem;
  scena za smugą pozostaje widoczna.
- `shot_t0250.png`: wyraźny jasny klin/słup w prawej części szyby na tle ciemnej korony drzew;
  oddzielny problem zielonej płaszczyzny nie jest przedmiotem tej poprawki.
- `shot_t2590.png`: smugi przy lewym słupku A i po prawej od osi drogi, nakładane na drzewa i chodnik.
- `shot_t3180.png`: podobny układ smug przy innej scenerii; mleczne plamy w dolnej części szyby.
  Korona drzewa przenikająca kabinę to osobne #6.

Łukowo rozszerzający się kształt i powtarzalność względem szyby pasują do maski niewytartych pól.
To mocna przesłanka, **bez potwierdzenia renderem A/B po wyłączeniu filmu**; diagnoza nie jest pomiarem GPU.

Sprawdzone alternatywy:

- **Wydech/VFX:** wyszukiwanie `ParticleSystem`, `smoke`, `exhaust` w C#, shaderach, scenach i prefabach
  `_Project` nie wykazało emitera dymu. W Audio są odwołania do hamulca wydechowego i nagrań.
  Rura jest geometrią za kabiną (`tools/blender/truck/exterior/chassis.py:302`, `:370`), z wylotem ku tyłowi.
  Brak podstaw do zmiany położenia rury, wiatru lub warstw kamery.
- **Brud teksturowy/odbicie:** materiał przedniej szyby ma `_Grime = 0` (`TruckAssetBuilder.cs:408`);
  proceduralny film działa niezależnie. Odbicie kabiny to łagodne przejście dach/deska zależne od kierunku
  odbicia (`TruckGlass.shader:258`), bez maski pionowych pól.
- **Post-process:** Bloom i Vignette w `Rendering/Settings/VP_World.asset` są nieaktywne; brak tam
  efektu nakładającego podobne kolumny. Ta poprawka nie zmienia profilu.
- **Mgła/volumetria:** `Rendering/Shaders/KamionAtmosphere.hlsl:22–30` całkuje wygaszenie zależne
  od głębokości i wysokości; nie zawiera lokalnej kolumny. Nie znaleziono emitera wolumetrycznego
  w sprawdzonych assetach `_Project`. Nie wyłączamy atmosfery świata.

## Zmiana

`TruckGlass.shader:167` i `:234`: proceduralny film jest liczony tylko dla ściany zewnętrznej
lub kamery poza kabiną. Wewnętrzna ściana widziana z kabiny ma `film = 0`, co usuwa wkład maski
zarówno do rozpraszania, transmisji, jak i szorstkości. Obie ścieżki jakości mają ten sam warunek.
`CabInteriorLighting.cs:319–328,356` już dostarcza klasyfikację kamery; nie dodano nowego stanu.

Widok zewnętrzny zachowuje film na bliższej i dalszej szybie oraz pozostałe właściwości szkła.
W kabinie pozostają absorpcja, Fresnel, odbicia i opcjonalny brud teksturowy. To kompromis czytelności
opisany w uzupełnieniu ADR 0059, a nie fizyczna symulacja brudu. Nie trzeba regenerować materiałów/prefabów;
zmiana dotyczy istniejącego shadera. Bez nowych tekstur, przebiegów, wariantów i kodu w pętli jazdy.

## Weryfikacja i otwarte

- `git diff --check`: PASS.
- Statyczna kontrola obu warunków oraz tabeli 8 kombinacji `_Wiper` 0/0.35 × ściana
  wewnętrzna/zewnętrzna × kamera kabina/zewnętrzna: PASS. Film wyłączony przy `_Wiper = 0`;
  przy 0.35 usunięty tylko dla ściany wewnętrznej widzianej z kabiny.
- Nie uruchamiano Unity, kompilacji shadera, testów Unity ani playera. Brak obrazu po poprawce;
  **visual QA pozostaje otwarte**, podobnie koszt GPU i kontrola zachowania klasyfikacji kamer.
- W kolejnej sesji z autoryzacją buildów: przejazd Białystok–Tykocin z tym samym kadrem na High,
  kontrola miejsc t=50/250/2590/3180, porównanie obrazu przed/po. Potwierdzić brak kolumn także
  po rozgrzaniu jazdy i przy zmianie kierunku słońca, w clear/overcast/lowsun oraz na Low (fast), Medium i Ultra.
- Sprawdzić kamerę zewnętrzną z przodu i z boku, dalszą szybę przez kabinę, lusterka oraz przełączanie
  kabina/zewnętrze. Film na zewnątrz ma pozostać, a szyba z kabiny nadal mieć odbicia i absorpcję.
  Jeśli smuga pozostanie, wykonać izolacyjne A/B filmu i refleksu bez równoczesnego wyłączania atmosfery.

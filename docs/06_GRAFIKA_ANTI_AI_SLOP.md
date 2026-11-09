# 06 — Grafika i standard „zero AI slop”

Właściciel wymaga: **gra nie może wyglądać na AI slop ani na kolejną słabą grę truck z Google Play.** Ten dokument definiuje, co to znaczy w praktyce i jak to sprawdzamy.

## 1. Kierunek artystyczny
**Fotograficzny realizm współczesnej Polski, spokojny i wiarygodny** — jak dobre zdjęcie z telefonu zrobione w Białymstoku w zwykły dzień, a nie render reklamowy. Jakość wynika ze **spójności**: poprawne proporcje i skala, kalibrowane światło, materiały o realnych wartościach, detal tam, gdzie patrzy kierowca, i zużycie świata (łaty na asfalcie, zacieki, wyblakłe linie, kurz na progach).

Paleta Podlasia: przygaszone zielenie, szarości betonu i płyty, czerwień cegły, częste zachmurzenie, długie zimowe szarości (sezony później). Nie podkręcamy nasycenia.

## 2. Czerwone flagi „AI slop” i słabej gry mobilnej — zakazane
- Jednolity szum proceduralny „na wszystkim”, ten sam brud w każdym miejscu; albo odwrotnie — sterylna czystość.
- Przesycone kolory, teal-orange, przesadny bloom, świecące emisje, „HDR look”, winieta i aberracja chromatyczna dla efektu.
- Plastikowy połysk: jednolity roughness, zbyt błyszczący metal i opony, brak mikrodetalu.
- Idealna symetria i identyczne bevele wszędzie; brak zużycia, szczelin paneli, uszczelek, śrub.
- Widoczne kafelkowanie tekstur, powtarzające się te same budynki/drzewa/samochody obok siebie.
- Błędne wskazówki skali: za duże drzwi/okna, za niskie krawężniki, za wąskie pasy, „zabawkowe” latarnie.
- Rozmyte, „topiące się” bryły i zniekształcone napisy (typowe dla generatorów 3D/2D AI). **Wygenerowane obrazy 2D nie mogą udawać modeli ani tekstur bez obróbki i kontroli.**
- Obiekty unoszące się nad ziemią, brak cieni kontaktowych/AO, drzewa bez osadzenia w gruncie.
- „Generyczna Europa” zamiast Polski: złe znaki, złe linie, złe krawężniki, złe latarnie, złe tablice rejestracyjne.
- UI: neonowe gradienty, glassmorphism, emoji jako ikony, generyczne „gamingowe” fonty, grafiki menu z generatora obrazów, natrętne pop-upy.

## 3. Jak osiągamy realizm przy budżecie 0 zł
- **Zdjęcia właściciela** (Białystok, ciężarówka na parkingu) — referencje i źródło tekstur. Instrukcja dla właściciela: zdjęcia nawierzchni prostopadle, w pochmurny dzień, z kartką A4 dla skali; elewacje frontalnie; detale z bliska.
- **Biblioteki CC0** ze skanów (np. Poly Haven, ambientCG — sprawdź licencję każdego zasobu) jako baza materiałów, HDRI do kalibracji.
- **Własne generatory PBR** (Python/Blender) tylko jako warstwy wariacji i zużycia nakładane na fotograficzną bazę, sterowane maskami (krawędzie, krzywizna, ekspozycja na deszcz, ślady kół), a nie jako jedyne źródło.
- **Wartości fizyczne**: tabela referencyjnych albedo/roughness dla asfaltu, betonu, lakieru, gumy, szkła, tworzyw, trawy (zapisz źródła), kontrola histogramu albedo w walidatorze.
- **Texel density** spójne (ustal w ADR, np. osobno dla drogi, budynków przy drodze, kabiny, zewnętrza ciężarówki) i sprawdzane walidatorem.

## 4. Technika renderingu (URP mobile)
- Linear, kalibrowana ekspozycja, tonemapping Neutral/ACES (ADR po testach), realne natężenie słońca/nieba, mgła atmosferyczna lekka.
- Oświetlenie: główne światło kierunkowe dynamiczne (pora dnia), light probes + reflection probes (rozmieszczane przez generator), baked AO dla statycznych obiektów, cienie kaskadowe dopasowane do profilu, cienie kontaktowe/AO tanim sposobem.
- Asfalt: warstwa bazowa + łaty + spękania + koleiny (wypełniające się wodą w deszczu) + linie jako decale; mokry asfalt: roughness/normal blending, kałuże z maską, odbicia przez probe/SSR tylko na profilu High.
- Szyby kabiny: krople, wycieraczki z maską, lekki brud, odbicia deski.
- Roślinność: LOD + impostory, wiatr subtelny, brak poppingu (cross-fade/dithering).
- Lusterka: render textures z ograniczonym zasięgiem i warstwami, częstotliwość/rozdzielczość zależna od profilu — ale zawsze użyteczne do cofania.
- Anty-aliasing: MSAA 2–4× (tile-based GPU), krawędzie linii drogi bez migotania (mip bias, odpowiednie filtrowanie).
- Dynamic resolution, upscaling tam, gdzie dostępny i lepszy od natywnej niższej rozdzielczości.
- ASTC, mipmapy, streaming tekstur, SRP Batcher, GPU instancing, culling, HLOD.

## 5. Bramka wizualna — checklista (każda zmiana wizualna i każda bramka etapu)
1. Zestaw **kamer kontrolnych** (stałe pozycje, FOV, pora dnia, pogoda): kabina dzień, kabina noc, deska z bliska, zewnętrze ¾ przód, bok zestawu, tył naczepy, siodło/podwozie, koło z bliska, skrzyżowanie z wysokości oczu, ulica w perspektywie, krajobraz z dystansu, deszcz noc.
2. Render z edytora **i zrzut z telefonu** (scrcpy/screencap) — oba w raporcie, podpisane źródłem.
3. **Side-by-side z referencją** (zdjęcie właściciela / zdjęcie referencyjne) w tym samym kadrze.
4. Przegląd przez **innego agenta niż autor** (agent `visual-critic`) wg sekcji 2: lista problemów z lokalizacją na obrazie, priorytetem i propozycją poprawki.
5. Kontrole automatyczne: histogram albedo, texel density, brak tekstur > budżet, brak brakujących normalnych/UV, brak obiektów pod/nad terenem.
6. Wynik: `PASS` / `FAIL` + lista; FAIL blokuje merge.

## 6. Budżety wydajności (hipotezy startowe — ratyfikuj pomiarami)

| | Samsung A (Medium/Low, minimum) | Flagowiec (High/Ultra, cel jakości) |
|---|---|---|
| Cel FPS | stabilne 30 | 60 High / 30 Ultra |
| Frame time p95 | ≤ 33 ms | ≤ 16,6 ms (High) |
| Draw calls (hipoteza) | ≤ 300–400 | ≤ 700–1000 |
| Trójkąty w kadrze (hipoteza) | ≤ 400–600 tys. | ≤ 1,5–2 mln |
| Pamięć aplikacji | zmierz próg ubijania procesu na urządzeniu, zostaw zapas | j.w. |
| Test termiczny | 30 min jazdy bez spadku poniżej celu | j.w. |

Mierz p50/p95/p99, hitching (np. przy streamingu i floating origin), pamięć PSS, alokacje, temperaturę/throttling. Nie średni FPS z pierwszej minuty.
Każda kosztowna funkcja ma przełącznik w profilu jakości. Nie wyłączaj kluczowych elementów (lusterko do cofania) dla ładnego benchmarku.

## 7. UI i marka
- Język wizualny inspirowany prawdziwymi wyświetlaczami ciężarówek i nawigacją: czytelny, spokojny, funkcjonalny. Projekt w Figma nie jest wymagany — UI Toolkit/UGUI z systemem stylów w kodzie.
- Fonty z otwartą licencją pozwalającą na osadzenie w grze (sprawdź licencję; dla znaków drogowych — font zgodny wyglądem z polskimi znakami, ale z jasną licencją, lub własny).
- Ikony własne, spójne, wektorowe. Grafiki menu = rendery z silnika (prawdziwa gra), nie obrazy z generatora.
- Nazwa marki ciężarówki, logo, firmy z ładunkami, reklamy przy drogach — fikcyjne, zaprojektowane z sensem (nie losowe zlepki liter).

# Przegląd M69 night-lamps-s21 (chmura B, PR #87) — s20, 2026-11-15

**Werdykt: SCAL (z erratą nieblokującą, §5).** Wszystkie kryteria akceptacji M69 są spełnione.

| Kryterium | Wynik |
|---|---|
| odcinki z rozstawami | 16 (każdy ≥ 10 par) |
| typy opraw z sylwetką i ≥ 3 kadrami | 4 (T1–T4); T5 niekompletny i tak oznaczony |
| kadry nocne z punktami a–f | 20 |
| tabela „dla silnika” | jest |
| źródło barwy | 7 ulic, dokumenty ZDM |
| powielanie M60 | brak |

Najcenniejsze dla gry są dokumenty przetargowe ZDM: **4000 K na Andersa, 1000-lecia i Maczka, przejścia 5700 K oraz redukcja do 70 % w godz. 22–5**. Najważniejsza luka, czyli brak nocnych kadrów LED z trasy C po 2023, jest uczciwie oznaczona.

- Gałąź `origin/research/night-lamps-s21` @ `6321f9b7a`: 65 plików, +4 597, wszystkie w `research/night-lamps-s21/` ✓.
- Manifest: 84 wiersze. User-Agent `research-client/1.0 (generic)` ✓. Google nie użyto ✓.
- Licencje: Commons CC0 (Rakoon), Panoramax CC BY-SA 4.0 z dopiskiem „referencja”, Openverse/Flickr CC BY 2.0 i inne (wg wiersza) ✓.
- Audyt: seed 20261115, 17/84 wierszy, 14 PASS / 3 FIX.
- Overpass był niedostępny, więc użyto OSM API 0.6 w kaflach. Pakiet zawiera surowe dane (`osm-street-lamps.json`) i skrypt rozstawów ✓.

## 1. Co obejrzałem sam (7 z 32 plików, pojedynczo; próba wybrana ręcznie, nie losowo)
| Kadr | Ocena |
|---|---|
| cm_kol (K69-052, Kołłątaja) | ✓ Ciepłe, żółto-pomarańczowe światło; 5–6 jednoramiennych łukowych latarń przy krawędzi; na mokrej jezdni jasność pulsuje w rytmie słupów; pierwszy plan ciemniejszy; śnieg |
| ov_10c97958 (K69-038) | ✓ Światło sodowe; jezdnia oświetlona ciągle, bez czarnych przerw; mgiełka i łuna, gwiazdki wokół opraw |
| pnx_3eba62ce (K69-058, typ T1) | ✓ Na pierwszym planie dwuramienna łukowa latarnia z płaskimi, lekko uniesionymi oprawami; jasnoszary słup. **≈** Latarnia „po prawej jednoramienna (T2)” w tej rozdzielczości wygląda raczej na dwuramienną (do sprawdzenia) |
| pnx_c1a5e40e (K69-034) | ✓ Neutralna lub zimna biel, latarnia parkowa z kloszem, silna poświata, różowo-zielone odblaski obiektywu, jasny krąg na trawie; w głębi kolejne białe post-topy |
| cm_014 (K69-045) | ✓ Światło sodowe, mgła, duża poświata wokół opraw, mokra kostka z odbiciami, chodnik oświetlony tymi samymi oprawami (oprawy to raczej głowice na krótkich wysięgnikach niż „łukowe” — drobiazg) |
| ov_88e3040d (K69-039) | ✓ Czarno-białe zdjęcie, dyfrakcyjne gwiazdy, śnieg, długi czas naświetlania (smugi świateł aut) |
| cm_kra (K69-051) | ✓ Ciepłe światło na elewacjach, oprawy poza kadrem, cienki śnieg, niebo szaro-fioletowe |

## 2. Źródła sprawdzone
- Postępowanie e-zamówień 93688: tytuł „Dostawa i montaż opraw oświetleniowych na terenie Miasta Białegostoku (I)”, znak ZDM-XIV.271.31.2023, załącznik „Zał. nr 9 do SWZ – Warunki techniczne.pdf”. Wszystko istnieje i zgadza się z sources.md ✓. **Treści skanu PDF (4000 K, lista ulic) recenzent nie pobierał ani nie czytał**, więc te cytaty pozostają niezweryfikowane przez recenzję. Pakiet podaje sha256 pliku i cytat ze strony 1.
- Liczby OSM (n par, mediany) można odtworzyć z dołączonego `osm-street-lamps.json` i `tools/osm_spacing.py`. Nie przeliczałem ich ponownie.

## 3. Wnioski dla gry (ADR 0191, 0192)
- **Barwa:** na trasie C **4000 K** (Andersa, 1000-lecia, Maczka, Wysockiego, Kuronia, Mickiewicza, Dywizjonu 303 — przetargi 2023/2024). Przesunąć `k_Led` z ok. 3000–3500 K na ok. 4000 K. Dodać kolor przejść dla pieszych **5700 K**, świecący 100 % całą noc. W ADR 0191 zmienić „LED UNVERIFIED” na przetarg ZDM 2023 (SOURCED); stan w terenie w 2026 pozostaje UNVERIFIED.
- **Redukcja nocna:** 70 % w godz. 22–5, przejścia 100 %. Opcjonalnie dodać nocny preset.
- **Rozstaw:** Andersa 41,6, Maczka 40,4, Tysiąclecia 34,8, Sokólska 32,4 m (ortofoto C60), Kombatantów 33 m. Dla GP dziś jest 36 m, czyli o 4–6 m za mało na Andersa i Maczka. W mieście mediany 20–45 m.
- **Typ T1:** dwuramienna łukowa w pasie dzielącym (Andersa, Maczka, Tysiąclecia). Wysięg ramienia 0,13–0,17 h (~1,4–1,9 m przy h = 11), głowica płaska, lekko uniesiona (0…+10°). Wysokość h: UNVERIFIED (dokumenty: „w gestii Wykonawcy”), gra zostaje przy 11 m (WORKING_VALUE).
- **Pule światła:** na suchej jezdni oświetlenie jest ciągłe, bez czarnych dołów. Pulsowanie widać tylko na mokrej, z odbić. Rozważyć mniejszy kontrast dyfuzyjny (dziś min/szczyt 0,44–0,49), a pulsowanie zostawić odblaskowi GGX. Halo słabe; silne tylko we mgle (promień 0,2–0,3 wysokości słupa).
- Osobnego oświetlenia chodników i DDR nie ma.

## 4. Luki (zgodne z README)
Brak nocnych kadrów LED z trasy C po 2023 (zdjęcia właściciela). Brak wysokości montażu. Rozstaw na Kuronia, Mickiewicza, Dywizjonu 303 i Wysockiego UNVERIFIED. Commons przez całą sesję odpowiadał 429.

## 5. Errata (nieblokująca)
```
1. K69-058: „po prawej jednoramienna łukowa (T2)” — sprawdzić w pełnej rozdzielczości; w 800 px słup po prawej wygląda na dwuramienny.
2. Tabela K69 „dla silnika”, rondo Putry: barwa „4000 K?” — rondo nie jest wymienione w dokumencie → wpisać UNVERIFIED (z adnotacją „ulice dochodzące 4000 K”).
3. Pliki tools/ + gen_frames.py / build_manifest.py w katalogu głównym pakietu — przenieść do tools/ (porządek).
4. Prośba do właściciela: nocne zdjęcia Andersa/Maczka/rondo Putry (barwa LED, pule) — dopisać do listy zdjęć właściciela.
```
Nic nie scalono ani nie scommitowano.

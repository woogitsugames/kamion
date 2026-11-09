# Unity look v2 — świat C v2 w URP (2026-11-09)

Źródło: **edytor Unity 6.3, URP, batchmode** (`pwsh scripts/visual-qa.ps1 -Scene WorldC|WorldC_High -Tier … -Lighting …`),
2340×1080 z MSAA i skalą renderu profilu, zmniejszone do 1280 px JPG. Zrzuty z telefonów (natywna rozdzielczość) są
w sekcji „Telefony” niżej. Decyzje: ADR 0012 (tiery treści, kompresja siatek, pas terenu, instancing), ADR 0010 (niebo).
Porównanie z renderami Blendera: `docs/reports/visual/world-c/` (EEVEE, offline — tam są kępy trawy, proceduralne
spękania asfaltu i mech, których shader gry jeszcze nie ma).

## Podsumowanie dla właściciela (PL)
- **Świat v2 jest w grze:** place, budynki (LOD0 z rampami przy trasie, bryły LOD1 dalej), ogrodzenia, bariery, 2 300
  elementów wyposażenia (latarnie, znaki z prawdziwymi licami, sygnalizatory, wiaty, bramy) i **≈ 108 000 drzew**
  (sosna, brzoza, olsza, klon, lipa, krzewy) z LOD i impostorami — wszystko rysowane GPU instancingiem.
- **Trzy profile, dwie paczki treści.** Low/Medium używają lekkiej wersji świata (`WorldC`), High — pełnej
  (`WorldC_High`: teren 1 m przy drogach, wszystkie budynki LOD0). Kolizja jest identyczna, więc fizyka nie zależy od
  profilu.
- **Trasa startowa przejechana** (test PlayMode, nowa kolizja z budynkami, ogrodzeniami i słupami): ciągnik solo i zestaw
  40 t, 2,4 km, bez przelecenia przez podłoże. Po drodze znaleziony i naprawiony błąd: kolizja latarni obejmowała wysięgnik
  nad jezdnią i stawała się „ścianą” (to samo zatrzymało autopilota na S24+).
- **Niebo:** kolor liczony fizycznie (rozpraszanie w atmosferze w 12 pasmach widma), a nie z aproksymacji Preethama —
  zniknął fioletowo-łupkowy odcień przy horyzoncie. Niebo nadal jest **ciemniejsze niż na typowym zdjęciu z telefonu**:
  przy stałej ekspozycji „jak światłomierz” błękit 90° od słońca ma jasność szarej karty. Telefon robi z tego jasny błękit
  lokalnym tonemappingiem HDR. Czy chcemy wyglądu „jak aparat w telefonie” (jaśniejsze, bardziej nasycone niebo), to
  decyzja artystyczna — **potrzebne Twoje zdjęcia z pogodnego dnia** (owner photos), zanim to zmienię.
- **Cienie bez „turkusu”:** niebieska składowa światła z nieba jest stłumiona (nasycenie 55 %), żeby cienie były
  szaroniebieskie, a nie cyjanowe (uwaga #3 z przeglądu r2).

## Kamery kontrolne
| Kamera | Low | Medium | High | Pochmurno |
|---|---|---|---|---|
| Kierowca, Andersa → Rondo Putry | [Low](driver-andersa-to-putry_Low-clear.jpg) | [Medium](driver-andersa-to-putry_Medium-clear.jpg) | [High](driver-andersa-to-putry_High-clear.jpg) | [Low](driver-andersa-to-putry_Low-overcast.jpg), [Medium](driver-andersa-to-putry_Medium-overcast.jpg) |
| Rondo Putry z ~40 m | | [Medium](putry-above_Medium-clear.jpg) | [High](putry-above_High-clear.jpg) | [Medium](putry-above_Medium-overcast.jpg) |
| Brama Kwadrat Parku | | [Medium](kwadrat-park-gate_Medium-clear.jpg) | | [High](kwadrat-park-gate_High-overcast.jpg) |
| Rampy Kwadrat Parku | [Low](stretch-05-docks_Low-clear.jpg) | | [High](stretch-05-docks_High-clear.jpg) | [Medium](stretch-05-docks_Medium-overcast.jpg) |
| Wylot DK8/DK19 | [Low](dk8-dk19-exit_Low-clear.jpg) | [Medium](dk8-dk19-exit_Medium-clear.jpg) | [High](dk8-dk19-exit_High-clear.jpg) | [Medium](dk8-dk19-exit_Medium-overcast.jpg) |
| Zestaw przy bramie | | [Medium](truck-at-gate_Medium-clear.jpg) | | |

## Co widzę (porównanie z renderami Blendera)
| Kadr | Unity v2 | Blender (world-c) |
|---|---|---|
| Andersa | Bloki i hale po bokach, latarnie co ~33 m, znaki, ogrodzenia, drzewa w tle; asfalt i trawa z tekstur proceduralnych | ten sam układ; w Blenderze dodatkowo spękania i łaty asfaltu oraz kępy trawy przy krawężnikach |
| Rampy | 11 bram z numerami, uszczelnienia, odboje, żółte pasy — na Low/Medium też (budynki LOD0 do 60 m od trasy) | identyczna geometria; Blender ma brud na fartuchu i plamy |
| DK8 | Las sosnowo-brzozowy z LOD0 przy drodze i impostorami dalej, bariera, czerwona droga rowerowa | ten sam las; impostory w Unity są płaskie i trochę szare z bliska (Low: od 10 m) |
| Pochmurno | Płaskie, jasnoszare niebo CIE, brak cieni, kontrast jak w pochmurny dzień | podobnie |

## Poprawki pipeline’u w tej pętli
1. Impostory jako „pionowe słupy”, tablice i siatka ogrodzeń do góry nogami → odwrócone V w imporcie GLB (glTF ma v=0 u góry).
2. Ściany hal jak marmur → osobny styl „ściana” (drobne ziarno, bez plam makro).
3. Rampy na Low/Medium były bryłą bez bram → budynki LOD0 dla kafli ≤ 60 m od trasy startowej.
4. Za dużo trójkątów drzew w lesie przy DK8 (Medium 0,78 mln) → LOD drzew 20/60 m przy LOD bias 1 (Medium: 0,28 mln).
5. Niebo: magenta Preethama → spektralne rozpraszanie; beżowy horyzont przy 3 długościach fali → 12 pasm + rozpraszanie
   drugiego rzędu + balans bieli do słońca.

## Liczby (szacunek CPU z `stats.txt`, NIE liczniki GPU)
| Kadr | Low: draw / tris świat + instancje | Medium | High |
|---|---|---|---|
| Andersa | 167 / 215 k + 60 / 19 k | 246 / 459 k + 68 / 54 k | 343 / 1 024 k + 120 / 152 k |
| Rondo Putry z góry | 190 / 282 k + 50 / 8 k | 254 / 403 k + 78 / 17 k | 303 / 977 k + 125 / 49 k |
| Rampy | 167 / 217 k + 22 / 11 k | 247 / 366 k + 26 / 34 k | 323 / 1 055 k + 77 / 226 k |
| DK8 (las) | 43 / 90 k + 62 / 89 k | 47 / 91 k + 84 / 280 k | 71 / 362 k + 120 / 974 k |

## Nadal do zrobienia
- Kępy trawy (detail grass) i shader asfaltu z `TEXCOORD_1` (koleiny, brud przy krawężniku) — w Blenderze są, w grze nie.
- Impostory: 1 kąt, bez normalnych; z bliska (Low) widać, że to płaty.
- 88 latarni/znaków stoi na jezdni (dane generatora, lista w `artifacts/world/…-props-on-road.txt`) — zgłoszone world-builderowi.
- Ocena `visual-critic` tej wersji i porównanie ze zdjęciami właściciela.

# Tor A6: wnętrze kabiny po recenzji i gotowe do importu do gry

**Co to jest:** poprawki wnętrza kabiny po recenzji `visual-critic` (`docs/reports/visual/REVIEW-2026-11-09.md`, werdykt A5: „FAIL, blisko”) oraz przygotowanie wnętrza do importu do Unity (A6). Wnętrze ma teraz 3 poziomy szczegółów (LOD), scalone materiały, wypaloną mapę światła otoczenia, pliki FBX i opis importu (manifest) dla agenta Unity (krok A7, robi go lider).

Wszystko nadal powstaje ze skryptów: nic nie było klikane ręcznie w Blenderze.

## Co zmieniłem (punkty recenzji)

| # | Uwaga krytyka | Co zrobiłem | Dowód |
|---|---|---|---|
| 4 | Wieniec kierownicy przecina oba okrągłe zegary (w tym ciśnienie powietrza) | Usunąłem okrągłe zegary. Ciśnienie w obu obwodach, paliwo i AdBlue są teraz na ekranie 12,3″. Na ekranie jest jedna duża prędkość (zamiast dwóch) i obrotomierz z zieloną strefą. Ekran siedzi niżej, w „wannie” deski pod kapturem, cały w górnym oknie kierownicy. Doszedł **automatyczny test linii wzroku** (`sightline_test.py`): sprawdza promieniami z oczu kierowcy (plus ±2 cm ruchu głowy), czy kierownica albo kaptur nie zasłaniają ekranu i jego najważniejszych pól. Jeśli coś zasłania, test kończy się błędem. | `sightline.json`: PASS, 0 % zasłonięcia dla wszystkich pól (LOD0, LOD2, szyba 19° koncepcji B). Przed zmianą: 64 % okrągłych zegarów zasłonięte, rząd kontrolek 51 %. |
| 5 | Wnętrze w grze zrobi się czarną plamą (brak światła odbitego w URP) | Jaśniejsze tworzywa w średnich tonach: dół deski 0,20, słupki A 0,27, boczki drzwi 0,20, ściany 0,165, zasłony 0,10 (góra deski zostaje ciemna, żeby nie odbijała się w szybie). Do tego **drugi zestaw renderów „URP-like”**, który odtwarza model oświetlenia gry: słońce z cieniem, otoczenie z nieba bez odbić, tylko wypalona mapa światła otoczenia, niebo bez HDR. | `*_urp.jpg`, `cycles_vs_urp_*.jpg` |
| 10 | Kierownica jak w autobusie z lat 90. | Szerokie, płaskie ramiona opuszczone o 14°, z wbudowanymi panelami przycisków (klawisze równo ze wspólną ramką, szczeliny ok. 0,8 mm). Twarda poduszka z ostrą krawędzią 2–3 mm i wąską linią rozerwania. Wieniec o przekroju „jajowatym”, z wgłębieniami na palce i podparciem kciuków przy ramionach. | `kierownica_overcast.jpg`, `wariant_znak_piasta.jpg` |
| 11 | Fotele jak klocki | Zaokrąglone siedzisko i oparcie, zawinięte boczki, „wodospad” z przodu siedziska. Zagniecenia od siedzenia: przód siedziska, styk z oparciem, lędźwie, boczek od strony drzwi u kierowcy. Osobny zagłówek na dwóch prętach, widoczny pas (taśma, prowadnica przy ramieniu, klamra). Kieszeń na tyle oparcia, amortyzator zawieszenia z tyłu. | `fotel_overcast.jpg`, `lezanka_overcast.jpg` |
| 12 | Pusta płyta deski po stronie pasażera, kaptur „doklejony”, góra deski biała w niskim słońcu | Dwie półki z gumową matą i rantem (środek i strona pasażera), kratka głośnika w rogu, uchwyt na dokumenty, uchwyt na kubek i USB przy konsoli, linie podziału paneli. Kaptur wyrasta z deski i ma 3 mm szczelinę podziału na styku. Soft-touch jest bardziej matowy i słabiej błyszczy. W ujęciu z niskim słońcem poprawiłem proporcję słońca do nieba (było ok. 20:1, przy niskim słońcu to za dużo). | `pasazer_lowsun.jpg`, `porownanie_pasazer_lowsun.jpg` |
| 15 | Zaszumione AO, szyby i zasłony w wypalaniu, dużo zmarnowanego miejsca, „tekturowe” tło | Nowa mapa otoczenia (szczegóły niżej). Tło renderów to teraz **własny** plac logistyczny: zróżnicowany las sosnowo-brzozowy z kart, hala z doków, łaty i spękania asfaltu, betonowe płyty, naczepy, maszty z oprawami, chmury. Nic nie jest pobrane z internetu. | wszystkie kadry |

## Rendery kontrolne (1600×900)

Cycles (referencja, światło odbite) i URP-like (model oświetlenia gry), te same kamery co w A5:

| | Cycles | URP-like |
|---|---|---|
| Oczy kierowcy, pochmurno | ![](kierowca_overcast.jpg) | ![](kierowca_overcast_urp.jpg) |
| Oczy kierowcy, niskie słońce | ![](kierowca_lowsun.jpg) | ![](kierowca_lowsun_urp.jpg) |
| Zegary | ![](zegary_overcast.jpg) | ![](zegary_overcast_urp.jpg) |
| Fotel pasażera, pochmurno | ![](pasazer_overcast.jpg) | ![](pasazer_overcast_urp.jpg) |
| Fotel pasażera, niskie słońce | ![](pasazer_lowsun.jpg) | ![](pasazer_lowsun_urp.jpg) |
| Z leżanki | ![](lezanka_overcast.jpg) | ![](lezanka_overcast_urp.jpg) |
| Kierownica | ![](kierownica_overcast.jpg) | ![](kierownica_overcast_urp.jpg) |
| Fotel kierowcy | ![](fotel_overcast.jpg) | ![](fotel_overcast_urp.jpg) |

Przed i po (A5 → A6): `porownanie_*.jpg`. Cycles obok URP-like: `cycles_vs_urp_*.jpg`. Warianty do Twojej decyzji: `wariant_trim_pasazer.jpg`, `wariant_trim_fotel.jpg`, `wariant_znak_piasta.jpg`. Sama mapa światła otoczenia, bez kolorów: `ao_check_*.jpg`, atlas: `ao_atlas_preview.jpg`.

## Najważniejszy wniosek z renderów URP-like (dla `rendering-perf`)

- **Pochmurny dzień:** w modelu gry wnętrze jest czytelne. Deska, konsola, drzwi i fotele mają rysunek i średnie tony, nie ma czarnej plamy.
- **Niskie słońce (9°, z przodu z boku):** poza miejscami, gdzie wpada słońce, wnętrze robi się prawie czarne (`cycles_vs_urp_pasazer_lowsun.jpg`). Tak wygląda URP bez światła odbitego. Samo rozjaśnienie materiałów tego nie naprawi, bo całe oświetlenie wnętrza pochodzi z nieba. Propozycja do decyzji `rendering-perf`: mapę otoczenia (`T_Cab_AO_*`) traktować jako wypalone światło kabiny i dodać mały, niecieniujący „fill” kabinowy albo własną sondę światła w kabinie, zależną od położenia słońca. Ostateczną odpowiedź da dopiero pierwszy kadr z URP i z telefonu (A7).
- Ważne odkrycie po drodze: zwykłe krótkie AO (0,6 m) w URP daje wnętrze **prześwietlone**, a nie czarne, bo w URP niebo oświetla wnętrze tak, jakby kabina nie miała dachu. Dlatego mapa „AO” w A6 to naprawdę **światło otoczenia kabiny**: Cycles liczy je z równomiernego białego nieba, z odbiciami i z rzeczywistymi kolorami powierzchni. Zawiera i przesłonięcie przez dach, i cienie kontaktowe, i rozjaśnienie od podsufitki. W URP mnoży światło pośrednie (rozproszone i odbicia).

## A6: co jest gotowe do importu (`art-source/truck/interior/export/`)

| | LOD0 (High) | LOD1 (Medium) | LOD2 (Low) |
|---|---|---|---|
| Trójkąty (cel) | **78 381** (≤ 90 tys.) | **37 767** (~40 tys.) | **21 574** (~20 tys.) |
| Przed czyszczeniem | 96 896 | 45 220 | 23 958 |
| Usunięte ukryte ściany | 8 733 | 3 761 | 1 247 |
| Obiekty (≈ wywołania rysowania z podzestawami) | 21 | 21 | 19 |
| Plik | `SM_CabInterior_LOD0.fbx` (8,6 MB, **poza gitem**, generowany) | `…LOD1.fbx` (4,3 MB) | `…LOD2.fbx` (2,4 MB) |

- **LOD-y są odtwarzalne:** ten sam generator z innym zagęszczeniem siatki, plus lista drobiazgów pomijanych w niższych LOD-ach.
- **Ukryte ściany** usuwam ostrożnie. Ścianka znika tylko wtedy, gdy nie widać jej z żadnego z ok. 80 punktów widzenia (głowa kierowcy w zakresie ruchu, pasażer, leżanka, osoba stojąca, podłoga przy pedałach, kamery renderów, kamery zewnętrzne przez szyby) **i** jednocześnie jest czymś zakryta w promieniu 5 cm. Części ruchome nie są czyszczone.
- **Materiały:** 49 materiałów roboczych scaliłem w **5 nieprzezroczystych zestawów** (tworzywo, skóra, tkanina, guma, metal) i **atlas naklejek** (przeszycia, kratki, symbole), czyli 6 atlasów. Do tego szkło, ekrany (obraz z gry) i lusterka (render texture). Różnice między dawnymi materiałami (kolor, chropowatość, zużycie, perforacja, metaliczność) przeszły do danych wierzchołków. Dokładny kontrakt shadera jest w manifeście (`shader_contract`). To przepis na jeden Shader Graph „Kamion/CabInterior” dla agenta Unity.
- **Tekstury w 3 profilach**, kwadraty o bokach będących potęgą dwójki (pod ASTC): High 1024/512, Medium 512/256, Low 256/128. Mapa otoczenia: LOD0 2048, LOD1 1024, LOD2 512 (i mniejsze kopie). Razem ok. 21 MB PNG na dysku. W pamięci GPU po ASTC to ułamek tego.
- **Punkt zaczepienia:** początek kabiny to `CAB_MOUNT_REF`, ten sam punkt co `CabPivot` w obecnej ciężarówce testowej (wysokość dolnej krawędzi kabiny 1,15 m, środek długości kabiny). Wnętrze wstawia się jako dziecko obiektu zawieszenia kabiny, bez przesunięcia.
- **Nazwane obiekty dla gry:** `EYE_POINT` (oczy kierowcy, w Unity (−0,55; 1,35; 0,225) względem zaczepu), `H_POINT`, `WHEEL_CENTRE`. Ruchome części z osiami obrotu: `STEERING_WHEEL` (oś kolumny = lokalne Y), `STALK_Indicator`, `STALK_Retarder`, `STALK_AMT`, `PEDAL_Brake`, `PEDAL_Accel`, `LEVER_ParkBrake`. Ekrany pod obraz z gry: `DISPLAY_Cluster`, `DISPLAY_Infotainment`, `DISPLAY_Tachograph`, `DISPLAY_Radio`, `DISPLAY_BunkPanel`. Lusterka pod render texture: `MIRROR_MainL/R`, `MIRROR_WideL/R`, `MIRROR_Kerb`, `MIRROR_Front`. `CAB_ShellPlaceholder` to tymczasowa karoseria (do wyłączenia po A3).
- **Kontrola eksportu:** `check_export.py` wczytuje FBX z powrotem i porównuje go z manifestem (obiekty, trójkąty, zestawy UV, kolory wierzchołków, materiały, położenia punktów, rozmiary tekstur). Wynik: **CHECK PASS** dla wszystkich LOD-ów.

## Pętla visual QA: iteracje

1. **Iteracja 1** (kierownica i kaptur): test linii wzroku zaliczony, ale klawisze na ramionach wchodziły w piastę, a kaptur zasłaniał rząd kontrolek przy ruchu głowy o 2 cm (test to wyłapał). Poprawiłem spód kaptura i położenie panelu klawiszy.
2. **Iteracja 2** (pierwszy pełny zestaw): zewnętrzna kolumna klawiszy znikała w nachyleniu ramienia; poduszka nadal miękka; kieszeń fotela schowana w skorupie; góra deski beżowa w niskim słońcu; półka pasażera poza kadrem.
3. **Iteracja 3:** ramię płaskie pod panelem, poduszka z ostrą krawędzią, nowe tło. Z diagnozy wyszło, że beżowa deska to nie połysk, tylko zbyt silne słońce względem nieba (ok. 20:1 przy +1,6 EV). Spękania asfaltu wyglądały jak wyschnięte błoto.
4. **Iteracja 4:** zbalansowane niskie słońce, rzadsze i cieńsze spękania, ciemniejszy las. Druga półka na środku deski.
5. **URP-like 1–3:** pierwsza wersja z krótkim AO dała prześwietlone wnętrze (patrz wniosek wyżej), więc zmieniłem wypalanie na światło otoczenia kabiny. Odbicia nieba na ciemnych tworzywach też muszą być przesłonięte, bo URP robi to samo. Na koniec przeszedłem na wierne odtworzenie URP: światło bezpośrednie bez AO, a otoczenie (SH) × mapa.
6. **URP-like 4–7:** ekran zegarów pokazywał teksturę tachografu (błąd nazw, poprawiony). Pas i przeszycia świeciły, bo naklejki brały neutralną wartość mapy; teraz dziedziczą ją z powierzchni pod spodem. Na wieńcu, który się obraca, wypalony wzór obracałby się razem z nim, więc dostaje stałą wartość. Na konsoli brakowało fragmentu płyty, więc usuwanie ukrytych ścian zaostrzyłem do warunku „niewidoczna **i** zakryta”. Metal dostawał „rozproszone” otoczenie i był za jasny, poprawione.

## Znane braki

- **Brak kadru z prawdziwego URP i z telefonu.** Bramka `docs/06` §5 pkt 2 dalej nie jest spełniona; to A7 (Unity i Samsung A).
- Mapa otoczenia: na dużych gładkich panelach (oparcia od tyłu, góra deski przy szybie, siedzisko) widać jeszcze lekkie plamy i szwy między wyspami UV (`ao_check_*.jpg`). Pod ciemnym kolorem prawie ich nie widać, ale do A6.1: osobne, większe wyspy dla dużych paneli i bake w wyższej rozdzielczości dla oparć.
- W URP-like z leżanki górna, zwrócona do nieba powierzchnia konsoli jest jaśniejsza niż w Cycles (otoczenie zależne od kierunku). Do sprawdzenia na pierwszym kadrze URP.
- Niskie słońce w URP: wnętrze bardzo ciemne. To decyzja oświetleniowa (`rendering-perf`), opisana wyżej.
- Wariant koncepcji B (szyba 19°): zegary są widoczne (test PASS), ale słupek A nadal wymaga A3.
- Tło renderów (plac, las, hala) jest własne i służy tylko renderom, nie jest zasobem gry.
- Commit `wip` z przerwania zawiera LOD0 FBX (8,6 MB, LFS). Kolejny commit wyłącza go z gita (jest generowany), ale w historii gałęzi plik zostaje.

## Licencje (do wpisu przez lidera w `docs/LICENSES.md`)
Nowych zasobów zewnętrznych brak. Tło, drzewa i tekstury są generowane skryptem (własne, objęte licencją projektu). Font Inter (OFL 1.1) już jest w `docs/LICENSES.md` (`font-inter`), a jego użycie się nie zmieniło. Proponowany wpis: `truck-interior-a6 | własne, generowane (tools/blender/truck/interior/*.py) | licencja projektu | wnętrze kabiny LOD0–2, tekstury, tło renderów kontrolnych (tylko render)`.

## Pytania do Ciebie
1. Kolor wstawek: grafit, piasek, koniak czy łupek? (`wariant_trim_*.jpg`). Krytyk poleca piasek albo koniak, bo dodają wnętrzu średnich tonów, co pomaga w grze.
2. Czy cyfrowe zegary bez okrągłych tarcz (decyzja wymuszona widocznością) są w porządku?
3. Znak na piaście: TRAKT, BIELIK, NAREW czy bez znaku? (`wariant_znak_piasta.jpg`)

## Jak odtworzyć
```
uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/make_textures.py
blender -b --factory-startup --python tools/blender/truck/interior/build_interior.py -- --out docs/reports/visual/truck-A6 --samples 512 --stats docs/reports/visual/truck-A6/stats.json
blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/interior/sightline_test.py -- --report docs/reports/visual/truck-A6/sightline.json
blender -b --factory-startup --python tools/blender/truck/interior/a6_export.py -- --lods 0,1,2 --urp-out docs/reports/visual/truck-A6
blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/interior/check_export.py
python tools/blender/truck/interior/variants.py --out docs/reports/visual/truck-A6
```
Czasy (RTX 5070): tekstury ok. 10 s, 8 renderów Cycles 512 spp ok. 2 min, eksport 3 LOD-ów z wypalaniem 4096 spp i 8 renderami URP-like ok. 5 min. Diagnostyka: `a6_export.py … --debug-ao` (sama mapa otoczenia), `--debug-col` (same kolory wierzchołków).

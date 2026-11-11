# REVIEW 2026-11-11 s10 — GPT strumienie H / I / L (niescalone)

Recenzent: visual-critic (niezależny, nie autor). Zakres: `docs/owner/GPT-TASK-03-S10.md` H, I, L.
Źródła: `artifacts/edge-far-r2/`, `artifacts/furniture-r1/`, `artifacts/viaduct-r10/` (kopie na main), gałęzie
`gpt-edge-r2` @027e7589, `gpt-furniture-r1` @ea0b4d67, `gpt-viaduct-r1` @1acc16af (wszystkie z bazy main 9e6e9fde).
Wszystkie dowody to rendery z edytora (2340×1080). **Zrzutu z telefonu brak w żadnym strumieniu** — bramka telefonu u lidera.

## Co zrobiłem sam (nie z deklaracji)
- Obejrzałem PNG w pełnej rozdzielczości: H `edge-south`/`edge-east`/`edge-north` High-clear, arkusze `compare-*`, `compare-skyline`;
  I `furniture-fence`, `-footing-slope`, `-old-concrete`, `-old-steel`, `-sign-back` + arkusze route/detail; L `dk8-bearing`,
  `dk8-under-span`, `dk8-abutment`, `dk8-west-interior`, `paired-*`, `details-final`, referencje `reference-render.jpg`, `refp45.jpg`, `ref-ortho-putry.jpg`.
- Uruchomiłem testy w worktree: `test_far_field_boundary.py` 13 passed; `test_furniture_r1.py` 9 passed; `test_viaduct_underdeck.py` 7 passed.
- Porównałem `stats.txt` przed/po (Low) — zgodne z deklaracjami (niżej).
- Różnica pikseli przed/po (ImageMagick AE, fuzz 6 %): I trasa Low-overcast 0,000–0,075 % pikseli (`stretch-05-docks` 0, `dk8-dk19-exit` 0,001 %), detale 0,08–0,65 %;
  L `dk8-bearing` 2,2 %, `dk8-under-span` 1,7 %, trasa `g3b`/`route-putry` do 0,11 %.
- Kolor filarów Putry (L, `after/High-overcast/dk8-bearing.png`, ROI na trzonie): **107/99/58** i **80/75/47** sRGB, sd 9–13;
  zdjęcie CC0 `ref7204.jpg` (filar w cieniu): **79/67/37**, **81/69/42**, sd 19–24.
- `git merge-tree main <gałąź>`: H — czysto; I — konflikty `streetscape_qa.json`, `world_manifest.json`, `LICENSES.md`, `materials.py` (oba dopisy na końcu pliku, trywialne);
  L — `streetscape_qa.json`, `world_manifest.json`, `LICENSES.md`. Generated: regeneracja.

---

## H — ADR 0085 r2, tło za krawędzią świata — **scalenie: PASS (warunkowy)**

**Uwagi lidera s9:** (1) `edge-south` — kremowy biurowiec regionu wrócił (prawa strona kadru, x≈1530–2000 w High-clear), długiej hali
`_FAR_FACADE` w jego miejscu już nie ma; test „far_field ∩ obrysy regionu = ∅” istnieje i przechodzi (13/13). **Zamknięte.**
(2) Kadr z lasem Pietrasze zamykającym horyzont: **nie dostarczony z wysokości oczu** — `edge-pietrasze-horizon` patrzy w las z bliska
(widać tylko pnie, horyzontu brak), a jedyny kadr z horyzontem to diagnostyka z 40 m (autor uczciwie tak to opisuje). **Otwarte (P2).**
(3) `export/export` usunięte z gałęzi (0 ścieżek w drzewie); 204 MB leży w `artifacts/edge-far-r2/quarantine/` poza gitem — lider może skasować.

**Budżet Low (z stats.txt):** 16 par, delta drawsEst 0, trisK 0 lub −1 (Pietrasze 82→81). Siatka Low 24 826 → 24 508 tris. Zgodne z deklaracją.
Uwaga: względem main **bez** tła cała 0085 dalej dokłada odziedziczone +2…4 draws/kadr (ADR to przyznaje) — to decyzja o scaleniu Argona, nie regresja r2.

**Regresje poza zakresem:** brak widocznych. Zmiana `WorldSurface.shader` ograniczona do gałęzi `#if _FAR_FACADE` (okna wstęgowe z `COLOR_0.a`) — nie dotyka innych materiałów.
`build_world.py` woła `far_field.build_far_field` na końcu buildu i nadpisuje manifest — po scaleniu każdy build świata generuje tło; sprawdzić czas buildu.

**Jakość (bez upiększania):** r2 to praktycznie tylko naprawa błędu z s9. Część „jakość tła” z zadania (sylwetki zabudowy/lasu z BDOT/NMT, brak ściany) nie została
widocznie posunięta: w `edge-east`/`edge-south` horyzont to rzadkie, małe pudełka bloków na płaskim polu, bez mgiełki rozdzielającej plany — czyta się jak
„koniec mapy w grze mobilnej”, nie jak przedmieścia Białegostoku. Na `compare-skyline` (40 m) widać prostokątne ciemne „karty” lasu (prawa połowa kadru) — odziedziczone.

| # | Pri | Kamera | Problem | Propozycja |
|---|---|---|---|---|
| H1 | P1 | `edge-east`, `edge-south` High-clear, środek kadru y≈430–470 | Tło za granicą: pojedyncze bloki/domki na pustym, równym polu, brak masy zabudowy i drzew na drugim planie; jezdnia kończy się barierą i trawą — droga nie ma kontynuacji w far-field. | Kontynuacja jezdni (pas asfaltu do 300–600 m) w far-field; gęstość zabudowy z BDOT (nie tylko największe obiekty); zadrzewienia przydrożne z BDOT; mgiełka 0098 wyraźnie zdejmująca kontrast dalszych planów. |
| H2 | P2 | `edge-pietrasze-horizon` | Kadr nie dowodzi tezy (las zamyka horyzont) — kamera praktycznie w lesie. | Kamera z jezdni DK8/DK19 na wysokości kabiny (~2,4 m), widok wzdłuż osi drogi na północ. |
| H3 | P2 | `compare-skyline` 40 m | Ciemne prostokątne karty lasu widoczne z góry (odziedziczone). | W rundzie roślinności (0088) — fade/dither kart HLOD. |
| H4 | P2 | — | Zrzutu z telefonu brak. | Lider: A16 Low, `edge-south` + `edge-east`. |

Oceny 1–10: skala/proporcje 6 · światło 6 · materiały tła 4 · osadzenie 5 · powtarzalność 5 · polskie realia 4 · czytelność 6 · artefakty 7.
**Werdykt jakości: FAIL jako „tło gotowe do bramki 3”; PASS jako naprawa błędu blokującego z s9.** Scalać (nic nie psuje, usuwa dubel).

---

## I — ADR 0102, meble uliczne r1 — **scalenie: PASS (warunkowy)**

**Deklaracje vs pomiar:** relief stopni 147→107, maks. 1,087→0,411 m, floating 4→0/223 — zgodne z `final-metrics.json` (nie mierzyłem w Unity).
Draws Low delta 0, tris do +1,18 % — zgodne z `frame-budget*.json`. 806 prymitywów dróg/barier/krawężników identycznych bajtowo — **względem bazy 9e6e9fde,
nie aktualnego main** (main ma już 0100 r3 z barierami/krawężnikami), więc po scaleniu powtórzyć `protected-geometry` na zintegrowanym main.

**Regresje:** brak. Kadry trasy różnią się o < 0,1 % pikseli — to znaczy również, że **z perspektywy kierowcy zmiana jest praktycznie niewidoczna**.

**Co widać:**
- `furniture-footing-slope` (High-overcast, x≈970–1060, y≈570–650): wcześniej słup wchodził w skarpę bez podstawy; teraz jest ścięty ostrosłup cokołu — poprawa,
  ale cokół jest ciemny (zmierzone **73/72/63** vs ściana oporowa obok **120/118/112**), ostry, czysty, bez obsypki na krawędzi — wygląda jak doklejony klocek.
- `furniture-fence` (High-overcast, x≈0–1000, y≈560–680): podmurówka schodkuje, ale stopnie są wysokie (lewa część wizualnie ~0,8–1 m), płaskie, jednolicie szare,
  bez desek prefabrykowanych i fug; siatka panelowa idealnie prosta (brak zwisu/odkształceń). Autor sam pisze „ciężka”. Zgadzam się — P1.
- `furniture-old-concrete`: przed/po prawie identyczne. Słup „stary betonowy 9 m” jest smukły, gładki, jasny i czysty — czyta się jak stalowy. Prawdziwe wirowane
  słupy betonowe mają wyraźną zbieżność, ~25–30 cm średnicy u dołu, fakturę i zacieki (WORKING_VALUE, do potwierdzenia zdjęciem). To „zabawkowa latarnia” z docs/06 §2.
- `furniture-old-steel`: dodana płyta podstawy na krawędzi chodnika, wysięgnik prosty — OK.
- `furniture-sign-back`: przed i po **niemal identyczne** (szary tył, 2 obejmy, jasna naklejka) — w tym kadrze zmiana nie zaszła albo była już na main.
- Rdza przy ziemi, brud, naklejki: **niewidoczne** w żadnym dostarczonym kadrze (autor przyznaje). Referencje (`refs-sheet.jpg`) to małe nocne/pod słońce klatki
  dashcamu — nie da się na nich zweryfikować rodzin lamp. Przypisanie rodzin do ulic: UNVERIFIED.

| # | Pri | Kamera | Problem | Propozycja |
|---|---|---|---|---|
| I1 | P1 | `furniture-fence` | Podmurówka za wysoka i płaska; prostopadłościenne stopnie bez faktury; siatka idealnie płaska. | Podmurówka prefabrykowana 20–30 cm (deski ~2,5 m z fugą), na skarpie stopnie do ~25 cm + obsypka; beton z zabrudzoną dolną krawędzią; ±2–3 cm odkształceń paneli. |
| I2 | P1 | `furniture-old-concrete` | Betonowy słup nieodróżnialny od stalowego. | Zbieżność, większa średnica u dołu, albedo betonu z fakturą, zacieki od oprawy, stara oprawa zamiast płaskiego „pudełka LED” — wszystko z dziennego zdjęcia Mapillary. |
| I3 | P2 | `furniture-footing-slope` | Cokół za ciemny i ostry, bez kontaktu z gruntem. | Albedo jak `concrete_base`, faza krawędzi, decal ziemi/trawy u podstawy. |
| I4 | P2 | wszystkie | Zużycie (rdza/brud/naklejki) niewidoczne z odległości kierowcy. | Kamera zbliżeniowa 1,5 m od słupa + maska rdzy czytelna z ~10 m. |
| I5 | P2 | — | Referencje słabe, rodziny UNVERIFIED; telefon brak. | Mapillary dzienne, 5–10 m od słupa, po 2 na rodzinę. |

Oceny 1–10: skala/proporcje 5 · światło 6 · materiały 4 · zużycie/osadzenie 5 · powtarzalność 5 · polskie realia 5 · czytelność 6 · artefakty 7.
**Werdykt jakości: FAIL (cel „meble jak w Białymstoku” nieosiągnięty, poprawa głównie w danych QA); scalenie PASS** — wartość techniczna (0 floating, relief) bez regresji.

---

## L — ADR 0105, wiadukt DK8 Putry pod pomostem — **scalenie: PASS (warunkowy)**

**Budżet Low (z stats.txt):** delta drawsEst 0 we wszystkich 5 parach; trisK 278→279, 298→301, 216→218, 260→264 (+1,5 %), 181→183 — mieści się w +3 %, zgodne.
Uwaga: nowa kamera `dk8-east-north` Low ma drawsEst **497** (przed SRP batching) — powyżej hipotezy 300–400 z docs/06 §6; brak pary „przed”, więc nie wiem, ile dokłada L. P2: pomiar A16.

**Filary „czerwonawe” (uwaga z innej recenzji):** w kadrach L **nie potwierdzam**. Filary Putry są ochrowe/żółte (107/99/58), a zdjęcie CC0 7204 i Mapillary p45
pokazują właśnie malowane żółto-ochrowe filary tego wiaduktu — kolor ma pokrycie w referencji (materiał `pier_yellow` istniał przed L). Wartości 75/60/58 nie znalazłem
w żadnym mierzonym ROI; jeśli uwaga dotyczyła wiaduktu Bieżeństwa (hero; na main są niezacommitowane zmiany `viaduct_biezenstwa.*`), to jest poza zakresem L.
Różnica względem zdjęcia: render bardziej zielonkawo-żółty (R/G 1,08 vs 1,17) i **płaski** (sd 9–13 vs 19–24) — brak plam, zacieków na wysokości i ciemniejszego dołu, więc plastik.

**Regresje:** pomost/bariery/ekrany nietknięte (autor: SHA geometrii pomostów identyczne; wizualnie potwierdzam na `paired-*`). Kadry trasy: zmiana do 0,11 % pikseli.
`roads_qa.json` na gałęzi traci 4 wpisy mostów (`w1101181473` 219,4 m / 7 podpór, `w173956078` 212,9 m / 5 podpór) — wygląda na generated z innego stanu;
**sprawdzić po regeneracji**, czy QA mostów na zintegrowanym main ma te wpisy (P1 dla lidera, niewidoczne w renderze).

**Co widać:**
- `dk8-bearing` / `dk8-under-span`: filary dostały oczep (płyta) + blok łożyska + krótkie ciemne zacieki pod oczepem + rurę spustową przy filarze. Realna poprawa względem
  „rura wbita w pomost” z before. Ale oczep to jasnoszara czysta płytka szersza od filara — wygląda jak podstawka; kroplownika z dołu nie widać.
- **Schody skarpowe** (`dk8-abutment` x≈660–1170, y≈340–630; `dk8-west-interior` x≈1280–1620, y≈360–680): pełny betonowy klin ze stopniami wyciętymi w jednej ścianie,
  przyklejony do pionowej ściany, **kończy się na ścianie bez spocznika, bez wyjścia i bez balustrady**; w `dk8-abutment` ekran akustyczny/słupek przechodzi przez bryłę schodów.
  To „schody donikąd” — typowy błąd generatora. Realne schody skarpowe biegną po nachylonej skarpie nasypu do chodnika na koronie, z poręczą stalową.
- Spód pomostu (`dk8-under-span`, lewa górna ćwiartka): smugowa, rozmazana tekstura — najpewniej rozciągnięte UV (odziedziczone); bardzo ciemny w overcast (autor przyznaje; 0098/0101).
- Plamy farby, zacieki pod dylatacjami: na Low/High praktycznie niewidoczne.
- Ortofoto (`ref-ortho-putry.jpg`): dwa łańcuchy i łuk zgodne z planem; układ podpór/schodów to WORKING_VALUE.

| # | Pri | Kamera | Problem | Propozycja |
|---|---|---|---|---|
| L1 | P1 | `dk8-abutment`, `dk8-west-interior`, `dk8-east-north` | Schody donikąd: kończą się na ścianie, bez spocznika i balustrady; kolizja z ekranem akustycznym. | Sprawdzić w ortofoto/Mapillary, czy schody tu istnieją; jeśli nie — usunąć. Jeśli tak — bieg po skarpie do chodnika na koronie, spocznik, poręcz obustronna; test przecięcia z ekranami. |
| L2 | P1 | `dk8-bearing`, `dk8-under-span` | Filary płaskie, jednolite, lekko zielonkawe vs zdjęcie. | Odcień w stronę zdjęcia (R/G ~1,17; przez kontrakt `_Tint` ADR 0086), maska zabrudzenia dołu 0,5–0,8 m, pionowe zacieki od oczepu na ~1/3 wysokości, łuszczenie farby. |
| L3 | P2 | `dk8-bearing` | Oczep czysty, jasny, „podstawka”. | Beton jak dźwigar, ciemniejsza dolna krawędź, widoczny kroplownik. |
| L4 | P2 | `dk8-under-span` | Smugi/rozciągnięte UV na spodzie pomostu. | Triplanar albo UV z rzutu z dołu dla spodu. |
| L5 | P2 | `dk8-east-north` Low | drawsEst 497. | Pomiar na A16; ewentualnie cull detali pod pomostem na Low. |
| L6 | P2 | — | `roads_qa.json` traci 4 wpisy mostów. | Regeneracja i diff po scaleniu. |

Oceny 1–10: skala/proporcje 5 · światło 4 · materiały 4 · zużycie/osadzenie 4 · powtarzalność 6 · polskie realia 6 (kolor filarów, ekrany zgodne) · czytelność 5 · artefakty 4 (schody/ekran).
**Werdykt jakości: FAIL (L1 to błąd geometryczny widoczny z drogi bocznej); scalenie PASS warunkowe** — bez regresji pomostu i budżetu; L1 poprawić w r2 przed bramką 3
albo przy scaleniu wyłączyć generację schodów (flaga w `viaduct_underdeck.json`).

---

## Podsumowanie dla lidera
| Strumień | Scalenie | Jakość | Najważniejsze |
|---|---|---|---|
| H 0085 r2 | PASS | FAIL (tło nadal „koniec mapy”) | dubel biurowca naprawiony + test 13/13; kadru Pietrasze z oczu kierowcy brak |
| I 0102 | PASS | FAIL | zmiany niewidoczne z drogi (< 0,1 % pikseli); podmurówka ogrodzenia i słup betonowy słabe |
| L 0105 | PASS warunkowy | FAIL | schody donikąd przecinające ekran; filary żółte = zgodne z referencją, nie czerwone |

Kolejność scalania: H (bez konfliktów) → I → L; po każdym regeneracja `build_world.py` + import, potem ponowny `protected-geometry` (I) i diff `roads_qa` (L) na zintegrowanym main.
Poza zakresem (do wiadomości): na main i gałęziach śledzone jest `tools/worldgen/.venv/` (8339 plików, DLL do 23 MB) — higiena repo, osobne zadanie.

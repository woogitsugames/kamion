# ADR 0343 — Bok kabiny TRAKT: przetłoczenia, rynienka, kratka, kierunkowskaz boczny, żebra owiewki, brud boczny

Status: Proposed, 2026-11-24 (agent cab-side-s24, gałąź `cab-side-s24`). Zmiana modelu i tekstur zewnętrza ciągnika —
do oceny przez `visual-critic` (autor nie zatwierdza własnej pracy).
Powiązane: ADR 0340 (otwarte pkt 3: „ściana boczna kabiny jest dużą, gładką powierzchnią”), 0047 (front „modern”),
0175 (przepisy wyglądu), 0181 (soczewki lamp), 0039/0061 (budżety LOD), docs/07 §2–3, docs/06 §2.

## Kontekst (zmierzone na renderach)

W okienku lusterka klasy II (`MirrorDump`, RT ×3, `artifacts/cab-side-s24/before/mirror_res3/`) bok kabiny to pas
oglądany 3–15° od blachy. Składa się z trzech pól: bok wysokiego dachu z owiewką boczną (góra), **szyba drzwi** (środek —
to ona jest „lustrem nieba”, nie lakier) i dolna połać drzwi. Przed zmianą jedynymi cechami były linie szczelin drzwi,
wnęka uchwytu i płaski arkusz owiewki. Przy tak ostrym kącie mapa normalnych nie daje nic — czyta się tylko to, co
wystaje z blachy albo ma kontrast albedo.

## Decyzja

Wszystko w generatorze (`tools/blender/truck/exterior/body.py: side_detail()`, wywoływane z `build.py` i `a6_export.py`),
wymiary `WORKING_VALUE` dobrane z klasy pojazdu, bez kształtów konkretnego producenta. Bryła kabiny (loft, szyby,
linie drzwi, wymiary `dims.json`) bez zmian.

1. **Przetłoczenie boczne** (`relief()` — nakładka na poszycie, przesunięcie h · profil(z) · wybieg(y)): ostra górna
   krawędź na 1,845 m, 11 mm, wybieg w dół 140 mm; biegnie przez drzwi (`door_swage_*`, część `DOOR_*`, otwiera się z
   drzwiami), krótki odcinek panelu sypialni do wnęki uchwytu i panel narożny, gdzie wygasa na promieniu słupka A.
2. **Przetłoczenie boku dachu** (3,365 m, 8 mm, nad łączeniem dachu 3,30 m, pod promieniem dachu) z wybiegami.
3. **Rynienka nad drzwiami** (3,034–3,050 m, 11 mm, ciemne tworzywo) + warga gumowa (tylko bake).
4. **Kratka wywiewu kabiny** w panelu sypialni nad wnęką uchwytu (180 × 280 mm): tacka, rama, 6 żaluzji 32°.
5. **Kierunkowskaz boczny** na stałym panelu narożnym (145 × 55 mm, środek 1,40 m nad jezdnią, 0,5 m od czoła):
   podstawa, uszczelka (bake), soczewka bursztynowa w grupie `IND_L` / `IND_R` (styl soczewki FLUTE, ADR 0181).
   Wysokość ≤ 1,5 m i odległość od przodu ≤ 1,8 m przyjęte za `regs_check.py` (R48 6.5, kat. 5); tekst regulaminu w tym
   zadaniu nie był czytany: `UNVERIFIED`. Istniejący powtarzacz na nadkolu zostaje.
6. **Owiewka boczna**: trzy przetłoczone żebra na odsłoniętej części za narożnikiem kabiny.
7. **Uszczelki drzwi** jako warga gumowa obok szczelin (tył, góra, przód) — elementy `bk_*`, tylko do bake'u
   (normal + kolor); `a6_export.bake_only()` rozpoznaje prefiks `bk_`.
8. **Brud boczny** (`materials.side_grime()`, maska brudu G wypalana w pełnej sile, gra skaluje `_Dirt`):
   rozbryzg za kołem przednim (wachlarz od −0,34 m za osią, do ~2,05 m wysokości i ~2,9 m za osią, smugi wzdłuż kierunku
   wyrzutu + luźny rozprysk; lakier i tworzywo stopni), zacieki pod osprzętem (wnęka uchwytu, kratka, koniec rynienki,
   klamka, kierunkowskaz, tylna szczelina drzwi — różna siła po stronie kierowcy i pasażera), drobne rysy wokół klamki
   (dwie rodziny cienkich linii) i otarcia dołu drzwi nad stopniami.

Już istniało i zostaje bez zmian: stopnie z perforowanymi stopnicami, wnęka z uchwytem, klamka z zamkiem, osłona
zbiornika / skrzynek (`skirt_panel_*` z przetłoczeniem, wywietrznikami i zatrzaskami), powtarzacz na nadkolu.

### LOD
LOD1 traci żaluzje kratki (`side_vent_louvre`, rama i tacka zostają); LOD2 traci przetłoczenia, kratkę, żebra owiewki
i podstawę kierunkowskazu (soczewka i rynienka zostają). Cele decymacji bez zmian (`TRI_TARGET`).

## Skutki (zmierzone)
- Trójkąty (manifest, z bryłami kolizji; limity 140 000 / 45 000 / 17 900): LOD0 105 898 → 107 493, LOD1 42 999 → 43 000,
  LOD2 17 838 → 17 702.
- Texel density High bez istotnej zmiany: Paint 554 → 556 px/m, Trim 278 → 278 px/m. Rozmiary atlasów bez zmian.
- Walidatory: `check_export.py` PASS, `check_fit.py` PASS (0 wierzchołków wnętrza poza poszyciem), `test_truck_regs.py` 5 passed.
- Szerokość: najdalej wystają żaluzje kratki (+18 mm od poszycia na wysokości 2,6 m, gdzie kabina jest już węższa) i
  soczewka kierunkowskazu (+13 mm → 2,516 m); limit 2,55 m zachowany (`regs_check`: szerokość nadwozia).
- Czas eksportu z bake'iem: 1374 s i 1264 s (dwa przebiegi na PC s24).
- W lusterku (edytor, PC High, clear, RT ×3 — `artifacts/cab-side-s24/compare/`): w pasie kabiny widać kratkę, rynienkę,
  półkę przetłoczenia na dolnej połaci drzwi i żebra owiewki. Środkowe pole pasa to nadal szyba drzwi odbijająca niebo —
  tego ta zmiana nie dotyka (i nie powinna: to szkło).

## Otwarte
1. Ocena `visual-critic` i właściciela (kierunek artystyczny: wysokość i siła przetłoczenia, kratka po obu stronach).
2. Zrzut z playera Windows po scaleniu — dowody są z edytora.
3. Klamka pozostaje wpuszczona (płaska); wystający pałąk czytałby się w lusterku lepiej, ale zmienia charakter drzwi —
   decyzja właściciela.
4. Aliasing RT lusterek (ADR 0340, otwarte 1) ogranicza czytelność drobnego detalu przy skali 1×.

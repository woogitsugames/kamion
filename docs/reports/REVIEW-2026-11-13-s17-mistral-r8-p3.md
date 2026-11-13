# Przegląd PR #50 (M53, Mistral) — zabudowa: dopasowanie zdjęć, wielka płyta, kolory elewacji

**Werdykt: NADAL DO POPRAWY (manifest budynków); CZĘŚCIOWO przyjęte zad. 2 i 4.** Gałąź `origin/research/mistral-p3-buildings-2` @ d21885205, tylko `research/mistral/p3-buildings-2/` (README, manifest 43 w., audit, sources, .gitignore, state.json). Poprawki: blok M53-FIX w `docs/owner/MISTRAL-FIXES-8.md`.

## Próba własna (seed 53113, `random.Random(53113).sample(ids,10)` = 23 %)
Obejrzane JPG + geometria: pozycja kamery z `seq_az.json`, obrysy LoD1 (`lod1_wgs84.json`; measuredHeight sprawdzone na 12 id w GML GUGiK `Data/raw/gugik/lod1-2024-2061` — **12/12 zgodne**), adresy z OSM `osm_buildings.json`.

| id | ustalenie |
|---|---|
| 001 | PASS — stacja z czerwoną wiatą jest w kadrze; wysokość 4,5 m ESTIMATED do przyjęcia |
| 006 | **FAIL** — Andersa 46 (JRG-2) nie ma w kadrze: park, ławki, bloki 5–6 kondygnacji i kolorowe bloki; w sektorze NE od kamery (gdzie stoi JRG) LoD1 nie ma budynku ≥ 10 m w promieniu 200 m → zdjęcie patrzy na ~S–SW (Tysiąclecia 44/54/58). Kolor [206,179,199] jest z innego obiektu |
| 008 | **FAIL** (status `OK`) — Sokólska 9 leży poza kadrem (sam manifest podaje pos 133 %). Na zdjęciu widać napisy „Zagumienna 40” (szczyt w środku kadru) i „…stoczek 29” (blok po prawej) → patrzenie ~335°, a nie 15° z sekwencji. Ten sam plik dotyczy **M53-011 i M53-012** (Białostoczek 34 i 27, brg 16° i 13° — poza kadrem): ich pomarańczowy kolor to szczyt Zagumiennej 40 |
| 013 | budynek wiarygodny (blok 5 kondygnacji przy kamerze); **kolor FAIL**: [52,44,41] „ciemnobrązowy”, a blok jest kremowobiały z czerwonobrązowymi balkonami |
| 018 | NIEPEWNE — stary 2-kondygnacyjny budynek z cegły/tynku pasuje do 6,23 m, ale sam manifest pokazuje FH = Jurowiecka 50 |
| 024 | **uzasadnienie fałszywe** — na zdjęciu stoi 12-kondygnacyjny punktowiec z muralem (ks. Sopoćko), a nie Białostoczek 14 (15,95 m) ani 18 (18,7 m). Kandydaci z LoD1 przy azymucie: Białostoczek 11/13A/15/17/19A (34,6–36,2 m). Z tego samego pliku przyjęty **M53-019 (Białostoczek 18, `OK-POŚREDNIE`) jest błędny** |
| 027 | odrzucenie zbyt ostrożne — 2-kondygnacyjny dom z dachem dwuspadowym pasuje do Białostoczek 4 (8,31 m) |
| 029 | PASS — tytuł autora; ok. 15 kondygnacji ↔ 39,61 m. Licencja CC BY-SA = tylko referencja. Kolor [245,206,183] jest różowawy, a budynek biały. Na dachu logo sklepu — nie do odtworzenia |
| 035 | PASS — zielony biurowiec to jedyny budynek ≥ 20 m w sektorze (Tysiąclecia 6, 23,91 m, ok. 8 kondygnacji). Kolor „oliwkowy” [153,140,110] zaniżony — w rzeczywistości żółtozielony |
| 041 | **typ FAIL** — „blok mieszkalny (TBS)”, a na zdjęciu dom jednorodzinny z poddaszem. Tożsamość niepewna: bliżej, w 31–43 m, stoją Tysiąclecia 29 i 31/2 |

**Wynik próby: 3/10 PASS, 4 FAIL/fałszywe** (006, 008, 024, 041), 3 częściowe. Poza próbą obalone jeszcze 011, 012, 019. Mistral w audycie podał **9/9 PASS** przy kryterium wizji „NIE DOTYCZY”, czyli samokontrola była zawyżona.

## Błędy systemowe
- Azymut liczony z toru sekwencji (GPS EXIF Commons zaokrąglony do 1″ ≈ 20–30 m) myli się o dziesiątki stopni. Treść zdjęć (napisy z adresem!) nie była sprawdzana.
- `kondygnacje_ze_zdjęcia` to `mh/2,9` albo OSM, a nie policzone na zdjęciu. Audyt C (mh ↔ kond·2,9) jest więc tautologią.
- `kolor_srgb`: w próbie 4 z 5 wartości błędne (k-means z cieni, drzew i niewłaściwych obiektów). Kolumna nie nadaje się do użycia.
- 037–043 „TBS 1999+”: na zdjęciu 037 widać szeregowe domy wielorodzinne z dachami dwuspadowymi, a nie bloki TBS. README jednocześnie przypisuje Wysokiemu Stoczkowi wielką płytę — to sprzeczność.

## Co przyjęte (fakty dla agentów budynków, ADR 0171)
- **MPZP (zad. 4) ZWERYFIKOWANE** w PDF z BIP (uchwała XXVII/451/26 z 25.06.2026): dach płaski 0°–15°; elewacje maks. 3 kolory w odcieniach bieli, beżu, brązu i szarości plus barwy naturalnych materiałów; pokrycie dachów skośnych brąz / ciemna czerwień / szarość; akcenty ≤ 10 % tylko dla usług edukacji. Plan dotyczy NOWEJ zabudowy — nie opisuje stanu obecnego.
- **Systemy (zad. 2)** — sprawdzone wyrywkowo na Osiedlowniku (blog z bibliografią prasy; źródło wtórne): Białostoczek OWT-67/OWT-75 (Inwestprojekt) potwierdzony. Wysoki Stoczek: „u schyłku PRL” wielka płyta, nazwa systemu UNVERIFIED. Przypisania systemu per budynek = UNVERIFIED.
- **Wysokości**: measuredHeight w manifeście = GML GUGiK 2024 (12/12 zgodne), ale ważne tylko tam, gdzie budynek jest dobrze zidentyfikowany. Nie dotyczy to 006, 008, 011, 012, 019.
- **Kolory obserwowane na obejrzanych zdjęciach** (ESTIMATED, wzrokowo):
  - bloki OWT na Białostoczku: kremowobiałe / jasnobeżowe, balkony czerwonobrązowe lub pomarańczowe, szczyty pastelowo pomarańczowe i żółtozielone (Zagumienna 40, Białostoczek 29);
  - 12-kondygnacyjne punktowce: białe z żółtymi, czerwonymi i pomarańczowymi panelami balkonowymi, mural na szczycie;
  - Tysiąclecia 6: żółtozielony;
  - Tysiąclecia 10: biały;
  - domy na Skidelskiej i Wileńskiej: szary lub biały tynk, dachy dwuspadowe brązowe.
  Te kolory nie spełniają MPZP — to stan sprzed planu.

NASTĘPNY KROK: lider wysyła M53-FIX (`docs/owner/MISTRAL-FIXES-8.md`) do Mistrala; agenci 0171 biorą tylko sekcję „Co przyjęte”.

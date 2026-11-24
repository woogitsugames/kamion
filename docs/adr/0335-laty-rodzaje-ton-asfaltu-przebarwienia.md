# ADR 0335 — Łaty asfaltu w czterech rodzajach, ton asfaltu na km, nieregularny ślad oleju, przebarwienia krawędzi

Status: propozycja (gałąź `patches2-s24`, nie scalone). Źródło: krytyk build #5 (`artifacts/critic-s24-build5/CRITIC.md`,
pkt 4: „Łaty wciąż prostokątne … asfalt jednolity na prostych odcinkach”; klatki `t2931`, `t0950`, `t3261`).

## Kontekst

ADR 0322 / 0323 dały łatom zaokrąglone narożniki, szum obrysu i zalewkę, ale nadal jeden wspólny „kształt”: prostokąt
zjedzony szumem (55 %) albo prostokąt z cięciem piłą (45 %). Prawdziwe naprawy różnią się budową i obrysem
(zdjęcia Commons DW671 `cs11749508`, `cs7403215`: długie ciemne pasy w śladach kół, jasny piasek przy krawędzi, ciemne
i jasne odcinki jezdni na przemian co kilkadziesiąt metrów). Asfalt poza łatami miał jeden ton na kilometry, smuga
oleju była równą linią w osi każdego pasa. Dodatkowo błąd w generatorze: na dwupasmowej jezdni dwukierunkowej łata
„na cały pas” (3,25 m) po odsunięciu od korony o 0,4 m wychodziła za krawężnik i była odrzucana — pełnopasowych łat
praktycznie nie było (w teście syntetycznym 4 z 80).

## Decyzja

Wszystko, co się da, w masce piksela (`WorldPBR _DECAL_PATCH`), bez nowej geometrii: ta sama siatka (kwadraty 2,5 x 2 m),
ta sama liczba trójkątów na łatę, budżet ADR 0327 nietknięty przez kształt.

1. **Rodzaj łaty w `UV1.y`** (`roads/decals.py`): `kind + 0.02 + 0.96 * ziarno`, dekodowane `floor` / `frac` w shaderze
   (przesunięcie 0,02 chroni przed przeskokiem `floor` przy interpolacji przy cięciu kafla). `UV1.y < 1`, brak i `>= 5`
   = stara maska (łaty podwórzowe `yard_wear`, stare dane).
   - 1 **frezowanie + nakładka** (pół łat „na cały pas”, 3–8 m): proste cięcia poprzeczne (szum 4 mm), brzegi podłużne
     poszarpane 2–7 cm, narożniki ścięte / wykruszone nieregularnie (r 0,06–0,35 m modulowany szumem), zalewka tylko
     wzdłuż dwóch cięć poprzecznych.
   - 2 **wykop** (druga połowa łat pełnopasowych, 20 % małych, część łat w śladzie koła): prostokąt z zaokrągleniem
     0,12–0,40 m, boki prawie proste (1–2 cm), ciągła zalewka bitumiczna po całym obwodzie 2,5–8 cm o zmiennej szerokości,
     rzadkie przerwy.
   - 3 **na gorąco** (dziury, małe 0,6–1,5 m, 80 % małych): owalna plama z dwóch oktaw szumu (nieregularne płaty),
     miękki, rozmazany rzut 4–9 cm, bez zalewki.
   - 4 **koleina** (30 % łat w śladzie koła długich 8–25 m + połowa krótkich): pas wzdłuż śladu o szerokości wędrującej
     60–115 %, ostro zakończone / poszarpane końce na pierwszych 12 % długości, miękkie boki z szumem 3–6 cm.
2. **Wiek i ton**: wiek (UV1.x) trójmodalny zamiast równomiernego: 35 % świeże, 35 % pośrednie, 30 % wyblakłe
   (`patch_age`). Ton na łatę 0,82–1,18 x, w łacie plamienie szumem 0,9 m (±7 %), świeża gładsza / stara szorstsza
   (gładkość x 1,12 .. 0,9). WORKING_VALUE.
3. **Łata pełnopasowa mieści się w pasie** (`fits_lane`): szerokość przycięta do `2 (|lat| − 0,08)` i
   `2 (hw − 0,05 − |lat|)`; pomija się test „0,4 m od korony”, który wcześniej ją wycinał.
4. **Ton asfaltu na kilometry** (`_ROADWEAR`): dwie oktawy szumu w przestrzeni obiektu (90 m i 23 m) ±9–12 % jasności
   oraz ±2 % przesunięcie ciepłe/zimne; ta sama funkcja na wstęgach, płytach skrzyżowań i łatach skrzyżowań (brak szwów);
   świeży asfalt (`paintFresh`) bez zmian.
5. **Ślad oleju** (pas środkowy `_DripBand`): wędruje ±8 % pasa, występuje na ok. 65 % drogi (odcinki 17 m), kropkowany
   (szum 0,9 m), z rzadkimi plamami 0,3–0,8 m (ciemniejsze, gładsze).
6. **Przebarwienia krawędzi** (tylko wstęgi, `w.y < 15`): w odcinkach 3–14 m ciemny osad z odpływu / spalin (do −17 %)
   albo jasny piasek (+9 %) na zewnętrznych 0,15–1,1 m.

## Konsekwencje

- Reimport shadera i przebudowa regionów z łatami (UV1.y łat zmienia się; `world_manifest` sha). Łaty pełnopasowe
  pojawiają się teraz na dwupasmowych drogach dwukierunkowych (liczba łat rośnie): patrz „Wyniki” (budżet).
- Wszystkie progi to WORKING_VALUE oceniane wzrokowo wobec Commons DW671; brak danych SOSN/DSN.

## Wyniki

(uzupełnione po pomiarach: liczby łat, trójkąty `stretch_04`, testy, render przed|po)

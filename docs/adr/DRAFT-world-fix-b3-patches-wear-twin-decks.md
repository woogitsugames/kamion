# DRAFT: łaty asfaltu, łamanie kolein, wspólna bariera bliźniaczych pomostów (world-fix-b3-s24)

Status: propozycja (numer nada lider).

## Kontekst
Build #3 (artifacts/full-build-3-s24): jasne prostokątne łaty na DW671 (zmierzone 1,47x jaśniejsze od jezdni, lin.),
ciemne regularne smugi kolein na wlotach rond DK65/Knyszyn, ostatni wolny koniec bariery w C (w173956078 R,
E -749,2 N 50,7: kapa pomostu 0,145 m < 0,30 m, jezdnia łącznicy w173956079 1,15-1,65 m dalej).

## Decyzja
1. `decal_patch` (WorldPBR `_DECAL_PATCH`, WorldPbrMaterials): zaokrąglone narożniki 0,10-0,45 m, poszarpany obrys
   (value noise w przestrzeni obiektu, 0,05-0,14 m), alpha blend (kolejka Geometry+12, po farbie, przed olejem);
   ton fresh 0,72 / aged 0,76 (było 0,88 / 1,08). WORKING_VALUE.
2. Koleiny `_ROADWEAR`: łamane szumem 1-6 m wzdłuż drogi (55-125 % dawnej siły, średnio ~0,84), na płytach skrzyżowań x0,5.
   WORKING_VALUE (ocena wobec klatki t=1530).
3. Bliźniacze pomosty ze szczeliną 1,0-2,5 m między jezdniami i kapą < 0,30 m: jedna wspólna bariera w osi szczeliny
   + betonowa płyta przykrycia szczeliny (`TWIN_SHARED_*`, furniture.py), zamiast urwanej bariery na kapie.
   Praktyka: bariera dwustronna w pasie dzielącym (EN 1317-2; GDDKiA „Wytyczne stosowania drogowych barier
   ochronnych na drogach krajowych” 2010 — punkt UNVERIFIED). Progi WORKING_VALUE.

## Konsekwencje
Wymaga reimportu wszystkich regionów (materiały decal_patch / shader) i przebudowy regionów z łatami (ton w glb).
Średnie przyciemnienie kolein spada o ~16 % na wszystkich drogach — do potwierdzenia przez visual-critic.

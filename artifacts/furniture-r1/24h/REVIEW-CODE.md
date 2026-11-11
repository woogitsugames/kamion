# Niezależny przegląd kodu — furniture r1, ADR 0120

Recenzent: subagent furniture_review, inny niż autor. Oceniono kod i próbki atlasów;
finalne rendery nie były jeszcze dostępne. Nie jest to PASS wyglądu ani budżetu.

- Krótszy niż 0,35 m odcinek omijał limit wzniosu podmurówki. Usunięto próg długości,
  zachowano bezpiecznik głębokości podziału i dodano regresję odcinka 0,30 m / 0,30 m.
- UV tyłu A-7 nie odpowiadały maskom mocowań; ponadto poprzednia propozycja
  normalizacji wychodziła poza atlas. Przyjęto wskazany przez recenzenta zakres
  poziomy 1 m oraz pionowy inset 0,6 względem wysokości używanej do obejm.
- Pozycje śladów korozji dostosowano do nowych UV. Obrzeża tarcz oraz tablice E-2
  bez tych samych mocowań otrzymały czysty fragment atlasu. Brak nowych slotów.
- Lokalny koszt siatki i dodatkowych słupków wzrasta; sam niezmieniony koszt
  prototypów lamp nie dowodzi zachowania globalnego limitu +2% tris Low.
  Ten punkt pozostaje otwarty do pomiaru wszystkich kamer.
- Jaśniejszy atlas cokołu nie dowodzi poprawnego kontaktu ani usunięcia ostrych
  krawędzi. Potrzebne są rendery cokołu z bliska i z perspektywy kierowcy.
- Recenzent nie znalazł zmian funkcji barier ani nowych slotów prototypów.

Następny przegląd: komplet arkuszy before/after, pary zdjęcie/render,
zestawienie osobnych liczników siatek i instancji Low/High, a następnie poprawki.

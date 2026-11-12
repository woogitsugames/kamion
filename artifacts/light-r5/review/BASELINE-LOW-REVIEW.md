# Przegląd świeżego baseline Low — r5

Obejrzałem wszystkie 327 ujęć: 18 kontaktówek po 109 kamer dla Clear, Overcast i Night. Źródłem jest seria baseline.20261112-114440.log, main 889201d5 po własnej regeneracji i imporcie. Kontaktówki służą przeglądowi całej trasy; nie zastępują natywnych cropów subtelnego bandingu ani pomiaru GPU.

Clear: fotograficzne chmury są widoczne na całej trasie, bez dawnego ukośnego odcięcia źródła w 2948595898752384 / 303305168125936. Przy horyzoncie pozostaje szerokie przejście w szarość. Drogi i fasady mają czytelny układ cieni; biały furgon hall4 nadal ma bardzo płaską jasną powierzchnię, mimo braku dawnego clippingu. Nie przypisuję tego automatycznie ekspozycji ani nie ruszam pigmentu lub geometrii aut. Porównanie z High ma rozstrzygnąć spójność tonu, nie rozpoznawalność D51.

Overcast: brak nagłego szwu sky–fog w przeglądzie. Niskie tony drogi i część fasad są dość ciemne i płaskie, a białe auta nadal dominują jasnością; to nie jest dopasowanie fotometrii do konkretnego zdjęcia. Szczegóły asfaltu, geometrii i roślin pozostają poza zakresem korekty światła. Nowa LUT musi być oceniona pod kątem jasnych ścian, bieli, zieleni, granicy mgły oraz kompozycji szkła.

Night: światła rzeczywiście tworzą lokalne plamy na Putry, przy remizie, pomiędzy blokami i pod wiaduktem. Nie podtrzymuję ogólnego stwierdzenia „brak plam”. Hierarchia pozostaje nierówna: miejscami szeroki jasny pierwszy plan i bardzo ciemny dystans; g3a-eye-s0262, office1, fence2, stretch-03 i doki są słabo czytelne. Okna są czarne, głowice lamp zwykle wyglądają jak wąskie jasne kreski bez fotograficznego rozproszenia. Zegary i nawigacja kabiny zachowują barwy; sama kabina jest ciemna. Nie podnosimy globalnego EV jako zastępstwa brakujących lokalnych źródeł. Tone LUT może poprawić zgodność Low/High, ale nie rozwiąże rozmieszczenia lub fizyki świateł.

Wynik: baseline kompletny do porównania, bez pełnego PASS nocy, bandingu, wszystkich odbić, ruchu lub GPU. Wstępne odrzucone serie v6 i tone-world-v1 nie są wynikiem końcowym. Natywna ocena kadrów eksperymentu i osobny przegląd High nastąpią po poprawnym zakończeniu serii świata.

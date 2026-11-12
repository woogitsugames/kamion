# Zakres planowanej r3 — przed zmianą

Nowy baseline powstaje ze złączonego main 14ccbaf1 i life-r2 C. Kadry r2 nie są bazą pomiarową r3. Najpierw obejrzeć nowy baseline z dodatkowym tyłem, kołem i rzeczywistą flotą 20/35/45 m. Przed jego ukończeniem nie zmieniać produkcji.

- Brud osobówek: zachować affine UV1 wysokości od rzeczywistego progu, rozkład 10/35/35/20, beżowo-szary osad i miękki monotoniczny zanik. Podnieść zasięg głównie za osiami i z tyłu, nie na całych drzwiach. Parametry dopiero po obrazie; żadnej nowej próbki tekstury, przebiegu ani dzielenia starego filmu. Statyczne w=2 z r2 pozostają osobnym ramieniem.
- Koła: cienkie ramiona mają pojedyncze płaskie czoło; szerokie mają już grzbiet, a beczka ma 70 mm. Rozważyć dwie fazowane powierzchnie cienkich ramion i mocniej czytelny przekrój istniejących szerokich. Zachować oponę, piastę, obrys, kolizję i grupy materiałów. Dodatkowe trójkąty będą policzone per prototyp i wszystkie kamery; brak zgody na zmianę budżetu trasy.
- Czerń: pierwszy pomiar drzwi/asfalt w clear po light r1; overcast i Pearl bez regresji. Nie zmieniać pigmentu lub globalnego światła z założenia. Jeśli potrzebna ablacja F0, tylko dane aktywnego lakieru, z osobnym dowodem.
- Wspólne materiały rim mają zastosowania poza autami. Nie przyciemniać ich globalnie. Opona już ma przypisanie tekstury i UV; zdiagnozować natywne przypisanie oraz oglądany bok zamiast dodawać duplikat mapy.

Plan nie jest wykonaniem ani akceptacją. GPU/A16, sezonowe dopasowanie brudu i unikalność wszystkich tablic pozostają UNVERIFIED. Dokładny audyt ma odrzucać niezależnie wzrost draws świata i instancji, a nie sumę znoszącą wzrost jednej kategorii.

Odczyt eksportera: crease_normals domyślnie scala normalne do 38° (globalnie, bez zmiany r3). Dotychczasowe szerokie grzbiety około 12 mm przy szerokości 38–64 mm mogą trafiać poniżej tego progu; sam grzbiet nie gwarantuje czytelnej fazy. Kandydat po baseline powinien mieć lokalny przekrój dający odrębne normalne po tym samym eksporcie; cienkie ramiona dwie powierzchnie. Zweryfikować wyeksportowane normalne i obraz, nie tylko liczbę trójkątów. To hipoteza przyczyny płaskości, nie jeszcze pomiar obrazu.

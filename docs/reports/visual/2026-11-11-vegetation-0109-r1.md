# Visual critic — vegetation r1, wariant B — 2026-11-11

Ocena niezależnego subagenta visual-critic. Ograniczona poprawka edytorowa: PASS. Ogólny realizm roślinności: FAIL. Pełna bramka urządzeniowa: niepotwierdzona.

Obejrzano wszystkie 24 arkusze after B, wszystkie 32 porównania focus PRZED/PO oraz 27 par fotograficznych obejmujących 27 różnych referencji (po jednym profilu jakości na referencję). Nie oceniano odrzuconego A. Krytyk nie uruchamiał Unity ani testów. Autor osobno obejrzał 24 arkusze kontrolne i 18 arkuszy foto-review obejmujących wszystkie 54 porównania zdjęcie/przed/po.

## Ograniczona poprawka

Trawa w route-onramp-andersa-above, r10_fence_2, driver-andersa-to-putry i g3a-rondo-bie-approach ma czytelniejszą wariację większych obszarów zieleni i przesuszenia w obu profilach i obu pogodach. Detal podłoża oraz drobne elementy High pozostają czytelne. Krytyk nie widzi spłaszczenia faktury.

Berberys w photo-biezenstwa-ground i g3a-rondo-bie-approach we wszystkich czterech warunkach ma spójniejszą górną krawędź, bez oczywistej wystającej płaskiej warstwy. To usuwa artefakt, ale nie daje fotograficznego realizmu żywopłotu.

Korony dk8-dk19-exit, driver-andersa-to-putry i route-putry-approach zachowują sylwetkę i rozkład jasności. Stała maska pikseli daje równe statystyki przed/po. Nie ma widocznej nowej regresji B; nie jest to naprawa Putry.

Wszystkie 67 kamer razy cztery warunki: delta draws 0 i delta triangles 0%. Cztery żywopłoty: 18 402 trójkąty przed/po. To dane edytora, nie pomiar czasu GPU telefonu.

Odchylenie średnich pełnych bloków 32 px grass-only wynosi przed/po: High-clear 3,18/3,50; High-overcast 2,98/3,90; Low-clear 4,42/5,48; Low-overcast 3,61/5,17. Mediana jasności wzrasta o około 18–19 jednostek sRGB. B jest też jaśniejszy i bardziej suchy; w ocenionych kadrach krytyk nie widzi przepalenia ani jednolitego żółtego trawnika.

## Otwarty backlog

P0: nie stwierdzono w ocenionym zakresie.

| Priorytet | Kadr | Problem | Kierunek |
|---|---|---|---|
| P1 | dk8-dk19-exit, boki górnej części, zwłaszcza overcast | Sosny mają grube, płaskie, odseparowane piętra koron; problem istnieje przed zmianą. | Profil skupisk igliwia i drobne gałęzie, porównanie z bliską referencją w istniejącym budżecie. |
| P1 | fire-station-ref7197, rząd przy ogrodzeniu, najmocniej Low | Tuje to regularne fasetowane wrzeciona i stożki; problem istnieje przed zmianą. | Zróżnicować obrys i skupiska gałązek oraz zacienienie Low. |
| P1 | sbs-g3-b-209622370971977, 4312632558767412, 468026894483428, 810525063224609 | Zdjęcia mają rytm drzew i wielowarstwową zieleń przy Putry, render głównie płaski pas trawy. | Uzupełnić nasadzenia ze źródeł i skalibrowanych kamer; obecne pozy nie potwierdzają przesunięć w metrach. |
| P2 | photo-biezenstwa-ground i lewy brzeg g3a-rondo-bie-approach | Berberys wciąż ciągłą burgundową bryłą o twardym boku. | Rozbić obrys i skupiska liści, bez ponownego odsłonięcia rdzenia. |
| P2 | r10_fence_2 dół, pobocza route-putry-approach | Trawa nadal płaskim dywanem; łaty słabo powiązane z użytkowaniem miejsca. | Powiązać następny etap z koszeniem, przejściem do krawężnika i źródłami; bez równomiernego szumu. |

Oceny 1–10: trawa 6; berberys 5; korony 5; sosny 3; tuje 3; skala i osadzenie 6; światło i paleta 6; materiały i mikrodetal 5; naturalność rozmieszczenia 4; artefakty statyczne 7.

Nie stwierdzono konkretnej nowej regresji B blokującej ograniczoną korektę. Ogólny FAIL wynika z otwartego backlogu. Referencje mają źródła, daty i autorów, lecz pozy pozostają UNVERIFIED. Różnic sezonu, ekspozycji i perspektywy nie przypisuje się zmianie r1. Bez telefonu i sekwencji ruchu nie zatwierdza się LOD, migotania, poppingu ani pełnej bramki urządzenia.

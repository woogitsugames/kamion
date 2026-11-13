# STATUS — gpt-s16 r2 / ADR 0154
2026-11-13T00:44:31.2008646+01:00
Gałąź gpt-s16-r2 od ukończonej i wypchniętej r1 eb718b7f8.
Merge origin/main: konflikty tylko w pięciu produktach generated/GLB; zgodnie ze zleceniem ours + pełna regeneracja. Kod scalony automatycznie, bez ręcznych edycji roads/overrides/audio/fizyki.
Gotowe do recenzji: NIE. W tle: przygotowanie baseline nowego scalonego świata.
NASTĘPNY KROK: pwsh artifacts/gpt-s16-r2/baseline-world.ps1
Dalej: import, minimum6ulicdomów i kamerykontrolne przed zmianą; następnievegetation/plantings, testy i recenzja.
R1: GIS927passed3xfailed,EditMode452passed,616par,niezależnyPASSedytora; telefonlider.
Sprzątanie: jedenworktree, kompaktowedowody, odrzuconePNG r1pozostały po blokadzie automatycznego przeglądu.
Limit całej sesji około10:34 13.11.2026.

Dodano recepty importu/renderów i generator12pozna6rzeczywistych ulicach OSM. Referencje zdjęciowe będą oznaczone jako typologiczne, bo repo dokumentuje brak zdjęć bocznych ulic regionu. Generator baseline w tle; kod produktu nadal bez r2.

Dodano audyt semantyczny świata: hashe wszystkich węzłów poza plots, identyczność rekordów instancji nie-high i tożsamości/pozycji drzew ogrodowych. To ma wykrywać uboczne zmiany po generatorze, a nie tylko liczyć przyrost trójkątów.

Zweryfikowano6lokalnych fotografii P07/P08/P10/P12/P14/P17: pełne SHA256 z istniejącym manifestem, autorzy/licencje w reference-provenance.json. Bez kopiowania oryginałów, bez URLdostępowych, bez pikseli w teksturach gry.

Przygotowano niepodłączone szkice algorytmów w artifacts: poszerzenie istniejących koron high bez nowych instancji oraz dodatkowe fronty z twardym limitem geometrii, keepoutami bram i niezmiennymi obwiedniami istniejących rendererów. Baseline ich nie importuje. Kod produktu nadal bez r2; szkice zostaną przeniesione po baseline i usunięte.

Szkice sprawdzone na niezależnej sztucznej posesji: brama otwarta, oba poziomy w tym samym materiale, niezmienione części bazowe, deterministyczne bufory, limit0blokuje dodanie, Low/las bez zmiany. To sprawdzenie algorytmu, nie dowód świata/wyglądu.

Pozy uliczne użyją scalonych po nazwie linii OSM, aby krótkie odcinki grafu między skrzyżowaniami nie ograniczały dwóch ujęć tej samej ulicy. Nadal wyłącznie rzeczywiste osie, bez przesuwania domów lub źródeł.

Świat baseline wygenerowany: 598.9563807 s, bez fallback=True. NASTĘPNY KROK: import i kamery baseline.

Baseline:597.2s bezfallback; audyt2151chronionych węzłów,32grupplots,116drzewogrodowych. Sześć ulic: Skidelska,Racławicka,Grodzieńska,Wileńska,Olsztyńska,Michała Motoszko; Brzeska/Wołkowyska nie miały dostępnych bram w zebranym planie, więc nie użyto zmyślonych póz. 12rzeczywistychpozycji +30G3.

Import baseline zakończony.

Zapisano before/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Baseline90kamer×4warunki zapisany przed zmianą produktu;458natywnych materiałów zahashowanych. Podłączono szkice do plantings/vegetation przez2addytywne hooki stage.py. Importer obsługuje garden_canopy_width wyłącznie za jawnym polem i tierhigh; nie zmienia shaderów. Dodano8przypadków EditMode, w tym zachowanie compactTRS. Sprawdzenie sztucznej posesji na prawdziwych modułach przechodzi:2segmenty,33.2m,420trisLow,bramaotwarta,deterministyczność.

# ADR 0154 — niezależna ocena wizualna B

**PASS dla konkretnej, lokalnej poprawy koron High i uzupełnienia frontowych żywopłotów.** Pasujące obrazy B pokazują większe korony ponad dachami oraz nowe nasadzenia za wybranymi płotami. Nie znalazłem nowej widocznej regresji wymagającej poprawki w tym ograniczonym zakresie.

**PARTIAL dla pełnego fotograficznego D51.** Istniejące formy drzew, nierówna gęstość zieleni, otwarte trawniki i uproszczona zabudowa nadal nie odpowiadają standardowi fotograficznej ulicy. Ta recenzja nie zamyka D51, Gate 3, testu telefonu ani przejazdu w ruchu.

Wynik dotyczy iteracji B. Wstępna ocena A była PARTIAL, ponieważ efekt na pierwszych dalekich kadrach był zbyt mały. B ma inne, dopasowane pozycje kamer oraz poprawione ustalanie wysokości względem istniejących dachów; obrazy A nie są podstawą poniższego PASS.

## Rzeczywiście obejrzane dowody

- Wszystkie **32 końcowe arkusze overviews**, po 8 dla Low-clear, Low-overcast, High-clear i High-overcast: 90 kamer na warunek, łącznie **360 par** przed/po. To przegląd pełnego zestawu na skali arkuszy, nie deklaracja odczytania każdego drobnego detalu każdej pary.
- Wszystkie **24 końcowe photo-pairs**, po 6 ulic w każdym warunku. Każdy arkusz zawiera zdjęcie typologiczne oraz dwa pasujące ujęcia przed/po.
- Większe ujęcia `inspection/b/garden_03_a-{before,after}.jpg` i `garden_04_a-{before,after}.jpg`.
- Osobne pełne pary najwyższego MAE: High-overcast `garden_04_b`, `garden_04_a`, `garden_06_b`, `garden_06_a`, `garden_03_a`, `garden_02_b`; ponadto Low-clear i Low-overcast `garden_01_a/b` dla oceny nowych żywopłotów.
- Opis źródeł i licencji w `reference-provenance.json`, audyt `world-integrity.json`, końcowe `CAMERAS.md` i struktura `camera-counts.json`. Przejrzano też źródła opisane w REVIEW-PREFLIGHT.md. Nie uruchamiałem Unity, adb, generatorów ani testów i nie zmieniałem kodu.

Referencje P07/P08/P10/P12/P14/P17 są jawnie **typologiczne, z innych lokalizacji i poz**. Nie służą do potwierdzania zgodności konkretnej ulicy, kalibracji albedo ani kopiowania liczby drzew. Ich piksele nie zostały przeze mnie skopiowane do zasobów gry.

## Co faktycznie się poprawiło

| Kamery | Zaobserwowany efekt B | Granica wniosku |
|---|---|---|
| `garden_04_a`, High-clear i High-overcast | Najbardziej czytelna poprawa: korony po lewej stronie oraz w osi ulicy wystają wyżej ponad dachy i tworzą wyraźniejszą warstwę zieleni między budynkami a niebem. | Nadal płaskie, warstwowe formy koron. Nie jest to odpowiednik zwartej, dojrzałej zieleni P12. |
| `garden_04_b`, oba High | Większy zasięg koron nad ulicą i za posesjami; obraz jest mniej pusty nad dachami. Zmiana odpowiada najwyższemu MAE, ale została oceniona wzrokowo. | Główne ogrodzenie i szerokie otwarte fragmenty posesji pozostają takie jak wcześniej. |
| `garden_03_a`, oba High oraz większe inspection/b | Korona za prawą kalenicą jest szersza i wyraźniej wystaje nad dach; dalsze korony po lewej także zyskują objętość na obrazie. | Efekt lokalny. Na dużym obrazie szczególnie widać nagie długie konary i geometryczne płaty liści. |
| `garden_02_a/b`, oba High | Drzewa za domami mają większy obrys i są lepiej czytelne ponad zabudową. Nowy kadr B `02_b` pokazuje ogród i korony znacznie użyteczniej niż pierwotny narożnik ściany w A. | Duży trawnik i przerwy w pierzei pozostają. Brak podstaw do deklaracji pełnego dopasowania do P10. |
| `garden_06_a/b`, oba High | Korony i brzoza przy brzegu kadru są większe; zieleń mocniej zaznacza działki i pionową skalę ulicy. | W `06_a` korony nadal są rozstrzelone i mają szerokie puste przerwy. |
| `garden_01_a/b`, oba Low i oba High | Wcześniej puste odcinki za przeziernym płotem otrzymują osobne, przycięte żywopłoty. Zieleń wypełnia część frontów i pozostawia widoczne przejścia; brak nowej bariery w osi jezdni. | Mały, lokalny efekt. Zabudowa wielorodzinna w kadrze nadal jest słabym odpowiednikiem typologii starej zielonej ulicy P08. |
| `garden_05_a/b` | Drobna poprawa koron nad lub za dachami i lokalny detal frontów. | Najmniej przekonujący dowód szerokiej zmiany charakteru ulicy; nie przedstawiam go jako dużej poprawy. |

W Low nie pojawia się poprawa wysokich koron, ponieważ zmieniane drzewa są High-only. Oba Low warunki pokazują lokalne uzupełnienia żywopłotów, a ogólna pustka nad częścią dachów pozostaje. Rozróżnienie profili jest widoczne i nie należy przypisywać Low efektu obserwowanego w High.

## Regresje od tej zmiany

**Nie wykryto nowego blokującego problemu w obejrzanych obrazach B.** Nie widzę nowej geometrii na jezdni, żywopłotu zamykającego wyraźnie widoczną bramę, lewitującej podstawy nasadzeń, kolorowych plam atlasu ani zmiany bliskich elementów kabiny i pojazdów. Szersze korony zmieniają kontur nieba zgodnie z celem; nie zauważyłem nowej rażącej kolizji z dachami w ocenionych ujęciach. Statyczny obraz nie dowodzi braku każdej kolizji poza kadrem.

Pozostałe kamery tras, lasu, placu, kabiny i landmarków zachowują kompozycję oraz główne obiekty przed/po. Audyt integralności jest z tym zgodny, lecz nie był użyty zamiast oglądania PNG.

## Dlaczego fotograficzne D51 pozostaje PARTIAL

1. **Parasolowe korony i poziome półki liści:** najbardziej widoczne `garden_04_a` oraz dalsze drzewa `garden_04_b`. Poszerzenie zwiększa obrys, ale nie zmienia budowy prototypu ani liczby płatów liści. Na fotografii P12 masa zieleni ma znacznie bardziej ciągły, nieregularny charakter.
2. **Długie nagie konary i odseparowane fragmenty koron:** `garden_03_a`, `garden_06_a`. Problem występuje w baseline; większa skala B czyni istniejącą formę łatwiejszą do zauważenia. Nie deklaruję, że samo skalowanie naprawiło naturalność drzewa.
3. **Nierówna gęstość i otwarty trawnik:** `garden_04_a` oraz `garden_06_a/b`, szczególnie Low, nadal mają rozległe puste pasy między jezdnią, płotem i domami. Nie wolno na tej podstawie dodawać drzew bez odniesienia do danych, ale efekt fotograficznej ulicy pozostaje niepełny.
4. **Niedoskonałe dopasowanie typologii i materiałów:** `garden_01_a/b` pokazuje większe powtarzalne elewacje, podczas gdy P08 przedstawia małą ulicę starszych domów. Uproszczone płaszczyzny domów, ciemne jednolite otwory i powtarzalne ogrodzenia są widoczne także w pozostałych kadrach. To zastany zakres, nie nowa regresja ADR 0154.
5. **Brak pomiarowej zgodności zdjęć:** inne ulice, światło i pozy wykluczają PASS zgodności z fotografią. Można zaakceptować kierunek lokalnego efektu, a nie ogłosić odtworzenie tych miejsc.

## Koszt i granice akceptacji

Końcowy raport CPU pokazuje brak wzrostu draws w obu Low warunkach i maksymalny przyrost dokładnych trójkątów **0,718622%**, przy niezmienionych liczbach instancji Low i ich trójkątów. `world-integrity.json` nie zgłasza błędów dla chronionych 2151 siatek, 125450 rekordów nie-High i 116 instancji ogrodowych. Są to pomocnicze dowody zachowania zakresu i budżetu CPU, **nie pomiar GPU ani dowód fotograficznej jakości**. W tej recenzji nie certyfikuję wyników pełnych testów uruchamianych równolegle przez autora.

PASS jest ograniczony do lokalnej poprawy koron/frontów i braku zaobserwowanego pogorszenia w statycznych renderach edytora. Telefon, ASTC, FPS, termika, migotanie liści i popping podczas jazdy pozostają niezweryfikowane. Pełne fotograficzne D51 oraz Gate 3 pozostają otwarte.

# Niezależny krytyk — przed próbą A

Krytyk vegetation_critic obejrzał zdjęcie Rakoon i dwa pełne kadry Low-overcast oraz przeczytał diff i testy. Potwierdził, że na zdjęciu są gęste, niskie nasadzenia o nierównym obrysie i drobnej strukturze, a w renderze dominują ciągłe, gładkie boki burgundowej bryły. Zdjęcie ma poruszenie i inną perspektywę, więc nie pozwala kalibrować poszczególnych liści ani prześwitów. Kandydat pozostaje niezaakceptowaną hipotezą.

Kryteria odrzucenia na 16 próbach:

- Duże otwory z widoczną trawą lub przeciwległym bokiem, szczególnie na końcach i górze; pustą skorupę należy odrzucić.
- Brak poprawy bryłowych boków, gdy zmienia się tylko jasność lub liczba kropek.
- Zaniki w Low, schodkowane otwory, jasne obwódki, odkryte trójkąty, pasy na połączeniach lub odcięta podstawa.
- Regularna kratka liści i prześwitów; stała faza rozsuwa warstwy, ale nie eliminuje powtarzalności.
- Utrata ciemnego wnętrza i kontaktu z gruntem, zbyt jasny krzew albo czarna plama w clear/overcast.
- Wzrost wywołań lub przekroczenie budżetu trójkątów. Identyczna geometria nie dowodzi równego kosztu alpha ani cieni.

Testy potwierdzają zmianę materiałów, niezmienną geometrię oraz inne rodziny żywopłotów. Nie potwierdzają prześwitów, skali UV, mipmap ani cieni. Statyczne próby nie potwierdzają braku migotania w ruchu. Bez telefonu koszt GPU pozostaje UNVERIFIED.

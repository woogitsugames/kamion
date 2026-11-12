# Przegląd wizualny r3 night1

Obejrzano 12 arkuszy 960 px: baseline i night1 dla Low/High × clear/overcast/dusk. Każdy pokazuje siedem kadrów; razem 42 kadry na etap. Obejrzano również backlight-details-Low-960.jpg, backlight-details-High-960.jpg oraz photo-night-reference-vs-render-960.jpg.

Clear i overcast: na arkuszach brak zauważalnej regresji deski, foteli, widoku kierowcy i lusterek. To ocena autora, nie niezależna akceptacja ani twierdzenie o identyczności każdego piksela. Hashe części obrazów różnią się; pomiar jednej pary Low overcast daje bardzo małe różnice w ROI przycisków i zero w kontrolnych fragmentach deski/zegarów.

Dusk: symbole przycisków są miejscowo podświetlone. Korpusy, szwy i kratki nie wyglądają na emitujące światło. Efekt na szerokich kadrach jest subtelny; izolowany render shaderowy potwierdza niezależność od ambient, dzień/off i cap. Low zachowuje miękkie drobne napisy, High jest wyraźniejszy. Nie zgłaszamy naprawy rozdzielczości drobnych oznaczeń ani zmiany nocnej palety LCD.

Fotografia Volvo pokazuje pełniejszą ciemność nocy i inną kabinę, układ panelu oraz ekspozycję. Nasz preset dusk to zmierzch, więc nie wyprowadzamy z tej pary zgodności jasności całego wnętrza ani celu liczbowego. Nie dodano odbić światła paneli na szybach ani dekoracyjnych lamp. Głębszy stan nocny świata pozostaje zależny od dziedziny światła, a pomiar GPU A16 od lidera.

Wybrano night1 do końcowej walidacji bez dalszej zmiany parametrów. Brak nowych shaderowych eksperymentów po zaliczonych 301 EditMode i porównaniu wszystkich budżetów. Pozostają pełne fidelity/GIS oraz sprzątanie wygenerowanych plików przed zamknięciem rundy.

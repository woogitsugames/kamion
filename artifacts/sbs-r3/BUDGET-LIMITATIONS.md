# Budżet wspólnej bazy r3 względem r2

Estymacje edytora, 168 wierszy: 42 kamery × Low/High × clear/overcast. Produkcyjne kamery i zdjęcia nie zmieniły się. Świat zmienił się wskutek integracji main; nie jest to izolowany koszt zmiany narzędzia SBS i nie jest to pomiar A16/GPU.

Audyt wskazał 38 z 84 wierszy Low ze wzrostem draws oraz 22 z 84 ze wzrostem liczby trójkątów przekraczającym 2% względem r2. Dla całej wspólnej bazy nie można więc zadeklarować spełnienia limitu Low +0 draws / ≤2% tris. Listy dokładnych kamera:stan znajdują się w AUDIT.json (low_draw_increases, low_triangle_increases_over_2pct), a wartości statyczne i instancje osobno w counters/camera-counters.csv.

Maksimum Low: 810 = 445 statycznych + 365 instancji. Zakres delta draws Low: −17…+29; trójkąty: 0…+10 tys. Maksimum High: 1376 = 945 + 431. Zakres delta draws High: −33…+49; trójkąty: −2…+10 tys. To wartości całego świata z tej epoki, a nie wkład konkretnej domeny.

Nie koryguję geometrii ani shaderów innych dziedzin. Własne zmiany produkcyjne SBS r3 dotyczą raportu i rejestru ocen, bez runtime i bez zmiany kamer, więc nie powodują samodzielnie kosztu renderowania. Wspólny wzrost wymaga analizy właścicieli integracji na tych samych kadrach i pomiaru telefonu przez lidera. R3 nie ogłasza PASS budżetu zintegrowanego świata.

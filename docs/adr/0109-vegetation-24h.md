# ADR 0109 — Roślinność w cyklu 24 h

## Runda r1

Stan: praca w toku, bez deklaracji PASS wyglądu ani wydajności telefonu.

Recenzja 0088 wskazała trawę bez wariacji w skali metrów, prześwietlone korony Putry, walcowate żywopłoty i uproszczone sosny. Punktem odniesienia jest aktualny main 4c9905b1, nie dawna macierz 0088.

Najpierw odtwarzamy baseline Low/High w clear/overcast. Maska B opisuje stan koszenia i suchości, a nie zinwentaryzowane uszkodzenia. Zmiana nie może tworzyć jednolitej piaskowej obwódki wokół każdego trawnika. Pola mają skalę metrów i są zakotwiczone w świecie. Zachowujemy R (odległość), G (las) i A (zmapowane odsłonięte podłoże).

Budżet Low: brak dodatkowych draw calls, trójkąty do +2 procent względem tej samej kamery. Zmiany podłoża wykorzystają istniejące maski i próbki tekstur. Szybka ścieżka lasu pozostaje aktywna. Wartości artystyczne są WORKING_VALUE; wyniki telefonu są UNVERIFIED, ponieważ telefony należą do lidera.

Dowody i kolejne kroki: artifacts/vegetation-r1/STATUS.md. Raport rundy powstanie po kontroli obrazów i testach.

# Wariant A — odrzucony po obrazie
Cztery wąskie pierścienie i32/86 bocznych kart zachowały98/224 tris na drzewo,
ale pozostawiły widoczny stożek z płaskimi klinami i trójkątnymi dziurami.
To regresja fotograficzna względem baseline, NIE kandydat do integracji.
Dowody: preview-crowns-early (8 PNG), review/preview-crowns-early (4 JPG),
wariant A GLB/spec/dims/builder/meta w variants/a, World623,9s bez fallbacków.
Audyt techniczny PASS nie stanowił oceny wyglądu. Pełny GIS nie był uruchomiony.
Waiter pierwszego pliku testów zatrzymany przed slotem i Pythonem (77232,
rodzic22324/candidate30960, tożsamość sprawdzona); rodzice zakończeni kodem1.
Nie jest to porażka pytest: plik testów jeszcze nie ruszył. Własny bilet usunięty
po potwierdzeniu braku procesu; cudzych slotów i procesów nie dotykano.
Następna próba zachowa oryginalne karty/UV i budżet alfa, a zmieni tylko
nieregularną obwiednię rdzenia bez pełnych pierścieniowych półek.

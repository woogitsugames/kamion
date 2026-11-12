Diagnostyka klina — uruchomić dopiero jeśli cztery świeże ujęcia farfield-check nadal pokazują problem.

pwsh artifacts/light-r3/run-light-batch.ps1 -Jobs artifacts/light-r3/farfield-mask.json -Gate3 artifacts/light-r3/qa-cameras.json -Mask FarField_

To istniejący VisualQaRunner -qaMask: wybrane sloty renderera rysowane magentą, zachowany depth i reszta sceny. Wrapper wymaga świeżego zwykłego PNG i maski dla każdej kamery oraz dodatniej liczby znalezionych slotów w logu. Sam fakt istnienia pliku maski nie potwierdza, że wybrano właściwy obiekt.

Jeśli klin nie jest magentowy, drugi kontrolny przebieg można wykonać dla Mask Apron, z osobnym katalogiem wyjściowym. Nie nadpisywać pierwszych dowodów. Nazwy z WorldEdgeBuilder: WorldEdge/Apron oraz WorldEdge/WorldFarField/FarField_*. To wyłącznie QA; żadnych zmian plików edge lub geometrii.

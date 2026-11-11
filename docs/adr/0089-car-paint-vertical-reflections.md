# ADR 0089: osobowki - lakier, kola i brud per instancja
Status: WIP; R1 zabrudzenie odrzucone wizualnie, R2 oczekuje renderow i recenzji.
Baza: main43bc53a7, swiezy world/PBR/import oraz kanoniczne Truck/Trailer przed porownaniem;192SHA/Fab15bez fallback.
Aktualna baza po korekcie TintA ma High-overcast drzwi38.672 i czysta maske81.017 sRGB, wiec nie dodajemy podbicia pigmentu ani dolnej granicy odbicia.
Pomiar GPU Color-property wykryl ponowne dekodowanie HDRPearl1.6/1.9/3.2 do2.812/4.104/12.922; SetLinearPearlTint koduje gamma przed SetColor, zachowujac liniowe proporcje i helperTint.
Oddzielna korektaPearl: Highov drzwi38.356/maska78.519; bez zmiany brudu, geometrii i pigmentu. Historyczne74 nie jest aktualnym celem maski.
LOD0 kola14->22segmenty z wierzcholkiem styku; LOD1pozostaje10, bez nowego pasma runtime/materialu/draw. Zmiana obejmuje istniejace25m (37.5mHigh), nie tylko<8m.
Guma i zakurzona felga neutralne szare przy zblizonej luminancji, ciemne dno zachowane; naturalne swiatlo nadal zmienia kanalowe RGB.
Osobne przezroczyste skory brudu usuniete; CARPAINT odwraca dotychczasowy dolny mnoznik car_grime i naklada film/roughness na malowana powloke, clean0 usuwa oba dawne pasy.
Cztery poziomy i faza z hasha poczatku instancji wzgledem _KamionGIRect, raz per vertex; bez nowych runtime pol/tekstur/draw. GPU RenderMeshInstanced1007instancji i18LOD/przesuniec potwierdza stabilnosc.
R1 film za slabo czytelny; diagnostyka prawdziwej sceny potwierdzila aktywne UV/maski/poziomy, hipoteza braku pasma UV odrzucona.
R2 WIP: wzgledna zmiennosc istniejacej maski fan/drop, neutralny grit.16linear, ograniczone opacity.85/top.85m, clean0 i normalna gornych paneli wykluczone; brak globalnego rozjasnienia.
Budzet R1 oryginalnych59kamer: Lowdraw-23..0, High-42..0 i brak wzrostu zaokraglonych trianglesK; estymacje edytora, koszt GPU/telefonu UNVERIFIED.
375GISpass/1knownxfail,17celowanychPASS; finalne EditMode/R2/review jeszcze wymagane.292before +4wheelbaseline;8nowychkamer R1 to AFTER-only, bez wymyslonych par.
Dowody: artifacts/car-paint-r1/STATUS.md, R1-SELF-CRITICISM.md, pearl-probe.json, pearl-only-delta.json, instanced-film-gpu-proof.json i metrics-before-vs-r1.json.

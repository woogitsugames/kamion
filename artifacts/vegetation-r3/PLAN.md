# Runda r3 — drzewa rozpoznawalności D51

Cel: przywrócić cztery korony po lewej stronie G3-B około s=120, potwierdzone lokalnym ortofoto GUGiK 2024, nie zmieniając geometrii dróg ani budynków. Zdjęcie Mapillary z 2017 r. pokazuje ten sam charakter zieleni; poza ma klasę B, nie status pomiaru.

Punkty są środkami koron odczytanymi z ortofoto, nie pomierzonymi pniami. Pozycja około ±3 m, wysokość 12,5–15 m i lipa jako model liściastego pozostają WORKING_VALUE. Źródło oraz pin ortofoto: tree-proposal.json, ortho.json. Ortofoto nie staje się teksturą gry. Planowana korekta będzie danymi w posiadanym vegetation.py; nie edytuje overrides.yaml Claude.

Przed implementacją: ukończyć baseline 25 póz B Low/High clear/overcast i test red. Nie zmieniać generatora podczas tej kolejki. Kamery kontrolne są odzyskane z r1 B po kontroli siedmiu hashy źródeł oraz 130 hashy GLB; baseline-provenance.json ujawnia ponowne użycie.

W implementacji użyć istniejących modeli i instancji. Wszystkie punkty przechodzą dotychczasową maskę blocked i teren zc; żaden punkt nie uchyla blokady. Punkty poza granicami kafla odpadają zamiast korzystać z obcięcia indeksu na brzeg. Istniejący obiekt OSM/BDOT ma pierwszeństwo w deduplikacji 1,8 m. Wysokość drzewa jest roboczym parametrem danych, nie pochodną koloru ortofoto. QA ma podać kandydatów, odrzucenia blocked, deduplikację i wynikową liczbę instancji.

Po wdrożeniu: celowane testy w heavy, generator w heavy, kontrola Megascans bez fallback, import przez slot Unity i próba kamery B/120. Jeśli wszystkie punkty są odrzucone, sprawdzić miejsce wobec maski i źródeł; nie wyłączać blokad. Następnie pełne 67 kamer plus 25 póz B, oba profile i pogody; draws +0 na Low i trójkąty do +2%. Dane geometryczne, nie rozjaśnienie palety, mają rozstrzygnąć D51. Pełny GIS i EditMode dopiero na końcu rundy.

Otwarte po tej rundzie, jeżeli nie będą potrzebne do celu: jasność Putry, sosny, tuje, krawężnikowe pobocza, Pietrasze i wariant listopadowy. Kontynuować pętlę do 2026-11-12 21:30:50 Europe/Warsaw.

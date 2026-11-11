# Roślinność — druga runda cyklu 24 h, gałąź gpt-vegetation-r3

Start 2026-11-12 około 00:08 Europe/Warsaw. Termin całej sesji bez zmian: 2026-11-12 21:30:50.

R1 przekazano do main przez robocopy: 1454 pliki, 2,564 GB, 0 failed; hash REPORT zgodny. Kod i dokumenty r1 są na gpt-vegetation-r1, bez push i bez scalenia do main. Gałąź r2 należy do wcześniejszego worktree i pozostała nietknięta.

Utworzono r3 z poprzedniej rundy i scalono main bez konfliktów: 49de5a4e. Nowe źródła świata różnią się tylko danymi SBS; kod vegetation i pozostały generator bez zmian. Skrypt slotów ma już pulę heavy także w tym worktree. Wszystkie ciężkie zadania obejmuje heavy z właścicielem gpt-vegetation-r3; każdy Unity osobno z właścicielem gpt-vegetation.

Nowy HANDOVER i recenzja D51 wskazują bloker B8 dla tej dziedziny: brak drzew po lewej stronie kadru sbs-g3-b-297817221966185. D51 nadaje rozpoznawalności pierwszeństwo przed kolorem. Zanim skorygujemy paletę Putry z planu r1, sprawdzimy ten brak w źródłach i ortofoto. Nie zmieniamy cudzych overrides.yaml, dróg, ekranów ani budynków.

Pierwszy audyt: w streetscape_sources nie ma żadnego OSM natural=tree_row i są tylko dwa natural=tree. W promieniu 150 m od kamery są dwa punkty BDOT (jeden mały las za kamerą) i dwie linie oddziałowe, bez rzędu drzew. Nie wystarczy dopisać nieużywanej obsługi tree_row, by rozwiązać tę scenę. Następny krok: ortofoto i daty referencji, kontrola aktualności widocznych drzew, potem decyzja oparta na źródłach.
Obejrzano ortofoto 2024 z manifestu ortho.json i nakładkę istniejących centrów drzew. Korony po północno-wschodniej stronie Andersa w polu widzenia B/120 istnieją na ortofoto, a generator ma tam pustkę. Fotografia ma datę 2017-07-29; obecność zieleni potwierdza nowsze źródło. Następny krok: pomiar środków koron, jawna niepewność pozycji/wysokości i test bezpiecznego osadzenia.
Baseline kontrolny odzyskano z r1 B (268 obrazów), bez ponownego renderowania: siedem hashy źródeł/kamer zgodnych, zero zmian generatora/assetów przy merge i 130 hashy GLB zgodnych. Przywrócono migawkę własnych prawidłowych metadanych B. Nie deklarujemy tych kontrolnych jako świeżych renderów. Wybrano 25 póz B i przygotowano świeży baseline zdjęciowy Low/High clear/overcast. Następny krok: render przed zmianą punktów drzew.
Zapisano pary foto before Low-clear-photo-1280x720. Następny krok: porównać z photo-references.json.
Zapisano pary foto before Low-clear-photo-2048x1152. Następny krok: porównać z photo-references.json.
Zapisano pary foto before Low-clear-photo-2048x1536. Następny krok: porównać z photo-references.json.
Zapisano pary foto before Low-overcast-photo-1280x720. Następny krok: porównać z photo-references.json.
Zapisano pary foto before Low-overcast-photo-2048x1152. Następny krok: porównać z photo-references.json.
Propozycja obejmuje cztery korony z ortofoto, z niepewnością pozycji około 3 m. Wysokość 12,5–15 m i lipa jako zastępnik liściastego są WORKING_VALUE, nie inwentaryzacją. Dodano testy obecności, blokowanej nawierzchni, deduplikacji z OSM i obcego kafla, przed implementacją. Następny krok: test red w heavy i zakończenie baseline Unity.
Zapisano pary foto before Low-overcast-photo-2048x1536. Następny krok: porównać z photo-references.json.
Zapisano pary foto before High-clear-photo-1280x720. Następny krok: porównać z photo-references.json.
Zapisano pary foto before High-clear-photo-2048x1152. Następny krok: porównać z photo-references.json.
Zapisano pary foto before High-clear-photo-2048x1536. Następny krok: porównać z photo-references.json.

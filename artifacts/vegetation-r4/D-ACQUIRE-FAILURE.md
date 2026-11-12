# Acquire D zakończone przed uruchomieniem pracy

Sekwencja 24975 zakończyła się kodem 1 około 15:12. Wrapper zgłosił Heavy acquisition failed. Szczegółowy wcześniejszy komunikat potomnego skryptu nie został zachowany w lokalnym pliku; nie przypisujemy przyczyny zmianie PHONE_RUN ani nie raportujemy błędu testów. Ostatni odczyt przed zakończeniem pokazywał 0/3 zajętych heavy, PHONE_RUN i dwa zgłoszenia przed nami.

Kontrola po zakończeniu, 15:13:23: brak pytest-green-d.log, world-candidate-d.log i pliku ukończenia; brak wykonawczego procesu D lub Pythona tej sesji; brak własnego heavy slotu oraz biletu kolejki. Odczyt procesów zawierał tylko sam proces wykonujący diagnostykę, który zakończył się wraz z poleceniem. Testy i World D nie zostały uruchomione. Nie usuwano cudzych slotów ani blokady telefonu.

Aktualny main zawiera f7d0e5a0 z 14:49:36: PHONE_RUN blokuje wyłącznie pulę Unity; ciężki Python nadal wymaga heavy i limitu trzech zadań. Poprzedni proces Acquire rozpoczęto przed tą zmianą i miał starą treść skryptu w pamięci. To wyjaśnia wcześniejsze oczekiwanie na PHONE_RUN, ale nie dowodzi przyczyny jego późniejszego błędu.

Wznawiamy jednorazowo ten sam, niezmieniony produkcyjnie wariant D z aktualnym skryptem main i zwykłą kolejką FIFO. Wrapper ma teraz pełny transcript green-d-pipeline-resume.log i odmawia startu, jeśli istnieje poprzedni log testów, World, ukończenia albo tego wznowienia. Następny błąd należy najpierw zbadać w tym logu; bez automatycznej pętli ponowień. Kontrola formalna D nadal ma 41 testów i nie ma jeszcze wyniku. Unity nadal musi czekać na PHONE_RUN.

# Przygotowanie ADR 0154 — bez zmian produktu w r1
Źródło: ADR 0132, sekcja „Samokrytyka”: korony z ortofoto stoją na właściwych miejscach, ale prototypy są cienkie i otwarte. To uzasadnia najpierw poprawę szerokości istniejących koron, zamiast masowego dodawania nowych instancji.
Baza r1: 99 posesji, 479 m istniejących żywopłotów, 117 drzew ogrodowych (116 po deduplikacji). Wszystkie pozostają tier high.
Bieżąca estymata High: stretch_04 1 981 055 tris, route_onramp_andersa_above 1 974 384; próg testów 2 000 000. Regeneracja po merge może zmienić bazę.
Pomysł do sprawdzenia na baseline: szersze korony liściaste istniejących drzew high, bez nowych modeli/instancji/trójkątów. Jeśli potrzebne, pole opt-in szerokości w danych i addytywna obsługa w importerze, bez zmian shaderów.
Shader Vegetation obsługuje normalne transformowane macierzą; billboard obraca się po dwóch osiach poziomych. Równe poszerzenie X/Z zachowuje azymut i skalę pionową. Wymaga testów i oględzin, nie jest jeszcze wdrożone.
Wysokość tylko tam, gdzie korona nie sięga nad dach; wymiary WORKING_VALUE. Gatunki jak istniejące lipa/klon/brzoza; sosny nie poszerzać automatycznie.
Żywopłoty: plantings.py, odczyt helperów z plots.py bez jego edycji. Tylko część nieobsadzonych frontów, bramy/dojścia pozostają otwarte; użyć istniejącego plot_kit i obu warstw plots/plots_low. Nie dodawać nowych materiałów lub grup chunków.
Warunek draws +0 można wesprzeć sprawdzeniem, że wszystkie nowe trójkąty należą do istniejących grup chunk/layer/material i nie rozszerzają ich obwiedni; potem rzeczywisty pomiar każdej kamery Low. Limit nowej geometrii przed pełnym generatorem.
Najbliższe ulice wg aktualnych posesji i OSM: Skidelska13, Michała Motoszko8, Racławicka5, Olsztyńska5, Grodzieńska4, Wileńska3, Łańcucka3, pozostałe1–2. Wybrać co najmniej6 ulic i dwie pozy na ulicę.
Autor ponownie obejrzał mapillary_sheet1/2: P07/P08/P12 gęste wysokie korony i zielone fronty, P14/P17 nowsza zabudowa z inną gęstością. Nie ujednolicać wszystkich działek.
Zdjęcia spoza regionu są referencją typologiczną (docs/refs/posesje-bialystok.md: brak pokrycia bocznych ulic regionu). Tak podpisać pary; nie przedstawiać ich jako zgodnych lokalizacji/poz.
W kolejnym baseline użyć kopii scalonego origin/main oraz regeneracji; nie porównywać nowego świata ze starymi renderami r1. PHONE_RUN i sloty pozostają obowiązkowe.

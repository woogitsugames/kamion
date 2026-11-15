# Errata godzin własnych recenzji — agent knyszyn

Raport utworzony: 2026-11-16T00:00:51.394679+01:00 (rzeczywisty zegar Python, Bruksela).

**Potwierdzam 10 własnych pól JSON z ręcznie wpisaną orientacyjną godziną, bez pomiaru czasu oględzin.** Wszystkie te oględziny odbyły się 15.11.2026. Dokładną godzinę należy usunąć; dotyczy to także błędnej daty 16.11 przy R150. Nie wolno zastępować jej czasem recenzji root, commitu ani NTFS.

Nie edytowano wcześniejszych plików. To lista do jawnego commitu erraty koordynatora.

| Plik względem s21 | Pole | Obecna błędna wartość | Zalecana data |
|---|---|---|---|
| `01-lampy/lit-rear-round13/peer-review.json` | `/reviewed_at_brussels` | `2026-11-15T23:43:00+01:00` | 2026-11-15; godzina niezmierzona |
| `01-lampy/retroreflection-round14/peer-review.json` | `/reviewed_at_brussels` | `2026-11-16T00:05:00+01:00` | 2026-11-15; godzina niezmierzona |
| `02-brud/europe-used-trailers-round15/peer-review.json` | `/reviewed_at_brussels` | `2026-11-15T23:39:00+01:00` | 2026-11-15; godzina niezmierzona |
| `02-brud/roadtour-original-check-round19/peer-review.json` | `/reviewed_at_brussels` | `2026-11-15T23:53:00+01:00` | 2026-11-15; godzina niezmierzona |
| `02-brud/winter-world-round17/peer-review.json` | `/reviewed_at_brussels` | `2026-11-15T23:34:00+01:00` | 2026-11-15; godzina niezmierzona |
| `04-dk65/forest-context-round8/dictionary-check.json` | `/checked_at_brussels` | `2026-11-15T23:30:00+01:00` | 2026-11-15; godzina niezmierzona |
| `04-dk65/forest-context-round8/source-review.json` | `/reviewed_at_brussels` | `2026-11-15T23:23:00+01:00` | 2026-11-15; godzina niezmierzona |
| `04-dk65/temporary-marking-round7/peer-review.json` | `/reviewed_at_brussels` | `2026-11-15T23:26:00+01:00` | 2026-11-15; godzina niezmierzona |
| `06-region-ring/monki-landmark-round7/review.json` | `/reviewed_at_brussels` | `2026-11-15T23:59:00+01:00` | 2026-11-15; godzina niezmierzona |
| `07-bialystok-dojlidy/winter-streets-round8/review.json` | `/reviewed_at_brussels` | `2026-11-15T23:49:00+01:00` | 2026-11-15; godzina niezmierzona |

Dodatkowo dwie te same orientacyjne godziny powtórzono w README: `04-dk65/forest-context-round8/README.md` (23:23) i `07-bialystok-dojlidy/winter-streets-round8/README.md` (23:49). Usunąć wyłącznie godzinę własnego odczytu, zachowując datę i jawną notę erraty.

`01-lampy/front-approval-round15/peer-review.json` pozostaje bez zmiany: `2026-11-15T23:55:02.030719+01:00` pochodzi z rzeczywistego wywołania `datetime.now(ZoneInfo(...))` podczas zapisu po oględzinach. To czas zapisu recenzji, nie początek oglądania ani data fotografii.

Przeszukano JSON całego s21, również inne formaty pól review/check/snapshot. Starsze własne recenzje bez godzin nie wymagają tej poprawki. Dat zdjęć, EXIF, publikacji, HTTP i wersji źródłowych oraz godzin innych autorów nie zmieniamy. Pełne ścieżki JSON, wartości, pochodzenie i wyłączenia znajdują się w `corrections.json`.

Od teraz dokładny czas będzie pochodził wyłącznie z odczytu narzędzia lub zegara. Jeśli moment wydarzenia nie został zmierzony, zapiszę tylko datę i brak potwierdzonej godziny.

## Zastosowana errata koordynatora

Zastosowano16.11.2026(zmierzonyczas zapisu wcorrections.json):10ręcznie wpisanych godzin zastąpiono potwierdzonądatą15.11bezpozornejprecyzji;2READMEusuwająniezmierzonegodziny. Poprzedniewartościzachowane wcentralnymraporcie jako błędne, w tymR15016.11 00:05 iMońki23:59. Niepodmieniono na godzinyroot,NTFSani commitów. Datyzdjęć/EXIF/publikacji/HTTPi zmierzonyczasActros23:55:02zostają. Errata dotyczy metrykczasu, nie cofa faktycznychoglądów/werdyktów obrazów.

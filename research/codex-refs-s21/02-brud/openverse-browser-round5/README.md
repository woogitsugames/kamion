# Openverse — publiczny frontend, obieg 5

Cel: znaleźć nowe brudne dwuskrzydłowe tyły naczep przy licencjach CC0 / CC BY / CC BY-SA, korzystając z normalnego UI, bez ponawiania wcześniejszego API403.

## Wynik

**0 obejrzanych indywidualnych fotografii, 0 pobrań, 0 nowych pojazdów i 0 kwalifikowanych kadrów** (liczniki dziennika screening.json). Manifest ma wyłącznie nagłówek; nie tworzy się pozornych referencji fotograficznych dla strony błędu.

[Strona główna Openverse](https://openverse.org/) działała. Pierwsze zapytanie „dirty semi-trailer rear doors” pokazało brak wyników. Następnie zaznaczono checkboxy Zero, Attribution i Attribution-Share-Alike: UI pokazywał Filters (3), a URL zawierał `license=cc0,by,by-sa`. Innych licencji nie zaznaczono.

Po wyszukaniu [muddy trailer back z tym filtrem](https://openverse.org/search?q=muddy+trailer+back&license=cc0,by,by-sa) ekran ładowania przeszedł w wewnętrzną stronę błędu. Adres dotyczył nowego zapytania, lecz komunikat odwoływał się do poprzedniego „dirty semi-trailer rear doors”. Nie traktuje się tego jako wiarygodnie ukończonego wyszukiwania ani dowodu nieistnienia odpowiednich fotografii. Status HTTP **UNVERIFIED** — nie potwierdzono403 lub429.

Na tym zakończono obieg: bez reload, iterowania wariantów, odpytywania API, logowania i CAPTCHA. Nie otwierano linków zewnętrznych zaproponowanych przez stronę błędu. Żadnego obrazu nie opisano z tytułu lub siatki. CUA zakończono completion_summary, Chrome zwolniony; źródła wcześniejszych obiegów pozostają stabilne.

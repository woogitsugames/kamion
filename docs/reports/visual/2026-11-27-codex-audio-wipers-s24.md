# Wycieraczki TRAKT w DrivingLab

2026-11-27 · PC High · 960 × 444 · clear i overcast · PASS dla badanych kadrów.

Porównano bazę z zaparkowanymi piórami, końcową pozycję nawrotu w obu
warunkach oświetlenia i połowę suwu w clear. Użyto kamer `cab-driver`
i `truck-front`. Po korekcie kierunku obrotu skrócono lewy łuk z 95° do 72°,
aby zachować odstęp od słupka A. Prawy łuk ma 95°. [ADR 0355](../../adr/0355-wycieraczki-i-pisk-hamulca-serwisowego.md)

Niezależny `visual-critic` obejrzał arkusze i pełne PNG. W obu wariantach
oświetlenia pióra pozostają w obrysie szyby przy nawrocie. W połowie suwu ich
sylwetki się nie nakładają. W badanych kadrach przejrzystość i odbicia poza
piórami wyglądają jak w bazie. Ocena dotyczy sprawdzonych faz statycznych.

| Kamera | Szacowane draw calle przed → po | Trójkąty w estymacie przed → po |
|---|---:|---:|
| `cab-driver` | 236 → 236 | 177 455 → 177 455 |
| `truck-front` | 106 → 106 | 299 018 → 299 018 |

Estymaty pochodzą z `stats.txt` Visual QA przed grupowaniem SRP. W katalogu
`artifacts/codex-audio-wipers-s24` są `compare-clear.png`, `compare-overcast.png`,
`compare-midstroke.png` oraz źródłowe PNG i statystyki z obu rund.

# Przegląd RESEARCH-PACK-02 (s16, 2026-11-13) — NIEPEŁNY, PRZERWANY PRZEZ LIMIT

Status: **przegląd nie został wykonany merytorycznie.** Na polecenie koordynatora (limit 5 h) zapisano tylko to, co zrobiono do tej pory: rozpakowanie i inwentaryzację plików. Żadna paczka nie ma jeszcze werdyktu, nie wykonano próby prawdziwości, kontroli licencji ani porównania z `research/g5-*`, `g7-*`, `g10-*`, `research/gptpro/*`. Nic nie przyjęto do `research/gptpro/`. Nic nie commitowano. Nie uruchamiano Unity ani skryptów z ZIP.

## 1. Co zrobiono

ZIP-y z `C:\Users\matma\Downloads\` rozpakowane (`unzip`, bez uruchamiania czegokolwiek) do osobnych katalogów `research/_incoming/<nazwa>/`. W żadnej paczce nie ma plików `.py/.sh/.js/.bat/.exe`.

**`research/_incoming/` ZOSTAWIONY** (nie usunięty), do dokończenia przeglądu w kolejnej sesji. Katalog nie jest śledzony przez git (nie dodawać do commita).

| Paczka | Katalog w `_incoming` | Plików | Rozmiar | Zawartość (tylko inwentarz) | Werdykt |
|---|---|---|---|---|---|
| P2 nawierzchnie | `p2-surfaces` | 41 | 16 MB | README, manifest, sources, audit_20_percent.json, 33 JPG (P2-001..033), 4 PDF (P2-034..037) | NIEPRZEJRZANA |
| P3 zabudowa | `p3-building-typology` | 67 | 17 MB | j.w., 62 JPG (P3-001..062), `docs/mpzp_bialostoczek_uchwala.pdf` | NIEPRZEJRZANA |
| P5 audio 2 | `p5-audio-refs-2` | 56 | 74 MB | j.w. plus `download_list.csv`; 1 WAV, ok. 40 MP3, 5 OGG, 1 OPUS | NIEPRZEJRZANA |
| P6 regiony 2 | `p6-next-regions-2` | 34 | 7 MB | j.w., JPG (G01–G14, U01-a..h), PDF (U01, U04), tekstowe `P6-K00-kafle.txt`, `P6-R00-trasy.json/.txt`, `P6-C00/G00-osm.txt` | NIEPRZEJRZANA |
| P8 ograniczenia 2 | `p8-truck-restrictions-2` | 10 | 7,6 MB | 6 PDF (P8-012, 014, 015, 016, 017, 025); **uwaga: ZIP ma dodatkowy katalog nadrzędny `gptpro-p8-truck-restrictions-2/`** (reszta paczek nie) | NIEPRZEJRZANA |
| P9 meble 2 | `p9-street-furniture-2` | 18 | 7,7 MB | 6 PDF, 1 DOCX (P9-007), 6 JPG (P9-301..306), `P9-401.csv` | NIEPRZEJRZANA |
| P10 zieleń 2 | `p10-street-greenery-2` | 17 | 5,1 MB | 13 JPG (P10-101..114, bez 108) | NIEPRZEJRZANA |

Spostrzeżenia formalne z samego inwentarza (do potwierdzenia):
- Wszystkie paczki mają README.md, manifest.csv, sources.md, audit_20_percent.json (zgodnie z zasadami D–F paczki 02). Zdjęcia są JPG, nie PNG (brak problemu LFS dla obrazów).
- P5: pliki audio, w tym `*.ogg` (LFS wg `.gitattributes`); `*.wav` także LFS. Zgodnie ze zleceniem do gita tylko metadane (manifest, README, sources, download_list.csv), pliki audio lokalnie poza gitem.
- P8, P9, P2, P3, P6: PDF-y mają trafić do repo tylko jeśli są dokumentami urzędowymi (art. 4 pr. aut.) i ≤ 5 MB; nie sprawdzano.
- P9-007 to DOCX: sprawdzić pochodzenie i licencję przed przyjęciem.
- P8: numeracja plików niecią­gła (P8-012…025), P10 bez P10-108: sprawdzić w manifeście, czy to pozycje link-only.

## 2. Do zrobienia w kolejnej sesji (kolejność)

Dla każdej paczki z `research/_incoming/<nazwa>/`:
1. Przeczytać README.md, manifest.csv (kodowanie `utf-8-sig`), sources.md, audit_20_percent.json. Zgodność plików z manifestem.
2. Licencje: kolumna `licencja`; odrzucić NC/ND/Google/bez licencji; Mapillary CC BY-SA tylko odczyt treści; sprawdzić rozmiary PDF > 5 MB.
3. Próba prawdziwości ≥ 20 % (WebFetch, OSM; seed podać w raporcie; Python tylko z `-I`).
4. Porównanie z `research/g5-street-furniture`, `g7-street-greenery`, `g10-truck-restrictions`, `research/gptpro/{2-next-regions,3-s8-signs,9-audio-refs}` (co nowego, co koliduje).
5. Przyjęte → `research/gptpro/<pN-slug>/` (bez odrzuconych; audio tylko metadane).
6. Na końcu usunąć `research/_incoming/` (uwaga na junctiony? nie dotyczy, to zwykłe katalogi).

Priorytet pod aktywnych agentów: P6 (0166 Dojlidy/Krywlany: kafle `P6-K00-kafle.txt`, trasy `P6-R00-trasy.json`), P9 (0162 meble: `P9-401.csv` — prawdopodobnie przystanki ze współrzędnymi), P10 (0163 zieleń), potem P8, P2, P3, P5.

## 3. Przekaż agentom (0162, 0163, 0166)

Brak ustaleń: przegląd merytoryczny nie został wykonany, więc nie przekazuję żadnych liczb ani faktów (nie zgaduję). Wskazówki wyłącznie lokalizacyjne, do własnej weryfikacji agenta po przeglądzie: 0166 → `research/_incoming/p6-next-regions-2/files/P6-K00-kafle.txt`, `P6-R00-trasy.json`; 0162 → `.../p9-street-furniture-2/files/P9-401.csv`; 0163 → `.../p10-street-greenery-2/manifest.csv`. Wszystko UNVERIFIED do czasu przeglądu.

## 4. Braki do kolejnej paczki

Nieoddane (bez zmian): P1 (zdjęcia trasy), P4 (przepisy ciężarówki), P7 (tablice, uzupełnienie G3). Braki w oddanych paczkach: do ustalenia po przeglądzie.

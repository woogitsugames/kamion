# Prompt dla sesji Claude Code w chmurze (Fable, do 5 agentów, tylko GitHub) — s20

Wklej całość poniżej w tamtą sesję. Te zadania NIE idą już do Mistrala (M58, M60, M65, M66, M68) — Mistralowi zostają FIXES-10/11/12 i bloki z `MISTRAL-DOKONCZ-S20.md` (M57, M59, M61, M63, M52-FIX-4) oraz później M64, M67, M69.

```
Pracujesz w repo GitHub woogitsugames/kamion (Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1; Unity, ale Ty NIE masz Unity, telefonów ani lokalnych danych Data/raw — tylko git/GitHub i internet). Twoja rola: zespół badawczy (do 5 subagentów naraz, model Fable), który dostarcza dane referencyjne dla agentów budujących świat. Nie zmieniasz kodu gry ani danych regionów.

NAJPIERW przeczytaj w repo (origin/main): CLAUDE.md, docs/owner/AGENT-RULES.md (p. 5–6: źródła i zakaz zmyślania), docs/06 (anti-slop), docs/owner/MISTRAL-TASKS-9.md (bloki M58 i M60), docs/owner/MISTRAL-TASKS-10.md (bloki M65, M66, M68 + część wspólna na górze pliku), oraz jako wzór oczekiwanego poziomu i typowych błędów recenzje: docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md, docs/reports/REVIEW-2026-11-14-s20-mistral-m56.md, docs/reports/REVIEW-2026-11-13-s20-mistral-m47-fix2.md. Te recenzje pokazują, za co odrzucamy pracę: opisy kadrów niezgodne z obrazem, oznaczanie SOURCED bez źródła, kierunki magnetyczne zamiast prawdziwych, samokontrola bez ponownego obejrzenia obrazów, za mało kadrów obiektu.

ZADANIA (jeden subagent na zadanie, równolegle; każdy we własnej gałęzi od najnowszego origin/main):
1. M58 — Dojlidy/Krywlany: słupki z łańcuchem, ogrodzenia, oznakowanie pasa widoczne z drogi → gałąź research/cloud-p15-dojlidy-details, katalog research/cloud/p15-dojlidy-details/
2. M60 — zmierzch w mieście: niebo, luminancja, oświetlenie ulic trasy, zapalone okna → research/cloud-p17-dusk-lighting, katalog research/cloud/p17-dusk-lighting/ (uwaga: gra ma już plamy latarni i okna nocą — ADR 0191/0192 w docs/adr; dane mają posłużyć do kalibracji, wskaż konkretne liczby do porównania)
3. M65 — drogi dla rowerów z czerwonego asfaltu (trasa C i Dojlidy: way_id, szerokości, przejazdy) → research/cloud-p22-red-bike-paths, katalog research/cloud/p22-red-bike-paths/
4. M66 — sygnalizatory w Białymstoku: tarcze, komory, daszki, warianty → research/cloud-p23-traffic-signals, katalog research/cloud/p23-traffic-signals/
5. M68 — ściana lasu przy Krywlanach: sylwetka, krawędź, podszyt, gatunki → research/cloud-p25-krywlany-forest, katalog research/cloud/p25-krywlany-forest/
Treść, kryteria akceptacji, kolumny manifestu i struktura wyniku — DOKŁADNIE jak w odpowiednim bloku M5x/M6x, tylko z prefiksem „cloud” zamiast „mistral” w gałęzi i katalogu oraz id wierszy C58-NNN, C60-NNN, C65-NNN, C66-NNN, C68-NNN.

ZASADY TWARDE:
- Źródła wyłącznie otwarte (D43): OSM (Overpass API — zapisz zapytanie i datę), GUGiK (ortofoto/NMT/LoD przez publiczne WMS/WMTS/usługi), Wikimedia Commons, Openverse (CC0/CC BY/CC BY-SA), Panoramax, KartaView, Mapillary (tylko jeśli masz własny token — nigdy go nie zapisuj), Dz.U./ISAP, otwarte dane Białegostoku, BIP. ZAKAZ: Google Maps / Street View / Earth / 3D Tiles (także pośrednio), Bing, Apple, Yandex.
- Każdy opis kadru = to, co WIDAĆ na obrazie, który faktycznie obejrzałeś (pobierz, pomniejsz do ≤ 960 px, a znaki/detale oglądaj w wycinku 3× z pełnej rozdzielczości). Czego nie widać — UNVERIFIED. Żadnych liczb bez źródła lub pomiaru (wtedy ESTIMATED + metoda). Kierunek kadru = azymut geograficzny (z API źródła albo z geometrii), nie magnetyczny EXIF.
- Ten sam plik (md5) = jeden wiersz albo identyczny opis; zaznacz duplikaty.
- Samokontrola 20 % z jawnym seedem: PONOWNE obejrzenie obrazów wylosowanych wierszy i porównanie z opisem; zapisz w audit_20_percent.json, co poprawiłeś.
- Bez marek i logo w opisach przeznaczonych do gry (piszesz „zakład”, „sieć sklepów”).
- ZDJĘCIA NIE DO GITA (pliki obrazów i ZIP-y — .gitignore w katalogu). Zamiast ZIP-a: w manifeście bezpośredni URL pliku (do oryginału, nie miniatury), licencja, autor, sha256 pobranego pliku, oraz skrypt fetch.py w katalogu zadania, który pobiera wszystkie pliki z manifestu do files/ i weryfikuje sha256 (lider uruchomi go lokalnie).
- Zmieniaj wyłącznie swój katalog research/cloud/<zadanie>/. Nie ruszaj main, kodu, docs/ poza swoim katalogiem.

ZAPIS CIĄGŁY (sesja może zostać przerwana w każdej chwili): po każdym kroku commit + push na gałąź zadania, a w katalogu plik STATUS.md (co zrobione, liczby, NASTĘPNY KROK).

NA KOŃCU każdego zadania: ostatni commit + push, otwórz PR do main (tytuł „research(cloud): M58 …” itd.; w opisie: liczba wierszy, liczba obejrzanych kadrów, wynik samokontroli, luki, ile plików do pobrania przez fetch.py i ich łączny rozmiar; zakończ „🤖 Generated with [Claude Code](https://claude.com/claude-code)”). NIE scalaj PR — scala lider po recenzji. Gdy wszystkie 5 PR są otwarte, napisz krótkie podsumowanie: numery PR, gałęzie, co niekompletne.
```

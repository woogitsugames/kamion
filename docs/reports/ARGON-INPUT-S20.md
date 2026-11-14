# Dane wejściowe dla Argona (lider s20, 14.11 wieczór) — CZYTAJ przed kolejną rundą 0188 i 0193

Research chmury scalony do main (`git merge origin/main` w worktree): research/cloud/p22-red-bike-paths (M65), research/cloud/p23-traffic-signals (M66). Szczegóły i listy dróg/węzłów: docs/reports/REVIEW-2026-11-14-s20-cloud-m65.md, -m66.md.

## 0188 (DDR) — poprawki do gałęzi ddr-0188 (stan c77df2c86)
- NIE czerwone pole na każdym przejeździe: skrzyżowanie z P11-063 i rondo Putry mają przejazdy tylko BIAŁE (P-11).
- Dojlidy: DDR ciepło-szara, nie czerwona (także na P11-001).
- Czerwonobrązowe DDR tylko w rejonie ronda Putry (9 dróg) — osobny, mocniejszy materiał.
- Listy dróg/węzłów, strona DDR względem jezdni, szerokości 2,45–2,8 m: w REVIEW-…-cloud-m65.md.

## 0193 (sygnalizatory) — poprawki do gałęzi sigplate-0193 (stan ff4909ba7)
- Tarcza tylko na głowicach NAD JEZDNIĄ (nie na słupkach przy krawędzi ani dla pieszych).
- Tarcza 0,85 × 1,40 m (Dz.U. rys. 10.28), biała obwódka 40 mm, margines 20 mm (zamiast ~0,56 × 1,30 i żółtawej).
- Tarcza ZA obudową, nie przed nią.
- Daszek ≥ 0,20 m (ok. 0,22) zamiast 0,17.

## 0187 (las) — dane M68 w przeglądzie (docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md, gdy gotowe).
## 0189 (brama szpitala) — dane M62 scalone (research/mistral/p19-hospital-gate, errata w README).

## 0187 (las) — dane M68 scalone (research/cloud/p25-krywlany-forest; szczegóły docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md)
- PTLZ `12617d4f-…` (BDOT liściasty) wg BDL ~70 % sosny; PTLZ `1ac1a146-…` „zagajnik” ma drzewa 85–99 lat, H 27–29 m → oba `forest_stand` z `mix` i `height_m`; pas młodnika 5–10 m od ulicy zostaje.
- Sosna 24–29 m (CHM p50 26 / p90 29, max 33) — domyślne pine 14–24 m za niskie ~5 m; emergenty share 0,03 @ 29–32 m (WORKING_VALUE).
- Skład kafla: sosna 64 %, brzoza 26 %, olsza 4 %, dąb 4 %, świerk 2 % (gra 0,14–0,20 świerka — za dużo). UNDERSTOREY: shrub 0,55, spruce 0,15, pineyoung 0 (leszczyna, kruszyna; pokrycie 0,9–1,0).
- Pełna wysokość ściany po ~5 m od okapu; płaszcz krzewów tylko na ~7 % (Mickiewicza) / 19 % (lotnisko) długości — nie na każdej ścianie. Pnie widoczne na ~połowie ściany. Sylwetka ±2–2,5 m, wierzchołki co 8–14 m.
- tree_stand NMPT 2023: ROD 4–10 m (pokr. 0,43–0,45), wood-NW 8–19 m (0,58), skatepark 5–11 m (0,28) — sprawdź na P11-056 przed zmianą gęstości.

# ADR XXXX — noc na PC: reflektory mijania wg UN R112 kl. B, 16 pul latarni, highlight na tierach PC
Status: Proposed (agent night-pc-s23, rendering-perf, gałąź `night-pc-s23`), 2026-11-16. Numer nada lider.
Powiązane: ADR 0062 / 0191 (pule), 0199 (kalibracja zmierzchu), 0216 (LED), 0108 r2 (eksperymentalny rzut reflektorów),
0269 (tiery PC), D73 (Windows główną platformą). ADR 0197 (światła pojazdu) nie istnieje w main — PR #79 `lights-0197`
nie scalony; ta zmiana nie dotyka `TruckLights` ani assetów pojazdu.

## Kontekst (render BEFORE, PC High/Low, `-Pc`, WorldC + World_knyszyn, dusk/night, `-TruckLamps low`)
1. **Reflektory nie oświetlały drogi** w żadnym tierze: `projectedHeadlamps = 0` we wszystkich presetach LP_* (ADR 0108 r2
   zostawił to jako eksperyment), Unity Lights pojazdu brak. Z kabiny na nieoświetlonej DK65 (Knyszyn) jezdnia przed
   ciężarówką była czarna — świeciły tylko soczewki.
2. Stary kształt wiązki (ADR 0108 r2) był symetrycznym stożkiem z odcięciem na −0,002 (prawie poziomo, bez pochylenia
   pojazdu) — bez asymetrii prawego pobocza, w odróżnieniu od znaków (`FurnitureSignForward.hlsl`: 15° upsweep).
3. PC High miał 8 pul (tablica shadera = 8): latarnie dalej niż ~8 najbliższych od punktu 30 m przed kamerą nie dawały
   plamy. PC Low 6 pul. Latarnie na Low w obecnym main świecą (soczewka + pule + podłoga nocna) — w kadrach BEFORE PC Low
   pule są widoczne; nie odtworzyłem „niewidocznych latarni na Low” (dotyczyło zapewne mobilnego Low z 4 pulami).
4. Okna, niebo i ekspozycja nocy (ADR 0199) — w kadrach bez błędów kierunku (brak teal-orange, bez przepaleń: clip ≤ 0,11 %
   kadru); presety są wspólne z telefonem i pilnowane testami → bez zmian (patrz Otwarte).

## Decyzja
1. **Wiązka mijania** (`KamionLampPools.hlsl` `KamionHeadlampRelI` + bliźniak C# `Rendering/Runtime/Sky/HeadlampBeam.cs`):
   ruch prawostronny, kąty jako tangensy w układzie kabiny. Odcięcie poziome `KAMION_BEAM_AIM` = 1,5 % poniżej horyzontu
   (WORKING_VALUE; zakres pochylenia z UN R48 6.2.6.1.1 dla h > 1 m — UNVERIFIED, nie pobrano tekstu), na prawo od
   kolana wznosi się pod 15° do +1,57° nad kolano. I/Ipk = H(h)·V(pod odcięciem) albo poświata 1,2 % nad odcięciem.
   Kształt dopasowany do tabeli **UN R112, załącznik 3, kolumna klasy B** (`mlit.go.jp/jidosha/un/UN_R112.pdf`, s. 23,
   SOURCED): 75R, 50R ≥ 10 100 cd; 50V ≥ 5 100; 25L/25R ≥ 1 700; strefa IV ≥ 2 500; 50L ≤ 13 200; 75L ≤ 10 600;
   B50L ≤ 350; BR ≤ 1 750; strefa III ≤ 625. Wynik przy Ipk = 20 000 cd (`projectedHeadlampPeakCd`, WORKING_VALUE):
   75R 19 626, 50R 17 039, 50V 19 189, 25L 2 865, 25R 1 840, 50L 10 465, 75L 3 684, B50L 94, BR 152, strefa IV min 5 170,
   strefa III max 187 cd — wszystkie punkty w granicach (test EditMode). Zasięg do 150 m (dawniej 90 m). Bez przesłaniania.
   Oświetlenie drogi z lampy na 1,1 m: 5 m 9 lx, 10 m 2,9 lx, 20 m 1,05 lx, 30 m 0,47 lx, 50 m 0,14 lx (E = I·cos/d²).
2. **Highlight GGX reflektorów** w `KamionLampPoolsLit` (ta sama normalizacja co pule) za flagą tieru `lampPoolSpecular`
   (`_KamionLampSpec`, teraz wysyłany zawsze — także na drogach bez latarni). Na mokrym (`rq_wet=1`, mokro nadal poza
   produkcją, ADR 0108 r3) jezdnia w wiązce ciemnieje, a pule latarni dają smugi w stronę widza — zgodnie z fizyką.
3. **Tiery PC** — nowy `Rendering/Runtime/PcNightLighting.cs` (osobna tabela, by nie kolidować z polami cieni/AA/roślinności
   w `PcTierTable`), wołany jedną linią na końcu `PcGraphicsTiers.Overlay`:

   | PC tier | pule | highlight | reflektory na świecie |
   |---|---|---|---|
   | Low | 8 (było 6) | nie | tak |
   | Medium | 12 (było 8) | tak (było nie) | tak |
   | High | 16 (było 8) | tak | tak |
   | Ultra | 16 (było 8) | tak | tak |

   Nowe pole `QualityProfile.Tier.projectedHeadlamps` (domyślnie false → telefony bez zmian, asset bez migracji);
   `WorldAtmosphere.Push`: `HeadlampsOverride ?? (preset.projectedHeadlamps || tier.projectedHeadlamps)`.
   `StreetLamps.MaxPools` 8 → 16 (tablice shadera 16; pętla kończy się na `_KamionLampCount`, więc telefon liczy 4–8 jak
   dotąd), `PoolFocusAhead(n)` = 30 m × max(1, n/8) — przy 16 pulach punkt wyboru 60 m przed kamerą (dodatkowe latarnie
   wydłużają oświetloną drogę przed pojazdem, nie za nim). `PcTierTable.lampPools` nadpisane (lider: złożyć po scaleniu
   obu gałęzi). Żadnych nowych Unity Lights, przebiegów, tekstur ani słów kluczowych.
4. **visual-qa `-Pc`** (ADR 0269 propozycja 2, commit `7d7d2f1f4`): `-qaPcTiers 1` → `PcGraphicsTiers.ForceEnabled`,
   asset `URP_PC_<tier>` i `Overlay` tieru; stan edytora przywracany w `finally`. Log: `[VISUALQA] PC tier High: pipeline URP_PC_High`.

## Czego NIE zrobiono (świadomie)
- **Cienie z latarni** (spot shadows): shadery świata (WorldSurface/WorldPBR) nie czytają Unity Lights (ADR 0062), więc
  cień padałby tylko na pojazdy i rekwizyty, a additional-light shadows to cecha assetu URP spoza assetów mobilnych
  (ryzyko strippingu wariantów, ADR 0269). Nieopłacalne bez zmiany pass świata — poza zakresem.
- Presety LP_Dusk/LP_Night, `NightWindows`, `TruckLights` (MarkerNits, świateł pozycyjnych naczepy) — wspólne z
  telefonem / poza `Rendering/**`; kadry `lamp-trailer`, `truck-rear34` pokazują boczne pomarańczowe i tylne czerwone
  obrysówki czytelne nocą (bez zmian w tej gałęzi).

## Budżet
- Draws / shadow draws / tris (`stats.txt`, WorldC High night): identyczne przed i po (np. cab-driver 673 / 788 / 857 977).
- Pamięć: +2 × 8 float4 w globalnych tablicach (256 B). Warianty shaderów: 0 nowych.
- ALU (szacunek): reflektory ~2 × (3 exp + ~30 ALU) na piksel świata, gdy mijania włączone; pule +8 iteracji na PC High.
- **Czas klatki: niezmierzony w playerze.** Edytor (RTX 5070, 1080p, MSAA 4×, 300 renderów/kamera, 2 powtórzenia
  `timing2/`): cab-driver all 10,74 / 9,95 ms, bez wiązki 10,66 / 9,98, pule 8 12,08 / 8,86, nic 14,87 / 9,50 ms — rozrzut
  między powtórzeniami (±3 ms) większy niż jakakolwiek różnica; edytor nie rozstrzyga kosztu. Do pomiaru:
  `pc-metrics.ps1` High noc, A/B `-ExtraPlayerArgs` z `rq_headlamps=0,rq_lamppools=8` (lider, slot heavy).

## Walidacja
- Rendery (`artifacts/night-pc-s23/`): `before/`, `after1/` (2 sceny × PC High/Low × dusk/night × 8 kamer = 64+64 PNG),
  `after1-wet/` (High night, `rq_wet=1`), zestawienia `view/` (góra przed, dół po), `view-wet/` (sucho/mokro), `lum-before-after1.txt`.
  Obejrzane: knyszyn High/Low night cab-driver (wiązka na DK65, widoczne kolano odcięcia 15° na barierze), dk65-inlet-south,
  rynek-grodzienska-north (dalsze pule); WorldC High night cab-driver (plama wiązki do ~40 m), driver-andersa (sucho/mokro).
- Liczby (luma pasa dolnego, p50): knyszyn High night cab-driver 9,1 → 11,0, dk65-inlet-south 10,1 → 13,8; WorldC High
  night cab-driver p90 32,0 → 37,1; zmierzch ±0–1,4; przepalenia bez zmian (≤ 0,11 %).
- EditMode (`artifacts/night-pc-s23/editmode-20261116-192935.xml`): 1132, 1109 pass, 22 fail, 1 skip. `PcNightLightingTests`
  14/14 (punkty R112, strefy III/IV, asymetria, tiery, Overlay, stałe HLSL = C#); HeadlampProjection 9/9, StreetLampOptics
  10/10, NightIntegration 6/6, DuskCalibration 6/6, NightWindow 7/7, PcGraphicsTier 14/14, FurnitureSign 16/16. Porażki poza
  diffem: `CarPaintMaterialTests.DepositionChannel_*` (2, znane z ADR 0199/0216) i
  `StartClearanceTests.ImportedScene_BakedSpawnIsTheImportersStart` (20 regionów: sceny `_Generated` skopiowane z main mają
  spawn 12 m, importer po ADR 0277 chce 90 m — wymaga reimportu regionów, nie dotyczy oświetlenia).

## Otwarte
1. Ekspozycja nocy jest stała (dobrana pod ulice z latarniami, ADR 0199): na nieoświetlonej drodze obraz jest bardzo
   ciemny, a wiązka czyta się słabiej niż oczami kierowcy. Propozycja: adaptacja ekspozycji do luminancji kadru tylko na PC
   (nowy ADR, decyzja właściciela — to zmiana „wyglądu”).
2. Pochylenie 1,5 % i Ipk 20 000 cd — WORKING_VALUE; wysokość kotwic `LIGHT_LowBeam_*` z modelu.
3. Brak przesłaniania wiązki (np. przez pojazd z przodu) — przy ruchu ulicznym będzie potrzebne.
4. Pomiar w playerze Windows (p50/p95/p99) i ocena krytyka wizualnego.

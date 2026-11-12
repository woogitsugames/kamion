# ADR 0156 — ElevenLabs REGEN-04: kabina bez obciążenia 900–1500 obr/min
Status: Proposed (agent audio, s16), 2026-11-12. Ocena brzmienia: właściciel (telefon, głośnik i słuchawki).

## Kontekst
ADR 0148 (pkt 6): w zestawie ElevenLabs komórki **kabina / bez obciążenia 1200 i 1500 obr/min** (źródło
`ENG_CAB_OFF_1800 (3)`, przestrojone ×0,985 / ×1,232) mają słabą linię zapłonu, 7,5–7,7 dB nad tłem. Dla porównania
zewnątrz bez obciążenia ma 21–25 dB, a kabina pod obciążeniem 11–19 dB. Toczenie na biegu i hamowanie silnikiem przy
1000–1500 obr/min brzmi w kabinie jak szum bez tonu. Silnik ElevenLabs zostaje bez zmian (decyzja właściciela,
ADR 0142), dlatego właściciel wygenerował partię `docs/owner/ELEVENLABS-REGEN-04.md` (22:45–22:48, v3, 12 s, wpływ 80 %,
po 4 warianty): `ENG_CAB_OVERRUN_SWEEP (1)–(4)` (zjazd obrotów bez gazu) i `ENG_CAB_IDLE_STEADY (1)–(4)` (równy jałowy).

## Analiza 8 ujęć
Narzędzie `tools/audio/el_regen04.py analyse` → `artifacts/audio-regen04/analysis/` (`regen04.json/csv`, arkusze
`ENG_CAB_OVERRUN_SWEEP.png`, `ENG_CAB_IDLE_STEADY.png`). Ślad: Viterbi drabiny harmonicznych (`el_regen01.salience_track`),
obr/min = linia × 20 (zapłony R6, konwencja ADR 0137). Plateau: okno ≥ 2 s, w którym ślad trzyma się ±5 % mediany.
Linia = wyrazistość linii nad medianą ±25 Hz widma Welcha. YIN = okres / linia (0,5 = słychać oktawę niżej, ADR 0138).
Trzaski = energia > 4 kHz w oknach 5 ms o 15 dB ponad medianę z 0,5 s.

| ujęcie | LUFS | obr/min start → koniec (maks. @ s) | spadek monot. | trzaski [s] | plateau: s, obr/min, linia dB, YIN |
|---|---|---|---|---|---|
| OVERRUN_SWEEP (1) | −30,1 | 1918 → 892 (1938 @ 1,5) | 45 % | 8,3; 11,5 | 0–3,4: 1928, 9,9, **0,51**; 6,5–10,5: 934, 6,0 |
| OVERRUN_SWEEP (2) | −31,6 | 964 → 1933 (2001 @ 11,0) | 5 % | 2,1; 7,0 | 7,0–10,3: 1913, 6,1, **0,50** |
| OVERRUN_SWEEP (3) | −35,1 | 1501 → 883 (1877 @ 4,2) | 43 % | — | 6,0–8,6: 934, 16,7, 1,01 |
| OVERRUN_SWEEP (4) | −32,4 | 1752 → 914 (1770 @ 0,6) | 37 % | — | 7,1–10,9: 904, 15,8, 1,01 |
| IDLE_STEADY (1) | −41,7 | 763 → 792 | — | — | 0–10,1: 758, 15,4, 1,01 |
| IDLE_STEADY (2) | −44,4 | 721 → 558 (dryf w dół) | — | 9,7; 10,0 | 0–2,9: 721, 24,2, 1,05 |
| IDLE_STEADY (3) | −38,2 | 1017 → 993 | — | — | 0–12,0: 1017, 16,4, 0,96 |
| **IDLE_STEADY (4)** | −40,5 | 1438 → 1477 | — | — | **0–8,3: 1461, 19,9, 0,95**; 7,8–11,3: 1420, 10,3 |

Wnioski:
- **Żaden zjazd nie jest zjazdem.** Model najpierw podnosi obroty do 1750–2000, potem spada w ~1,5 s do plateau
  ~900 obr/min (monotoniczność 5–45 %). Z szybkiego spadku nie da się wyciąć 1200/1500 metodą `el_sweepcut` (segment
  < 1 s na komórkę). Plateau ~1900 w (1) i (2) jest okresowe o oktawę niżej (YIN 0,50–0,51). (1) i (2) mają trzaski.
- **Jałowy nie jest jałowym, i dobrze.** Każdy wariant „idle” stoi na innych obrotach (758 / 721→558 / 1017 / 1461).
  (4) to stały 1461 obr/min w kabinie z drabiną 73/146/219 Hz, linią 19,9 dB, spójnym okresem i poziomem
  (odchylenie 0,45 dB). To jest dokładnie brakująca komórka 1500 bez obciążenia.

## Decyzja
Komórki `el_engine_cab_off_1200` i `el_engine_cab_off_1500` są wycinane z **`ENG_CAB_IDLE_STEADY (4)`, okno 1,75–8,25 s**.
Okno wybrał `el_regen04.py scan` (koszt 2 × odchylenie poziomu − linia, bez trzasków). Obróbka jak `el_prepare.sweep_cell`:
śledzenie linii 66–80 Hz, `warp_to_constant` prostuje ją na obr/min / 20 (×0,807–0,851 dla 1200, ×1,008–1,063
dla 1500), `flatten_level` (1,2 / 1,0 dB), szew 40 ms, głośność = LUFS komórki syntezy (−31,2 / −30,9 LUFS, jak dotąd),
bez limitera. Pętle mają 7,91 s i 6,32 s (było 6,05 / 4,84 s).

Kandydaci odrzuceni (`artifacts/audio-regen04/cut/dry.txt`):
- 1200 z IDLE_STEADY (3) (×1,17): linia 17,7 dB, ale skok barwy do komórki 900 wynosi 5,1 dB (z (4): 3,1 dB).
- 900: IDLE (1) 18,5 dB, IDLE (3) 17,7 dB, OVERRUN (4) 13,8 dB. Wszystkie gorsze od obecnej `ENG_CAB_OFF_2100 (2)`
  (22,3 dB), więc 900 zostaje bez zmian.
- 600: IDLE (1) 18,4 dB, a szew HF ma 6,1 dB (próg el_verify 6). Obecna `ENG_CAB_IDLE_SLOW (4)` ma 21,2 dB i zostaje.
- 1800/2100 poza zakresem zadania. Żadne ujęcie nie daje tam czystego tonu (plateau ~1900 jest o oktawę za nisko).

Odtwarzalność: `el_prepare.py` bierze komórki z `el_regen04.CELLS` (zamiast `ENGINE_PICK` dla kab./off 1200/1500).
Pełne `el_prepare.py` daje bajtowo te same WAV co `el_regen04.py cut`, a pozostałe 22 komórki, hamulec i zdarzenia
są bez zmian (git: zmienione tylko 2 WAV). `el_regen04.py cut` podmienia w `el_manifest.json` tylko dwa wpisy
i dopisuje prompt `ENG_CAB_IDLE_STEADY` (REGEN-04). `el_prepare.py` gubi przy tym prompty „`<ID> REGEN-02`” dopisane
przez `el_fx.py`. To stary problem, nie z tego zadania, dlatego manifest pochodzi z `el_regen04.py cut`.

## Liczby przed / po
Komórki (pętla ×2, linia przy obr/min / 20 ±3 %, `el_regen04.cell_row`). Ta sama miara na plikach z main daje
8,1 / 8,2 dB. ADR 0148 podał 7,5–7,7 dB starszym przebiegiem tej miary.

| kabina, bez obc. | linia przed → po | YIN przed → po | LUFS | źródło po |
|---|---|---|---|---|
| 600 | 21,2 (bez zmian) | 1,04 | −38,9 | IDLE_SLOW (4) |
| 900 | 22,3 (bez zmian) | 1,01 | −34,0 | CAB_OFF_2100 (2) |
| **1200** | **8,1 → 20,6 dB** | 0,81 → 0,95 | −31,2 | IDLE_STEADY (4) ×0,82 |
| **1500** | **8,2 → 21,1 dB** | **0,49 → 0,95** | −30,9 | IDLE_STEADY (4) ×1,02 |

Stara komórka 1500 była okresowa o oktawę za nisko (YIN 0,49). Nowa trzyma okres.

Lustro runtime (`tools/audio/el_regen04_ab.py`; `runtime_sim.LayerGrid`, crossfade equal-power jak `EngineSoundBank.incoherent`,
mnożnik kabiny 0,7, obciążenie 0, sam silnik; przed = main, po = gałąź; `artifacts/audio-regen04/ab/ab.json`):

| stała praca, obr/min | 600 | 750 | 900 | 1050 | 1200 | 1350 | 1500 |
|---|---|---|---|---|---|---|---|
| linia dB przed | 19,4 | 17,9 | 24,2 | 18,8 | **5,5** | **6,8** | **5,6** |
| linia dB po | 19,4 | 17,9 | 24,2 | 20,5 | **19,2** | **22,2** | **20,4** |
| RMS dBFS przed / po | −36,6 / −36,6 | −36,1 / −36,1 | −34,1 / −34,1 | −33,9 / −33,4 | −33,1 / −32,9 | −33,3 / −32,5 | −33,1 / −32,9 |

Toczenie na biegu 1500 → 900 obr/min w 12 s (1 s postoju na końcach; okna 0,5 s):

| | przed | po |
|---|---|---|
| linia, mediana w zjeździe | 13,6 dB | **21,4 dB** |
| linia, minimum w zjeździe | −0,2 dB | 9,9 dB |
| RMS 1–13 s | −33,4 dBFS | −33,0 dBFS |
| rozpiętość poziomu w zjeździe (0,5 s) | 2,0 dB | 2,6 dB |
| maks. skok 100 ms / 0,5 s | 2,67 / 0,89 dB | 2,57 / 1,24 dB |
| modulacja 60–130 Hz (CV) | 0,52 | 0,49 |

Skoki barwy między sąsiednimi komórkami (`el_verify` timbre, średnie |Δ| tercji): 600–900 3,50 (bez zmian),
900–1200 3,64 → **3,13**, 1200–1500 3,55 → 3,53, 1500–1800 2,79 → 3,58. Ten ostatni jest teraz na poziomie
pozostałych kroków wiersza (3,1–3,6).

## Validation
- `el_verify.py`: 0 FAIL, cab_off_1200 wysokość +0,1 %, szew 0,09, HF na zawinięciu 2,4 dB; cab_off_1500 −0,4 %,
  0,38, 4,2 dB; brak komórek „octave-low” (była 1500). Arkusz: `artifacts/audio-regen01/verify/grid_cab.png`
  (obejrzany: w nowych 1200/1500 widać poziome linie k × obr/min / 20, czego w starych nie było).
- Spektrogram zjazdu przed/po: `artifacts/audio-regen04/ab/ab_coast.png` (obejrzany: przed linia znika przy 2–6 s,
  czyli 1400–1200 obr/min; po jest ciągła drabina 1./2./3. harmonicznej przez cały zjazd).
- pytest `tools/audio/tests`: 46 passed.
- EditMode / APK: patrz niżej (Wyniki testów).

## Odsłuch dla właściciela
`artifacts/audio-regen04/ab/coast_1500_900_{before,after}.wav` (14 s, toczenie na biegu, sam silnik w kabinie,
jedno wzmocnienie na parę) oraz `fixed_<obr/min>_{before,after}.wav` (4 s, stała praca 600–1500). W grze:
Ustawienia → DŹWIĘK → Silnik: ElevenLabs, kamera w kabinie, rozpędzić na wysokim biegu i puścić gaz.

## Open
- Minimum linii w zjeździe (9,9 dB przy ~1050–1100 obr/min) wypada w przejściu 900 ↔ 1200. To dwa różne nagrania
  i linie o tej samej częstotliwości sumują się z przypadkową fazą. W stałym punkcie 1050 linia ma 20,5 dB.
- 1200 i 1500 pochodzą z jednego nagrania (jak wcześniej `CAB_OFF_1800 (3)`). Między nimi crossfade łączy dwa
  przesunięte w czasie kawałki tego samego materiału.
- Kabina/bez obciążenia 1800/2100 (`CAB_OFF_1200 (4)`) ma nadal tylko 10,6–10,7 dB, a 1800 jest o oktawę za nisko
  (YIN 0,51). REGEN-04 tego nie naprawia.
- Wniosek do kolejnych promptów: model zamiast zjazdu robi „wzrost, potem szybki spadek”. Stałe obroty dostajemy
  pewniej z promptu „steady idle”, który i tak wychodzi na losowych obrotach, a te mierzymy.
- Odrzuconych ujęć nie kasujemy (D54); zostają w `art-source/audio/elevenlabs/`.

## Wyniki testów
(uzupełniane)

# ADR 0176 — Synteza warstw bez nagrań: retarder, zdarzenia hamulca silnikowego, fazy AMT, osuszacz v2
Status: Proposed (agent audio, s17), 2026-11-13. Ocena brzmienia: właściciel (głośnik telefonu i słuchawki).
Kontynuacja ADR 0007 (warstwy sterowane fizyką), 0012 (perspektywa kabiny), 0134 (synchronizacja AMT hamulcem silnikowym),
0142 (zestaw ElevenLabs), 0145 (opony).

## Kontekst
Trzy niezależne poszukiwania (G9, GPT P5, Mistral M55; `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md`, PR #47)
nie znalazły w wolnych źródłach nagrań: retardera hydrodynamicznego, hamulca silnikowego pojedynczego pojazdu, AMT ani
regeneracji osuszacza. Dotychczas:
- retarder: jedna pętla `retarder_loop` (ton 350 Hz, wzmocnienie ~ napełnienie^0,9, wysokość ~ prędkość drogowa), czyli przy
  pełnym napełnieniu i 5 km/h grał prawie tak głośno jak przy 85 km/h (-6 dB w obu przypadkach), choć fizyka daje 0,4 kW i 600 kW;
- hamulec silnikowy: tylko pętla siatki obrotów (`ebrake_*`), bez zamknięcia i otwarcia przepustnicy;
- AMT: jeden sampel `gearshift_air` na początku zmiany biegu;
- osuszacz: `air_dryer_purge(_b)` — wybuch 0,1 s, potem szybki zanik.

## Decyzja
Synteza z prostych modeli fizycznych w `tools/audio/synth0176.py` (numpy/scipy, kod w repo, licencja własna), renderowana
przez `render_all.py` (zewnątrz + kabina przez `sfx_layers.cab_filter`). Wszystkie liczby to `WORKING_VALUE` (fikcyjna
ciężarówka, bez pomiaru konkretnego produktu).

| warstwa | model | sterowanie w grze |
|---|---|---|
| `retarder_tone_loop` | ton przejścia łopatek: 23 łopatki wirnika, 25 stojana, przełożenie 1,7 wału → wirnik; 1000 obr/min wału = BPF 651,7 Hz; wstęgi boczne rzędu wału (bicie), pętla = całkowita liczba obrotów wirnika | wzmocnienie = vol · 0,35 · napełnienie^0,8 · min(1, n_wału/1600)^1,5; wysokość = n_wału/1000 (0,2–2,5) |
| `retarder_flow_loop` | szum przepływu oleju (pasmo ~0,6·BPF), „oddech” raz na obrót, rzadkie trzaski kawitacji | wzmocnienie = vol · 0,65 · √(Retarder.Power / maxPower); ta sama wysokość |
| `ebrake_engage` | klik zaworu, uderzenie przepustnicy o ogranicznik, narastanie ciśnienia w kolektorze (niskie „łup” przez rezonanse wydechu `EXH_EXT`) | zdarzenie z `DrivelineSfx` (stan aktuatora `EngineBrakeState` rośnie o 0,12 od minimum) |
| `ebrake_release` | zrzut przeciwciśnienia przez rurę wydechową (impuls + szum przez `EXH_EXT`), odpowietrzenie cylindra | zdarzenie (stan spada poniżej 0,88 maksimum); głośność = vol · (0,4 + 0,6·clamp((rpm−900)/1100)) · maks. stan aktuatora |
| `amt_disengage` | zawór, „pft” cylindra, tuleja wychodzi z zębów | wejście w `ShiftNeutral` |
| `amt_engage`, `_b` | kłapnięcie sprzęgła kłowego przez mody obudowy skrzyni + luz (3 / 2 odbicia) | wejście w `ShiftEngage`, na zmianę |
| `amt_clutch_chuff` | odpowietrzenie aktuatora sprzęgła | wyjście z `ShiftEngage` (sprzęgło zamknięte) |
| `air_dryer_purge_v2`, `_v2b` | adiabatyczny wydmuch zbiornika przez kryzę (przepływ dławiony, potem poddźwiękowy), poziom ~ √(ṁ·U⁵), częstotliwość szczytu 0,2·U/D ograniczona tłumikiem do 5,2 kHz; 4,0 L / 6 mm i 3,4 L / 5,5 mm; potem cichy przepływ regeneracji | wyłączenie sprężarki (regulator), na zmianę |

Wpięcie w grę (`TruckAudioController`): retarder tone + flow i fazy AMT oraz osuszacz v2 grają w **zestawie proceduralnym**
(w zestawie ElevenLabs zostają nagrania ADR 0142: `elRetarder`, `elGearshiftUp/Down`, `elAirDryerPurge`). Zdarzenia
hamulca silnikowego grają w **obu zestawach** (żaden ich nie miał). Bez zaimportowanych klipów 0176 zachowanie jest jak przed
zmianą. `DrivelineSfx` to struktura bez alokacji (test jednostkowy); detektor hamulca silnikowego jest zamrożony na czas zmiany
biegu (synchronizacja ADR 0134 nie jest dźwignią), po zmianie: dźwignia dalej wciśnięta = dalej włączony, puszczona = cicho wyłączony.

## Dowody (pomiar, `C:\Users\matma\Documents\Claude\kamion\artifacts\audio-synth-0176\`)
- `checks.json`: szwy pętli (`analyze.seam_metrics`) ratio d1/d2: tone 0,70/0,70, flow 0,36/0,28, kabina 0,40/0,92 i 0,23/0,48
  (< 1 = szew nie wyróżnia się); jednorazowe: pierwsza/ostatnia próbka 0,0 (brak kliknięcia); szczyt −1 dBFS.
- Prawo retardera przy pełnym napełnieniu (vol 0,5): 10 km/h tone −43,8 / flow −33,0 dB; 30 km/h −29,5 / −18,7 dB; 85 km/h
  −16,0 / −9,8 dB (stara pętla: −6 dB przy każdej prędkości).
- Osuszacz v2 vs plik porównawczy P5-006 (tylko porównanie, nie trafia do buildu): energia w oknach 0,05–0,15 / 0,15–0,3 /
  0,3–0,6 / 0,6–1,0 s: −28,7 / −30,5 / −34,0 / −39,3 dB vs −29,3 / −28,9 / −34,3 / −39,5 dB; centroid 5,2–5,4 kHz vs 5,0–5,5 kHz.
  Pierwsza wersja szkicu (2 L / 8 mm, bez limitu tłumika) gasła 25 dB za szybko i miała centroid 8–10 kHz — poprawiona.
- Spektrogramy przed/po: `spec/before_after_{retarder,ebrake_events,amt,dryer}.png`, scen: `spec/scene_*.png`, referencje
  `spec/references.png` (obejrzane).
- Testy: `DrivelineSfxTests` (11, czyste) + istniejące testy audio w PlayMode (`artifacts/tests/`).

## Odsłuch właściciela (A = main, B = 0176), `artifacts/audio-synth-0176/ab/`
`retarder_{ext,cab}` (zjazd 85 → 12 km/h na pełnym retarderze), `amt_{ext,cab}` (3 zmiany w górę pod obciążeniem),
`ebrake_{ext,cab}` (dwa włączenia hamulca silnikowego), `dryer_{ext,cab}` (dwa wyłączenia sprężarki). Pytania: czy retarder
w B nie jest za cichy (−3,6 LU vs A w scenie zewnętrznej — celowo, bo maleje z prędkością), czy fazy AMT brzmią jak skrzynia
a nie pneumatyka, czy „łup” zamknięcia przepustnicy nie jest za mocny, czy dłuższy wydmuch osuszacza (scena zewn. +3,6 LU vs A,
słyszalny ~1,5 s zamiast ~0,3 s) nie jest za natarczywy przy postoju.

## Konsekwencje
- Zero nowych zasobów z zewnątrz; rejestr: `docs/LICENSES.md` `audio-procedural-driveline-0176`.
- Opcjonalna partia ElevenLabs (`docs/owner/ELEVENLABS-REGEN-05.md`) — prompty dla właściciela, niczego nie wysłano.
- Testy w zestawie PlayMode (asmdef EditMode nie referuje `Game.Audio`; zmiana asmdef = lider).
- Otwarte: odsłuch na telefonie (głośnik + słuchawki). Scena `retarder_cab`: licznik HF-transientów (> 4 kHz, 15 dB nad
  medianą) B 332 vs A 95, ale sam sygnał warstw retardera (B − A, tło identyczne) daje 0, a pętle powielone ×4 po 0–1.
  Transienty są w tle sceny (silnik/opony w kabinie): stara głośna pętla retardera je maskowała, nowa (cichsza przy niskiej
  prędkości) odsłania. Do sprawdzenia przy odsłuchu tła kabiny (poza zakresem 0176).

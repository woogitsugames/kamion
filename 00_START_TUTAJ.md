# 00 — START TUTAJ (instrukcja dla właściciela, nie dla sesji)

Pakiet startowy dla lokalnej sesji Claude Code, która ma zbudować mobilny symulator ciężarówki (Android → iOS).
Przygotowany 9.11.2026 na podstawie researchu oraz porównania 9 promptów z innych modeli (Mistral, GPT, Gemini, Kimi i in.).

## Co jest w paczce

```
truck-sim-starter/
├── 00_START_TUTAJ.md            ← ten plik (dla Ciebie)
├── PROMPT_STARTOWY.md           ← wklejasz jako pierwszą wiadomość w sesji
├── CLAUDE.md                    ← stałe zasady projektu (sesja czyta je przy każdym starcie)
├── docs/
│   ├── 01_WIZJA_I_ZAKRES.md
│   ├── 02_STACK_SRODOWISKO_NARZEDZIA.md   ← co zainstalować, MCP, skille
│   ├── 03_ETAPY_I_BRAMKI.md
│   ├── 04_FIZYKA.md
│   ├── 05_MAPA_BIALYSTOK_I_DANE.md
│   ├── 06_GRAFIKA_ANTI_AI_SLOP.md          ← standard jakości wizualnej
│   ├── 07_CIEZAROWKA_3D.md
│   ├── 08_AUDIO.md
│   ├── 09_AGENCI_I_WORKFLOW.md
│   ├── 10_ARCHITEKTURA_I_DLC.md
│   └── 11_DECYZJE_WLASCICIELA.md           ← Twoje odpowiedzi, zablokowane decyzje
└── .claude/
    ├── agents/                  ← 9 wyspecjalizowanych subagentów (Opus)
    └── skills/                  ← 5 skilli projektowych (build, visual QA, fizyka, Blender, GIS)
```

## Co zrobić krok po kroku

1. **Zainstaluj Claude Code na Windows** (jeśli jeszcze nie masz): `winget install Anthropic.ClaudeCode`, potem `claude` i zaloguj się kontem z dostępem do Opus.
2. **Utwórz folder projektu** na szybkim dysku z dużą ilością miejsca (≥ 300 GB wolnego), **nie w OneDrive**, np. `D:\Projekty\truck-sim`.
3. **Rozpakuj zawartość tej paczki do tego folderu** (tak, żeby `CLAUDE.md` i `.claude\` były bezpośrednio w `D:\Projekty\truck-sim`).
4. Podłącz Samsunga przez USB, włącz debugowanie USB, zaakceptuj na telefonie odcisk komputera.
5. Otwórz terminal w folderze projektu i uruchom `claude`.
6. Wklej całą zawartość `PROMPT_STARTOWY.md` jako pierwszą wiadomość.
7. Sesja zrobi audyt komputera, pokaże listę instalacji do zatwierdzenia, zainstaluje środowisko i poprowadzi Etap 0.

## Co będzie od Ciebie potrzebne (sesja o to poprosi)

- Kliknięcia w UAC/instalatory, logowanie do Unity Hub (darmowa licencja Personal), autoryzacja `gh` do GitHuba.
- **Zdjęcia referencyjne** (najważniejsze dla jakości i darmowe): kabina i zewnętrze dowolnej nowoczesnej ciężarówki na parkingu/MOP, oraz ulice startowego fragmentu Białegostoku. Lista ujęć będzie w `docs/06` i `docs/07`.
- Ocena „feelingu” jazdy na telefonie po każdej bramce, bo tego żadne testy nie zastąpią.
- Docelowo pożyczenie/dostęp do flagowca (np. Galaxy S/Tab S ze Snapdragonem 8 Elite) do strojenia profilu High/Ultra; do tego czasu testujemy na Samsungu A.

## Opcjonalnie, ale warto

- Zainstaluj w Claude Code plugin **Superpowers** (sesja zrobi to sama, jeśli się zgodzisz — szczegóły w `docs/02`).
- Jeśli chcesz rozmawiać z sesją z telefonu — użyj Claude desktop/web połączonego z tą maszyną.

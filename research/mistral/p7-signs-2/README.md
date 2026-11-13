# P7 — signs-2: aktualizacja oznakowania (rondo Putry / Andersa / Tysiąclecia + nowe korytarze)

**Stan badania: w toku (rozpoczęto 13 listopada 2026 r.). Materiał referencyjny dla projektu Kamion.**

Gałąź: `research/mistral-p7-signs-2` od najnowszego `origin/main` (bazowy commit 8c65107f7f0090e0829f7dbd3638d14f6204ec1b).

## Cel i zakres

1. Aktualny stan bramownic i tablic w rejonie ronda Putry / Andersa / al. Tysiąclecia (oba kierunki) — z uwzględnieniem zdjęć 2025–2026 tam, gdzie istnieją w dozwolonych źródłach; weryfikacja aktualności treści z 2024 r. (paczka G3).
2. Epoki bramownic Andersa 2019–2026: oś czasu zmian tablicy pasa 2 (Augustów / Kuźnica / Centrum).
3. Nowe obszary: DK19 (do 15 km od miasta), DK65 (do Bobrownik), DK8 na północ (kierunek Porosły/Jurowce; uwaga: Tykocin leży przy DW671/DW676, nie przy DK8 — szczegóły w README), S19 (nowe odcinki 2025–2026), S8 do węzła Białystok Zachód.
4. Manifest zgodny ze schematem research/gptpro/3-s8-signs/manifest.csv (bez konwersji do generatora).

## Źródła (twarde ograniczenia)

- Panoramax (api.panoramax.xyz, CC BY-SA 4.0 — share-alike: referencja, nie tekstura)
- Wikimedia Commons (CC0/CC BY-SA per plik)
- Openverse (tylko CC0/BY/BY-SA)
- BIP / GDDKiA / ZDiT (dokumenty urzędowe, art. 4 pr. aut.)
- Mapillary: brak tokenu — pozycje wyłącznie UNVERIFIED / referencja przez wcześniejszą paczkę G3
- KartaView: API niedostępne z tego środowiska (api.openstreetcam.org / api.kartaview.org nieodpowiadają) — opisane w sources.md
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles — nie użyto

## Struktura (uzupełniana w trakcie badania)

| Plik | Zawartość |
|---|---|
| `README.md` | Niniejszy opis, metoda, wyniki, braki. |
| `manifest.csv` | Spis obserwacji (id P7-NNN). |
| `sources.md` | Źródła, licencje, daty dostępu. |
| `timeline_andersa.md` | Oś czasu epok bramownic Andersa 2019–2026. |
| `audit_20_percent.json` | Samokontrola 20% z jawnym seedem. |
| `files/` | Zdjęcia (NIE w gicie; ZIP jako załącznik do PR / release). |

Ten plik będzie aktualizowany wraz z postępem badania.

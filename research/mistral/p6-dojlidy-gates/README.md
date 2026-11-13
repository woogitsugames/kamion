# mistral-p6-dojlidy-gates — bramy Dojlidy/Krywlany: szerokości, promienie łuków, RS16, PZZ, organizacja ruchu

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą; świat Białegostoku 1:1 (OSM + GUGiK); gra komercyjna, budżet 0 zł.
**Zadanie M49:** uzupełnienie luk po paczce research/gptpro/p6-next-regions-2 (dalej: P6) — szerokości bram wjazdowych (12 bram bez szerokości), promienie łuków wjazdu (14 bram bez promieni), dokładna pozycja RS16 (WIM Zabłudowska), adres/brama PZZ (Elewatorska vs Zbożowa), organizacja ruchu na końcówkach dojazdów (Myśliwska, Karpińskiego, Dojlidy Fabryczne, rondo Meyera, Adama Mickiewicza) z numerami dokumentów BIP/ZDM.
**Gałąź:** research/mistral/p6-dojlidy-gates (od origin/main). **Data:** 2026-11-13. **Język:** polski.
**Status: W TOKU** — plik roboczy; kolejne commity uzupełniają wyniki (pomiary programowe na ortofoto GUGiK trwają).

## 1. Cel
1. Szerokość bramy wjazdowej (m) i promień łuku wjazdu (m, krawędź jezdni) dla 14 bram z P6 (G01–G14): pomiar na ortofotomapie GUGiK (GSD ≤ 0,25 m), z datą zdedrywowaną ze skorowidza, metodą i niepewnością ±m. Dla Elektrociepłowni Białystok (Andersa 15) — wskazanie bramy dla ciężarówek (brak w OSM).
2. Dokładna pozycja stacji ważenia RS16 (WIM, ul. Zabłudowska, DK19) — obecnie ESTIMATED ±150 m.
3. Adres i brama Podlaskich Zakładów Zbożowych: „Elewatorska 14" czy ul. Zbożowa — rozstrzygnięcie źródłem urzędowym.
4. Organizacja ruchu (zarządzenia ZDM/ZDiT Białystok w BIP): Myśliwska, Karpińskiego (KAN), Dojlidy Fabryczne (zakaz 3,5 t?), rondo Meyera, Adama Mickiewicza (maxweight 8) — numer dokumentu, data, treść, odcinek.

## 2. Metoda
- **Ortofotomapa:** GUGiK WCS `Orthoimagery_High_Resolution` (PZGIK, dane otwarte), wycinki 160×160 m = 1600×1600 px (10 cm/px) — bboxy identyczne jak wycinki P6 (files/M49-GXX.jpg), wariant PNG do analizy programowej.
- **Skorowidz ortofotomapy WFS:** https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze — usługa oczekuje bbox w kolejności (N,E) dla EPSG:2180 (weryfikacja empiryczna). Dla Białegostoku atrybuty: godło, akt_rok, piksel, kolor, nr_zglosz, url_do_pobrania (bez daty dziennej — data nalotu UNVERIFIED, kandydacy wg P6: 2024-03-30 / 2025-04-18).
- **OSM:** API 0.6 (api.openstreetmap.org), wycinki map?bbox= ±200 m; transformacja EPSG:2180 własnym modułem TM/GRS80 (zwalidowany na parach z manifestu P6, Δ < 0,5 m).
- **Szerokość bramy (3 metody programowe, wzajemnie krzyżowane):**
  1. Skan prostopadły do linii ogrodzenia OSM (way barrier=fence przez node bramy), stacje co 0,5 m, ±2,5 m — przejście „nie-trawa" (asfalt/struktura) przez node = prześwit bramy.
  2. Szerokość asfaltowego podjazdu w profilach prostopadłych do drogi serwisowej (way zawierający node bramy) w odległości 3–15 m od bramy (auto-detekcja granic asfaltu).
  3. Cięciwa między końcami ways barrier=fence tam, gdzie ogrodzenie ma przerwę w geometrii OSM (metoda P6).
  Analiza obrazu (model wizyjny) — wyłącznie jakościowo (typ bramy, strona ulicy, sezon, pojazdy); próby ilościowe nie są powtarzalne (wartości-kotwice), NIE stanowią źródła liczb.
- **Wynik:** mediana dostępnych pomiarów (≥ 2 tam, gdzie możliwe), niepewność ±1–3 m jawnie; brak pomiaru → UNVERIFIED/ESTIMATED z opisem metody.
- **Promień łuku wjazdu (krawędź jezdni):** wycinek 60–80 m na skrzyżowaniu podjazd×ulica, programowa segmentacja asfaltu i dopasowanie okręgu do granicy jezdni; weryfikacjaMode: niepewność ±2–3 m; brak wykrycia → UNVERIFIED.

## 3. Struktura
README.md (ten plik), manifest.csv (id M49-NNN, utf-8), sources.md, audit_20_percent.json (samokontrola ≥ 20% pozycji, jawny seed), files/ (wycinki ortofoto — POZA git, w .gitignore, archiwum ZIP poza repo), files/docs/ (PDF urzędowe ≤ 5 MB — w gicie).

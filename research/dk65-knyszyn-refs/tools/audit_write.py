"""Merge automatic checks (audit_raw.json) with manual re-view verdicts -> audit_20_percent.json"""
import json, sys
raw = json.load(open(sys.argv[1]))
V = {
 "K1-006": ("FIX", "Ponowne obejrzenie zoom km 12,00: lewej linii krawędziowej nie widać wyraźnie (wcześniej 'ciągła słabo widoczna'); pozycja L wzięta z krawędzi asfaltu → status UNVERIFIED, opis poprawiony."),
 "K1-007": ("FIX", "Zoom km 12,50: lewa linia krawędziowa jest przerywana (krótkie kreski), nie ciągła → poprawiono opis."),
 "K1-011": ("PASS", "Zoom km 14,50: L ciągła −3,25, oś ciągła, P przerywana wzdłuż poszerzenia — zgodne."),
 "K1-020": ("PASS", "Zoom km 21,65: obie krawędziowe przerywane, oś przerywana — zgodne."),
 "K1-021": ("PASS", "Zoom km 22,00: jw. — zgodne."),
 "K1-024": ("PASS", "Zoom km 24,60: L ciągła, oś długie kreski, P ciągła ~+2,75 — zgodne."),
 "K1-025": ("PASS", "Zoom km 25,00: L ciągła −3,75, oś ciągła −0,75, P przerywana +2,25, zatoka P — zgodne."),
 "K1-031": ("PASS", "API ways 200; tagi lanes/surface/maxspeed zgodne z data/osm_route_ways.json."),
 "K1-042": ("PASS", "API 200; Tykocka secondary ref=671."),
 "K1-044": ("PASS", "API 200."),
 "K1-046": ("PASS", "Panoramax search URL 200; liczba zgodna z query_log."),
 "K1-050": ("PASS", "jw."),
 "K1-064": ("PASS", "Ponownie obejrzane: niebieska tabliczka UL. GRODZIEŃSKA na białym tynku — zgodne."),
 "K1-066": ("PASS", "Ponownie obejrzane w 960 px: 2 kondygnacje + lukarny, czerwony dach, kremowe kolumny portyku, żółte obramienia — zgodne; dodatkowo widać szyldy biblioteki i ośrodka kultury."),
 "K1-067": ("PASS", "Pomnik na granitowym cokole + blok z tablicą, kostka z czerwonym wzorem — zgodne."),
 "K1-070": ("PASS", "Biały parterowy dom, czerwono-brązowa dachówka, brązowy płot, słup — zgodne."),
 "K1-078": ("PASS", "Ciemnoczerwona cegła + tynk, napis firmowy — zgodne."),
 "K1-088": ("PASS", "Podwójna ciągła oś → przerywana, chodnik L, znak pieszo-rowerowy P, słupy z wysięgnikami L — zgodne."),
 "K1-091": ("PASS", "Peron, latarnia z 2 ramionami, trakcja, EZT — zgodne; ~3 km od trasy (współrzędne Commons)."),
 "K1-092": ("PASS", "Żółty budynek dworca 2 kondygnacje z tablicą nazwy — zgodne."),
 "K1-100": ("PASS", "Granitowa tablica złote litery 1930 — zgodne."),
 "K1-106": ("PASS", "OSM way 1511762690 200; cytat Auto Świat sprawdzony (WebFetch 2026-11-15)."),
 "K1-111": ("PASS", "URL 200; cytat o oddaniu 20.10.2026 zgodny."),
 "K1-112": ("PASS", "gov.pl nadal niedostępne (ConnectionError) — wiersz już UNVERIFIED, bez zmian."),
 "K1-113": ("FIX", "Ponowne obejrzenie wycinka: obiekt to płyta wiaduktu na przyczółkach nad wykopem korytarza S19 (N–S), droga objazdem łukiem obok — doprecyzowano opis."),
 "K1-116": ("PASS", "OSM way 200."),
 "K1-118": ("FIX", "URL bez bbox zwracał 400 → podmieniono na przykładowe zapytanie z bbox (200)."),
 "K1-122": ("PASS", "WMS 200; ponowne obejrzenie zoomów km 17–25: brak cieni słupów przy jezdni poza zatoką km 19."),
}
out = {"seed": raw["seed"], "metoda": "random.seed(20261115); random.sample(range(N), ceil(0.2*N)); ponowne obejrzenie obrazu (zoom ortofoto / JPG 960 px) + ponowny sha256 + ponowne pobranie URL",
       "n_rows": raw["n_rows"], "n_audited": raw["n_pick"], "items": []}
for c in raw["picked"]:
    v, note = V[c["id"]]; c.update({"wynik": v, "uwagi": note}); out["items"].append(c)
out["pass"] = sum(1 for i in out["items"] if i["wynik"] == "PASS"); out["fix"] = sum(1 for i in out["items"] if i["wynik"] == "FIX")
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1); print(out["pass"], out["fix"], len(out["items"]))

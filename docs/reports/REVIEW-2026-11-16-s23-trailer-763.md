# REVIEW 2026-11-16 s23 — naczepa, tridem 6,32/7,63/8,94 m (D79, ADR 0280 §9.4) — werdykt: **SCAL warunkowo**
Przesunięcie o −0,07 m jest czyste: tridem, błotniki, chlapacze i lampa boczna 3 przesunęły się razem. Koła siedzą centrycznie w łukach (`blender-after/zbl_kolo`, `bok_szary`). Chlapacz jest tuż za osią 3 (wg danych ~0,15 m: 9,622−8,94−0,536). Piwoty kół siedzą w środkach (`pivoty_34tyl`), LOD2 jest spójny z LOD0 (`lod2_34tyl`). Obrysówki zachowują rytm, a `_CurtainAxles` w shaderze jest zsynchronizowany. Export PASS (LOD0 89 000/90 000), regs 158/158. Na statycznym zrzucie Unity `trailer-34` nie widać szwów ani z-fightingu. Proporcje zestawu (`zestaw_bok`, 16,50 m) są wiarygodne.
Uwaga do dowodu: `before/` to rendery z `docs/` z be4287762, czyli przodka lamplens-0181 (424db34e0). Nie pokazują stanu sprzed tej zmiany, bo mają czyste felgi i starą tablicę. Wiarygodne przed/po jest tylko w Unity (`cmp/uside_ba`) i w logu UV.
- **P1 (sprzed zmiany, nie blokuje):** na beczce obręczy widać czerwone plamy i tekst z atlasu Metal, czyli czerwoną flagę z docs/06 §2 („zniekształcone napisy”).
  - Pomiar: 639/10 661 tekseli kół. UV kół nakłada się z CHASSIS na 7 506 tekseli, bo koło zapasowe dzieli UV z 1L.
  - Stan sprzed zmiany potwierdzony niezależnie: `cmp/old_metal_C.png` i `old_LOD0.fbx` mają ten sam git-hash co `main:art-source/truck/trailer/export/…`.
  - Plamy są wyraźne w `zbl_kolo` i `zbl_lampy`, a w LOD2 felgi mają różowawy odcień. W Unity z 3/4 felgi są ciemne i nie rzucają się w oczy.
  - Poprawka: własna wyspa UV dla zapasu, rebake atlasu Metal i reguła w `check_export`: „wheel texels R−G>0,2 = 0” (docs/06 §5).
- **P1 (warunek scalenia):** przed scaleniem wpisz zadanie z poprzedniego punktu do HANDOVER/backlogu. Nowe rendery w `docs/reports/visual/trailer-curtainsider/` pokazują czerwone felgi i nie mogą zostać uznane za wzorzec.
- **P2:** render `gora_szary_overcast_lod0` jest prawie czarny (sylwetka bez światła pod przekrojem), więc nic nie dowodzi. Doświetl go od dołu albo usuń.
- **P2 (do weryfikacji, prawdopodobnie sprzed zmiany):** w `blender-after/zbl_lampy` tablica „BI 8N402” jest wyblakła i nie ma pola UE, a w be4287762 była czytelna.
- **P2:** opona w Unity jest wciśnięta o 2,1 cm (art 0,536 / fizyka 0,515, udokumentowane). Pod ładunkiem to wiarygodne ugięcie, przy pustej naczepie będzie przesadą.
Oceny 1–10: proporcje 8 · koła/błotniki/chlapacze 8 · materiał felg 4 · artefakty poza felgami 8 · czytelność dowodu 6.

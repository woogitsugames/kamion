# ADR 0118, asphalt r1 — candidate2

Ocena: warunkowa, bez pełnego wizualnego PASS. Niezależny subagent `asphalt_visual_critic` obejrzał 14 arkuszy Low/High overcast: trzy referencje Mapillary, stara droga, nowa droga, świeża i stara łata. Autor zmian również obejrzał wszystkie te arkusze oraz pełne podglądy wybranych kamer. Dowody: `artifacts/asphalt-r1/review-candidate2-960/`, uwagi szczegółowe `VISUAL-CRITIC.md` i `SELF-REVIEW.md`.

Stara droga ma wyraźniejsze miękkie ślady kół. Referencja 150280503737744 uzasadnia ich mocniejszy kontrast, ale render pozostaje bardziej regularny. W referencjach wiaduktu 303305168125936 i 454716650857984 nawierzchnia jest spokojniejsza, więc globalny wzór zużycia może być zbyt podobny między drogami. Światło i pozy nie są dokładnie dopasowane; zgodności fizycznego albedo nie potwierdzono.

Łaty są czytelniejsze, lecz zbyt płaskie i prostokątne. Ciemny obrys starej łaty wzmacnia efekt naklejki. Część farby na nowej nawierzchni jest lepiej zachowana, ale na pozostałych pasach nadal są ubytki; kontrola nowej drogi nie ma PASS. To priorytety P1. Mniejsza regularność śladów zależna od nawierzchni jest P2.

Drobny falisty wzór przy krawężniku jest widoczny w kontroli natywnej. Wyłączenia poszczególnych warstw go nie usunęły, przyczyny nie ustalono. Krytyk nie potwierdził jednoznacznego moiré na arkuszach 960 px; taki rozmiar nie rozstrzyga stabilności w ruchu. Low i High mają podobne ograniczenia.

EditMode 275/275 passed. Autor obejrzał ponadto wszystkie 28 contact sheets dla 312 par z 78 kamer w czterech warunkach. Liczniki candidate2: wszystkie mesh/instance delta 0. Pomiar kontrastu renderu z r1 wycofano po wykryciu błędnego odtworzenia anchor przy seat=road; patrz artifacts/asphalt-r1/CORRECTION-2026-11-12.md. Nie przypisujemy wycofanym liczbom wartości dowodowej. Końcowy GIS: 521 passed, 1 xfailed. Audyt 196 odwołań bez rozbieżności po odtworzeniu metadanych. Physics/gate3: 47 passed, 1 znana porażka odtwarzalności top_speed_flat_comb.json. Fidelity exit 0. Te wyniki nie zmieniają warunkowej oceny obrazu. A16 UNVERIFIED, telefonu nie używano. Wartości wizualne WORKING_VALUE. Ta recenzja nie daje zgody na bezwarunkową integrację.




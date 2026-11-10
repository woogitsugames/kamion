# Fab i Patch: licencje a D40 (stan 2026-11-10)

Zakres: tylko publiczne strony, bez logowania i bez pobierania plików. Nic z Fab ani Patch nie trafiło do repo.

## Wniosek

- **Fab (Megascans, licencja Fab Standard): tak, warunkowo.** Wolno w Unity i w komercyjnej grze na Androida/iOS, bez atrybucji. Warunek twardy: żaden plik z Fab (źródłowy ani przetworzony) nie może leżeć w publicznym repo.
- **Fab, pozycje CC BY: tak, warunkowo.** Wolno wszędzie, także w publicznym repo, ale z atrybucją w grze i w `docs/LICENSES.md`; licencja każdej pozycji do potwierdzenia po zalogowaniu.
- **Megaplants (drzewa Quixel): nie teraz.** Tylko formaty Unreal i USD, funkcja oznaczona jako eksperymentalna.
- **Patch: nie rozszerzać D40.** Realistyczne pozycje to te same skany Poly Haven i ambientCG, które D40 już dopuszcza; reszta to stylizowane low-poly.

Czego nie udało się potwierdzić:
- **Wiążący tekst Fab EULA.** Strona `fab.com/eula` oddaje bez JavaScriptu tylko streszczenie, które samo zastrzega, że „is not legally binding”. Punkty oparte wyłącznie na streszczeniu mają niżej znacznik `UNVERIFIED`.
- **Typ licencji na karcie pozycji.** Pole „License terms” pokazuje „-” bez wybrania licencji po zalogowaniu.
- **„Free forever”.** Żaden oficjalny tekst, który dało się odczytać, tego nie obiecuje.

## Fab Standard License

Źródła: [streszczenie licencji](https://www.fab.com/eula), [typy licencji i progi](https://dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab), [ogłoszenie Quixel z listopada 2026](https://quixel.com/news/update-megascans-are-going-free-again), [CG Channel, 2026-11-06](https://www.cgchannel.com/?p=179945).

| Pytanie | Odpowiedź | Podstawa |
|---|---|---|
| Unity | Tak | streszczenie: „usage is not limited to Unreal Engine” |
| Gra komercyjna Android/iOS | Tak | streszczenie: „Use the assets commercially or privately” |
| Publiczne repo | **Nie** | streszczenie zakazuje rozdawania pozycji osobno, także za darmo; dzielenie się dozwolone tylko ze współpracownikami, wprost przez „private repository” |
| Atrybucja | Niewymagana | streszczenie: „not required to give credit to the publisher” |
| Redystrybucja | Tylko jako część gry (build) | jak wyżej |
| AI | Zależy od pozycji | znacznik NoAI zakazuje zbierania danych dla generatywnego AI; pozycje Megascans mają na karcie „Allows usage with AI: Yes” |
| Próg przychodu | 100 000 USD brutto w 12 miesięcy dzieli cennik Personal i Professional; oba dają te same prawa | dokumentacja Fab; dla pozycji darmowych bez znaczenia praktycznego (`UNVERIFIED`) |
| Free forever | `UNVERIFIED` | patrz niżej |

Publiczne repo: streszczenie nie wymienia słowa „public”, ale zakaz samodzielnej redystrybucji i wyjątek ograniczony do współpracowników dają jednoznaczny wniosek praktyczny. Na forum Epic to samo pytanie ([wątek o GitHubie](https://forums.unrealengine.com/t/github-project-distribution-and-free-fab-assets/2665655)) zostało bez odpowiedzi Epic. CG Channel pisał w 2024 r. o ograniczeniach dla projektów w pełni open source ([artykuł](https://www.cgchannel.com/?p=162523)).

Zakaz obejmuje też pochodne, z których da się odzyskać zasób: zaimportowane siatki i tekstury w `game/Assets/`, atlasy, wypalone mapy. To interpretacja ostrożna (`UNVERIFIED` wobec pełnego EULA), ale jedyna bezpieczna.

## Megascans / Quixel na Fab

- **Cena:** Quixel ogłosił w listopadzie 2026, że cała biblioteka jest darmowa na Fab; karty pozycji mają być przestawione do 12 listopada 2026. Sprawdzone dziś pozycje pokazują „Free” albo „From Free”.
- **Poza Unreal:** tak, jeśli pozycję pozyskano na Fab na licencji Fab Standard. Stare pobrania z Bridge zostają „UE-only” (wypowiedź moderatora na [forum Epic, 2024](https://forums.unrealengine.com/t/megascans-license/2081542)). Dla Kamiona: pozyskiwać wyłącznie przez Fab.
- **Formaty:** skany powierzchni i dekale mają zestaw tekstur i glTF; obiekty 3D (sprawdzone „Street Curbs”) mają FBX, glTF, GLB, USDZ. Import do Unity przez glTFast, jak w ADR 0011.
- **Konto:** pozyskanie wymaga konta Epic właściciela i akceptacji aktualnych warunków. Agenci nie logują się i nie zakładają kont.
- **Free forever:** artykuł CG Channel pisze „seemingly for good”, ogłoszenie Quixel tego nie obiecuje. Licencja jest przypisana do konta Epic. Czy pozycja pozyskana za darmo zostaje na koncie po ewentualnej zmianie ceny: `UNVERIFIED`. Poprzednio (koniec 2024) darmowość była czasowa, więc warto pozyskać potrzebne pozycje teraz.
- **Megaplants:** karta „Baltic Pine” podaje formaty Unreal Engine i USD, wymaga wtyczki Procedural Vegetation Editor i Nanite Foliage, a Epic sam odradza wydawanie projektów na funkcjach eksperymentalnych. Dla mobilnego Unity nieprzydatne bez własnej konwersji i redukcji.

## Pozycje CC BY na Fab

- Streszczenie: użycie reguluje sama licencja Creative Commons (CC BY 4.0). Unity, komercja, modyfikacje i redystrybucja są dozwolone, także w publicznym repo.
- Obowiązki: autor, tytuł, link do źródła i licencji, informacja o zmianach; w grze (ekran „O grze”) i w `docs/LICENSES.md`.
- Znacznik NoAI nie może być łączony z CC BY (dokumentacja Fab).
- CC BY nie da się odwołać wobec już pozyskanej kopii (zasada licencji CC), więc to jedyny wariant Fab z pewnym „na zawsze”. Zapisać datę, URL i zrzut karty z licencją.
- Ryzyko: pozycje pochodzą od użytkowników (dawny Sketchfab). Nikt nie gwarantuje, że wystawca miał prawa do skanu; skany z logo lub marką odrzucać.

## Patch (patch.gg)

Źródła: [strona główna](https://patch.gg/), [regulamin, aktualizacja 2026-11-06](https://patch.gg/terms), [dokumentacja](https://docs.patch.gg/llms.txt), [API wyszukiwania](https://docs.patch.gg/api-reference/assets/search-the-asset-library.md).

- **Czym jest:** platforma gier i modów z biblioteką cudzych otwartych zasobów oraz CLI `pch` i serwerem MCP. Strona: każdy zasób ma „its licence and credit line attached”.
- **Licencje:** per zasób, identyfikatory SPDX. Domyślny filtr wyszukiwania obejmuje CC0-1.0, CC-BY-4.0 i MIT.
- **Skąd zasoby (zaobserwowane w wynikach):** Poly Haven, ambientCG, Kenney, KayKit (CC0); Polyfork, Amazon Berkeley Objects, incompetech (CC BY 4.0).
- **Unity, komercja, publiczne repo:** rozstrzyga licencja zasobu. CC0 bez warunków; CC BY z atrybucją. Regulamin Patch nie dokłada ograniczeń do zasobów na otwartych licencjach.
- **Konto:** przeglądanie i wyszukiwanie działa bez konta; konto (18+) potrzebne do publikowania i biblioteki. Czy pobranie plików przez CLI wymaga konta: `UNVERIFIED`.
- **AI:** regulamin pozwala Patch trenować własne modele na pracach otwartych opublikowanych na Patch i zakazuje masowego zbierania treści Patch do trenowania AI. Dotyczy publikujących, nie nas.
- **Free forever:** tak dla CC0 i CC BY (licencje nieodwołalne), niezależnie od losów Patch.
- **Gwarancja licencji:** brak. Patch jest pośrednikiem; poprawność licencji trzeba sprawdzić u źródła.
- **Jakość:** wyniki realistyczne (PBR) to wyłącznie Poly Haven i ambientCG. Pozostałe mają cechy „low-poly, stylised”, czyli wprost to, czego zakazuje `docs/06`. Zapytania o krawężniki, krzewy i trawę jako modele: 0 wyników.

## Przydatne pozycje (wszystkie darmowe dziś, licencja do potwierdzenia przy pozyskaniu)

Fab, Quixel Megascans, licencja Fab Standard (poza publicznym repo):

| # | Pozycja | Do czego | Link |
|---|---|---|---|
| 1 | Street Curbs | krawężniki (FBX/glTF, 0,17 × 1,04 × 0,12 m) | https://www.fab.com/listings/30f9c32a-7ddb-44ce-8ac1-5c878dd752a2 |
| 2 | Modular Curb | krawężniki modułowe | https://www.fab.com/listings/5debfb8f-59d4-456f-b074-6ead0ce343aa |
| 3 | Round Manhole Cover | studzienka (dekal, 1 × 1 m, 8192 px/m) | https://www.fab.com/listings/2e07c844-34c4-4e4b-acee-b7869a66494f |
| 4 | Metal Manhole Cover | studzienka | https://www.fab.com/listings/11eb03b4-09a9-475a-9721-1a4cc09b4839 |
| 5 | Round Drain Cover | wpust deszczowy | https://www.fab.com/listings/16f36535-a188-4989-8d1c-5bb790290378 |
| 6 | Square Rusty Drain | kratka ściekowa | https://www.fab.com/listings/2ae59500-f274-4ca6-9684-692a6957af53 |
| 7 | Urban Trash | śmieci uliczne | https://www.fab.com/listings/4eb4b87c-92bf-495a-b68a-5877fc07094f |
| 8 | Trash Bag Pack | worki na śmieci | https://www.fab.com/listings/e735f250-bc37-42bc-9828-0af395974b77 |
| 9 | Trash Can | kosz | https://www.fab.com/listings/35267674-3634-4fd2-bca2-423fbc7da4b3 |
| 10 | Grass Clumps | kępy trawy | https://www.fab.com/listings/d22b2fc3-9389-4d39-894c-5369a7e49ddf |
| 11 | Wild Grass | trawa nieskoszona (pobocza) | https://www.fab.com/listings/5848d16a-f6ab-45a7-b69f-fe21dcbe4669 |
| 12 | Boxwood | krzew (bukszpan) | https://www.fab.com/listings/ae90090d-cafb-4431-a74f-8cded15f93e1 |
| 13 | Elderberry | krzew (bez czarny) | https://www.fab.com/listings/d72dd7bb-d514-4a14-8b4b-3333c99057fb |
| 14 | Silver Birch Bark | kora brzozy do własnych drzew | https://www.fab.com/listings/eb28e8b4-3198-4cf3-a42b-b3e12b612d06 |
| 15 | Birch Tree Trunk | pień brzozy | https://www.fab.com/listings/a2289955-a389-4fdb-a17b-b27c4146b03d |
| 16 | Pine Bark | kora sosny do własnych drzew | https://www.fab.com/listings/5f6f6a17-3b21-470a-b74b-fbbf80c6dc11 |
| 17 | Linden Branch | gałąź lipy (atlas liści do własnych drzew) | https://www.fab.com/listings/d8c3a5b3-7212-45b7-93b2-6c630333ec13 |
| 18 | Granite Rock | kamień polny | https://www.fab.com/listings/01d40602-eb64-448b-af63-a7896924280a |
| 19 | Small Granite Rock | drobne kamienie | https://www.fab.com/listings/d4de5337-7536-41df-9706-2825dc0a9dad |

Całych drzew (sosna, lipa, brzoza) w formacie dla Unity nie ma: są tylko Megaplants (Baltic Pine https://www.fab.com/listings/a2b04e81-5075-479f-a9d2-4940022f330a, Silver Birch https://www.fab.com/listings/94262633-61ed-4f4b-993e-dbc24af3e6ba; Unreal i USD). Drzewa zostają w naszych generatorach, z korą i gałęziami ze skanów.

Fab, słupki od wystawców (wynik wyszukiwania z filtrem `licenses=cc-by`; karta nie pokazuje licencji bez logowania, więc CC BY jest `UNVERIFIED`):

| # | Pozycja | Wystawca | Link |
|---|---|---|---|
| 20 | Bollard scan No. 1 (OBJ/glTF) | 3Dystopia | https://www.fab.com/listings/61af600f-4358-4571-a937-8ddccd03dd48 |
| 21 | Bollard coated with small stones | matousekfoto | https://www.fab.com/listings/fcf52dd8-45ed-4a28-afe2-927168bccdd3 |
| 22 | Rounded corner bollard | Axonite | https://www.fab.com/listings/b595d70a-cf45-4ef3-a6bd-9933ec18b3d6 |

Patch (identyfikatory z `GET https://patch.gg/api/v1/assets/search`; wszystkie CC0-1.0 i wszystkie dostępne już bezpośrednio z Poly Haven / ambientCG w ramach D40):

| # | Identyfikator | Do czego |
|---|---|---|
| 23 | `polyhaven:water_manhole_cover` | studzienka (model) |
| 24 | `ambientcg:ManholeCover001` … `010` | studzienki (dekale) |
| 25 | `polyhaven:metal_trash_can`, `polyhaven:trashbag` | kosz, worek |
| 26 | `polyhaven:rock_07`, `polyhaven:rock_09`, `polyhaven:boulder_01` | kamienie (12–66 tys. trójkątów) |
| 27 | `polyhaven:pine_sapling_small`, `polyhaven:fir_sapling` | młode iglaki (ok. 0,4 mln trójkątów, wymagają LOD) |
| 28 | `polyhaven:tree_stump_01`, `polyhaven:pine_roots` | pniaki, korzenie |

## Rekomendacja dla D40

Rozszerzyć D40 o Fab, nie rozszerzać o Patch. Proponowana treść (D45):

1. **Dopuszczone:** pozycje Quixel Megascans z Fab na licencji Fab Standard oraz pozycje Fab z licencją CC BY 4.0 potwierdzoną na karcie po zalogowaniu. Megaplants i pozycje innych wystawców na Fab Standard: nie.
2. **Pozyskanie:** tylko właściciel, na swoim koncie Epic, wyłącznie przez Fab (nigdy Bridge). Dla każdej pozycji zrzut karty z licencją i datą do `Data/raw/fab/<id>/`.
3. **Poza publicznym repo (Fab Standard):** pliki źródłowe w `Data/raw/fab/` (już poza gitem), wyniki importu w `game/Assets/_Generated/` (poza gitem, ADR 0011) albo w prywatnym repo/LFS. W publicznym repo tylko manifest (`Data/SourceManifests/fab-*.json`: URL, data, SHA256, licencja) i wpis w `docs/LICENSES.md`. Test w CI lub `doctor.ps1`: żaden plik z manifestu Fab nie jest śledzony przez git.
4. **Skutek dla odtwarzalności (zasada 7):** build z czystego klonu publicznego repo nie będzie kompletny bez prywatnych plików. Wymaga ADR i decyzji właściciela, czy to akceptuje.
5. **CC BY:** atrybucja w grze i w `docs/LICENSES.md`; pliki mogą być w repo.
6. **Bez marek:** odrzucać skany z logo, napisami producentów, tablicami.
7. **Przed wydaniem w sklepie:** przeczytać pełny Fab EULA po zalogowaniu i dopisać dokładne brzmienie punktów oznaczonych tu `UNVERIFIED` (`LEGAL_REVIEW_REQUIRED`).
8. **Patch:** bez zmian w D40. Można używać jako wyszukiwarki, a pliki brać ze źródła (Poly Haven, ambientCG).

Pytanie do właściciela: czy zakłada (lub ma) konto Epic i zgadza się na punkt 4?

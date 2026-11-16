# Światła drogowe — jednoczesność i kwantyzacja, runda 21

2026-11-16. 0fotografii. Cztery wiersze warunków/interpretacji; brak zmian bazowych24norm i wcześniejszego HR16. Odczytano istniejący pełny R48Rev12, wydrukowaną s32 oraz pełny dwustronicowy projekt UN GRE2024/5. Stronę R48 z punktami i obie strony projektu obejrzano również jako lokalne bitmapy pozaGit.

## R48: zakres sumowania w snapshotcie2014

SOURCED [R48Rev12,16.10.2014, pkt6.1.9.1–.2,s32]: limit430000cd odpowiada wartości odniesienia100 dla zespołu reflektorów drogowych, **które mogą być włączone jednocześnie**. Wprost użyto możliwości jednoczesnego załączenia, a nie wyłącznie chwilowego stanuON. Punkt6.1.9.2 każe uzyskać tę wielkość przez dodanie indywidualnych oznaczeń odniesienia; reflektorom oznaczonym dosłownieR lubCR przyznaje referencję10. To szczególny zapis o starych oznaczeniach reflektorów, nie interpretacja R1 tylnej lampy ani dowolnego symboluR z klosza.

INFERENCE [zakres logiczny pkt6.1.9.1–.2]: dla generatora/konfiguracji instalacji badać dopuszczalne zbiory reflektorów mogących świecić razem. Wyłączenie lampki w jednym momencie samo nie usuwa jej z możliwej kombinacji. Nie należy sumować całego magazynu opcjonalnych części, ale rzeczywiste możliwości równoczesnego załączenia wymagają potwierdzenia układu połączeń/sterowania; nie udokumentowano tutaj instalacji konkretnego Actrosa czyVolvo.

Wersja: dokument16.10.2014, Rev12 obejmująca serię06 doSupplement4 z09.10.2014; katalogURL2015 nie jest datą dokumentu. Lokalny istniejący `research/gptpro/p4-truck-regulations/files/P4-001.pdf`, SHA25620300c933bfbd4557ed30245fe4365a0e8808c3d5014e66168fda23a6ec918dc. Pochodzenie opisane wcześniej w01/regulation-evidence.json. Oryginalny adres UNECE w norms.csv; bez nowych mirrorów i bez deklaracji aktualności prawnej2026.

## Odczytany projekt2024 — nie dowód przyjęcia

SOURCED [ECE/TRANS/WP.29/GRE/2024/5,06.02.2024,s1]: eksperciGTB przedstawiają propozycję suplementu do serii09 R48 na90sesjęGRE,29.04–03.05.2024. **PROPOSAL_NOT_ADOPTION_PROOF.** Nie ustalono uchwały przyjęcia, tekstu opublikowanego po przyjęciu, daty wejścia w życie, łańcucha poprawek ani stanu prawnego2026.

SOURCED [s2,I.Proposal, projektowana zmiana6.1.9.1; własny ogląd bitmapy]: pogrubiony nowy fragment przenosi podmiot na wartość odniesienia odpowiadającą sumarycznej maksymalnej światłości. Przekreślony jest fragment od430000cd do sformułowania wiążącego go z referencją. Po usunięciu skreśleń proponowane zdanie pozostawia limit **100 dla wartości odniesienia**, nadal dla reflektorów mogących być załączone jednocześnie. Nie odczytano tego jako usunięcia limitu100 ani jako obowiązującej zmiany normy2014.

SOURCED [s2,II.Justification,pkt1–2]: autorzy uzasadniają projekt nierównymi odstępami pomiędzy dozwolonymi oznaczeniami odniesienia i zaokrąglaniem do najbliższej określonej wartości. Według uzasadnienia błędy zaokrągleń mogą pozwolić, aby suma rzeczywistych maksimów przekroczyła430000cd, i dlatego zaproponowano rezygnację z podwójnego wymagania. To opis argumentacji autorów2024, nie nowy pomiar lamp i nie samodzielne potwierdzenie pełnej treści dowolnego wydaniaR149.

## Etykiety27.5 i30

SOURCED [wcześniej pełnie odczytany R14913.01.2020,5.1.3.6; HR16-01/02]: iloraz maksimum światłości przez4300 podlega zaokrągleniu do dyskretnej listy oznaczeń. INFERENCE [ta operacja]: odczyt27.5 lub30 nie odtwarza dokładnego maksimumcd. Mnożenie znaku przez4300 dawałoby nominalną wartość algebraiczną, nie odwrócony pomiar. Nie wyznaczono przedziałów odwrotnych, reguły remisu, mocyW, chwilowej jasności w grze ani rzeczywistego maksimum fizycznej części. Projekt2024 wyjaśnia praktyczny problem sumowania, lecz nie przypisuje starego DCR Actrosa/Volvo do konkretnej homologacjiR149. Nie zmieniono ustaleńHR16.

## Ślad źródeł

Pierwsze pełne otwarcie projektu przez web dało2strony/44linie; screenshot web zakończył sięTimeoutError. Następnie jeden zwykły download publicznego dokumentu UN dał prawidłowyPDF101570B, SHA2564539ee801a40662ce2e8c15d173b436ea3e2aa58743579039d8d443df1ac3c10. Nie było403 ani CAPTCHA i nie zmieniano hosta. SurowyPDF, ekstrakty i renderowane strony wyłącznie w `C:\Users\matma\Documents\Claude\kamion\Data\raw\refs\codex-s21\01-lampy\highbeam-simultaneous-round21`; doGit trafiają tylko parafrazy/CSV/JSON. Poppler zgłosił brak fontówSymbol/ArialUnicode; istotne liczby, zwykły tekst, pogrubienia i skreślenia na obejrzanych bitmapach czytelne. Bez Chrome, Commons, kodu gry i git.

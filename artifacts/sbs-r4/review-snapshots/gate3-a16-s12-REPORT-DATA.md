# gate3 A16 s12 - REPORT-DATA (build-qa, DONE 2026-11-12 ~15:30)

APK: artifacts/apk/kamion-0.1.0-11db0552fd.apk (205,0 MB, czysty, sha256 fae6e4a71722922c13424717d80bbb2731ab1009c12551e9ee5f7fa999faa886), z run-f.
APK run-e kamion-0.1.0-87dbeb392f-dirty.apk - NIE mierzony (dirty).
Telefon SM-A165F RFGL34SJYDZ, Low, 30 fps, autopilot 30 km/h, odblokowany caly pomiar. PHONE_RUN 14:19 -> usuniety po B.
Ostrzezenie skryptu: HEAD (863a25b9/19aa4c58) != 11db0552fd (commity docs lidera w trakcie); pomiar dotyczy 11db0552fd.

| | G3-A s12 | G3-A s10 | G3-B s12 | G3-B s10 |
|---|---|---|---|---|
| wynik | gate3/20261112-142003 | gate3/20261111-154331 | gate3/20261112-145646 | gate3/20261111-154538 |
| valid / klatek | True / 1747 | True / 2010 | True / 2049 | True / 2292 |
| fps sr. | 29,62 | 29,72 | 29,71 | 29,88 |
| p50/p95/p99/max ms | 33,33/33,51/50,01/83,3 | 33,33/33,49/50,0/83,3 | 33,33/33,47/49,995/50,2 | 33,33/33,46/33,69/50,2 |
| >33 / >50 ms | 285 / 20 | 275 / 20 | 254 / 19 | 255 / 8 |
| GPU p50/p95/p99 | 32,32/35,54/36,65 | 29,86/31,80/33,73 | 31,77/35,17/37,60 | 29,49/33,29/37,43 |
| CPU main p50/p95 | 23,16/31,83 | 22,75/30,13 | 21,21/28,93 | 21,54/28,59 |
| PSS MB | 879,9 | 835,3 | 909,5 | 826,3 |
| temp. przed/po C, thermal | 26,3/26,5, 0 | 25,5/25,6, 0 | 29,2/29,2, 0 | 25,7/25,8, 0 |
| budzet p95<=34/p99<=40/PSS<=1000 | OK/FAIL/OK | OK/FAIL/OK | OK/FAIL/OK | OK/OK/OK |
| kamery telefon | 57/57 | 0 | 46/46 | 0 |

Dowody: artifacts/gate3/<ts>/RFGL34SJYDZ/{gate3-result.json, drive/frametimes.csv, logcat-run.txt, cam/*.png}; logi artifacts/gate3-a16-s12/run-A.log, run-B.log; suspiciousLines 0.

Wnioski: GPU p50 +2,3-2,5 ms, p95 +1,9-3,7 ms -> GPU p95 35,2-35,5 ms > 33,3 ms (A16 Low teraz GPU-bound). G3-B p99 33,7 -> 50,0 (FAIL). PSS +45/+83 MB (<1000). Termika bez zmian. Przyczyna per-shader NIE zmierzona.
Werdykt: budzet wydajnosci POGORSZONY vs s10; A16 Low FAIL p99 w A i B.

# STATUS — M60 (cloud p17-dusk-lighting)

- 2026-11-14 krok 1: `sun.py` (NOAA/Meeus, selftest OK, tabela zmierzchu), `fetch.py`, `.gitignore`.
  Zebrane w scratch (jeszcze nie w manifeście): TED API — przetargi LED ZDM Białystok 2023–2026 (Andersa, Maczka, Al. 1000-lecia w 281034-2023),
  rozstaw słupów z ortofoto GUGiK (Andersa ~41,6 m n=6; Maczka ~40,4 n=6; Tysiąclecia S ~34,8 n=7; Sokólska ~32 n=5), klasy M (źródła wtórne),
  niebo: 4,3 lx @ −6° (Fotios 2024/Muneer), zenit V (Patat 2006), okna: 50 % maks. / 6 cd/m² (Novák 2025).
- NASTĘPNY KROK: kadry Commons (geosearch po trasie + osiedla; filtr elewacji Słońca `python3 sun.py elev <ISO>`), obejrzeć, policzyć okna;
  potem manifest.csv + README + audit.

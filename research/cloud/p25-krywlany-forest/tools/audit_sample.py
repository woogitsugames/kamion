# Odtworzenie próby samokontroli: python3 tools/audit_sample.py  (z katalogu zadania)
import csv,random
rows=list(csv.DictReader(open('manifest.csv',encoding='utf-8')))
idx=sorted(random.Random(20261114).sample(range(len(rows)),-(-len(rows)*20//100)))
print(len(rows),len(idx)); print([rows[i]['id'] for i in idx])

"""splice.py <target.py> <start marker> <end marker> <new source file>: replace target[start:end) by the file."""
import sys
p, a, b, f = sys.argv[1:5]
s = open(p, encoding='utf-8').read()
i, j = s.index(a), s.index(b)
assert i < j
open(p, 'w', encoding='utf-8').write(s[:i] + open(f, encoding='utf-8').read() + s[j:])
print("spliced", j - i, "chars ->", len(open(f, encoding='utf-8').read()))

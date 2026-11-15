import re,sys
for f in sys.argv[1:]:
    d={}
    for l in open(f,encoding='utf-8'):
        m=re.match(r'(\S+): objects=\d+ drawsEst=(\d+) .*trisK=(\d+)',l)
        if m: d[m[1]]=(int(m[2]),int(m[3]))
    for pre,lab in (('route-','route'),('seam_','seam'),('edge-','edge'),('',None)):
        v=[x for k,x in d.items() if k.startswith(pre)] if lab else None
        if v: print(f, lab, len(v), 'draws %d-%d tris %d-%dk'%(min(a for a,_ in v),max(a for a,_ in v),min(b for _,b in v),max(b for _,b in v)))
    print('  other world cams:',{k:v for k,v in d.items() if not re.match(r'(route-|seam_|edge-|cab-|truck|trailer|lamp|plate|chase)',k)})

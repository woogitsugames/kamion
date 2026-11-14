# Biblioteka: wczytanie NMPT (arkusze ASC 0,5 m, lot 2023-09-15), NMT (kafle WCS 1 m), NMPT WCS (1 m, lot 2025-04-18) i próbkowanie CHM = NMPT - NMT
import numpy as np, glob, os, re, tifffile
class Sheet:
    def __init__(s,fn):
        npy=fn+'.npy'
        with open(fn,'rb') as f:
            hdr={}
            pos=0
            while True:
                pos=f.tell(); l=f.readline().split()
                if l[0].decode().lower() in('ncols','nrows','xllcenter','yllcenter','xllcorner','yllcorner','cellsize','nodata_value'): hdr[l[0].decode().lower()]=float(l[1])
                else: break
            if os.path.exists(npy): a=np.load(npy,mmap_mode='r')
            else:
                f.seek(pos); a=np.fromstring(f.read(),sep=' ',dtype=np.float32).reshape(int(hdr['nrows']),int(hdr['ncols'])); np.save(npy,a)
        s.a=a; s.nr=int(hdr['nrows']); s.nc=int(hdr['ncols']); s.cs=hdr['cellsize']
        s.x0=hdr.get('xllcenter',hdr.get('xllcorner',0)+s.cs/2 if 'xllcorner' in hdr else None); s.y0=hdr.get('yllcenter',hdr.get('yllcorner',0)+s.cs/2 if 'yllcorner' in hdr else None)
        s.nd=hdr.get('nodata_value',-9999)
    def sample(s,E,N):
        c=np.rint((E-s.x0)/s.cs).astype(int); r=s.nr-1-np.rint((N-s.y0)/s.cs).astype(int)
        ok=(c>=0)&(c<s.nc)&(r>=0)&(r<s.nr); out=np.full(E.shape,np.nan,dtype=np.float32)
        v=np.asarray(s.a[r[ok],c[ok]]); v=np.where(v==s.nd,np.nan,v); out[ok]=v; return out
class Tiles:
    """kafle 250 m, 1 m; dsm_*.asc (multipart WCS) lub dtm_*.tif"""
    def __init__(s,pattern,kind,S=250):
        s.t={}; s.S=S
        for fn in glob.glob(pattern):
            x,y=map(int,re.findall(r'_(\d+)_(\d+)\.',fn)[0])
            try:
                if kind=='tif': a=tifffile.imread(fn).astype(np.float32)
                else:
                    b=open(fn,'rb').read().decode('latin1'); body=b.split('cellsize')[1].split('\n',1)[1].split('--wcs')[0]
                    a=np.array(body.split(),dtype=np.float32).reshape(S,S)
            except Exception as e: print('bad',fn,e); continue
            if a.shape!=(S,S): print('shape',fn,a.shape); continue
            a=np.where(a<-1000,np.nan,a); s.t[(x,y)]=a
    def sample(s,E,N):
        out=np.full(E.shape,np.nan,dtype=np.float32)
        tx=(np.floor(E/s.S)*s.S).astype(int); ty=(np.floor(N/s.S)*s.S).astype(int)
        for key in set(zip(tx.ravel().tolist(),ty.ravel().tolist())):
            if key not in s.t: continue
            m=(tx==key[0])&(ty==key[1]); a=s.t[key]
            c=np.clip(np.floor(E[m]-key[0]).astype(int),0,s.S-1); r=np.clip(s.S-1-np.floor(N[m]-key[1]).astype(int),0,s.S-1)
            out[m]=a[r,c]
        return out
class CHM:
    def __init__(s,sheetdir='sheets',demdir='dem'):
        s.sheets=[Sheet(f) for f in sorted(glob.glob(sheetdir+'/*.asc'))]
        s.dtm=Tiles(demdir+'/dtm_*.tif','tif'); s.dsm25=Tiles(demdir+'/dsm_*.asc','asc')
    def dsm23(s,E,N):
        out=np.full(E.shape,np.nan,dtype=np.float32)
        for sh in s.sheets:
            m=np.isnan(out)
            if not m.any(): break
            out[m]=sh.sample(E[m],N[m])
        return out
    def on(s,E,N):  # CHM ulistniony (2023-09-15)
        return s.dsm23(E,N)-s.dtm.sample(E,N)
    def off(s,E,N): # CHM bezlistny (2025-04-18)
        return s.dsm25.sample(E,N)-s.dtm.sample(E,N)

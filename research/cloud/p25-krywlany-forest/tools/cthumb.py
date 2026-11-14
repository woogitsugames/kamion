import json,os,time,subprocess,urllib.request,urllib.error,urllib.parse,sys
UA="kamion-research/1.0 (open-data reference collection)"
want=json.load(open('commons_want.json'))
os.makedirs('thumb',exist_ok=True)
def turl(u,w=1280):
    # .../commons/a/ab/Name.jpg -> .../commons/thumb/a/ab/Name.jpg/1280px-Name.jpg
    base,name=u.rsplit('/',1)
    return base.replace('/commons/','/commons/thumb/')+'/'+name+f'/{w}px-'+name
for r in want:
    fn=f"thumb/C{r['pageid']}.jpg"
    if os.path.exists(fn): continue
    u=turl(r['url'])
    for t in range(40):
        try:
            b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=90).read()
            open(fn,'wb').write(b); subprocess.run(['convert',fn,'-resize','960x960>',f"view/C{r['pageid']}.jpg"]); print('ok',r['pageid'],flush=True); break
        except urllib.error.HTTPError as e:
            ra=float(e.headers.get('retry-after') or 10)
            if e.code!=429: print('HTTP',e.code,u,flush=True); break
            time.sleep(min(ra,60)+2)
        except Exception as e: print(e,flush=True); time.sleep(5)
    time.sleep(3)
print('done')

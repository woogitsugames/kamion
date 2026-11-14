import json,urllib.request,urllib.parse,urllib.error,time,sys
UA="kamion-research/1.0 (open-data reference collection)"
def get(u,tries=60,binary=False):
    for t in range(tries):
        try:
            b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=120).read()
            return b
        except urllib.error.HTTPError as e:
            if e.code==429:
                ra=e.headers.get('retry-after'); time.sleep(min(60,(float(ra) if ra else 5)+1+t*0.5)); continue
            print('HTTP',e.code,u[:120],flush=True); return None
        except Exception as e:
            print(e,flush=True); time.sleep(5)
    return None
def api(p):
    p['format']='json'
    b=get("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(p))
    return json.loads(b) if b else None

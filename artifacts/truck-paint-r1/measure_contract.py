"""D30/D35 follow the existing r7 method; raw-native counterparts and causal controls remain separate."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,sys
root=Path(__file__).resolve().parent
BOX={"glass":(380,160,460,200),"corner":(478,215,495,255),"door":(514,218,533,252),"roof":(440,120,520,134)}
def get(stage,cond):return Image.open(root/stage/cond/"truck-34.png").convert("RGB")
def numbers(y):return {"p50":float(np.median(y)),"sd":float(y.std()),"p99_p50":float(np.percentile(y,99)-np.median(y)),"clip250":float((y>=250/255*100).mean())}
def stats(im,native=False):
 k=im.width/1024 if native else 1
 if not native:im=im.resize((1024,round(im.height*1024/im.width)),Image.Resampling.LANCZOS)
 Y=np.asarray(im,dtype=float)@np.array([.2126,.7152,.0722])/255*100
 out={}
 for name,box in BOX.items():
  x0,y0,x1,y1=[round(v*k) for v in box];a=Y[y0:y1,x0:x1];out[name]=numbers(a)
  if name=="door":out[name]["vertical_profile_range"]=float(np.ptp(a.mean(axis=1)))
 return out
for stage in sys.argv[1:] or ["before"]:
 result={}
 for cond in sorted((root/stage).iterdir()):
  if not cond.is_dir() or not(cond/"truck-34.png").exists():continue
  im=get(stage,cond.name);legacy=stats(im);native=stats(im,True)
  row={"legacy1024":legacy,"native":native,"regions1024":BOX,"method":"r7 measure.py copied method, native no-resize counterpart; no physical albedo claim"}
  for reference in ["before-near-pane-off","before-no-pane-fixed"]:
   ref=root/reference/cond.name/"truck-34.png"
   if ref.exists():
    d=stats(Image.open(ref).convert("RGB"))["glass"]["sd"]
    row[reference]={"sd":d,"D44_ov_ratio":legacy["glass"]["sd"]/max(d,1e-9)}
  row["gates"]={"D30_door_4_to_10":4<=legacy["door"]["vertical_profile_range"]<=10,"D35_roof":legacy["roof"]["p99_p50"] >= (10 if cond.name.startswith("High") else 6),"D34_glass_23_to_45":23<=legacy["glass"]["p50"]<=45,"D44_sunny_sd8":legacy["glass"]["sd"]>=8}
  result[cond.name]=row
  print(stage,cond.name,"glassp50/sd",round(legacy["glass"]["p50"],2),round(legacy["glass"]["sd"],2),"doorRange",round(legacy["door"]["vertical_profile_range"],2),"roof99-50",round(legacy["roof"]["p99_p50"],2))
 (root/(stage+"-contract-metrics.json")).write_text(json.dumps(result,indent=2)+"\n")
# Authoritative region placement proof, inspection output <=960.
im=get("before","High-overcast");im=im.resize((960,round(im.height*960/im.width)),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im)
for name,box in BOX.items():
 b=tuple(round(v*960/1024) for v in box);d.rectangle(b,outline="magenta",width=1);d.text((b[0],b[1]-12),name,fill="red")
im.save(root/"owner-roi-placement.jpg",quality=94)

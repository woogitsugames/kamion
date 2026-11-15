from PIL import Image
import numpy as np
from scipy.signal import correlate2d
p='research/dk65-knyszyn-refs/files/orto/junctions/'
a=np.asarray(Image.open(p+'J_rynek_W_north.jpg').convert('L').resize((350,350)),dtype=float)
b=np.asarray(Image.open(p+'J_rynek_knyszyn_north.jpg').convert('L').resize((300,300)),dtype=float)
t=a[75:200,260:345]; t=t-t.mean()
c=correlate2d(b,t,mode='valid'); y,x=np.unravel_index(c.argmax(),c.shape)
print('west window origin 1040,300 corresponds east',x*4,y*4,'peak',c.max())

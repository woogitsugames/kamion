import math
P = {'a': (53.158525, 23.153206), 'b': (53.157895, 23.153876), 'c': (53.15226, 23.166929), 'd': (53.159032, 23.151625)}


def dist(a, b):
    la1, lo1 = a
    la2, lo2 = b
    x = (lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2)) * 111320
    y = (la2 - la1) * 110574
    return math.hypot(x, y), math.degrees(math.atan2(x, y)) % 360


def near(la, lo):
    return ' '.join(f'{k}:{dist((la, lo), v)[0]:.0f}m@{dist((la, lo), v)[1]:.0f}' for k, v in P.items())

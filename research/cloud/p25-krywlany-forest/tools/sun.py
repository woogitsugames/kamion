import math,datetime,sys
def sun(lat,lon,dt_utc):
    # NOAA uproszczony
    d=(dt_utc-datetime.datetime(2000,1,1,12)).total_seconds()/86400
    g=math.radians((357.529+0.98560028*d)%360); q=(280.459+0.98564736*d)%360
    L=math.radians((q+1.915*math.sin(g)+0.020*math.sin(2*g))%360)
    e=math.radians(23.439-0.00000036*d)
    ra=math.atan2(math.cos(e)*math.sin(L),math.cos(L)); dec=math.asin(math.sin(e)*math.sin(L))
    gmst=(18.697374558+24.06570982441908*d)%24
    ha=math.radians((gmst*15+lon)%360)-ra
    la=math.radians(lat)
    el=math.asin(math.sin(la)*math.sin(dec)+math.cos(la)*math.cos(dec)*math.cos(ha))
    az=math.atan2(-math.sin(ha),math.tan(dec)*math.cos(la)-math.sin(la)*math.cos(ha))
    return round(math.degrees(az)%360),round(math.degrees(el))
for name,ts in [('P11-056','2023-08-14 15:57'),('D303 17:45','2023-08-14 15:45'),('17:42','2023-08-14 15:42'),('CIOL 2020 08:14','2020-07-26 06:14'),('MICK 2024 13:57','2024-06-23 11:57'),('2022-03-12 16:31','2022-03-12 15:31'),('pano 2019-09-01 12:10','2019-09-01 10:10'),('pano 2019-08-15 17:40','2019-08-15 15:40')]:
    print(name,sun(53.1,23.17,datetime.datetime.strptime(ts,'%Y-%m-%d %H:%M')))

[out:json][timeout:90][bbox:53.115,23.08,53.20,23.24];
(
 way["highway"]["name"~"^(Generała Władysława Andersa|Aleja Tysiąclecia Państwa Polskiego|Generała Stanisława Maczka|Sokólska|Włodzimierza Wysockiego|Kombatantów)$"];
 way["highway"]["junction"="roundabout"]["name"~"Putry"];
);
out geom tags;
node["highway"="street_lamp"];
out body;

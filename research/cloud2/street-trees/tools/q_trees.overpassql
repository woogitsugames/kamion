[out:json][timeout:180];
area["boundary"="administrative"]["admin_level"="8"]["name"="Białystok"]->.a;
(
  node["natural"="tree"](area.a);
  way["natural"="tree_row"](area.a);
  way["barrier"="hedge"](area.a);
);
out body geom;

[out:json][timeout:180][bbox:53.08,23.05,53.20,23.28];
(
  node["highway"="street_lamp"];
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|service|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"];
);
out geom tags;

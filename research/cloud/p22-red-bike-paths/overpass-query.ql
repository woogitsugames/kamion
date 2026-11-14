[out:json][timeout:180];
// M65: region C (bialystok-industrial-c) i Dojlidy (bialystok-dojlidy) — obwiednie WGS84 kafli EPSG:2180 (S,W,N,E)
(
  way["highway"](53.14883,23.14371,53.16827,23.17605);
  way["highway"](53.09265,23.16891,53.11210,23.20123);
  node["highway"~"^(crossing|traffic_signals)$"](53.14883,23.14371,53.16827,23.17605);
  node["highway"~"^(crossing|traffic_signals)$"](53.09265,23.16891,53.11210,23.20123);
  node["crossing"](53.14883,23.14371,53.16827,23.17605);
  node["crossing"](53.09265,23.16891,53.11210,23.20123);
  node["barrier"="kerb"](53.14883,23.14371,53.16827,23.17605);
  node["barrier"="kerb"](53.09265,23.16891,53.11210,23.20123);
);
out body geom qt;
